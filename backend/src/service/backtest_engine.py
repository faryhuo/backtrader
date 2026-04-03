import logging
from pathlib import Path
from typing import Optional

import backtrader as bt

from src.config.settings import IMAGES_DIR, ensure_resource_dirs
from src.config.worker_config import get_config as get_worker_config
from src.contracts.exceptions import StrategyLoadError
from src.db.storage.market_data import get_raw_data_json
from src.service.backtest_runner import BacktestRunnerError, run_backtest_legacy, run_backtest_worker
from src.service.strategy_loader import StrategyLoaderError, load_user_strategy as _load_user_strategy
from src.service.strategy_param_extractor import extract_strategy_params as _extract_strategy_params
from src.service.strategy_repo import (
    get_strategy_path as _get_strategy_path,
    get_user_strategy_code as _get_user_strategy_code,
    list_strategies as _list_strategies,
    save_user_strategy_code as _save_user_strategy_code,
)

logger = logging.getLogger(__name__)

DEFAULT_STRATEGY_NAME = None


def ensure_resource_files() -> None:
    """Maintain backward compatibility for callers ensuring resources exist."""
    ensure_resource_dirs()


def get_strategy_path(name: str) -> Path:
    try:
        return _get_strategy_path(name)
    except ValueError as exc:
        raise StrategyLoadError(str(exc)) from exc


def list_strategies() -> list[str]:
    ensure_resource_files()
    return _list_strategies()


def get_user_strategy_code(name: str) -> str:
    ensure_resource_files()
    try:
        return _get_user_strategy_code(name)
    except FileNotFoundError as exc:
        raise StrategyLoadError(f"Strategy '{name}' not found") from exc
    except ValueError as exc:
        raise StrategyLoadError(str(exc)) from exc


def save_user_strategy_code(name: str, code: str) -> None:
    ensure_resource_files()
    try:
        _save_user_strategy_code(name, code)
    except ValueError as exc:
        raise StrategyLoadError(str(exc)) from exc


def load_user_strategy(name: str) -> type[bt.Strategy]:
    """
    Load and compile a user strategy from file.

    Delegates to `src.service.strategy_loader` while preserving the existing
    `StrategyLoadError` surface for callers.
    """
    ensure_resource_files()
    try:
        return _load_user_strategy(name)
    except (StrategyLoaderError, ValueError) as exc:
        raise StrategyLoadError(str(exc)) from exc


def extract_strategy_params(name: str) -> list[dict[str, object]]:
    """
    Extract parameters from a strategy file safely.

    Delegates to `src.service.strategy_param_extractor` and keeps the public API
    stable for route handlers.
    """
    try:
        return _extract_strategy_params(name)
    except ValueError as exc:
        raise StrategyLoadError(str(exc)) from exc


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
                                        
                    # 记录完整的交易信息
                    complete_trade = {
                        'trade_num': len(self.trades) + 1,
                        'entry_date': str(open_info['date']),
                        'entry_price': round(open_info['price'], 2),
                        'exit_date': str(trade_info['date']),
                        'exit_price': round(trade_info['price'], 2),
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
    ticker: str = "AAPL",
    start_date: str = "2022-01-01",
    end_date: str = "2023-12-31",
    initial_cash: float = 100000.0,
    commission: float = 0.0005,
    stake: int = 100,
    strategy_name: Optional[str] = None,
    save_path: Optional[Path] = None,
    params: Optional[dict] = None,
    use_worker: Optional[bool] = None,
    sizer_type: str = "fixed_size",
    sizer_config: Optional[dict] = None,
    timeframe: str = "1d",
    data_source: Optional[str] = None,
) -> dict:
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

    # Normalize and validate strategy name (strip optional ".py" for worker path)
    strategy_name = get_strategy_path(strategy_name).stem
    
    # Determine whether to use worker pool
    worker_config = get_worker_config()
    should_use_worker = use_worker if use_worker is not None else worker_config.enabled
    
    if should_use_worker:
        try:
            return run_backtest_worker(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                initial_cash=initial_cash,
                commission=commission,
                stake=stake,
                strategy_name=strategy_name,
                save_path=save_path,
                params=params,
                sizer_type=sizer_type,
                sizer_config=sizer_config,
                timeframe=timeframe,
                data_source=data_source,
            )
        except BacktestRunnerError as exc:
            raise StrategyLoadError(str(exc)) from exc
    else:
        # Legacy in-process execution (not secure for untrusted code!)
        logger.warning(
            "Running backtest in-process (worker pool disabled). "
            "This is NOT secure for untrusted strategy code!"
        )
        strategy_cls = load_user_strategy(strategy_name)
        try:
            return run_backtest_legacy(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                initial_cash=initial_cash,
                commission=commission,
                stake=stake,
                strategy_cls=strategy_cls,
                strategy_name=strategy_name,
                trade_recorder_cls=TradeRecorder,
                save_path=save_path,
                params=params,
                timeframe=timeframe,
                data_source=data_source,
            )
        except BacktestRunnerError as exc:
            raise StrategyLoadError(str(exc)) from exc


__all__ = [
    "run_backtest",
    "get_user_strategy_code",
    "save_user_strategy_code",
    "list_strategies",
    "ensure_resource_files",
    "StrategyLoadError",
    "DEFAULT_STRATEGY_NAME",
    "get_strategy_path",
    "IMAGES_DIR",
    "get_raw_data_json",
    "extract_strategy_params",
]

