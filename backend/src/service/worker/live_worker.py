"""
Live Trading Worker - Isolated live/paper trading execution.

This module runs inside the worker process and manages live trading sessions
in complete isolation from the API process.

IMPORTANT: User strategy code is only loaded and executed here,
NEVER in the main API process.
"""

import logging
import threading
import time
from datetime import datetime
from multiprocessing import Queue
from typing import Any, Dict, Optional

from src.service.worker.task_models import (
    LiveEventType,
    LiveTradingEvent,
    LiveTradingTask,
)

logger = logging.getLogger(__name__)


class LiveWorkerSession:
    """
    Manages a live trading session within an isolated worker process.
    
    Handles:
    - Strategy loading and execution
    - Real-time data streaming
    - Order execution via broker
    - Event reporting to main process
    """
    
    def __init__(self, task: LiveTradingTask, event_queue: Queue):
        """
        Initialize the live trading session.
        
        Args:
            task: Live trading task configuration
            event_queue: Queue for sending events to main process
        """
        self.task = task
        self.event_queue = event_queue
        self.session_id = task.session_id
        
        self._cerebro = None
        self._store = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False
        self._current_pnl = 0.0
        self._position_size = 0.0
        self._last_heartbeat = datetime.now()
    
    def start(self) -> None:
        """Start the live trading session in a background thread."""
        if self._is_running:
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_session,
            name=f"LiveSession-{self.session_id[:8]}",
            daemon=True,
        )
        self._thread.start()
        self._is_running = True
        
        logger.info(f"Started live session {self.session_id}")
    
    def stop(self) -> None:
        """Stop the live trading session gracefully."""
        logger.info(f"Stopping live session {self.session_id}")
        self._stop_event.set()
        
        if self._cerebro:
            try:
                # Attempt to stop cerebro if running
                self._cerebro.runstop()
            except Exception as e:
                logger.warning(f"Error stopping cerebro: {e}")
        
        if self._store:
            try:
                self._store.stop()
            except Exception as e:
                logger.warning(f"Error stopping store: {e}")
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10.0)
        
        self._is_running = False
        self._send_event(LiveEventType.STOPPED, {"reason": "manual_stop"})
    
    @property
    def is_running(self) -> bool:
        """Check if session is running."""
        return self._is_running and not self._stop_event.is_set()
    
    def get_heartbeat(self) -> LiveTradingEvent:
        """Generate a heartbeat event with current status."""
        return LiveTradingEvent(
            session_id=self.session_id,
            event_type=LiveEventType.HEARTBEAT,
            data={
                "pnl": self._current_pnl,
                "position": self._position_size,
                "running": self._is_running,
            },
        )
    
    def _run_session(self) -> None:
        """Main session execution loop (runs in thread)."""
        try:
            # Import trading components HERE (in worker, not API process)
            import backtrader as bt
            
            from src.brokers.ccxt_adapter import CCXTBroker, CCXTData, CCXTStore
            from src.service.backtest_engine import TradeRecorder
            from src.service.strategy_repo import read_user_strategy_source
            from src.service.strategy_sandbox import execute_strategy_code
            from src.utils.config_loader import get_exchange_config, load_broker_config
            
            # 1. Load strategy
            try:
                strategy_path, source = read_user_strategy_source(self.task.strategy_name)
            except (FileNotFoundError, ValueError) as exc:
                self._send_event(LiveEventType.ERROR, {"error": str(exc)})
                return
            
            module_globals = execute_strategy_code(
                source,
                module_name=f"user_strategy_{self.task.strategy_name}",
                filename=str(strategy_path),
            )
            strategy_cls = module_globals.get("UserStrategy")
            
            if not strategy_cls or not issubclass(strategy_cls, bt.Strategy):
                self._send_event(
                    LiveEventType.ERROR,
                    {"error": "Invalid UserStrategy class"}
                )
                return
            
            # 2. Initialize broker/data components
            config = self.task.broker_config or load_broker_config()
            ex_config = get_exchange_config(self.task.exchange, config)
            
            if ex_config.adapter.lower() == "ccxt":
                self._store = CCXTStore(
                    exchange_id=ex_config.ccxt_id,
                    mode=self.task.mode,
                    config={
                        "default_market": ex_config.default_market,
                        "markets": ex_config.markets,
                    },
                    user_id=self.task.user_id,
                )
                self._store.start()
                
                broker = CCXTBroker(
                    store=self._store,
                    cash=self.task.initial_cash,
                    commission=self.task.commission,
                    session_id=self.task.session_id,
                )
                data_feed = CCXTData(
                    store=self._store,
                    symbol=self.task.symbol,
                    timeframe=self.task.timeframe,
                )
            else:
                # TODO: Add IBKR support
                self._send_event(
                    LiveEventType.ERROR,
                    {"error": f"Unsupported adapter: {ex_config.adapter}"}
                )
                return
            
            # 3. Setup Cerebro
            self._cerebro = bt.Cerebro()
            self._cerebro.addstrategy(strategy_cls)
            self._cerebro.adddata(data_feed)
            self._cerebro.setbroker(broker)
            
            # Add analyzers using centralized configuration
            from src.service.analyzer_config import configure_analyzers, AnalyzerMode
            configure_analyzers(self._cerebro, AnalyzerMode.LIVE, TradeRecorder)
            
            self._send_event(
                LiveEventType.STATUS_UPDATE,
                {"status": "running", "symbol": self.task.symbol}
            )
            
            # 4. Run cerebro (this will run until stopped)
            logger.info(f"Running cerebro for session {self.session_id}")
            self._cerebro.run()
            
            # 5. Session ended normally
            logger.info(f"Cerebro finished for session {self.session_id}")
            self._send_event(
                LiveEventType.STOPPED,
                {"reason": "completed", "final_value": self._cerebro.broker.getvalue()}
            )
        
        except Exception as e:
            logger.exception(f"Live session {self.session_id} failed: {e}")
            self._send_event(
                LiveEventType.ERROR,
                {"error": str(e), "error_type": type(e).__name__}
            )
        
        finally:
            self._is_running = False
            if self._store:
                try:
                    self._store.stop()
                except Exception:
                    pass
    
    def _send_event(self, event_type: LiveEventType, data: Dict[str, Any]) -> None:
        """Send an event to the main process."""
        event = LiveTradingEvent(
            session_id=self.session_id,
            event_type=event_type,
            data=data,
        )
        try:
            self.event_queue.put(event.to_dict(), timeout=1.0)
        except Exception as e:
            logger.error(f"Failed to send event: {e}")


__all__ = ["LiveWorkerSession"]
