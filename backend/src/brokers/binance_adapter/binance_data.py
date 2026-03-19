"""
Binance Data - Backtrader-compatible OHLCV data feed using python-binance.

Provides real-time data feed for Backtrader strategies.
"""

import logging
import time
from calendar import timegm
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
        self._live_buffer: List[list] = []
        self._consecutive_errors = 0
        self._historical_mode = False
        self._live_notified = False

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
        # Serve preloaded historical bars first without entering LIVE mode.
        if self._hist_buffer:
            loaded = self._consume_bar(self._hist_buffer)
            if loaded and not self._hist_buffer:
                self._historical_mode = False
                logger.info(
                    "Historical warmup finished for %s at %s; waiting for first live bar",
                    self._symbol,
                    self._last_bar_time.isoformat() if self._last_bar_time else "unknown",
                )
            return loaded

        # Then serve live bars collected from websocket / polling.
        if self._live_buffer:
            self._notify_live()
            return self._consume_bar(self._live_buffer)

        # Live wait-loop
        while self.store.is_running:
            try:
                new_bars = self._drain_live_bars()
                if new_bars:
                    self._live_buffer.extend(new_bars)
                    self._consecutive_errors = 0
                    self._notify_live()
                    return self._consume_bar(self._live_buffer)

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
        self._historical_mode = bool(self._hist_buffer)
        if self._historical_mode:
            self.put_notification(self.DELAYED)
        self._start_live_stream()

    def islive(self) -> bool:
        return True

    def haslivedata(self) -> bool:
        return self.store.is_running

    # ──────────────────────────── data fetching ────────────────────────────

    def _fetch_bars(self) -> List[list]:
        """Fetch OHLCV bars from Binance, filtering forming bars."""
        now_ms = int(time.time() * 1000)
        if self._last_bar_time:
            since = self._datetime_to_ms(self._last_bar_time) + 1
        else:
            since = now_ms - (self._tf_seconds * 5 * 1000)

        try:
            ohlcv = self.store.fetch_ohlcv(
                symbol=self._symbol,
                interval=self.ccxt_timeframe,
                limit=self.params.limit,
                since_ms=since,
            )
            logger.info(
                "Fetched %s raw bars for %s [%s] since=%s last_bar=%s",
                len(ohlcv or []),
                self._symbol,
                self.ccxt_timeframe,
                since,
                self._last_bar_time.isoformat() if self._last_bar_time else "none",
            )
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV: {e}")
            return []

        if not ohlcv:
            return []

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

        if not valid:
            logger.info(
                "No new closed bars for %s [%s]; raw=%s last_bar=%s now_ms=%s",
                self._symbol,
                self.ccxt_timeframe,
                len(ohlcv or []),
                self._last_bar_time.isoformat() if self._last_bar_time else "none",
                now_ms,
            )
        else:
            logger.info(
                "Accepted %s new closed bars for %s [%s]; first=%s last=%s",
                len(valid),
                self._symbol,
                self.ccxt_timeframe,
                datetime.utcfromtimestamp(valid[0][0] / 1000).isoformat(),
                datetime.utcfromtimestamp(valid[-1][0] / 1000).isoformat(),
            )

        if self.params.debug and valid:
            logger.debug(f"Fetched {len(valid)} new bars for {self._symbol}")

        return valid

    def _consume_bar(self, buffer_: List[list]) -> bool:
        """Pop one bar from a buffer and load into Backtrader lines."""
        if not buffer_:
            return False

        bar = buffer_.pop(0)
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

    def _start_live_stream(self) -> None:
        """Subscribe to live closed kline updates when the store supports it."""
        try:
            self.store.start_kline_stream(
                self._symbol,
                self.ccxt_timeframe,
                self._on_live_kline,
            )
        except Exception as exc:
            logger.debug(f"Failed to start live kline stream: {exc}")

    def _on_live_kline(self, bar: dict) -> None:
        """Receive live closed kline messages from the store."""
        if not bar.get('is_closed'):
            return

        normalized = [
            int(bar['time_ms']),
            float(bar['open']),
            float(bar['high']),
            float(bar['low']),
            float(bar['close']),
            float(bar['volume']),
        ]

        if not self._is_new_bar(normalized[0]):
            return

        self._live_buffer.append(normalized)

    def _drain_live_bars(self) -> List[list]:
        """Get new live bars from websocket first, then REST polling fallback."""
        if self._live_buffer:
            return []
        return self._fetch_bars()

    def _is_new_bar(self, ts_ms: int) -> bool:
        bar_dt = datetime.utcfromtimestamp(ts_ms / 1000)
        if self._last_bar_time and bar_dt <= self._last_bar_time:
            return False
        if self._hist_buffer and ts_ms <= self._hist_buffer[-1][0]:
            return False
        if self._live_buffer and ts_ms <= self._live_buffer[-1][0]:
            return False
        return True

    def _notify_live(self) -> None:
        if not self._live_notified:
            logger.info(
                "First live bar available for %s [%s]; switching feed to LIVE",
                self._symbol,
                self.ccxt_timeframe,
            )
            self.put_notification(self.LIVE)
            self._live_notified = True

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

            since = self._datetime_to_ms(start_dt)
            now_ms = int(time.time() * 1000)

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

    @staticmethod
    def _datetime_to_ms(dt_obj: datetime) -> int:
        """Convert a datetime to epoch milliseconds, treating naive values as UTC."""
        return int(timegm(dt_obj.utctimetuple()) * 1000 + dt_obj.microsecond / 1000)

