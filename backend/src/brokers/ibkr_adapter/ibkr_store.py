"""
IBKR Store wrapper for Backtrader.

This adapter keeps the same lifecycle as CCXTStore: start/stop the
underlying connection, create broker/data feeds, and hide env/config
plumbing needed for Interactive Brokers (Gateway/TWS).
"""

import logging
import os
from typing import Optional, Tuple

import backtrader as bt

logger = logging.getLogger(__name__)


class IBKRStoreError(Exception):
    """Raised when IBKR store cannot be initialized or used."""


def parse_timeframe(value: str) -> Tuple[bt.TimeFrame, int]:
    """
    Convert string timeframe to Backtrader (TimeFrame, compression).

    Supported values mirror config_loader.validate_timeframe: 1m/5m/15m/30m/1h/4h/1d.
    """
    normalized = value.lower()
    mapping = {
        "1m": (bt.TimeFrame.Minutes, 1),
        "5m": (bt.TimeFrame.Minutes, 5),
        "15m": (bt.TimeFrame.Minutes, 15),
        "30m": (bt.TimeFrame.Minutes, 30),
        "1h": (bt.TimeFrame.Hours, 1),
        "4h": (bt.TimeFrame.Hours, 4),
        "1d": (bt.TimeFrame.Days, 1),
    }

    if normalized not in mapping:
        raise ValueError(f"Unsupported timeframe '{value}' for IBKR data feed")

    return mapping[normalized]


class IBKRStore:
    """
    Thin wrapper around Backtrader's IBStore.

    The wrapper lets live_engine choose the correct adapter based on the
    exchange config without changing strategy code.
    """

    def __init__(
        self,
        mode: str = "paper",
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None,
        account: Optional[str] = None,
        connect_timeout: int = 15,
    ):
        self.mode = mode.lower()
        env_prefix = f"IBKR_{self.mode.upper()}"

        # Prefer explicit args, fallback to env, then sane defaults
        self.host = host or os.getenv(f"{env_prefix}_HOST", "127.0.0.1")
        default_port = 7497 if self.mode == "paper" else 7496
        self.port = int(port or os.getenv(f"{env_prefix}_PORT", default_port))
        self.client_id = int(client_id or os.getenv(f"{env_prefix}_CLIENT_ID", 1))
        self.account = account or os.getenv(f"{env_prefix}_ACCOUNT")
        self.connect_timeout = connect_timeout

        self._store: Optional[bt.stores.IBStore] = None
        logger.info(
            "Initialized IBKRStore mode=%s host=%s port=%s client_id=%s",
            self.mode,
            self.host,
            self.port,
            self.client_id,
        )

    def start(self) -> None:
        """Start IBKR store and establish connection to Gateway/TWS."""
        if self._store:
            logger.warning("IBKRStore already started")
            return

        try:
            self._store = bt.stores.IBStore(
                host=self.host,
                port=self.port,
                clientId=self.client_id,
                account=self.account,
                reconnect=True,
                timeout=self.connect_timeout,
            )
            logger.info("IBKRStore connected to %s:%s (clientId=%s)", self.host, self.port, self.client_id)
        except Exception as exc:
            logger.exception("Failed to start IBKRStore: %s", exc)
            raise IBKRStoreError(f"Failed to start IBKRStore: {exc}") from exc

    def stop(self) -> None:
        """Disconnect from IBKR."""
        if not self._store:
            return

        try:
            # IBStore exposes the connection on .conn; gracefully disconnect if available
            if hasattr(self._store, "conn") and self._store.conn is not None:
                self._store.conn.disconnect()
            logger.info("IBKRStore disconnected")
        finally:
            self._store = None

    def _ensure_started(self) -> bt.stores.IBStore:
        if not self._store:
            raise IBKRStoreError("IBKRStore not started. Call start() first.")
        return self._store

    def get_broker(self, initial_cash: float = 100000.0, commission: float = 0.001) -> bt.BrokerBase:
        """Return Backtrader broker bound to the IB store."""
        store = self._ensure_started()
        broker = store.getbroker()

        # In paper mode allow user-specified starting cash for a consistent experience
        if self.mode == "paper":
            broker.setcash(initial_cash)

        broker.setcommission(commission=commission)
        return broker

    def get_data(self, symbol: str, timeframe: str = "1m") -> bt.DataBase:
        """
        Create an IBKR data feed.

        Notes:
            - symbol must be a valid IBKR contract string (e.g., 'AAPL-STK-SMART-USD').
            - rtbar=True streams real-time bars; historical=False keeps the feed live-only.
        """
        store = self._ensure_started()
        tf, compression = parse_timeframe(timeframe)
        data = store.getdata(
            dataname=symbol,
            timeframe=tf,
            compression=compression,
            rtbar=True,
            historical=False,
            useRTH=True,
        )
        return data
