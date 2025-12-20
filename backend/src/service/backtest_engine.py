import logging
import re
from pathlib import Path
from typing import Optional

import backtrader as bt
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.config.settings import IMAGES_DIR, STRATEGY_DIR, ensure_resource_dirs
from src.config.sandbox_config import get_config as get_sandbox_config
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
    Extract parameters from a strategy file.
    Returns a list of dicts with name, value, and type info for each parameter.
    """
    strategy_cls = load_user_strategy(name)
    
    # Get the params from the strategy class
    # Backtrader stores params in a metaclass where each param is an attribute
    params_cls = getattr(strategy_cls, 'params', None)
    
    if params_cls is None:
        return []
    
    params_list = []
    
    # Backtrader's params metaclass stores param names in _getdefaults() or as direct attributes
    # We need to iterate through non-private attributes that are not methods
    if hasattr(params_cls, '_getdefaults'):
        # Get the list of param names from _getdefaults
        try:
            defaults = params_cls._getdefaults()
            if defaults:
                for param_name in defaults:
                    param_value = getattr(params_cls, param_name, None)
                    if param_value is not None:
                        params_list.append({
                            "name": param_name,
                            "value": param_value,
                            "type": type(param_value).__name__
                        })
        except Exception:
            pass
    
    # Fallback: iterate through attributes directly
    if not params_list:
        for attr_name in dir(params_cls):
            if attr_name.startswith('_'):
                continue
            attr_value = getattr(params_cls, attr_name, None)
            # Skip methods and callables
            if callable(attr_value):
                continue
            # Check if it's a simple value type (int, float, str, bool)
            if isinstance(attr_value, (int, float, str, bool)):
                params_list.append({
                    "name": attr_name,
                    "value": attr_value,
                    "type": type(attr_value).__name__
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
):
    if not strategy_name:
        available = list_strategies()
        if not available:
            raise StrategyLoadError("No strategies available; please add one in /resources/strategy")
        strategy_name = available[0]

    strategy_cls = load_user_strategy(strategy_name)

    cerebro = bt.Cerebro()
    # Pass params to strategy if provided, otherwise use strategy defaults
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
    cerebro.addanalyzer(TradeRecorder, _name="trade_recorder")  # 添加自定义交易记录器

    try:
        results = cerebro.run()
    except Exception as exc:
        logger.exception("Backtest run failed: %s", exc)
        raise
    strat = results[0]

    # 获取交易详情
    trade_details = strat.analyzers.trade_recorder.get_analysis()

    metrics = {
        "final_value": cerebro.broker.getvalue(),
        "sharpe": strat.analyzers.sharpe.get_analysis().get("sharperatio", None),
        "drawdown": strat.analyzers.drawdown.get_analysis().get("max", {}).get("drawdown", 0.0),
        "returns": strat.analyzers.returns.get_analysis().get("rnorm100", 0.0),
        "annual_returns": strat.analyzers.annual.get_analysis(),
        "sqn": strat.analyzers.sqn.get_analysis().get("sqn", None),
        "trades": strat.analyzers.trades.get_analysis(),
        "time_drawdown": strat.analyzers.timedraw.get_analysis(),
        "trade_details": trade_details,  # 添加详细的交易记录
    }

    target_path: Optional[Path] = Path(save_path) if save_path else None
    if target_path:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            plt.ioff()
            figures = cerebro.plot(style="candlestick", iplot=False)
            first_fig = figures[0][0] if figures and figures[0] else None
            if first_fig:
                first_fig.set_size_inches(18, 10)  # enlarge output
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
