"""
Binance Store - Connection management for Binance Spot/Futures via python-binance.

Responsibilities:
- REST client for market data and trading
- ThreadedWebsocketManager for real-time ticker/kline streams
- User Data Stream for account/order updates
- Binance testnet/live connection management
"""

import asyncio
import logging
from decimal import Decimal, ROUND_DOWN
import threading
import time
from typing import Callable, Dict, List, Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance import ThreadedWebsocketManager

logger = logging.getLogger(__name__)

# Import shared constants from package — avoids duplication
# (circular import safe: __init__.py imports us, but these are module-level constants)
from .common import TIMEFRAME_INTERVALS, TIMEFRAME_SECONDS, normalize_symbol

class BinanceStore:
    """
    Store for Binance Spot/Futures trading via python-binance.

    Manages:
    - REST client for market data queries and order placement
    - WebSocket streams for real-time ticker and kline updates
    - User Data Stream for account/order push notifications (live mode)
    - Paper trading simulation (no real API calls required)
    """

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        mode: str = "paper",
        exchange_id: Optional[str] = None,
        config: Optional[dict] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.mode = mode
        self.session_id = session_id
        self.config = config or {}
        self.market = str(self.config.get("default_market") or "spot").lower()

        self._running = False
        self._client: Optional[Client] = None

        # Paper trading state
        self._paper_mode = mode == "paper"

        # WebSocket state
        self._twm = None
        self._twm_started = False
        self._twm_loop: Optional[asyncio.AbstractEventLoop] = None
        self._active_streams: Dict[str, str] = {}
        self._stream_specs: Dict[str, dict] = {}
        self._stream_lock = threading.Lock()
        self._ws_recovering = False

        # Callbacks
        self._ticker_callback: Optional[Callable] = None
        self._kline_callbacks: Dict[str, Callable] = {}
        self._user_data_callback: Optional[Callable] = None

        # User Data Stream
        self._listen_key: Optional[str] = None
        self._listen_key_timer: Optional[threading.Timer] = None
        self._symbol_info_cache: Dict[str, dict] = {}

        logger.info(f"BinanceStore initialized: mode={mode}, session={session_id}")

    # ═══════════════════════════════ Lifecycle ═══════════════════════════════

    def start(self) -> None:
        """Start the store and connect to Binance or Binance testnet."""
        if self._running:
            return
        try:
            self._client = Client(
                self.api_key,
                self.api_secret,
                testnet=self._paper_mode,
            )
            if self.is_futures_market() and hasattr(self._client, "futures_ping"):
                self._client.futures_ping()
            else:
                self._client.ping()
            logger.info("BinanceStore started (%s mode, %s market)", self.mode, self.market)
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            raise
        self._running = True

    def stop(self) -> None:
        """Stop the store and clean up all connections."""
        logger.info("BinanceStore stopping")
        self._running = False
        self._stop_all_streams(clear_specs=True)
        self._stop_user_data_stream()
        self._shutdown_twm()
        logger.info("BinanceStore stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    def get_client(self) -> Client:
        if not self._client:
            raise RuntimeError("Store not started")
        return self._client

    def is_futures_market(self) -> bool:
        return self.market == "futures"

    # ═══════════════════════════ Callback Registration ═══════════════════════

    def set_ticker_callback(self, callback: Callable) -> None:
        """Register a callback for real-time ticker updates.
        Callback receives: {last, bid, ask, high, low, volume, timestamp}
        """
        self._ticker_callback = callback
        logger.info("Ticker callback registered")

    def set_user_data_callback(self, callback: Callable) -> None:
        """Register for User Data Stream events (executionReport, etc.)."""
        self._user_data_callback = callback

    # ═══════════════════════════ WebSocket Streams ═══════════════════════════

    def _ensure_twm(self) -> None:
        """Lazily initialize ThreadedWebsocketManager."""
        if self._twm_started and self._twm and self._twm.is_alive():
            return
        if self._twm_started:
            logger.warning("ThreadedWebsocketManager is marked started but not alive; recreating it")
            self._shutdown_twm()
        try:
            self._twm_loop = asyncio.new_event_loop()
            self._twm = ThreadedWebsocketManager(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=self._paper_mode,
                loop=self._twm_loop,
            )
            self._twm.start()
            self._twm_started = True
            logger.info("ThreadedWebsocketManager started")
        except Exception as e:
            logger.error(f"Failed to start ThreadedWebsocketManager: {e}")
            self._shutdown_twm()

    def _shutdown_twm(self) -> None:
        """Stop the websocket manager thread and release its private event loop."""
        twm = self._twm
        loop = self._twm_loop

        if twm:
            try:
                twm.stop()
            except Exception as e:
                logger.debug(f"TWM stop error (expected): {e}")

            try:
                if twm.is_alive():
                    twm.join(timeout=5)
                    if twm.is_alive():
                        logger.warning("ThreadedWebsocketManager did not stop within timeout")
            except Exception as e:
                logger.debug(f"TWM join error: {e}")

        if loop and not loop.is_closed():
            try:
                loop.close()
            except Exception as e:
                logger.debug(f"TWM loop close error: {e}")

        self._twm = None
        self._twm_started = False
        self._twm_loop = None

    def start_ticker_stream(self, symbol: str) -> None:
        """Start real-time ticker stream."""
        if not self._ticker_callback:
            return

        stream_name = f"ticker_{symbol}"
        if stream_name in self._active_streams:
            return
        self._stream_specs[stream_name] = {
            'kind': 'ticker',
            'symbol': symbol,
        }

        self._ensure_twm()
        if not self._twm:
            return

        def _on_msg(msg: dict):
            if msg.get('e') == 'error':
                logger.error(f"Ticker stream error: {msg}")
                self._handle_socket_error(stream_name, msg)
                return
            if self._ticker_callback:
                try:
                    self._ticker_callback({
                        'last': float(msg.get('c', 0)),
                        'bid': float(msg.get('b', 0)),
                        'ask': float(msg.get('a', 0)),
                        'high': float(msg.get('h', 0)),
                        'low': float(msg.get('l', 0)),
                        'volume': float(msg.get('v', 0)),
                        'timestamp': msg.get('E'),
                    })
                except Exception as e:
                    logger.debug(f"Ticker callback error: {e}")

        try:
            socket_fn = getattr(
                self._twm,
                "start_symbol_ticker_futures_socket" if self.is_futures_market() else "start_symbol_ticker_socket",
                None,
            ) or getattr(self._twm, "start_symbol_ticker_socket")
            key = socket_fn(callback=_on_msg, symbol=normalize_symbol(symbol).lower())
            self._active_streams[stream_name] = key
            logger.info(f"Ticker stream started for {symbol}")
        except Exception as e:
            logger.error(f"Failed to start ticker stream: {e}")

    def start_kline_stream(self, symbol: str, interval: str, callback: Callable) -> None:
        """Start real-time kline stream.
        Callback receives: {time_ms, open, high, low, close, volume, is_closed}
        """
        stream_name = f"kline_{symbol}_{interval}"
        if stream_name in self._active_streams:
            return
        self._stream_specs[stream_name] = {
            'kind': 'kline',
            'symbol': symbol,
            'interval': interval,
            'callback': callback,
        }

        self._ensure_twm()
        if not self._twm:
            return

        self._kline_callbacks[stream_name] = callback

        def _on_msg(msg: dict):
            if msg.get('e') == 'error':
                logger.error(f"Kline stream error: {msg}")
                self._handle_socket_error(stream_name, msg)
                return
            k = msg.get('k', {})
            if not k:
                return
            cb = self._kline_callbacks.get(stream_name)
            if cb:
                try:
                    cb({
                        'time_ms': k.get('t'),
                        'open': float(k.get('o', 0)),
                        'high': float(k.get('h', 0)),
                        'low': float(k.get('l', 0)),
                        'close': float(k.get('c', 0)),
                        'volume': float(k.get('v', 0)),
                        'is_closed': k.get('x', False),
                    })
                except Exception as e:
                    logger.debug(f"Kline callback error: {e}")

        try:
            socket_fn = getattr(
                self._twm,
                "start_kline_futures_socket" if self.is_futures_market() else "start_kline_socket",
                None,
            ) or getattr(self._twm, "start_kline_socket")
            key = socket_fn(
                callback=_on_msg,
                symbol=normalize_symbol(symbol).lower(),
                interval=TIMEFRAME_INTERVALS.get(interval, interval),
            )
            self._active_streams[stream_name] = key
            logger.info(f"Kline stream started for {symbol} [{interval}]")
        except Exception as e:
            logger.error(f"Failed to start kline stream: {e}")

    def start_user_data_stream(self, callback: Optional[Callable] = None) -> None:
        """Start User Data Stream for account/order push."""
        if callback:
            self._user_data_callback = callback
        if 'user_data' in self._active_streams:
            return
        self._stream_specs['user_data'] = {
            'kind': 'user_data',
        }
        self._ensure_twm()
        if not self._twm:
            return

        def _on_msg(msg: dict):
            if msg.get('e') == 'error':
                logger.error(f"User data stream error: {msg}")
                self._handle_socket_error('user_data', msg)
                return
            if self._user_data_callback:
                try:
                    self._user_data_callback(msg)
                except Exception as e:
                    logger.warning(f"User data callback error: {e}")

        try:
            socket_fn = getattr(
                self._twm,
                "start_futures_user_socket" if self.is_futures_market() else "start_user_socket",
                None,
            ) or getattr(self._twm, "start_user_socket")
            key = socket_fn(callback=_on_msg)
            self._active_streams['user_data'] = key
            logger.info("User data stream started")
        except Exception as e:
            logger.error(f"Failed to start user data stream: {e}")

    def _stop_all_streams(self, clear_specs: bool = False) -> None:
        if not self._twm:
            if clear_specs:
                self._stream_specs.clear()
            return
        for name, key in list(self._active_streams.items()):
            try:
                self._twm.stop_socket(key)
            except Exception:
                pass
        self._active_streams.clear()
        self._kline_callbacks.clear()
        if clear_specs:
            self._stream_specs.clear()

    def _handle_socket_error(self, stream_name: str, msg: dict) -> None:
        if not self._running:
            return

        error_type = str(msg.get('type') or '')
        error_message = str(msg.get('m') or '')
        should_recover = (
            error_type == 'ReadLoopClosed'
            or 'read loop has been closed' in error_message.lower()
        )
        if not should_recover:
            return

        logger.warning("Recovering Binance websocket connection after %s on %s", error_type or 'socket error', stream_name)
        self._schedule_websocket_recovery()

    def _schedule_websocket_recovery(self) -> None:
        with self._stream_lock:
            if self._ws_recovering or not self._running:
                return
            self._ws_recovering = True

        def _recover():
            try:
                self._recover_websocket_connection()
            finally:
                with self._stream_lock:
                    self._ws_recovering = False

        threading.Thread(target=_recover, name="binance-ws-recover", daemon=True).start()

    def _recover_websocket_connection(self) -> None:
        specs = dict(self._stream_specs)
        if not specs or not self._running:
            return

        self._stop_all_streams(clear_specs=False)
        self._shutdown_twm()
        time.sleep(0.2)

        for stream_name, spec in specs.items():
            kind = spec.get('kind')
            try:
                if kind == 'ticker':
                    self.start_ticker_stream(spec['symbol'])
                elif kind == 'kline':
                    callback = spec.get('callback')
                    if callback:
                        self.start_kline_stream(spec['symbol'], spec['interval'], callback)
                elif kind == 'user_data':
                    self.start_user_data_stream()
            except Exception as exc:
                logger.warning(f"Failed to recover stream {stream_name}: {exc}")

    def _stop_user_data_stream(self) -> None:
        if self._listen_key_timer:
            self._listen_key_timer.cancel()
            self._listen_key_timer = None

    # ═══════════════════════════ REST: Market Data ═══════════════════════════

    def fetch_ticker(self, symbol: str) -> dict:
        """Fetch ticker via REST. Returns {last, bid, ask, high, low, volume, timestamp}."""
        sym = normalize_symbol(symbol)

        try:
            if self.is_futures_market():
                fetch_fn = getattr(self._client, "futures_ticker", None)
                if fetch_fn:
                    t = fetch_fn(symbol=sym)
                else:
                    ticker = self._client.futures_symbol_ticker(symbol=sym)
                    book_ticker = self._client.futures_orderbook_ticker(symbol=sym)
                    t = {**ticker, **book_ticker}
            else:
                t = self._client.get_ticker(symbol=sym)
            return {
                'last': float(t.get('lastPrice', 0)),
                'bid': float(t.get('bidPrice', 0)),
                'ask': float(t.get('askPrice', 0)),
                'high': float(t.get('highPrice', 0)),
                'low': float(t.get('lowPrice', 0)),
                'volume': float(t.get('volume', 0)),
                'timestamp': t.get('closeTime') or t.get('time') or int(time.time() * 1000),
            }
        except BinanceAPIException as e:
            logger.error(f"Failed to fetch ticker for {symbol}: {e}")
            raise

    def fetch_ohlcv(
        self, symbol: str, interval: str = '1m',
        limit: int = 100, since_ms: Optional[int] = None,
    ) -> List[list]:
        """Fetch OHLCV via REST. Returns [[ts, o, h, l, c, v], ...]."""
        sym = normalize_symbol(symbol)

        try:
            params = self._build_kline_params(sym, interval, limit, since_ms)
            bars = [
                [k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])]
                for k in (
                    self._client.futures_klines(**params)
                    if self.is_futures_market() else
                    self._client.get_klines(**params)
                )
            ]
            return bars
        except BinanceAPIException as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
            raise

    def get_symbol_ticker(self, symbol: str) -> dict:
        """Get current price. Returns {symbol, price}."""
        sym = normalize_symbol(symbol)

        try:
            r = (
                self._client.futures_symbol_ticker(symbol=sym)
                if self.is_futures_market() else
                self._client.get_symbol_ticker(symbol=sym)
            )
            return {'symbol': r['symbol'], 'price': float(r['price'])}
        except BinanceAPIException as e:
            logger.error(f"Failed to get ticker: {e}")
            raise

    def get_order_book_ticker(self, symbol: str) -> dict:
        """Get best bid/ask."""
        sym = normalize_symbol(symbol)

        try:
            if self.is_futures_market():
                return self._client.futures_orderbook_ticker(symbol=sym)
            return self._client.get_order_book_ticker(symbol=sym)
        except BinanceAPIException as e:
            logger.error(f"Failed to get order book ticker: {e}")
            raise

    def get_order_book(self, symbol: str, limit: int = 10) -> dict:
        """Get market depth for a symbol."""
        sym = normalize_symbol(symbol)

        try:
            if self.is_futures_market():
                return self._client.futures_order_book(symbol=sym, limit=limit)
            return self._client.get_order_book(symbol=sym, limit=limit)
        except BinanceAPIException as e:
            logger.error(f"Failed to get order book for {symbol}: {e}")
            raise

    def get_klines(
        self, symbol: str, interval: str,
        limit: int = 500, start_time: Optional[int] = None,
    ) -> list:
        """Get raw klines (12-element Binance format). Use fetch_ohlcv() for normalized output."""
        sym = normalize_symbol(symbol)

        try:
            params = self._build_kline_params(sym, interval, limit, start_time)
            if self.is_futures_market():
                return self._client.futures_klines(**params)
            return self._client.get_klines(**params)
        except BinanceAPIException as e:
            logger.error(f"Failed to get klines: {e}")
            raise

    # ═══════════════════════════ REST: Trading ═══════════════════════════

    def create_order(
        self, symbol: str, side: str, order_type: str,
        quantity: float, price: Optional[float] = None,
    ) -> dict:
        sym = normalize_symbol(symbol)

        try:
            normalized_quantity = self.normalize_quantity(sym, quantity)
            params = {
                'symbol': sym,
                'side': side,
                'type': order_type,
                'quantity': self._decimal_to_str(normalized_quantity),
            }
            if order_type == 'LIMIT' and price:
                params['price'] = str(price)
                params['timeInForce'] = 'GTC'
            if self.is_futures_market():
                return self._client.futures_create_order(**params)
            return self._client.create_order(**params)
        except BinanceAPIException as e:
            logger.error(f"Failed to create order: {e}")
            raise

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        sym = normalize_symbol(symbol)

        try:
            if self.is_futures_market():
                return self._client.futures_cancel_order(symbol=sym, orderId=order_id)
            return self._client.cancel_order(symbol=sym, orderId=order_id)
        except BinanceAPIException as e:
            logger.error(f"Failed to cancel order: {e}")
            raise

    def get_order(self, symbol: str, order_id: int) -> dict:
        sym = normalize_symbol(symbol)

        try:
            if self.is_futures_market():
                return self._client.futures_get_order(symbol=sym, orderId=order_id)
            return self._client.get_order(symbol=sym, orderId=order_id)
        except BinanceAPIException as e:
            logger.error(f"Failed to get order: {e}")
            raise

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        try:
            params = {}
            if symbol:
                params['symbol'] = normalize_symbol(symbol)
            if self.is_futures_market():
                return self._client.futures_get_open_orders(**params)
            return self._client.get_open_orders(**params)
        except BinanceAPIException as e:
            logger.error(f"Failed to get open orders: {e}")
            raise

    def get_all_orders(self, symbol: str, limit: int = 100) -> list:
        try:
            params = {
                'symbol': normalize_symbol(symbol),
                'limit': limit,
            }
            if self.is_futures_market():
                return self._client.futures_get_all_orders(**params)
            return self._client.get_all_orders(**params)
        except BinanceAPIException as e:
            logger.error(f"Failed to get all orders for {symbol}: {e}")
            raise

    def get_my_trades(self, symbol: str, limit: int = 100) -> list:
        try:
            params = {
                'symbol': normalize_symbol(symbol),
                'limit': limit,
            }
            if self.is_futures_market():
                return self._client.futures_account_trades(**params)
            return self._client.get_my_trades(**params)
        except BinanceAPIException as e:
            logger.error(f"Failed to get trade history for {symbol}: {e}")
            raise

    def get_account(self) -> dict:
        try:
            if self.is_futures_market():
                return self._client.futures_account()
            return self._client.get_account()
        except BinanceAPIException as e:
            logger.error(f"Failed to get account: {e}")
            raise

    def get_position_information(self, symbol: Optional[str] = None) -> list:
        if not self.is_futures_market():
            return []
        params = {}
        if symbol:
            params["symbol"] = normalize_symbol(symbol)
        try:
            return self._client.futures_position_information(**params)
        except BinanceAPIException as e:
            logger.error(f"Failed to get futures positions for {symbol}: {e}")
            raise

    # ═══════════════════════════ Paper Trading ═══════════════════════════

    def is_paper_mode(self) -> bool:
        return self._paper_mode

    def uses_exchange_account_data(self) -> bool:
        """Whether balances/orders are sourced from exchange APIs."""
        return True

    def get_symbol_trading_rules(self, symbol: str) -> dict:
        sym = normalize_symbol(symbol)
        filter_types = ['LOT_SIZE']
        if self.is_futures_market():
            filter_types.insert(0, 'MARKET_LOT_SIZE')

        lot_filter = None
        for filter_type in filter_types:
            try:
                lot_filter = self._get_symbol_filter(sym, filter_type)
                break
            except ValueError:
                continue
        if lot_filter is None:
            raise ValueError(f"LOT_SIZE filter unavailable for {sym}")

        min_notional = None
        try:
            notional_filter = self._get_symbol_filter(sym, 'NOTIONAL')
            min_notional = notional_filter.get('minNotional')
        except ValueError:
            try:
                notional_filter = self._get_symbol_filter(sym, 'MIN_NOTIONAL')
                min_notional = notional_filter.get('minNotional')
            except ValueError:
                min_notional = None

        return {
            'symbol': sym,
            'min_qty': lot_filter.get('minQty'),
            'max_qty': lot_filter.get('maxQty'),
            'step_size': lot_filter.get('stepSize'),
            'min_notional': min_notional,
        }

    def get_symbol_info(self, symbol: str) -> dict:
        sym = normalize_symbol(symbol)
        cached = self._symbol_info_cache.get(sym)
        if cached:
            return cached

        try:
            if self.is_futures_market():
                exchange_info = self._client.futures_exchange_info()
                info = next(
                    (item for item in exchange_info.get('symbols', []) if item.get('symbol') == sym),
                    None,
                )
            else:
                info = self._client.get_symbol_info(sym)
        except BinanceAPIException as e:
            logger.error(f"Failed to get symbol info for {sym}: {e}")
            raise

        if not info:
            raise ValueError(f"Symbol info unavailable for {sym}")

        self._symbol_info_cache[sym] = info
        return info

    def normalize_quantity(self, symbol: str, quantity: float) -> Decimal:
        sym = normalize_symbol(symbol)
        quantity_decimal = Decimal(str(quantity))
        filter_types = ['LOT_SIZE']
        if self.is_futures_market():
            filter_types.insert(0, 'MARKET_LOT_SIZE')

        lot_filter = None
        for filter_type in filter_types:
            try:
                lot_filter = self._get_symbol_filter(sym, filter_type)
                break
            except ValueError:
                continue
        if lot_filter is None:
            raise ValueError(f"LOT_SIZE filter unavailable for {sym}")
        min_qty = Decimal(lot_filter['minQty'])
        max_qty = Decimal(lot_filter['maxQty'])
        step_size = Decimal(lot_filter['stepSize'])

        normalized = quantity_decimal.quantize(step_size, rounding=ROUND_DOWN)
        if step_size > 0:
            normalized = (normalized // step_size) * step_size

        if normalized < min_qty:
            raise ValueError(
                f"Order quantity {self._decimal_to_str(normalized)} is below Binance minQty "
                f"{self._decimal_to_str(min_qty)} for {sym}"
            )
        if normalized > max_qty:
            raise ValueError(
                f"Order quantity {self._decimal_to_str(normalized)} exceeds Binance maxQty "
                f"{self._decimal_to_str(max_qty)} for {sym}"
            )

        return normalized

    def _get_symbol_filter(self, symbol: str, filter_type: str) -> dict:
        info = self.get_symbol_info(symbol)
        for symbol_filter in info.get('filters', []):
            if symbol_filter.get('filterType') == filter_type:
                return symbol_filter
        raise ValueError(f"Filter {filter_type} unavailable for {symbol}")

    @staticmethod
    def _decimal_to_str(value: Decimal) -> str:
        return format(value.normalize(), 'f')

    def _build_kline_params(
        self,
        symbol: str,
        interval: str,
        limit: int,
        start_time: Optional[int] = None,
    ) -> dict:
        params = {
            'symbol': symbol,
            'interval': TIMEFRAME_INTERVALS.get(interval, Client.KLINE_INTERVAL_1MINUTE),
            'limit': limit,
        }
        if start_time:
            params['startTime'] = start_time
        return params
