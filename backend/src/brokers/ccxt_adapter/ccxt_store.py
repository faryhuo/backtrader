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
from typing import Any, Optional, Dict

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
        self._running = False

        logger.info(f"Initialized CCXTStore for {exchange_id} in {mode} mode")

    def start(self) -> None:
        """
        Start the CCXT store.

        This method:
        1. Loads API credentials from environment variables
        2. Initializes CCXT exchange instance
        3. Starts asyncio event loop in background thread
        """
        if self._running:
            logger.warning("CCXTStore already started")
            return

        self._load_credentials()
        self._init_exchange()
        self._start_event_loop()

        self._running = True
        logger.info(f"CCXTStore started for {self.exchange_id}")

    def stop(self) -> None:
        """Stop the CCXT store and clean up resources."""
        if not self._running:
            return

        self._running = False

        # Close exchange connection
        if self._exchange:
            self.run_coroutine(self._exchange.close())

        # Stop event loop
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        # Wait for thread to finish
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
            raise TimeoutError(f"Coroutine execution exceeded {timeout}s timeout")

    def _load_credentials(self) -> None:
        """
        Load API credentials from environment variables.

        Expected env var format:
        - CCXT_{EXCHANGE}_{MODE}_API_KEY
        - CCXT_{EXCHANGE}_{MODE}_SECRET
        - CCXT_{EXCHANGE}_{MODE}_PASSPHRASE (for exchanges that require it)

        Raises:
            ValueError: If required credentials not found
        """
        exchange_upper = self.exchange_id.upper()
        mode_upper = self.mode.upper()

        api_key_var = f"CCXT_{exchange_upper}_{mode_upper}_API_KEY"
        secret_var = f"CCXT_{exchange_upper}_{mode_upper}_SECRET"
        passphrase_var = f"CCXT_{exchange_upper}_{mode_upper}_PASSPHRASE"

        self.api_key = os.getenv(api_key_var)
        self.secret = os.getenv(secret_var)
        self.passphrase = os.getenv(passphrase_var)  # Optional, only for some exchanges

        if not self.api_key or not self.secret:
            raise ValueError(
                f"Missing API credentials. Set {api_key_var} and {secret_var} "
                f"in environment variables."
            )

        logger.info(f"Loaded credentials for {self.exchange_id} {self.mode} mode")

    def _init_exchange(self) -> None:
        """
        Initialize CCXT exchange instance.

        Configures exchange with:
        - API credentials
        - Testnet/sandbox URL for paper trading
        - Rate limits and other options

        Raises:
            ValueError: If exchange ID not supported
        """
        # Get exchange class
        exchange_class = getattr(ccxt, self.exchange_id, None)
        if not exchange_class:
            raise ValueError(f"Unsupported exchange: {self.exchange_id}")

        # Build exchange config
        exchange_config = {
            'apiKey': self.api_key,
            'secret': self.secret,
            'enableRateLimit': True,
            'timeout': 30000,  # 30 seconds
        }

        # Add passphrase if present (required for OKX)
        if self.passphrase:
            exchange_config['password'] = self.passphrase

        # Set sandbox URL for paper trading
        if self.mode == 'paper':
            exchange_config['sandbox'] = True

            # Exchange-specific testnet URLs
            testnet_urls = {
                'binance': {
                    'test': True,
                },
                'okx': {
                    'hostname': 'www.okx.com',  # OKX uses same URL for testnet
                },
                'bybit': {
                    'hostname': 'api-testnet.bybit.com',
                }
            }

            if self.exchange_id in testnet_urls:
                exchange_config.update(testnet_urls[self.exchange_id])

        # Initialize exchange
        self._exchange = exchange_class(exchange_config)

        logger.info(f"Initialized {self.exchange_id} exchange (sandbox={self.mode == 'paper'})")

    def _start_event_loop(self) -> None:
        """
        Start asyncio event loop in background thread.

        This allows async CCXT operations to run concurrently with
        Backtrader's synchronous execution.
        """
        def run_loop():
            """Background thread function that runs event loop."""
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            try:
                self._loop.run_forever()
            finally:
                # Clean up pending tasks
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()

                # Run until all tasks are cancelled
                self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                self._loop.close()

        self._thread = threading.Thread(target=run_loop, daemon=True, name=f"CCXT-{self.exchange_id}")
        self._thread.start()

        # Wait for loop to start
        import time
        timeout = 5
        start_time = time.time()
        while not self._loop or not self._loop.is_running():
            if time.time() - start_time > timeout:
                raise RuntimeError("Failed to start event loop within timeout")
            time.sleep(0.1)

        logger.info("Event loop started in background thread")

    async def _fetch_with_retry(self, coro: Any, max_attempts: int = 3) -> Any:
        """
        Execute coroutine with retry logic on network failures.

        Args:
            coro: Coroutine to execute
            max_attempts: Maximum number of retry attempts

        Returns:
            Result of coroutine execution

        Raises:
            Exception: If all retry attempts fail
        """
        last_error = None

        for attempt in range(max_attempts):
            try:
                return await coro
            except ccxt.NetworkError as e:
                last_error = e
                if attempt < max_attempts - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"Network error on attempt {attempt + 1}/{max_attempts}: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {max_attempts} attempts failed")
            except Exception as e:
                # Non-network errors are not retried
                logger.error(f"Non-retryable error: {e}")
                raise

        raise last_error

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
