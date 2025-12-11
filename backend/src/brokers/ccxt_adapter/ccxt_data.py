"""
CCXT Data - Live OHLCV data feed from CCXT exchanges.

This module provides a Backtrader-compatible data feed that fetches
real-time OHLCV bars from cryptocurrency exchanges via CCXT.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import backtrader as bt

from .ccxt_store import CCXTStore

logger = logging.getLogger(__name__)


class CCXTData(bt.DataBase):
    """
    Live data feed that fetches OHLCV from CCXT exchange.

    This class:
    - Polls exchange for latest OHLCV bars
    - Provides real-time market data to Backtrader strategies
    - Handles timeframe conversion (1m, 5m, 1h, etc.)

    Attributes:
        store: CCXTStore instance
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: CCXT timeframe string ('1m', '5m', '15m', '1h', etc.)
    """

    params = (
        ('timeframe', '1m'),  # CCXT timeframe (string)
        ('compression', 1),  # Backtrader bar compression (minutes multiplier)
        ('backfill_start', None),  # Optional: fetch historical data from this date
        ('backfill', False),  # Whether to backfill historical data
    )

    # Timeframe conversion: CCXT -> seconds
    _TIMEFRAME_MAP = {
        '1m': 60,
        '5m': 300,
        '15m': 900,
        '30m': 1800,
        '1h': 3600,
        '4h': 14400,
        '1d': 86400,
    }

    def __init__(self, store: CCXTStore, symbol: str, **kwargs):
        """
        Initialize CCXT data feed.

        Args:
            store: CCXTStore instance
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            **kwargs: Additional parameters
        """
        self.store = store
        self.exchange = store.get_exchange()
        self.symbol = symbol

        # Keep the CCXT timeframe string separate from Backtrader timeframe
        self.ccxt_timeframe = kwargs.get('timeframe', self.params.timeframe)

        # Store symbol for broker access
        self._symbol = symbol

        # Last fetched bar timestamp
        self._last_bar_time: Optional[datetime] = None

        # Historical data buffer (for backfill)
        self._hist_buffer = []

        # Forward caller kwargs so Backtrader params (timeframe/backfill/etc.) are honored
        super().__init__(**kwargs)

        # Validate timeframe
        if self.ccxt_timeframe not in self._TIMEFRAME_MAP:
            raise ValueError(
                f"Unsupported timeframe: {self.ccxt_timeframe}. "
                f"Supported: {list(self._TIMEFRAME_MAP.keys())}"
            )

        # Map CCXT timeframe to Backtrader timeframe/compression to satisfy analyzers
        self._timeframe, self._compression = self._map_to_bt_timeframe(self.ccxt_timeframe)

        logger.info(
            f"Initialized CCXTData for {symbol} with timeframe {self.ccxt_timeframe}"
        )

    def _load(self) -> bool:
        """
        Fetch next OHLCV bar from exchange.

        Returns:
            True if new bar available, False otherwise
        """
        try:
            # If backfilling, return from buffer first
            if self._hist_buffer:
                return self._load_from_buffer()

            # Fetch latest bars from exchange
            since = self._get_since_timestamp()
            limit = 2  # Fetch current and previous bar

            ohlcv = self.store.run_coroutine(
                self.exchange.fetch_ohlcv(
                    symbol=self.symbol,
                    timeframe=self.ccxt_timeframe,
                    since=since,
                    limit=limit
                )
            )

            if not ohlcv:
                return False

            # Get the latest complete bar (exclude current incomplete bar)
            # OHLCV format: [timestamp, open, high, low, close, volume]
            latest_bar = ohlcv[-1] if len(ohlcv) == 1 else ohlcv[-2]

            bar_timestamp = datetime.fromtimestamp(latest_bar[0] / 1000)

            # Check if this is a new bar
            if self._last_bar_time and bar_timestamp <= self._last_bar_time:
                return False  # No new bar

            # Update lines with new bar data
            self.lines.datetime[0] = bt.date2num(bar_timestamp)
            self.lines.open[0] = latest_bar[1]
            self.lines.high[0] = latest_bar[2]
            self.lines.low[0] = latest_bar[3]
            self.lines.close[0] = latest_bar[4]
            self.lines.volume[0] = latest_bar[5]

            # No open interest for crypto spot
            self.lines.openinterest[0] = 0

            self._last_bar_time = bar_timestamp

            logger.debug(
                f"New bar: {self.symbol} {bar_timestamp} - "
                f"O={latest_bar[1]} H={latest_bar[2]} L={latest_bar[3]} "
                f"C={latest_bar[4]} V={latest_bar[5]}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {self.symbol}: {e}")
            return False

    def _load_from_buffer(self) -> bool:
        """
        Load bar from historical data buffer.

        Returns:
            True if bar loaded, False if buffer empty
        """
        if not self._hist_buffer:
            return False

        bar = self._hist_buffer.pop(0)

        # Update lines
        self.lines.datetime[0] = bt.date2num(datetime.fromtimestamp(bar[0] / 1000))
        self.lines.open[0] = bar[1]
        self.lines.high[0] = bar[2]
        self.lines.low[0] = bar[3]
        self.lines.close[0] = bar[4]
        self.lines.volume[0] = bar[5]
        self.lines.openinterest[0] = 0

        return True

    def start(self) -> None:
        """Called when data feed starts."""
        super().start()

        # Backfill historical data if requested
        if self.params.backfill and self.params.backfill_start:
            self._backfill_data()

    def stop(self) -> None:
        """Called when data feed stops."""
        super().stop()
        logger.info(f"CCXTData stopped for {self.symbol}")

    def islive(self) -> bool:
        """
        Mark this as live data feed.

        Returns:
            True (always live)
        """
        return True

    def _get_since_timestamp(self) -> Optional[int]:
        """
        Get timestamp for 'since' parameter in fetch_ohlcv.

        Returns:
            Timestamp in milliseconds, or None
        """
        if not self._last_bar_time:
            # First fetch: get bars from last few periods
            timeframe_seconds = self._TIMEFRAME_MAP[self.params.timeframe]
            since_time = datetime.now() - timedelta(seconds=timeframe_seconds * 10)
            return int(since_time.timestamp() * 1000)

        # Subsequent fetches: get bars since last bar
        return int(self._last_bar_time.timestamp() * 1000)

    def _backfill_data(self) -> None:
        """
        Backfill historical data from backfill_start to now.

        This fetches historical bars and stores them in buffer
        for sequential loading.
        """
        try:
            start_time = self.params.backfill_start
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)

            since = int(start_time.timestamp() * 1000)

            logger.info(f"Backfilling {self.symbol} from {start_time}")

            # Fetch in chunks (exchanges limit to ~1000 bars per request)
            all_bars = []
            chunk_size = 1000

            while since < int(datetime.now().timestamp() * 1000):
                ohlcv = self.store.run_coroutine(
                    self.exchange.fetch_ohlcv(
                        symbol=self.symbol,
                        timeframe=self.ccxt_timeframe,
                        since=since,
                        limit=chunk_size
                    )
                )

                if not ohlcv:
                    break

                all_bars.extend(ohlcv)

                # Update since to last bar timestamp + 1ms
                since = ohlcv[-1][0] + 1

                # Avoid rate limits
                import time
                time.sleep(self.exchange.rateLimit / 1000)

            # Store in buffer
            self._hist_buffer = all_bars

            logger.info(f"Backfilled {len(all_bars)} bars for {self.symbol}")

        except Exception as e:
            logger.error(f"Failed to backfill data for {self.symbol}: {e}")

    def haslivedata(self) -> bool:
        """
        Check if live data is available.

        Returns:
            True if connected to exchange
        """
        try:
            # Simple ping to check connection
            self.store.run_coroutine(self.exchange.fetch_status())
            return True
        except:
            return False

    @staticmethod
    def _map_to_bt_timeframe(timeframe: str):
        """
        Convert CCXT timeframe string to Backtrader timeframe/compression.

        Returns:
            tuple: (bt.TimeFrame, compression)
        """
        import backtrader as bt  # Local import to avoid circulars at module import

        mapping = {
            '1m': (bt.TimeFrame.Minutes, 1),
            '5m': (bt.TimeFrame.Minutes, 5),
            '15m': (bt.TimeFrame.Minutes, 15),
            '30m': (bt.TimeFrame.Minutes, 30),
            '1h': (bt.TimeFrame.Minutes, 60),
            '4h': (bt.TimeFrame.Minutes, 240),
            '1d': (bt.TimeFrame.Days, 1),
        }

        if timeframe not in mapping:
            raise ValueError(f"Unsupported timeframe for Backtrader mapping: {timeframe}")

        return mapping[timeframe]
