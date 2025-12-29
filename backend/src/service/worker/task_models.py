"""
Task Models - Dataclasses for Worker IPC.

These models define the serializable data structures used for communication
between the main process and worker processes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


# =============================================================================
# Backtest Task Models
# =============================================================================

@dataclass
class BacktestTask:
    """
    Backtest task definition for worker execution.
    
    All fields must be JSON-serializable for IPC.
    """
    task_id: str
    strategy_name: str
    ticker: str
    start_date: str
    end_date: str
    initial_cash: float = 100000.0
    commission: float = 0.0005
    stake: int = 100
    # Sizer configuration
    sizer_type: str = "fixed_size"
    sizer_config: Optional[Dict[str, Any]] = None
    # Data timeframe
    timeframe: str = "1d"
    params: Optional[Dict[str, Any]] = None
    generate_chart: bool = True
    chart_save_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "strategy_name": self.strategy_name,
            "ticker": self.ticker,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_cash": self.initial_cash,
            "commission": self.commission,
            "stake": self.stake,
            "sizer_type": self.sizer_type,
            "sizer_config": self.sizer_config,
            "timeframe": self.timeframe,
            "params": self.params,
            "generate_chart": self.generate_chart,
            "chart_save_path": self.chart_save_path,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BacktestTask":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class BacktestResult:
    """
    Backtest execution result from worker.
    
    Contains all metrics and data needed by the API, serialized from worker.
    """
    task_id: str
    status: TaskStatus
    
    # Core metrics
    final_value: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_return: Optional[float] = None
    
    # Detailed metrics
    metrics: Optional[Dict[str, Any]] = None
    trade_details: Optional[Dict[str, Any]] = None
    equity_curve: Optional[Dict[str, float]] = None
    annual_returns: Optional[Dict[str, float]] = None
    
    # Chart
    chart_path: Optional[str] = None
    
    # Error info
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    # Timing
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "final_value": self.final_value,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "total_return": self.total_return,
            "metrics": self.metrics,
            "trade_details": self.trade_details,
            "equity_curve": self.equity_curve,
            "annual_returns": self.annual_returns,
            "chart_path": self.chart_path,
            "error": self.error,
            "error_type": self.error_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BacktestResult":
        """Create from dictionary."""
        status = data.get("status", TaskStatus.FAILED)
        if isinstance(status, str):
            status = TaskStatus(status)
        data["status"] = status
        return cls(**data)
    
    @classmethod
    def error_result(
        cls,
        task_id: str,
        error: str,
        error_type: str = "ExecutionError"
    ) -> "BacktestResult":
        """Create a failed result with error."""
        return cls(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=error,
            error_type=error_type,
        )


# =============================================================================
# Multi-Asset Backtest Task Models
# =============================================================================

@dataclass
class MultiAssetBacktestTask:
    """
    Multi-asset portfolio backtest task for worker execution.

    All fields must be JSON-serializable for IPC.
    """
    task_id: str
    tickers: List[str]
    weights: List[float]
    start_date: str
    end_date: str
    initial_cash: float = 100000.0
    commission: float = 0.0005
    strategy_name: Optional[str] = None
    rebalance_config: Optional[Dict[str, Any]] = None
    optimization_method: str = "equal_weight"
    timeframe: str = "1d"
    generate_chart: bool = True
    chart_save_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "tickers": self.tickers,
            "weights": self.weights,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_cash": self.initial_cash,
            "commission": self.commission,
            "strategy_name": self.strategy_name,
            "rebalance_config": self.rebalance_config,
            "optimization_method": self.optimization_method,
            "timeframe": self.timeframe,
            "generate_chart": self.generate_chart,
            "chart_save_path": self.chart_save_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MultiAssetBacktestTask":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class MultiAssetBacktestResult:
    """
    Multi-asset portfolio backtest result from worker.

    Contains all portfolio metrics and data needed by the API.
    """
    task_id: str
    status: TaskStatus

    # Portfolio-level metrics
    final_value: Optional[float] = None
    total_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    volatility: Optional[float] = None

    # Portfolio data
    equity_curve: Optional[Dict[str, float]] = None
    rebalancing_events: Optional[List[Dict[str, Any]]] = None
    asset_contributions: Optional[Dict[str, Dict[str, Any]]] = None
    optimization_history: Optional[List[Dict[str, Any]]] = None

    # Per-asset results
    per_asset_results: Optional[Dict[str, Dict[str, Any]]] = None

    # Chart
    chart_path: Optional[str] = None

    # Error info
    error: Optional[str] = None
    error_type: Optional[str] = None

    # Timing and memory
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    peak_memory_mb: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "final_value": self.final_value,
            "total_return": self.total_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "volatility": self.volatility,
            "equity_curve": self.equity_curve,
            "rebalancing_events": self.rebalancing_events,
            "asset_contributions": self.asset_contributions,
            "optimization_history": self.optimization_history,
            "per_asset_results": self.per_asset_results,
            "chart_path": self.chart_path,
            "error": self.error,
            "error_type": self.error_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "peak_memory_mb": self.peak_memory_mb,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MultiAssetBacktestResult":
        """Create from dictionary."""
        status = data.get("status", TaskStatus.FAILED)
        if isinstance(status, str):
            status = TaskStatus(status)
        data["status"] = status
        return cls(**data)

    @classmethod
    def error_result(
        cls,
        task_id: str,
        error: str,
        error_type: str = "ExecutionError"
    ) -> "MultiAssetBacktestResult":
        """Create a failed result with error."""
        return cls(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=error,
            error_type=error_type,
        )


# =============================================================================
# Live Trading Task Models
# =============================================================================

@dataclass
class LiveTradingTask:
    """
    Live trading session task for worker execution.
    
    Unlike backtest, live trading is long-running and requires
    bidirectional communication with the worker.
    """
    task_id: str
    session_id: str
    strategy_name: str
    symbol: str
    exchange: str
    mode: str  # 'paper' or 'live'
    timeframe: str = "1m"
    initial_cash: float = 10000.0
    commission: float = 0.001
    user_id: Optional[str] = None
    
    # Broker configuration (sensitive, passed securely)
    broker_config: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "exchange": self.exchange,
            "mode": self.mode,
            "timeframe": self.timeframe,
            "initial_cash": self.initial_cash,
            "commission": self.commission,
            "user_id": self.user_id,
            "broker_config": self.broker_config,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LiveTradingTask":
        """Create from dictionary."""
        return cls(**data)


class LiveEventType(str, Enum):
    """Types of events from live trading worker."""
    STATUS_UPDATE = "status_update"
    TRADE_EXECUTED = "trade_executed"
    ORDER_PLACED = "order_placed"
    ORDER_CANCELLED = "order_cancelled"
    POSITION_UPDATE = "position_update"
    PNL_UPDATE = "pnl_update"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    STOPPED = "stopped"


@dataclass
class LiveTradingEvent:
    """
    Event from live trading worker to main process.
    
    Used for real-time status updates, trade notifications, etc.
    """
    session_id: str
    event_type: LiveEventType
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "event_type": self.event_type.value if isinstance(self.event_type, LiveEventType) else self.event_type,
            "timestamp": self.timestamp,
            "data": self.data,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LiveTradingEvent":
        """Create from dictionary."""
        event_type = data.get("event_type", LiveEventType.ERROR)
        if isinstance(event_type, str):
            event_type = LiveEventType(event_type)
        data["event_type"] = event_type
        return cls(**data)


# =============================================================================
# Worker Control Messages
# =============================================================================

@dataclass
class WorkerCommand:
    """Command sent to worker for control operations."""
    command: str  # 'execute', 'stop', 'status', 'shutdown'
    task: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {"command": self.command, "task": self.task}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkerCommand":
        return cls(**data)


@dataclass
class WorkerResponse:
    """Response from worker."""
    success: bool
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "result": self.result,
            "error": self.error,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkerResponse":
        return cls(**data)


__all__ = [
    "TaskStatus",
    "BacktestTask",
    "BacktestResult",
    "MultiAssetBacktestTask",
    "MultiAssetBacktestResult",
    "LiveTradingTask",
    "LiveEventType",
    "LiveTradingEvent",
    "WorkerCommand",
    "WorkerResponse",
]
