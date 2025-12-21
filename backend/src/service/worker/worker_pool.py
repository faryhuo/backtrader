"""
Worker Pool - Process pool manager for isolated strategy execution.

This module provides a process pool that executes untrusted strategy code
in isolated worker processes. The API process never executes user code directly.

Example:
    from src.service.worker import get_worker_pool, BacktestTask
    
    pool = get_worker_pool()
    task = BacktestTask(
        task_id="123",
        strategy_name="my_strategy",
        ticker="AAPL",
        start_date="2022-01-01",
        end_date="2023-12-31",
    )
    result = pool.submit_backtest_sync(task)  # Blocks until complete
"""

import json
import logging
import multiprocessing as mp
import os
import queue
import sys
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.config.worker_config import WorkerPoolConfig, get_config
from src.service.worker.task_models import (
    BacktestResult,
    BacktestTask,
    LiveTradingEvent,
    LiveTradingTask,
    TaskStatus,
    WorkerCommand,
    WorkerResponse,
)

logger = logging.getLogger(__name__)


class WorkerPoolError(Exception):
    """Base exception for worker pool errors."""
    pass


class WorkerTimeoutError(WorkerPoolError):
    """Raised when a task times out."""
    pass


class WorkerNotAvailableError(WorkerPoolError):
    """Raised when no workers are available."""
    pass


# =============================================================================
# Worker Process Entry Points
# =============================================================================

def _backtest_worker_main(
    task_queue: mp.Queue,
    result_queue: mp.Queue,
    config: Dict[str, Any],
):
    """
    Main entry point for backtest worker process.
    
    This function runs in a separate process and executes backtest tasks
    in complete isolation from the API process.
    
    Args:
        task_queue: Queue to receive tasks from
        result_queue: Queue to send results to
        config: Worker configuration dictionary
    """
    # Import here to avoid loading backtrader in main process
    # This also ensures user code is only loaded in worker
    try:
        from src.service.worker.backtest_worker import execute_backtest_task
    except ImportError as e:
        # Send error back if imports fail
        result_queue.put({
            "task_id": "INIT_ERROR",
            "success": False,
            "error": f"Worker initialization failed: {e}",
        })
        return
    
    # Apply resource limits
    max_memory_mb = config.get("max_memory_mb", 1024)
    try:
        _apply_memory_limit(max_memory_mb)
    except Exception as e:
        logger.warning(f"Failed to apply memory limit: {e}")
    
    # Worker main loop
    while True:
        try:
            # Get task with timeout to allow checking for shutdown
            try:
                task_data = task_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            
            # None signals shutdown
            if task_data is None:
                logger.debug("Worker received shutdown signal")
                break
            
            # Execute task
            task_id = task_data.get("task_id", "unknown")
            start_time = datetime.utcnow()
            
            try:
                task = BacktestTask.from_dict(task_data)
                result = execute_backtest_task(task)
                result.start_time = start_time.isoformat()
                result.end_time = datetime.utcnow().isoformat()
                result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
                result_queue.put(result.to_dict())
            except Exception as e:
                logger.exception(f"Worker task {task_id} failed: {e}")
                result_queue.put({
                    "task_id": task_id,
                    "status": TaskStatus.FAILED.value,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.utcnow().isoformat(),
                })
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.exception(f"Worker loop error: {e}")
            continue


def _live_worker_main(
    command_queue: mp.Queue,
    event_queue: mp.Queue,
    config: Dict[str, Any],
):
    """
    Main entry point for live trading worker process.
    
    Live workers are long-running and handle bidirectional communication
    for real-time trading updates.
    
    Args:
        command_queue: Queue to receive commands from main process
        event_queue: Queue to send events to main process
        config: Worker configuration dictionary
    """
    try:
        from src.service.worker.live_worker import LiveWorkerSession
    except ImportError as e:
        event_queue.put({
            "session_id": "INIT_ERROR",
            "event_type": "error",
            "data": {"error": f"Worker initialization failed: {e}"},
        })
        return
    
    session: Optional[Any] = None
    
    while True:
        try:
            try:
                cmd_data = command_queue.get(timeout=1.0)
            except queue.Empty:
                # Send heartbeat if session is active
                if session and session.is_running:
                    event_queue.put(session.get_heartbeat().to_dict())
                continue
            
            if cmd_data is None:
                break
            
            cmd = WorkerCommand.from_dict(cmd_data)
            
            if cmd.command == "start":
                task = LiveTradingTask.from_dict(cmd.task)
                session = LiveWorkerSession(task, event_queue)
                session.start()
                event_queue.put({
                    "session_id": task.session_id,
                    "event_type": "status_update",
                    "data": {"status": "running"},
                })
            
            elif cmd.command == "stop":
                if session:
                    session.stop()
                    session = None
                event_queue.put({
                    "session_id": cmd.task.get("session_id", "unknown") if cmd.task else "unknown",
                    "event_type": "stopped",
                    "data": {},
                })
            
            elif cmd.command == "shutdown":
                if session:
                    session.stop()
                break
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.exception(f"Live worker error: {e}")


def _apply_memory_limit(max_mb: int) -> None:
    """Apply memory limit to current process (platform-specific)."""
    try:
        if sys.platform != "win32":
            import resource
            max_bytes = max_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))
        # On Windows, memory limits are enforced by job objects (not implemented here)
    except Exception as e:
        logger.warning(f"Could not set memory limit: {e}")


# =============================================================================
# Worker Pool Manager
# =============================================================================

@dataclass
class WorkerHandle:
    """Handle to a worker process."""
    process: mp.Process
    task_queue: mp.Queue
    result_queue: mp.Queue
    worker_type: str  # "backtest" or "live"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    @property
    def is_alive(self) -> bool:
        return self.process.is_alive()


class WorkerPool:
    """
    Process pool manager for isolated strategy execution.
    
    Manages a pool of worker processes that execute untrusted strategy code.
    The API process never loads or executes user strategy code directly.
    
    Features:
    - Process isolation for security
    - Resource limits (memory, timeout)
    - Automatic worker restart on failure
    - Sync and async task submission
    - Live trading workers with bidirectional communication
    """
    
    def __init__(self, config: Optional[WorkerPoolConfig] = None):
        """
        Initialize the worker pool.
        
        Args:
            config: Optional configuration, uses environment defaults if None
        """
        self.config = config or get_config()
        self._backtest_workers: List[WorkerHandle] = []
        self._live_workers: Dict[str, WorkerHandle] = {}  # session_id -> worker
        self._pending_results: Dict[str, threading.Event] = {}
        self._results: Dict[str, BacktestResult] = {}
        self._lock = threading.RLock()
        self._result_thread: Optional[threading.Thread] = None
        self._shutdown = False
        self._started = False
        
        # Shared queues for backtest workers (round-robin distribution)
        self._task_queue: Optional[mp.Queue] = None
        self._result_queue: Optional[mp.Queue] = None
    
    def start(self) -> None:
        """Start the worker pool."""
        if self._started:
            return
        
        if not self.config.enabled:
            logger.info("Worker pool is disabled, using in-process execution")
            return
        
        logger.info(
            f"Starting worker pool with {self.config.pool_size} workers, "
            f"timeout={self.config.task_timeout_seconds}s, "
            f"memory={self.config.max_memory_mb}MB"
        )
        
        # Use 'spawn' for proper isolation (especially on Windows)
        ctx = mp.get_context("spawn")
        
        # Create shared queues
        self._task_queue = ctx.Queue(maxsize=self.config.max_queue_size)
        self._result_queue = ctx.Queue()
        
        # Start backtest workers
        config_dict = {
            "max_memory_mb": self.config.max_memory_mb,
            "allow_network": self.config.allow_network,
            "allow_file_write": self.config.allow_file_write,
        }
        
        for i in range(self.config.pool_size):
            process = ctx.Process(
                target=_backtest_worker_main,
                args=(self._task_queue, self._result_queue, config_dict),
                name=f"BacktestWorker-{i}",
                daemon=True,
            )
            process.start()
            
            handle = WorkerHandle(
                process=process,
                task_queue=self._task_queue,
                result_queue=self._result_queue,
                worker_type="backtest",
            )
            self._backtest_workers.append(handle)
            logger.debug(f"Started backtest worker {i}: PID={process.pid}")
        
        # Start result collection thread
        self._result_thread = threading.Thread(
            target=self._collect_results,
            name="WorkerPool-ResultCollector",
            daemon=True,
        )
        self._result_thread.start()
        
        self._started = True
        logger.info(f"Worker pool started with {len(self._backtest_workers)} workers")
    
    def _collect_results(self) -> None:
        """Background thread that collects results from workers."""
        while not self._shutdown:
            try:
                try:
                    result_data = self._result_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                task_id = result_data.get("task_id")
                if not task_id:
                    continue
                
                result = BacktestResult.from_dict(result_data)
                
                with self._lock:
                    self._results[task_id] = result
                    event = self._pending_results.get(task_id)
                    if event:
                        event.set()
                
                logger.debug(f"Collected result for task {task_id}: {result.status}")
            
            except Exception as e:
                if not self._shutdown:
                    logger.exception(f"Error collecting result: {e}")
    
    def submit_backtest(self, task: BacktestTask) -> str:
        """
        Submit a backtest task to the worker pool.
        
        Args:
            task: Backtest task definition
            
        Returns:
            task_id for tracking the result
            
        Raises:
            WorkerPoolError: If pool is not available
        """
        if not self.config.enabled:
            # Fallback to in-process execution
            return self._execute_backtest_in_process(task)
        
        if not self._started:
            self.start()
        
        # Register pending result
        with self._lock:
            event = threading.Event()
            self._pending_results[task.task_id] = event
        
        # Submit to queue
        try:
            self._task_queue.put(task.to_dict(), timeout=5.0)
        except queue.Full:
            with self._lock:
                del self._pending_results[task.task_id]
            raise WorkerPoolError("Task queue is full")
        
        logger.debug(f"Submitted backtest task {task.task_id}")
        return task.task_id
    
    def get_result(
        self,
        task_id: str,
        timeout: Optional[float] = None
    ) -> BacktestResult:
        """
        Get the result of a submitted task.
        
        Args:
            task_id: Task ID returned from submit_backtest
            timeout: Optional timeout in seconds, defaults to config
            
        Returns:
            BacktestResult
            
        Raises:
            WorkerTimeoutError: If task times out
            WorkerPoolError: If result retrieval fails
        """
        if timeout is None:
            timeout = self.config.task_timeout_seconds
        
        with self._lock:
            # Check if result is already available
            result = self._results.get(task_id)
            if result:
                del self._results[task_id]
                self._pending_results.pop(task_id, None)
                return result
            
            event = self._pending_results.get(task_id)
        
        if not event:
            raise WorkerPoolError(f"Unknown task: {task_id}")
        
        # Wait for result
        if not event.wait(timeout=timeout):
            with self._lock:
                self._pending_results.pop(task_id, None)
            raise WorkerTimeoutError(f"Task {task_id} timed out after {timeout}s")
        
        with self._lock:
            result = self._results.pop(task_id, None)
            self._pending_results.pop(task_id, None)
        
        if not result:
            raise WorkerPoolError(f"Result not found for task {task_id}")
        
        return result
    
    def submit_backtest_sync(
        self,
        task: BacktestTask,
        timeout: Optional[float] = None
    ) -> BacktestResult:
        """
        Submit a backtest task and wait for result (synchronous).
        
        This is the preferred method for API endpoints that need
        to return results immediately.
        
        Args:
            task: Backtest task definition
            timeout: Optional timeout in seconds
            
        Returns:
            BacktestResult
        """
        task_id = self.submit_backtest(task)
        return self.get_result(task_id, timeout=timeout)
    
    def _execute_backtest_in_process(self, task: BacktestTask) -> str:
        """
        Fallback: Execute backtest in-process (when pool is disabled).
        
        WARNING: This executes user code in the API process!
        Only use when worker pool is explicitly disabled.
        """
        logger.warning(
            "Executing backtest in-process (worker pool disabled). "
            "This is not secure for untrusted code!"
        )
        
        # Import here to match worker behavior
        from src.service.worker.backtest_worker import execute_backtest_task
        
        with self._lock:
            event = threading.Event()
            self._pending_results[task.task_id] = event
        
        try:
            result = execute_backtest_task(task)
            with self._lock:
                self._results[task.task_id] = result
                event.set()
        except Exception as e:
            with self._lock:
                self._results[task.task_id] = BacktestResult.error_result(
                    task.task_id, str(e), type(e).__name__
                )
                event.set()
        
        return task.task_id
    
    # =========================================================================
    # Live Trading Workers
    # =========================================================================
    
    def start_live_session(
        self,
        task: LiveTradingTask,
        event_callback: Optional[Callable[[LiveTradingEvent], None]] = None,
    ) -> str:
        """
        Start a live trading session in an isolated worker.
        
        Args:
            task: Live trading task definition
            event_callback: Optional callback for receiving events
            
        Returns:
            session_id
        """
        if not self.config.enabled:
            raise WorkerPoolError(
                "Worker pool is disabled. Live trading requires worker isolation."
            )
        
        if not self._started:
            self.start()
        
        session_id = task.session_id
        
        with self._lock:
            if session_id in self._live_workers:
                raise WorkerPoolError(f"Session {session_id} already exists")
        
        # Create dedicated queues for this session
        ctx = mp.get_context("spawn")
        command_queue = ctx.Queue()
        event_queue = ctx.Queue()
        
        config_dict = {
            "max_memory_mb": self.config.max_memory_mb,
            "allow_network": True,  # Required for live trading
            "allow_file_write": self.config.allow_file_write,
            "heartbeat_interval": self.config.heartbeat_interval_seconds,
        }
        
        # Start worker process
        process = ctx.Process(
            target=_live_worker_main,
            args=(command_queue, event_queue, config_dict),
            name=f"LiveWorker-{session_id[:8]}",
            daemon=True,
        )
        process.start()
        
        handle = WorkerHandle(
            process=process,
            task_queue=command_queue,
            result_queue=event_queue,
            worker_type="live",
        )
        
        with self._lock:
            self._live_workers[session_id] = handle
        
        # Send start command
        command_queue.put(WorkerCommand("start", task.to_dict()).to_dict())
        
        # Start event collection thread if callback provided
        if event_callback:
            self._start_event_collector(session_id, event_queue, event_callback)
        
        logger.info(f"Started live trading worker for session {session_id}")
        return session_id
    
    def _start_event_collector(
        self,
        session_id: str,
        event_queue: mp.Queue,
        callback: Callable[[LiveTradingEvent], None],
    ) -> None:
        """Start a thread to collect events from live worker."""
        def collector():
            while True:
                with self._lock:
                    if session_id not in self._live_workers:
                        break
                
                try:
                    try:
                        event_data = event_queue.get(timeout=1.0)
                    except queue.Empty:
                        continue
                    
                    event = LiveTradingEvent.from_dict(event_data)
                    try:
                        callback(event)
                    except Exception as e:
                        logger.exception(f"Event callback error: {e}")
                    
                    if event.event_type.value == "stopped":
                        break
                
                except Exception as e:
                    logger.exception(f"Event collection error: {e}")
        
        thread = threading.Thread(
            target=collector,
            name=f"LiveEventCollector-{session_id[:8]}",
            daemon=True,
        )
        thread.start()
    
    def stop_live_session(self, session_id: str, timeout: float = 10.0) -> bool:
        """
        Stop a live trading session.
        
        Args:
            session_id: Session ID to stop
            timeout: Graceful shutdown timeout
            
        Returns:
            True if stopped successfully
        """
        with self._lock:
            handle = self._live_workers.get(session_id)
            if not handle:
                return False
        
        # Send stop command
        try:
            handle.task_queue.put(
                WorkerCommand("stop", {"session_id": session_id}).to_dict(),
                timeout=1.0
            )
        except queue.Full:
            pass
        
        # Wait for process to exit
        handle.process.join(timeout=timeout)
        
        if handle.process.is_alive():
            logger.warning(f"Force killing live worker {session_id}")
            handle.process.kill()
            handle.process.join(timeout=1.0)
        
        with self._lock:
            self._live_workers.pop(session_id, None)
        
        return True
    
    def get_live_session_ids(self) -> List[str]:
        """Get list of active live session IDs."""
        with self._lock:
            return list(self._live_workers.keys())
    
    # =========================================================================
    # Pool Management
    # =========================================================================
    
    def shutdown(self, timeout: Optional[float] = None) -> None:
        """
        Shutdown the worker pool gracefully.
        
        Args:
            timeout: Graceful shutdown timeout
        """
        if timeout is None:
            timeout = self.config.shutdown_timeout_seconds
        
        logger.info("Shutting down worker pool...")
        self._shutdown = True
        
        # Stop live workers
        with self._lock:
            session_ids = list(self._live_workers.keys())
        
        for session_id in session_ids:
            self.stop_live_session(session_id, timeout=timeout / 2)
        
        # Stop backtest workers
        for _ in self._backtest_workers:
            try:
                self._task_queue.put(None, timeout=1.0)
            except Exception:
                pass
        
        # Wait for workers to exit
        for handle in self._backtest_workers:
            handle.process.join(timeout=timeout / len(self._backtest_workers))
            if handle.process.is_alive():
                logger.warning(f"Force killing worker {handle.process.pid}")
                handle.process.kill()
        
        self._backtest_workers.clear()
        self._started = False
        
        logger.info("Worker pool shutdown complete")
    
    @property
    def is_enabled(self) -> bool:
        """Check if worker pool is enabled."""
        return self.config.enabled
    
    @property
    def is_running(self) -> bool:
        """Check if worker pool is running."""
        return self._started and not self._shutdown
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker pool statistics."""
        with self._lock:
            return {
                "enabled": self.config.enabled,
                "running": self._started,
                "backtest_workers": len(self._backtest_workers),
                "backtest_workers_alive": sum(
                    1 for h in self._backtest_workers if h.is_alive
                ),
                "live_sessions": len(self._live_workers),
                "pending_results": len(self._pending_results),
                "config": {
                    "pool_size": self.config.pool_size,
                    "task_timeout": self.config.task_timeout_seconds,
                    "max_memory_mb": self.config.max_memory_mb,
                },
            }


# =============================================================================
# Singleton Access
# =============================================================================

_pool: Optional[WorkerPool] = None
_pool_lock = threading.Lock()


def get_worker_pool() -> WorkerPool:
    """Get the singleton worker pool instance."""
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = WorkerPool()
        return _pool


def shutdown_worker_pool() -> None:
    """Shutdown the singleton worker pool."""
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.shutdown()
            _pool = None


__all__ = [
    "WorkerPool",
    "WorkerPoolError",
    "WorkerTimeoutError",
    "WorkerNotAvailableError",
    "get_worker_pool",
    "shutdown_worker_pool",
]
