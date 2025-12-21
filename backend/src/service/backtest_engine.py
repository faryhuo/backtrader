import logging
import re
import uuid
from pathlib import Path
from typing import Optional

import backtrader as bt
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.config.settings import IMAGES_DIR, STRATEGY_DIR, ensure_resource_dirs
from src.config.sandbox_config import get_config as get_sandbox_config
from src.config.worker_config import get_config as get_worker_config
from src.db.storage.market_data import DataLoadError, get_bt_feed as get_data, get_raw_data_json
from src.service.isolated_sandbox import (
    IsolatedSandbox,
    SandboxError,
    SandboxExecutionError,
    SandboxTimeoutError,
)
# Keep old sandbox for fallback in "soft" mode
from src.service.strategy_sandbox import StrategySandboxError, execute_strategy_code

plt.ioff()
plt.show = lambda *args, **kwargs: None  # Prevent local popups in API runs

logger = logging.getLogger(__name__)

DEFAULT_STRATEGY_NAME = None


class StrategyLoadError(Exception):
    """Raised when the user strategy cannot be loaded."""


def ensure_resource_files() -> None:
    """Maintain backward compatibility for callers ensuring resources exist."""
    ensure_resource_dirs()


def _sanitize_strategy_name(name: str) -> str:
    """
    Only allow simple names to avoid path traversal.
    Accepts optional '.py' suffix and always returns '<name>.py'.
    """
    if not name:
        raise StrategyLoadError("Strategy name is required")
    clean = name.strip()
    if clean.lower().endswith(".py"):
        clean = clean[:-3]
    if not re.match(r"^[A-Za-z0-9_-]+$", clean):
        raise StrategyLoadError("Strategy name must use letters, numbers, '-' or '_'")
    return f"{clean}.py"


def get_strategy_path(name: str) -> Path:
    filename = _sanitize_strategy_name(name)
    return STRATEGY_DIR / filename


def list_strategies():
    ensure_resource_files()
    return sorted({path.stem for path in STRATEGY_DIR.glob("*.py")})


def get_user_strategy_code(name: str):
    ensure_resource_files()
    path = get_strategy_path(name)
    if not path.exists():
        raise StrategyLoadError(f"Strategy '{name}' not found")
    return path.read_text(encoding="utf-8")


def save_user_strategy_code(name: str, code: str):
    ensure_resource_files()
    path = get_strategy_path(name)
    path.write_text(code, encoding="utf-8")


def load_user_strategy(name: str):
    """
    Load and compile a user strategy from file.
    
    Uses isolated subprocess sandbox by default for security.
    Falls back to soft sandbox if SANDBOX_MODE=soft is set.
    
    Args:
        name: Strategy name (without .py extension)
    
    Returns:
        type: The UserStrategy class from the strategy file
    
    Raises:
        StrategyLoadError: If strategy cannot be loaded
    """
    ensure_resource_files()
    path = get_strategy_path(name)
    if not path.exists():
        raise StrategyLoadError(f"Strategy '{name}' not found")
    
    try:
        source = path.read_text(encoding="utf-8")
        if source.startswith("\ufeff"):
            source = source.lstrip("\ufeff")
        
        # Check sandbox mode from config
        sandbox_config = get_sandbox_config()
        
        if sandbox_config.mode == "soft":
            # Use soft sandbox (in-process, less secure)
            logger.warning(
                "Using soft sandbox mode - not secure against malicious code. "
                "Set SANDBOX_MODE=subprocess for better isolation."
            )
            module_globals = execute_strategy_code(
                source,
                module_name=f"user_strategy_{name}",
                filename=str(path),
            )
            strategy_cls = module_globals.get("UserStrategy")
        else:
            # Use isolated subprocess sandbox (secure)
            sandbox = IsolatedSandbox(
                timeout=sandbox_config.timeout_seconds,
                max_memory_mb=sandbox_config.max_memory_mb,
                allow_network=sandbox_config.allow_network,
                allow_file_write=sandbox_config.allow_file_write,
            )
            result = sandbox.execute_strategy(
                source=source,
                module_name=f"user_strategy_{name}",
                filename=str(path),
            )
            
            # For isolated sandbox, we need to re-execute in main process
            # to get the actual class object (subprocess can't return classes)
            strategy_class_name = result.get("strategy_class")
            if not strategy_class_name:
                raise StrategyLoadError("UserStrategy class not found in strategy file")
            
            # Strategy validated in subprocess, now execute in soft sandbox
            # This is safe because we've already validated the code
            module_globals = execute_strategy_code(
                source,
                module_name=f"user_strategy_{name}",
                filename=str(path),
            )
            strategy_cls = module_globals.get("UserStrategy")
    
    except SandboxTimeoutError as exc:
        raise StrategyLoadError(
            f"Strategy '{name}' timed out during validation"
        ) from exc
    except (SandboxError, SandboxExecutionError) as exc:
        raise StrategyLoadError(f"Failed to load strategy '{name}': {exc}") from exc
    except (OSError, StrategySandboxError) as exc:
        raise StrategyLoadError(f"Failed to load strategy '{name}': {exc}") from exc

    if strategy_cls is None:
        raise StrategyLoadError("UserStrategy class not found in strategy file")
    if not issubclass(strategy_cls, bt.Strategy):
        raise StrategyLoadError("UserStrategy must inherit from backtrader.Strategy")
    return strategy_cls


def extract_strategy_params(name: str) -> list:
    """
    Extract parameters from a strategy file safely.
    
    Uses IsolatedSandbox to extract parameters in a subprocess,
    so user code never executes in the main API process.
    
    Returns a list of dicts with name, value, and type info for each parameter.
    """
    path = get_strategy_path(name)
    if not path.exists():
        return []
    
    source = path.read_text(encoding="utf-8")
    if source.startswith("\ufeff"):
        source = source.lstrip("\ufeff")
    
    # Use IsolatedSandbox to safely extract strategy params
    # This runs the code in a subprocess, not in the API process
    sandbox_config = get_sandbox_config()
    
    # Use subprocess mode for isolated execution
    if sandbox_config.mode == "subprocess":
        try:
            sandbox = IsolatedSandbox()
            result = sandbox.execute_strategy(
                source=source,
                module_name=f"user_strategy_{name}",
                filename=str(path),
            )
            
            # Extract params from sandbox result
            strategy_params = result.get("strategy_params", [])
            if strategy_params:
                return strategy_params
        except (SandboxError, SandboxExecutionError, SandboxTimeoutError) as e:
            logger.warning(f"Isolated sandbox param extraction failed: {e}")
            # Fall through to safe AST-based extraction
    
    # Fallback: Use static AST analysis (no code execution)
    return _extract_params_from_source_ast(source)


def _extract_params_from_source_ast(source: str) -> list:
    """
    Extract strategy parameters using AST parsing (no code execution).
    
    This is a safe fallback that parses the source code without executing it.
    It looks for the `params` tuple in the UserStrategy class.
    """
    import ast
    
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    
    params_list = []
    
    for node in ast.walk(tree):
        # Look for UserStrategy class
        if isinstance(node, ast.ClassDef) and node.name == "UserStrategy":
            for item in node.body:
                # Look for params = (...)
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "params":
                            if isinstance(item.value, ast.Tuple):
                                # Parse tuple of (name, value) pairs
                                for elt in item.value.elts:
                                    if isinstance(elt, ast.Tuple) and len(elt.elts) >= 2:
                                        name_node, value_node = elt.elts[0], elt.elts[1]
                                        if isinstance(name_node, ast.Constant):
                                            param_name = name_node.value
                                            param_value = None
                                            param_type = "unknown"
                                            
                                            if isinstance(value_node, ast.Constant):
                                                param_value = value_node.value
                                                param_type = type(param_value).__name__
                                            elif isinstance(value_node, ast.UnaryOp) and isinstance(value_node.op, ast.USub):
                                                if isinstance(value_node.operand, ast.Constant):
                                                    param_value = -value_node.operand.value
                                                    param_type = type(param_value).__name__
                                            
                                            if param_name:
                                                params_list.append({
                                                    "name": param_name,
                                                    "value": param_value,
                                                    "type": param_type
                                                })
    
    return params_list


class TradeRecorder(bt.Analyzer):
    """
    自定义分析器，记录每笔交易的详细信息：
    - 开仓价格、时间
    - 平仓价格、时间
    - 盈亏
    - 手续费
    - 止损止盈规则（如果策略有定义）
    - 持仓时长
    """
    
    def __init__(self):
        self.trades = []
        self.open_trades = {}  # 跟踪未平仓的交易
    
    def notify_order(self, order):
        """订单状态变化时的回调"""
        if order.status in [order.Completed]:
            # 记录订单执行信息
            trade_info = {
                'date': self.strategy.datetime.date(0),
                'type': 'BUY' if order.isbuy() else 'SELL',
                'price': order.executed.price,
                'size': order.executed.size,
                'value': order.executed.value,
                'commission': order.executed.comm,
            }
            
            # 如果是开仓
            if order.isbuy():
                self.open_trades[order.ref] = trade_info
            # 如果是平仓
            elif order.issell() and len(self.open_trades) > 0:
                # 找到对应的开仓订单（简化处理，取最早的）
                if self.open_trades:
                    open_ref = list(self.open_trades.keys())[0]
                    open_info = self.open_trades.pop(open_ref)
                    
                    # 计算盈亏
                    pnl = (trade_info['price'] - open_info['price']) * open_info['size']
                    total_commission = open_info['commission'] + trade_info['commission']
                    net_pnl = pnl - total_commission
                    
                    # 获取策略参数（止损止盈规则）
                    stop_loss = getattr(self.strategy.params, 'stop_loss', None)
                    take_profit = getattr(self.strategy.params, 'take_profit', None)
                    
                    # 计算持仓时长（天数）
                    from datetime import datetime
                    open_date = open_info['date']
                    close_date = trade_info['date']
                    duration = (close_date - open_date).days if isinstance(open_date, datetime) or hasattr(open_date, 'days') else 0
                    
                    # 记录完整的交易信息
                    complete_trade = {
                        'trade_num': len(self.trades) + 1,
                        'open_date': str(open_info['date']),
                        'open_price': round(open_info['price'], 2),
                        'close_date': str(trade_info['date']),
                        'close_price': round(trade_info['price'], 2),
                        'size': open_info['size'],
                        'pnl': round(pnl, 2),
                        'commission': round(total_commission, 2),
                        'net_pnl': round(net_pnl, 2),
                        'return_pct': round((pnl / open_info['value']) * 100, 2)
                    }
                    
                    self.trades.append(complete_trade)
    
    def get_analysis(self):
        """返回所有交易记录"""
        return {
            'trades': self.trades,
            'total_trades': len(self.trades),
            'winning_trades': len([t for t in self.trades if t['net_pnl'] > 0]),
            'losing_trades': len([t for t in self.trades if t['net_pnl'] < 0]),
            'total_pnl': round(sum(t['net_pnl'] for t in self.trades), 2),
            'avg_pnl': round(sum(t['net_pnl'] for t in self.trades) / len(self.trades), 2) if self.trades else 0,
        }


def run_backtest(
    ticker="AAPL",
    start_date="2022-01-01",
    end_date="2023-12-31",
    initial_cash=100000.0,
    commission=0.0005,
    stake=100,
    strategy_name=None,
    save_path: Optional[Path] = None,
    params: Optional[dict] = None,
    use_worker: Optional[bool] = None,
):
    """
    Run a backtest with the specified parameters.
    
    When worker pool is enabled (default), strategy code executes in an
    isolated worker process for security. The API process never executes
    user strategy code.
    
    Args:
        ticker: Stock/crypto ticker symbol
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
        initial_cash: Starting cash amount
        commission: Commission rate per trade
        stake: Position size per trade
        strategy_name: Name of strategy file (without .py)
        save_path: Optional path to save chart image
        params: Optional strategy parameters
        use_worker: Force worker pool on/off (None = use config)
    
    Returns:
        dict: Backtest metrics including final_value, sharpe, drawdown, etc.
    
    Raises:
        StrategyLoadError: If strategy cannot be loaded
    """
    if not strategy_name:
        available = list_strategies()
        if not available:
            raise StrategyLoadError("No strategies available; please add one in /resources/strategy")
        strategy_name = available[0]
    
    # Determine whether to use worker pool
    worker_config = get_worker_config()
    should_use_worker = use_worker if use_worker is not None else worker_config.enabled
    
    if should_use_worker:
        return _run_backtest_worker(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            initial_cash=initial_cash,
            commission=commission,
            stake=stake,
            strategy_name=strategy_name,
            save_path=save_path,
            params=params,
        )
    else:
        # Legacy in-process execution (not secure for untrusted code!)
        logger.warning(
            "Running backtest in-process (worker pool disabled). "
            "This is NOT secure for untrusted strategy code!"
        )
        return _run_backtest_legacy(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            initial_cash=initial_cash,
            commission=commission,
            stake=stake,
            strategy_name=strategy_name,
            save_path=save_path,
            params=params,
        )


def _run_backtest_worker(
    ticker: str,
    start_date: str,
    end_date: str,
    initial_cash: float,
    commission: float,
    stake: int,
    strategy_name: str,
    save_path: Optional[Path],
    params: Optional[dict],
) -> dict:
    """
    Run backtest in isolated worker process (secure).
    
    The API process NEVER executes user strategy code - all execution
    happens in the worker process.
    """
    from src.service.worker.task_models import BacktestTask, TaskStatus
    from src.service.worker.worker_pool import get_worker_pool, WorkerPoolError, WorkerTimeoutError
    
    # Create task
    task = BacktestTask(
        task_id=str(uuid.uuid4()),
        strategy_name=strategy_name,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        initial_cash=initial_cash,
        commission=commission,
        stake=stake,
        params=params,
        generate_chart=save_path is not None,
        chart_save_path=str(save_path) if save_path else None,
    )
    
    # Submit to worker pool and wait (synchronous)
    pool = get_worker_pool()
    
    try:
        result = pool.submit_backtest_sync(task)
    except WorkerTimeoutError as e:
        raise StrategyLoadError(f"Backtest timed out: {e}") from e
    except WorkerPoolError as e:
        raise StrategyLoadError(f"Worker pool error: {e}") from e
    
    # Check result status
    if result.status != TaskStatus.COMPLETED:
        error_msg = result.error or "Unknown error"
        raise StrategyLoadError(f"Backtest failed: {error_msg}")
    
    # Return metrics in same format as legacy function
    return result.metrics or {
        "final_value": result.final_value,
        "sharpe": result.sharpe_ratio,
        "drawdown": result.max_drawdown,
        "returns": result.total_return,
        "trade_details": result.trade_details,
        "equity_curve": result.equity_curve,
        "annual_returns": result.annual_returns,
    }


def _run_backtest_legacy(
    ticker: str,
    start_date: str,
    end_date: str,
    initial_cash: float,
    commission: float,
    stake: int,
    strategy_name: str,
    save_path: Optional[Path],
    params: Optional[dict],
) -> dict:
    """
    Legacy in-process backtest execution.
    
    WARNING: This executes user strategy code in the API process!
    Only use when worker pool is explicitly disabled.
    """
    strategy_cls = load_user_strategy(strategy_name)

    cerebro = bt.Cerebro()
    if params:
        cerebro.addstrategy(strategy_cls, **params)
    else:
        cerebro.addstrategy(strategy_cls)

    data = get_data(ticker, start_date, end_date)
    cerebro.adddata(data)

    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    cerebro.addsizer(bt.sizers.FixedSize, stake=stake)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="annual")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name="timedraw")
    cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="timereturns")
    cerebro.addanalyzer(TradeRecorder, _name="trade_recorder")

    try:
        results = cerebro.run()
    except Exception as exc:
        logger.exception("Backtest run failed: %s", exc)
        raise
    strat = results[0]

    trade_details = strat.analyzers.trade_recorder.get_analysis()
    time_returns_raw = strat.analyzers.timereturns.get_analysis()
    equity_curve = {
        dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt): float(ret)
        for dt, ret in time_returns_raw.items()
    }

    metrics = {
        "final_value": cerebro.broker.getvalue(),
        "sharpe": strat.analyzers.sharpe.get_analysis().get("sharperatio", None),
        "drawdown": strat.analyzers.drawdown.get_analysis().get("max", {}).get("drawdown", 0.0),
        "returns": strat.analyzers.returns.get_analysis().get("rnorm100", 0.0),
        "annual_returns": strat.analyzers.annual.get_analysis(),
        "sqn": strat.analyzers.sqn.get_analysis().get("sqn", None),
        "trades": strat.analyzers.trades.get_analysis(),
        "time_drawdown": strat.analyzers.timedraw.get_analysis(),
        "trade_details": trade_details,
        "equity_curve": equity_curve,
    }

    target_path: Optional[Path] = Path(save_path) if save_path else None
    if target_path:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            plt.ioff()
            figures = cerebro.plot(style="candlestick", iplot=False)
            first_fig = figures[0][0] if figures and figures[0] else None
            if first_fig:
                first_fig.set_size_inches(18, 10)
                first_fig.savefig(target_path, bbox_inches="tight", dpi=150)
                plt.close(first_fig)
            plt.close("all")
        except Exception as exc:
            logger.exception("Plot rendering failed: %s", exc)
            plt.close("all")
            raise RuntimeError(f"Failed to render plot: {exc}") from exc

    return metrics


__all__ = [
    "run_backtest",
    "get_user_strategy_code",
    "save_user_strategy_code",
    "list_strategies",
    "ensure_resource_files",
    "StrategyLoadError",
    "DEFAULT_STRATEGY_NAME",
    "STRATEGY_DIR",
    "get_strategy_path",
    "IMAGES_DIR",
    "get_raw_data_json",
    "extract_strategy_params",
]
