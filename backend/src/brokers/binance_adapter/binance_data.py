"""
Binance Data - Backtrader-compatible OHLCV data feed using python-binance.

Provides real-time data feed for Backtrader strategies.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional

import backtrader as bt

from .common import TIMEFRAME_SECONDS, map_to_bt_timeframe
from .binance_store import BinanceStore

logger = logging.getLogger(__name__)


class BinanceData(bt.DataBase):
    """
    Backtrader data feed for Binance OHLCV data.

    Features:
    - Forming bar filter (skips incomplete bars)
    - Historical backfill on start
    - Paper trading simulation
    """

    params = (
        ('timeframe', None),
        ('ccxt_timeframe', '1m'),
        ('compression', 1),
        ('backfill_start', None),
        ('backfill', False),
        ('limit', 50),
        ('pause', 1.0),
        ('debug', False),
    )

    def __init__(self, store: BinanceStore, symbol: str, **kwargs):
        self.store = store
        self._symbol = symbol

        # Handle timeframe
        ccxt_tf = kwargs.pop('timeframe', None) or kwargs.pop('ccxt_timeframe', None)
        self.ccxt_timeframe = ccxt_tf or self.params.ccxt_timeframe

        self._last_bar_time: Optional[datetime] = None
        self._hist_buffer: List[list] = []
        self._consecutive_errors = 0

        super().__init__(**kwargs)

        # Validate timeframe
        if self.ccxt_timeframe not in TIMEFRAME_SECONDS:
            raise ValueError(f"Unsupported timeframe: '{self.ccxt_timeframe}'")

        # Map to Backtrader units
        self._timeframe, self._compression = map_to_bt_timeframe(self.ccxt_timeframe)
        self.params.timeframe = self._timeframe
        self.params.compression = self._compression

        self._tf_seconds = TIMEFRAME_SECONDS[self.ccxt_timeframe]
        self._tf_ms = self._tf_seconds * 1000

        logger.info(f"BinanceData initialized: {symbol} [{self.ccxt_timeframe}]")

    # ──────────────────────────── Backtrader interface ────────────────────────────

    def _load(self) -> bool:
        """Load next bar into lines."""
        # Serve from buffer first
        if self._hist_buffer:
            return self._consume_bar()

        # Live wait-loop
        while self.store.is_running:
            try:
                new_bars = self._fetch_bars()
                if new_bars:
                    self._hist_buffer.extend(new_bars)
                    self._consecutive_errors = 0
                    return self._consume_bar()

                time.sleep(self.params.pause)

            except Exception as e:
                self._consecutive_errors += 1
                if self.params.debug or self._consecutive_errors % 10 == 0:
                    logger.error(f"Fetch error ({self._symbol}): {e}")

                if self._consecutive_errors >= 30:
                    logger.error(f"Too many errors, stopping data feed")
                    return False

                time.sleep(min(self.params.pause * self._consecutive_errors, 30))

        logger.info(f"Store stopped, ending data feed")
        return False

    def start(self) -> None:
        super().start()
        if self.params.backfill:
            self._perform_backfill()

    def islive(self) -> bool:
        return True

    def haslivedata(self) -> bool:
        return self.store.is_running

    # ──────────────────────────── data fetching ────────────────────────────

    def _fetch_bars(self) -> List[list]:
        """Fetch OHLCV bars from Binance, filtering forming bars."""
        if self._last_bar_time:
            since = int(self._last_bar_time.timestamp() * 1000) + 1
        else:
            since = int(
                (datetime.utcnow() - timedelta(seconds=self._tf_seconds * 5)).timestamp() * 1000
            )

        try:
            ohlcv = self.store.fetch_ohlcv(
                symbol=self._symbol,
                interval=self.ccxt_timeframe,
                limit=self.params.limit,
                since_ms=since,
            )
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV: {e}")
            return []

        if not ohlcv:
            return []

        now_ms = int(datetime.utcnow().timestamp() * 1000)
        valid = []

        for bar in ohlcv:
            ts = bar[0]
            # Skip forming (incomplete) bars
            if ts + self._tf_ms > now_ms:
                continue
            # Skip duplicates
            bar_dt = datetime.utcfromtimestamp(ts / 1000)
            if self._last_bar_time and bar_dt <= self._last_bar_time:
                continue
            valid.append(bar)

        if self.params.debug and valid:
            logger.debug(f"Fetched {len(valid)} new bars for {self._symbol}")

        return valid

    def _consume_bar(self) -> bool:
        """Pop one bar from buffer and load into Backtrader lines."""
        if not self._hist_buffer:
            return False

        bar = self._hist_buffer.pop(0)
        logger.debug(f"Loaded bar: O={bar[1]:.2f} H={bar[2]:.2f} L={bar[3]:.2f} C={bar[4]:.2f}")

        dt_obj = datetime.utcfromtimestamp(bar[0] / 1000)

        self.lines.datetime[0] = bt.date2num(dt_obj)
        self.lines.open[0] = float(bar[1])
        self.lines.high[0] = float(bar[2])
        self.lines.low[0] = float(bar[3])
        self.lines.close[0] = float(bar[4])
        self.lines.volume[0] = float(bar[5])
        self.lines.openinterest[0] = 0

        self._last_bar_time = dt_obj
        return True

    def _perform_backfill(self) -> None:
        """Fetch historical data before live feed starts."""
        if not self.params.backfill_start:
            logger.warning(f"Backfill requested but no backfill_start set")
            return

        try:
            start_dt = self.params.backfill_start
            if isinstance(start_dt, str):
                start_dt = datetime.fromisoformat(start_dt)

            logger.info(f"Backfilling {self._symbol} from {start_dt}...")

            since = int(start_dt.timestamp() * 1000)
            now_ms = int(datetime.utcnow().timestamp() * 1000)

            if since > now_ms:
                since = now_ms - (100 * self._tf_ms)

            batch_size = 1000
            total = 0

            while since < now_ms:
                bars = self.store.fetch_ohlcv(
                    symbol=self._symbol,
                    interval=self.ccxt_timeframe,
                    limit=batch_size,
                    since_ms=since,
                )

                if not bars:
                    break

                closed = [b for b in bars if b[0] + self._tf_ms <= now_ms]

                if not closed:
                    break

                self._hist_buffer.extend(closed)
                total += len(closed)
                since = bars[-1][0] + 1

                time.sleep(0.1)

            logger.info(f"Backfill complete: {total} bars loaded for {self._symbol}")

        except Exception as e:
            logger.error(f"Backfill failed: {e}")

    def get_current_price(self) -> Optional[float]:
        """Get latest close price."""
        if self._last_bar_time and len(self) > 0:
            return self.lines.close[0]
        return None

