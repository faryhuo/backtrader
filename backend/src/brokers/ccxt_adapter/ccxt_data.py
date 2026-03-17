"""
CCXT Data - Live OHLCV data feed from Binance Spot via CCXT.

Provides a Backtrader-compatible data feed that polls Binance for
real-time OHLCV bars, with forming-bar filtering and backfill support.
"""

import logging
import re
import time
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import backtrader as bt

from .ccxt_store import CCXTStore

logger = logging.getLogger(__name__)

# Timeframe string → seconds
_TIMEFRAME_SECONDS = {
    '1m': 60, '3m': 180, '5m': 300, '15m': 900, '30m': 1800,
    '1h': 3600, '2h': 7200, '4h': 14400, '6h': 21600,
    '8h': 28800, '12h': 43200, '1d': 86400,
    '3d': 259200, '1w': 604800, '1M': 2592000,
}


class CCXTData(bt.DataBase):
    """
    Live data feed that fetches OHLCV from Binance via CCXT.

    Features:
    - Forming-bar filter (skips incomplete bars to prevent future-leak)
    - Catch-up buffering (fetches multiple bars if behind)
    - Optional historical backfill
    - Retry on network errors with backoff
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
        ('max_fetch_retries', 3),
    )

    def __init__(self, store: CCXTStore, symbol: str, **kwargs):
        self.store = store
        self.exchange = store.get_exchange()
        self.symbol = symbol
        self._symbol = symbol  # used by broker._get_symbol()

        # Handle timeframe from kwargs
        ccxt_tf = kwargs.pop('timeframe', None) or kwargs.pop('ccxt_timeframe', None)
        self.ccxt_timeframe = ccxt_tf or self.params.ccxt_timeframe

        self._last_bar_time: Optional[datetime] = None
        self._hist_buffer: List[list] = []
        self._consecutive_errors = 0

        super().__init__(**kwargs)

        # Validate timeframe
        if self.ccxt_timeframe not in _TIMEFRAME_SECONDS:
            raise ValueError(f"Unsupported timeframe: '{self.ccxt_timeframe}'")

        # Map to Backtrader units
        self._timeframe, self._compression = _map_to_bt_timeframe(self.ccxt_timeframe)
        self.params.timeframe = self._timeframe
        self.params.compression = self._compression

        self._tf_seconds = _TIMEFRAME_SECONDS[self.ccxt_timeframe]
        self._tf_ms = self._tf_seconds * 1000

        logger.info(f"CCXTData initialized: {symbol} [{self.ccxt_timeframe}]")

    # ──────────────────────────── Backtrader interface ────────────────────────────

    def _load(self) -> bool:
        """Load next bar into lines. Returns True if bar loaded.

        For live feeds, this method blocks until a new bar is available
        or the store is stopped. Returning False only when the feed
        should truly end (store stopped / too many errors).
        """
        # Serve from buffer first
        if self._hist_buffer:
            return self._consume_bar()

        # Live wait-loop: keep polling until a bar arrives or store stops
        while self.store.is_running:
            try:
                new_bars = self._fetch_bars()
                if new_bars:
                    self._hist_buffer.extend(new_bars)
                    self._consecutive_errors = 0
                    return self._consume_bar()

                # No completed bar yet — wait and retry
                time.sleep(self.params.pause)

            except Exception as e:
                self._consecutive_errors += 1
                if self.params.debug or self._consecutive_errors % 10 == 0:
                    logger.error(f"Fetch error ({self.symbol}): {e}")

                # Give up after too many consecutive errors
                if self._consecutive_errors >= self.params.max_fetch_retries * 10:
                    logger.error(
                        f"Too many consecutive errors ({self._consecutive_errors}) "
                        f"for {self.symbol}, stopping data feed"
                    )
                    return False

                time.sleep(min(self.params.pause * self._consecutive_errors, 30))

        # Store was stopped — signal end of data
        logger.info(f"Store stopped, ending data feed for {self.symbol}")
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
        """Fetch OHLCV bars from exchange, filtering forming bars."""
        if self._last_bar_time:
            since = int(self._last_bar_time.timestamp() * 1000) + 1
        else:
            since = int(
                (datetime.utcnow() - timedelta(seconds=self._tf_seconds * 5)).timestamp() * 1000
            )

        ohlcv = self.store.run_coroutine(
            self.store._fetch_with_retry(
                lambda: self.exchange.fetch_ohlcv(
                    symbol=self.symbol,
                    timeframe=self.ccxt_timeframe,
                    since=since,
                    limit=self.params.limit,
                ),
                max_attempts=self.params.max_fetch_retries,
            ),
            timeout=30,
        )

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
            logger.debug(f"Fetched {len(valid)} new bars for {self.symbol}")

        return valid

    def _consume_bar(self) -> bool:
        """Pop one bar from buffer and load into Backtrader lines."""
        if not self._hist_buffer:
            return False

        bar = self._hist_buffer.pop(0)
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

    def _perform_backfill(self) -> None:
        """Fetch historical data before live feed starts."""
        if not self.params.backfill_start:
            return

        try:
            start_dt = self.params.backfill_start
            if isinstance(start_dt, str):
                start_dt = datetime.fromisoformat(start_dt)

            logger.info(f"Backfilling {self.symbol} from {start_dt}...")

            since = int(start_dt.timestamp() * 1000)
            now_ms = int(datetime.utcnow().timestamp() * 1000)
            batch_size = 1000
            total = 0

            while since < now_ms:
                bars = self.store.run_coroutine(
                    self.exchange.fetch_ohlcv(
                        symbol=self.symbol,
                        timeframe=self.ccxt_timeframe,
                        since=since,
                        limit=batch_size,
                    )
                )

                if not bars:
                    break

                closed = [b for b in bars if b[0] + self._tf_ms <= now_ms]
                if not closed:
                    break

                self._hist_buffer.extend(closed)
                total += len(closed)
                since = bars[-1][0] + 1

                # Respect rate limit
                time.sleep(self.exchange.rateLimit / 1000)

            logger.info(f"Backfill complete: {total} bars loaded for {self.symbol}")

        except Exception as e:
            logger.error(f"Backfill failed for {self.symbol}: {e}")

    # ──────────────────────────── price snapshot ────────────────────────────

    def get_current_price(self) -> Optional[float]:
        """Get latest close price (from last loaded bar or None)."""
        if self._last_bar_time and len(self) > 0:
            return self.lines.close[0]
        return None


def _map_to_bt_timeframe(tf: str) -> Tuple[int, int]:
    """Map CCXT timeframe string to (BT TimeFrame, compression)."""
    match = re.match(r"(\d+)([a-zA-Z]+)", tf)
    if not match:
        return bt.TimeFrame.Minutes, 1

    qty, unit = int(match.group(1)), match.group(2)

    if unit == 'm':
        return bt.TimeFrame.Minutes, qty
    elif unit == 'h':
        return bt.TimeFrame.Minutes, qty * 60
    elif unit == 'd':
        return bt.TimeFrame.Days, qty
    elif unit == 'w':
        return bt.TimeFrame.Weeks, qty
    elif unit == 'M':
        return bt.TimeFrame.Months, qty

    return bt.TimeFrame.Minutes, 1
