"""
CCXT Store - Central connection manager for Binance Spot via CCXT.

This module provides a Backtrader-compatible store that manages the CCXT Binance
exchange connection, handles async/sync bridging, and provides shared exchange
instance to CCXTBroker and CCXTData.
"""

import asyncio
import logging
import threading
import time
from typing import Any, Awaitable, Callable, Dict, Optional

import ccxt.async_support as ccxt

logger = logging.getLogger(__name__)

# Retry defaults
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_DELAY = 0.5  # seconds


class CCXTStore:
    """
    Store class that manages CCXT Binance Spot connection.

    Responsibilities:
    - Initializes Binance exchange instance (paper/testnet or live)
    - Manages asyncio event loop in background daemon thread
    - Provides run_coroutine() to bridge async CCXT with sync Backtrader
    - Provides fetch_ticker() for real-time price queries
    - Handles reconnection and retry on network failures

    Usage:
        store = CCXTStore(mode='paper')
        store.start()
        price = store.fetch_ticker('BTC/USDT')
        store.stop()
    """

    def __init__(
        self,
        exchange_id: str = 'binance',
        mode: str = 'paper',
        config: Optional[Dict] = None,
        user_id: Optional[str] = None,
    ):
        self.exchange_id = exchange_id.lower()
        self.mode = mode.lower()
        self.config = config or {}
        self.user_id = user_id

        self._exchange: Optional[ccxt.Exchange] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._loop_ready = threading.Event()
        self._running = False

        # Credentials (loaded in start())
        self.api_key: Optional[str] = None
        self.secret: Optional[str] = None

        logger.info(f"Initialized CCXTStore for {self.exchange_id} in {mode} mode")

    # ──────────────────────────── lifecycle ────────────────────────────

    def start(self) -> None:
        """Start the store: event loop → credentials → exchange → load markets."""
        if self._running:
            logger.warning("CCXTStore already started")
            return

        try:
            self._start_event_loop()
            self._load_credentials()
            self._init_exchange()

            # Verify connection by loading markets
            self.run_coroutine(
                self._fetch_with_retry(lambda: self._exchange.load_markets(), max_attempts=3),
                timeout=90,
            )

            self._running = True
            logger.info(
                f"CCXTStore started for {self.exchange_id} "
                f"(markets loaded: {len(self._exchange.markets)})"
            )
        except Exception as e:
            logger.error(f"Failed to start CCXTStore: {e}")
            self.stop()
            raise

    def stop(self) -> None:
        """Stop the store and clean up resources."""
        if not self._running and not self._thread:
            return

        self._running = False

        # Close exchange connection on the loop
        if self._exchange and self._loop and self._loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(self._exchange.close(), self._loop)
                future.result(timeout=5)
            except Exception as e:
                logger.warning(f"Error closing exchange: {e}")

        # Stop event loop
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        # Wait for thread
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        self._exchange = None
        logger.info(f"CCXTStore stopped for {self.exchange_id}")

    @property
    def is_running(self) -> bool:
        return self._running

    # ──────────────────────────── public API ────────────────────────────

    def get_exchange(self) -> ccxt.Exchange:
        """Get the CCXT exchange instance. Raises if store not started."""
        if not self._exchange:
            raise RuntimeError("CCXTStore not started. Call start() first.")
        return self._exchange

    def run_coroutine(self, coro: Any, timeout: float = 30) -> Any:
        """
        Execute an async coroutine from sync context via the background loop.

        Raises RuntimeError if loop not running, TimeoutError on timeout.
        """
        if not self._loop or not self._loop.is_running():
            raise RuntimeError("Event loop not running. Call start() first.")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            return future.result(timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Coroutine execution exceeded {timeout}s timeout")

    def fetch_ticker(self, symbol: str) -> Dict:
        """
        Fetch current ticker for *symbol* (e.g. 'BTC/USDT').

        Returns dict with at least: last, bid, ask, high, low, volume, timestamp.
        """
        return self.run_coroutine(
            self._fetch_with_retry(lambda: self._exchange.fetch_ticker(symbol)),
            timeout=10,
        )

    def get_account_balance(self, quote_currency: str = 'USDT') -> Dict[str, float]:
        """
        Fetch account balance from exchange.

        Returns dict with keys: free, used, total for the given quote currency.
        """
        balance = self.run_coroutine(
            self._fetch_with_retry(lambda: self._exchange.fetch_balance()),
            timeout=15,
        )
        currency_balance = balance.get(quote_currency, {})
        return {
            'free': float(currency_balance.get('free', 0)),
            'used': float(currency_balance.get('used', 0)),
            'total': float(currency_balance.get('total', 0)),
        }

    # ──────────────────────────── internals ────────────────────────────

    def _load_credentials(self) -> None:
        """Load API credentials via ConfigManager (DB → env fallback)."""
        from src.config.config_manager import ConfigManager

        config_manager = ConfigManager(user_id=self.user_id)
        creds = config_manager.get_ccxt_credentials(self.exchange_id, self.mode)

        self.api_key = creds.get("api_key")
        self.secret = creds.get("secret")

        if not self.api_key or not self.secret:
            if self.mode == 'live':
                raise ValueError(
                    f"Missing API credentials for LIVE mode. "
                    f"Configure them via Settings UI or set "
                    f"CCXT_{self.exchange_id.upper()}_{self.mode.upper()}_API_KEY/SECRET in .env"
                )
            logger.warning(
                f"No API credentials found for {self.exchange_id} {self.mode}. "
                "Some operations may fail."
            )

    def _init_exchange(self) -> None:
        """Initialize CCXT Binance exchange instance."""
        exchange_class = getattr(ccxt, self.exchange_id, None)
        if not exchange_class:
            raise ValueError(f"Unsupported exchange: {self.exchange_id}")

        exchange_config = {
            'apiKey': self.api_key,
            'secret': self.secret,
            'enableRateLimit': True,
            'timeout': 20_000,
            'options': {
                'defaultType': 'spot',
                'defaultMarket': 'spot',
            },
        }

        self._exchange = exchange_class(exchange_config)

        # Paper mode → Binance Spot testnet
        if self.mode == 'paper':
            self._exchange.set_sandbox_mode(True)

            if self.exchange_id == 'binance':
                self._exchange.options['defaultType'] = 'spot'
                self._exchange.options['defaultMarket'] = 'spot'
                self._exchange.options['defaultSubType'] = None

                self._exchange.urls.setdefault('api', {})
                self._exchange.urls['api'].update({
                    'public': 'https://testnet.binance.vision/api/v3',
                    'private': 'https://testnet.binance.vision/api/v3',
                    'v1': 'https://testnet.binance.vision/api/v1',
                })

            logger.info(f"Enabled sandbox/testnet mode for {self.exchange_id}")

    def _start_event_loop(self) -> None:
        """Start asyncio event loop in a background daemon thread."""
        if self._thread and self._thread.is_alive():
            return

        self._loop_ready.clear()

        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop_ready.set()
            try:
                self._loop.run_forever()
            finally:
                try:
                    pending = asyncio.all_tasks(self._loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        self._loop.run_until_complete(
                            asyncio.gather(*pending, return_exceptions=True)
                        )
                except Exception as e:
                    logger.error(f"Error cleaning up loop tasks: {e}")
                self._loop.close()

        self._thread = threading.Thread(
            target=run_loop, daemon=True, name=f"CCXT-{self.exchange_id}"
        )
        self._thread.start()

        if not self._loop_ready.wait(timeout=5.0):
            raise RuntimeError("Failed to start asyncio event loop within 5s")

    async def _fetch_with_retry(
        self,
        coro_factory: Callable[[], Awaitable[Any]],
        max_attempts: int = DEFAULT_MAX_RETRIES,
    ) -> Any:
        """Execute a coroutine factory with exponential backoff on network errors."""
        last_error = None

        for attempt in range(max_attempts):
            try:
                return await coro_factory()
            except (ccxt.NetworkError, ccxt.RequestTimeout) as e:
                last_error = e
                if attempt < max_attempts - 1:
                    wait_time = DEFAULT_RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        f"Network error ({self.exchange_id}): {e}. "
                        f"Retrying in {wait_time}s (attempt {attempt + 1}/{max_attempts})..."
                    )
                    await asyncio.sleep(wait_time)
            except Exception:
                raise  # Non-retryable

        raise last_error

    # ──────────────────────────── context manager ────────────────────────────

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False
