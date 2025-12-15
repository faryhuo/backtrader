"""
CCXT Data - Live OHLCV data feed from CCXT exchanges.

This module provides a Backtrader-compatible data feed that fetches
real-time OHLCV bars from cryptocurrency exchanges via CCXT.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

import backtrader as bt

from .ccxt_store import CCXTStore

logger = logging.getLogger(__name__)


class CCXTData(bt.DataBase):
    """
    Live data feed that fetches OHLCV from CCXT exchange.

    Features:
    - Real-time polling with 'Catch-Up' capability (buffering intermediate bars).
    - Filters incomplete 'forming' bars to prevent repainting/future leaks.
    - Auto-backfill support.
    - Robust error handling and retries.
    """

    params = (
        ('timeframe', None),       # Backtrader timeframe enum (override if needed)
        ('ccxt_timeframe', '1m'),  # CCXT timeframe string ('1m', '5m', '1h', etc.)
        ('compression', 1),        # Backtrader bar compression
        ('backfill_start', None),  # datetime/str: Start date for historical data
        ('backfill', False),       # bool: Enable historical backfill
        ('limit', 50),             # int: Fetch batch size (higher = better catch-up)
        ('pause', 1.0),            # float: Seconds to wait if no new data found
        ('debug', False),          # bool: Enable verbose logging
    )

    # Timeframe string to seconds mapping
    _TIMEFRAME_MAP = {
        '1m': 60,
        '3m': 180,
        '5m': 300,
        '15m': 900,
        '30m': 1800,
        '1h': 3600,
        '2h': 7200,
        '4h': 14400,
        '6h': 21600,
        '8h': 28800,
        '12h': 43200,
        '1d': 86400,
        '3d': 259200,
        '1w': 604800,
        '1M': 2592000,
    }

    def __init__(self, store: CCXTStore, symbol: str, **kwargs):
        self.store = store
        self.exchange = store.get_exchange()
        self.symbol = symbol

        # Handle params prioritization: kwargs > params > defaults
        ccxt_tf = kwargs.pop('timeframe', None) or kwargs.pop('ccxt_timeframe', None)
        self.ccxt_timeframe = ccxt_tf or self.params.ccxt_timeframe

        self._symbol = symbol
        self._last_bar_time: Optional[datetime] = None
        self._hist_buffer: List[list] = []  # Buffer for both backfill and live catch-up
        self._consecutive_errors = 0
        
        # Pass kwargs to parent (Backtrader handles standard params like 'fromdate')
        super().__init__(**kwargs)

        # 1. Validate Timeframe
        if self.ccxt_timeframe not in self._TIMEFRAME_MAP:
            # Try to parse numeric minutes if possible, or fail
            raise ValueError(f"CCXTData: Unsupported timeframe '{self.ccxt_timeframe}'")

        # 2. Map to Backtrader units
        self._timeframe, self._compression = self._map_to_bt_timeframe(self.ccxt_timeframe)
        self.params.timeframe = self._timeframe
        self.params.compression = self._compression
        
        # 3. Calculate timeframe duration in milliseconds
        self._tf_seconds = self._TIMEFRAME_MAP.get(self.ccxt_timeframe, 60)
        self._tf_ms = self._tf_seconds * 1000

        logger.info(f"Initialized CCXTData for {symbol} [{self.ccxt_timeframe}]")

    def _load(self) -> bool:
        """
        Main Backtrader method called to get the next bar.
        Returns True if a bar was loaded into self.lines, False otherwise.
        """
        # 1. Serve from buffer if available (Backfill or Catch-up)
        if self._hist_buffer:
            return self._consume_from_buffer()

        # 2. If buffer is empty, fetch new data from exchange
        try:
            new_bars = self._fetch_from_exchange()
            
            if new_bars:
                self._hist_buffer.extend(new_bars)
                self._consecutive_errors = 0 # Reset error count
                return self._consume_from_buffer()
            else:
                # No new data yet
                return False

        except Exception as e:
            self._consecutive_errors += 1
            if self.params.debug or self._consecutive_errors % 10 == 0:
                logger.error(f"CCXT Fetch Error ({self.symbol}): {e}")
            
            # Prevent rapid error looping
            time.sleep(self.params.pause)
            return False

    def _fetch_from_exchange(self) -> List[list]:
        """Fetch OHLVC data from exchange."""
        
        # Calculate 'since' timestamp
        if self._last_bar_time:
            # Ask for data starting 1ms after our last known bar
            since = int(self._last_bar_time.timestamp() * 1000) + 1
        else:
            # First run (no backfill): look back small amount
            since = int((datetime.utcnow() - timedelta(seconds=self._tf_seconds * 5)).timestamp() * 1000)

        # Run async call synchronously
        ohlcv = self.store.run_coroutine(
            self.exchange.fetch_ohlcv(
                symbol=self.symbol,
                timeframe=self.ccxt_timeframe,
                since=since,
                limit=self.params.limit
            )
        )

        if not ohlcv:
            return []

        # Validate and Filter Data
        valid_bars = []
        current_time_ms = int(datetime.utcnow().timestamp() * 1000)

        for bar in ohlcv:
            # bar format: [timestamp, open, high, low, close, volume]
            ts = bar[0]
            
            # 1. Check if bar is closed (Forming Filter)
            # A bar is closed if its start_time + duration <= current_time
            if ts + self._tf_ms > current_time_ms:
                continue # Skip forming bar

            # 2. Check strict timestamp ordering
            bar_dt = datetime.utcfromtimestamp(ts / 1000)
            if self._last_bar_time and bar_dt <= self._last_bar_time:
                continue # Skip duplicate or old bar

            valid_bars.append(bar)

        if self.params.debug and valid_bars:
            logger.debug(f"Fetched {len(valid_bars)} new bars for {self.symbol}")

        return valid_bars

    def _consume_from_buffer(self) -> bool:
        """Pop one bar from buffer and load into lines."""
        if not self._hist_buffer:
            return False

        bar = self._hist_buffer.pop(0)
        
        # bar: [timestamp_ms, open, high, low, close, volume]
        dt_obj = datetime.utcfromtimestamp(bar[0] / 1000)

        self.lines.datetime[0] = bt.date2num(dt_obj)
        self.lines.open[0] = bar[1]
        self.lines.high[0] = bar[2]
        self.lines.low[0] = bar[3]
        self.lines.close[0] = bar[4]
        self.lines.volume[0] = bar[5]
        self.lines.openinterest[0] = 0

        self._last_bar_time = dt_obj
        return True

    def start(self) -> None:
        super().start()
        if self.params.backfill:
            self._perform_backfill()

    def _perform_backfill(self):
        """Fetch historical data before live feed starts."""
        if not self.params.backfill_start:
            return

        try:
            start_dt = self.params.backfill_start
            if isinstance(start_dt, str):
                start_dt = datetime.fromisoformat(start_dt)
            
            logger.info(f"Backfilling {self.symbol} starting from {start_dt}...")
            
            since = int(start_dt.timestamp() * 1000)
            now_ms = int(datetime.utcnow().timestamp() * 1000)
            
            batch_size = 1000 # Max for many exchanges
            total_fetched = 0

            while since < now_ms:
                bars = self.store.run_coroutine(
                    self.exchange.fetch_ohlcv(
                        symbol=self.symbol,
                        timeframe=self.ccxt_timeframe,
                        since=since,
                        limit=batch_size
                    )
                )
                
                if not bars:
                    break

                # Filter closed bars only for backfill too
                closed_bars = [
                    b for b in bars 
                    if b[0] + self._tf_ms <= now_ms
                ]
                
                if not closed_bars:
                    break

                self._hist_buffer.extend(closed_bars)
                total_fetched += len(closed_bars)
                
                # Update 'since' to the last fetched timestamp + 1ms
                since = bars[-1][0] + 1
                
                # Respect rate limits
                time.sleep(self.exchange.rateLimit / 1000)

            logger.info(f"Backfill complete: loaded {total_fetched} bars.")

        except Exception as e:
            logger.error(f"Backfill failed for {self.symbol}: {e}")

    def islive(self) -> bool:
        return True

    def haslivedata(self) -> bool:
        return self.store.get_exchange() is not None

    @staticmethod
    def _map_to_bt_timeframe(tf: str) -> Tuple[int, int]:
        """Maps CCXT timeframe string to (BT TimeFrame, Compression)"""
        # Default to Minutes
        frame = bt.TimeFrame.Minutes
        compression = 1

        # Extract number and unit (e.g., '15m' -> 15, 'm')
        import re
        match = re.match(r"(\d+)([a-zA-Z]+)", tf)
        if match:
            qty, unit = int(match.group(1)), match.group(2)
            if unit == 'm':
                frame = bt.TimeFrame.Minutes
                compression = qty
            elif unit == 'h':
                frame = bt.TimeFrame.Minutes
                compression = qty * 60
            elif unit == 'd':
                frame = bt.TimeFrame.Days
                compression = qty
            elif unit == 'w':
                frame = bt.TimeFrame.Weeks
                compression = qty
            elif unit == 'M':
                frame = bt.TimeFrame.Months
                compression = qty
        
        return frame, compression
