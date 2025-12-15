"""
CCXT Store - Central connection manager for CCXT exchanges.

This module provides a Backtrader-compatible store that manages the CCXT exchange
connection, handles async/sync bridging, and provides shared exchange instance
to CCXTBroker and CCXTData.
"""

import asyncio
import logging
import os
import threading
import time
from typing import Any, Optional, Dict, Callable, Awaitable

import ccxt.async_support as ccxt

logger = logging.getLogger(__name__)


class CCXTStore:
    """
    Store class that manages CCXT exchange connection.

    This class:
    - Initializes CCXT exchange instance (paper or live mode)
    - Manages asyncio event loop in background thread
    - Provides run_coroutine() to bridge async CCXT with sync Backtrader
    - Handles reconnection logic on network failures

    Usage:
        store = CCXTStore(exchange_id='binance', mode='paper')
        store.start()
        exchange = store.get_exchange()
    """

    def __init__(self, exchange_id: str = 'binance', mode: str = 'paper', config: Optional[Dict] = None):
        """
        Initialize CCXT store.

        Args:
            exchange_id: CCXT exchange ID (e.g., 'binance', 'okx', 'bybit')
            mode: Trading mode ('paper' for testnet, 'live' for production)
            config: Optional broker configuration dict
        """
        self.exchange_id = exchange_id.lower()
        self.mode = mode.lower()
        self.config = config or {}

        self._exchange: Optional[ccxt.Exchange] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._loop_ready = threading.Event()  # Signal when loop is running
        self._running = False

        logger.info(f"Initialized CCXTStore for {exchange_id} in {mode} mode")

    def start(self) -> None:
        """
        Start the CCXT store.

        This method:
        1. Loads API credentials
        2. Starts asyncio event loop in background thread
        3. Initializes CCXT exchange instance (requires loop)
        4. Verifies connection
        """
        if self._running:
            logger.warning("CCXTStore already started")
            return

        try:
            # 1. Start Event Loop first (Exchange init often needs it for async calls)
            self._start_event_loop()

            # 2. Load Credentials
            self._load_credentials()

            # 3. Initialize Exchange
            self._init_exchange()

            # 4. Verify Connection & Load Markets
            # We run this on the loop to ensure async internals are set up
            self.run_coroutine(
                self._fetch_with_retry(lambda: self._exchange.load_markets(), max_attempts=3),
                timeout=90
            )
            
            self._running = True
            logger.info(f"CCXTStore started for {self.exchange_id} (Markets loaded: {len(self._exchange.markets)})")

        except Exception as e:
            logger.error(f"Failed to start CCXTStore: {e}")
            self.stop()
            raise

    def stop(self) -> None:
        """Stop the CCXT store and clean up resources."""
        if not self._running and not self._thread:
            return

        self._running = False

        # 1. Close exchange connection safely on the loop
        if self._exchange and self._loop and self._loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(self._exchange.close(), self._loop)
                future.result(timeout=5)  # Wait for close
            except Exception as e:
                logger.warning(f"Error closing exchange: {e}")

        # 2. Stop event loop
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        # 3. Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        logger.info(f"CCXTStore stopped for {self.exchange_id}")

    def get_exchange(self) -> ccxt.Exchange:
        """
        Get the CCXT exchange instance.

        Returns:
            CCXT exchange instance

        Raises:
            RuntimeError: If store not started
        """
        if not self._exchange:
            raise RuntimeError("CCXTStore not started. Call start() first.")
        return self._exchange

    def run_coroutine(self, coro: Any, timeout: float = 30) -> Any:
        """
        Execute async coroutine from sync context.

        This method bridges async CCXT operations with Backtrader's
        synchronous framework by running coroutines in the background
        event loop.

        Args:
            coro: Coroutine to execute
            timeout: Maximum time to wait for result (seconds)

        Returns:
            Result of coroutine execution

        Raises:
            RuntimeError: If store not started
            TimeoutError: If execution exceeds timeout
        """
        if not self._loop or not self._loop.is_running():
            raise RuntimeError("Event loop not running. Call start() first.")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            return future.result(timeout=timeout)
        except asyncio.TimeoutError:
            # We don't cancel the future here because it might be a critical operation
            # that should complete even if we stopped waiting.
            raise TimeoutError(f"Coroutine execution exceeded {timeout}s timeout")
        except Exception as e:
            # Re-raise exceptions from the coroutine
            raise e

    def _load_credentials(self) -> None:
        """
        Load API credentials from environment variables.
        """
        exchange_upper = self.exchange_id.upper()
        mode_upper = self.mode.upper()

        api_key_var = f"CCXT_{exchange_upper}_{mode_upper}_API_KEY"
        secret_var = f"CCXT_{exchange_upper}_{mode_upper}_SECRET"
        passphrase_var = f"CCXT_{exchange_upper}_{mode_upper}_PASSPHRASE"

        self.api_key = os.getenv(api_key_var)
        self.secret = os.getenv(secret_var)
        self.passphrase = os.getenv(passphrase_var)

        # Allow running without credentials ONLY in paper mode if specifically configured
        # But generally paper trading still needs API keys for most exchanges
        if not self.api_key or not self.secret:
             # Check if we are in a special 'simulation' mode that doesn't need keys? 
             # For now, strict check.
            if self.mode == 'live':
                raise ValueError(
                    f"Missing API credentials for LIVE mode. Set {api_key_var} and {secret_var}."
                )
            else:
                 logger.warning(
                     f"No API credentials found for {self.exchange_id} {self.mode}. "
                     "Some calls may fail if the exchange requires auth even for testnet."
                 )

    def _init_exchange(self) -> None:
        """
        Initialize CCXT exchange instance.
        """
        # Get exchange class
        exchange_class = getattr(ccxt, self.exchange_id, None)
        if not exchange_class:
            raise ValueError(f"Unsupported exchange: {self.exchange_id}")

        default_market = str(self.config.get('default_market', 'spot')).lower()
        if default_market in {'futures', 'future'}:
            default_type = 'future'
        else:
            default_type = 'spot'

        # Build exchange config
        exchange_config = {
            'apiKey': self.api_key,
            'secret': self.secret,
            'enableRateLimit': True,
            'timeout': 20000,  # ms
            'options': {'defaultType': default_type},  # 'spot' or 'future' (binance)
        }

        # Add passphrase if present (required for OKX, KuCoin, etc)
        if self.passphrase:
            exchange_config['password'] = self.passphrase

        # Initialize exchange
        self._exchange = exchange_class(exchange_config)

        # Enable sandbox/testnet if needed
        if self.mode == 'paper':
            self._exchange.set_sandbox_mode(True)

            # Explicit overrides for Binance Spot Testnet (https://testnet.binance.vision/)
            # Use updates instead of replacement to avoid stripping futures endpoints (fapi*) that CCXT expects.
            if self.exchange_id == 'binance':
                self._exchange.options['defaultType'] = default_type
                self._exchange.options['defaultMarket'] = default_type
                self._exchange.options['defaultSubType'] = None

                # Only override the spot base URLs; futures testnet URLs live under fapi*/dapi*.
                if default_type == 'spot':
                    self._exchange.urls.setdefault('api', {})
                    self._exchange.urls['api'].update({
                        'public': 'https://testnet.binance.vision/api/v3',
                        'private': 'https://testnet.binance.vision/api/v3',
                        'v1': 'https://testnet.binance.vision/api/v1',
                    })

            logger.info(f"Enabled sandbox mode for {self.exchange_id}")

    def _start_event_loop(self) -> None:
        """
        Start asyncio event loop in background thread.
        """
        if self._thread and self._thread.is_alive():
            return

        self._loop_ready.clear()

        def run_loop():
            """Background thread function that runs event loop."""
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop_ready.set()  # Signal ready

            try:
                self._loop.run_forever()
            finally:
                # Clean up pending tasks
                try:
                    pending = asyncio.all_tasks(self._loop)
                    for task in pending:
                        task.cancel()
                    
                    if pending:
                        self._loop.run_until_complete(
                            asyncio.gather(*pending, return_exceptions=True)
                        )
                except Exception as e:
                    logger.error(f"Error closing loop tasks: {e}")
                
                self._loop.close()
                logger.info("Event loop closed")

        self._thread = threading.Thread(target=run_loop, daemon=True, name=f"CCXT-{self.exchange_id}")
        self._thread.start()

        # Wait for loop to be ready
        if not self._loop_ready.wait(timeout=5.0):
             raise RuntimeError("Failed to start asyncio event loop within 5s")

    async def _fetch_with_retry(self, coro_factory: Callable[[], Awaitable[Any]], max_attempts: int = 3) -> Any:
        """
        Execute coroutine with retry logic on network failures.
        """
        last_error = None

        for attempt in range(max_attempts):
            try:
                return await coro_factory()
            except (ccxt.NetworkError, ccxt.RequestTimeout) as e:
                last_error = e
                if attempt < max_attempts - 1:
                    wait_time = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s
                    logger.warning(
                        f"Network error ({self.exchange_id}): {e}. Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
            except Exception:
                raise # Non-retryable

        raise last_error

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
