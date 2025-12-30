"""
Backtest Worker - Isolated backtest execution.

This module runs inside the worker process and executes backtests
in complete isolation from the API process.

IMPORTANT: User strategy code is only loaded and executed here,
NEVER in the main API process.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Configure logging for worker process
from src.utils.logger import setup_worker_logging
setup_worker_logging()
logger = logging.getLogger(__name__)


def _add_sizer(cerebro, task) -> None:
    """
    Add appropriate sizer based on task configuration.
    
    Args:
        cerebro: Backtrader Cerebro instance
        task: BacktestTask with sizer configuration
    """
    import backtrader as bt
    
    sizer_type = getattr(task, 'sizer_type', 'fixed_size') or 'fixed_size'
    sizer_config = getattr(task, 'sizer_config', None) or {}
    default_stake = getattr(task, 'stake', 100)
    
    if sizer_type == "percent_sizer":
        percents = sizer_config.get("percents", 10)
        cerebro.addsizer(bt.sizers.PercentSizer, percents=percents)
    elif sizer_type == "all_in_sizer":
        cerebro.addsizer(bt.sizers.AllInSizerInt)
    elif sizer_type == "risk_sizer":
        # Use PercentSizerInt with risk-based percentage
        risk_percent = sizer_config.get("risk_percent", 2)
        cerebro.addsizer(bt.sizers.PercentSizerInt, percents=risk_percent)
    elif sizer_type == "kelly_sizer":
        # Kelly sizing approximated via percent sizer
        # In practice, Kelly requires win rate and win/loss ratio from strategy
        kelly_fraction = sizer_config.get("percents", 25)  # Conservative Kelly
        cerebro.addsizer(bt.sizers.PercentSizer, percents=kelly_fraction)
    else:  # fixed_size or unknown
        stake = sizer_config.get("stake", default_stake)
        cerebro.addsizer(bt.sizers.FixedSize, stake=stake)


def execute_backtest_task(task: "BacktestTask") -> "BacktestResult":
    """
    Execute a backtest task in the worker process.
    
    This function loads the user strategy, runs the backtest,
    and returns serialized results.
    
    Args:
        task: BacktestTask with all parameters
        
    Returns:
        BacktestResult with metrics and data
    """
    from src.service.worker.task_models import BacktestResult, BacktestTask, TaskStatus
    
    task_id = task.task_id
    logger.info(f"Starting backtest task {task_id}: {task.strategy_name} on {task.ticker}")
    
    try:
        # Import backtrader and related modules HERE (in worker, not API process)
        import backtrader as bt
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        
        from src.db.storage.market_data import get_bt_feed
        from src.service.strategy_repo import read_user_strategy_source
        from src.service.strategy_sandbox import execute_strategy_code
        
        # Disable matplotlib popups
        plt.ioff()
        plt.show = lambda *args, **kwargs: None
        
        # 1. Load strategy file
        try:
            strategy_path, source = read_user_strategy_source(task.strategy_name)
        except (FileNotFoundError, ValueError) as exc:
            return BacktestResult.error_result(
                task_id,
                str(exc),
                "StrategyLoadError",
            )
        
        # 2. Execute strategy code in soft sandbox (we're already isolated)
        try:
            module_globals = execute_strategy_code(
                source,
                module_name=f"user_strategy_{task.strategy_name}",
                filename=str(strategy_path),
            )
        except Exception as e:
            return BacktestResult.error_result(
                task_id,
                f"Strategy load failed: {e}",
                "StrategyLoadError"
            )
        
        strategy_cls = module_globals.get("UserStrategy")
        if strategy_cls is None:
            return BacktestResult.error_result(
                task_id,
                "UserStrategy class not found in strategy file",
                "StrategyLoadError"
            )
        
        if not issubclass(strategy_cls, bt.Strategy):
            return BacktestResult.error_result(
                task_id,
                "UserStrategy must inherit from backtrader.Strategy",
                "StrategyLoadError"
            )
        
        # 3. Load market data
        try:
            timeframe = getattr(task, 'timeframe', '1d') or '1d'
            data = get_bt_feed(task.ticker, task.start_date, task.end_date, timeframe=timeframe)
        except Exception as e:
            return BacktestResult.error_result(
                task_id,
                f"Failed to load market data: {e}",
                "DataLoadError"
            )
        
        # 4. Setup Cerebro
        cerebro = bt.Cerebro()
        
        if task.params:
            cerebro.addstrategy(strategy_cls, **task.params)
        else:
            cerebro.addstrategy(strategy_cls)
        
        cerebro.adddata(data)
        cerebro.broker.setcash(task.initial_cash)
        cerebro.broker.setcommission(commission=task.commission)
        
        # Dynamic sizer selection
        _add_sizer(cerebro, task)
        
        # Add analyzers using centralized configuration
        from src.service.analyzer_config import configure_analyzers, AnalyzerMode
        from src.service.backtest_engine import TradeRecorder
        configure_analyzers(cerebro, AnalyzerMode.BACKTEST, TradeRecorder)
        
        # 5. Run backtest
        logger.info(f"Running backtest for {task.ticker} from {task.start_date} to {task.end_date}")
        results = cerebro.run()
        strat = results[0]
        
        # 6. Extract metrics using centralized function
        from src.service.analyzer_config import extract_metrics
        metrics = extract_metrics(strat, cerebro.broker)
        
        # Map canonical names to legacy format for BacktestResult compatibility
        final_value = metrics["final_value"]
        sharpe = metrics["sharpe_ratio"]
        max_dd = metrics["max_drawdown"]
        total_return = metrics["total_return"]
        annual_returns = metrics["annual_returns"]
        trade_details = metrics["trade_details"]
        equity_curve = metrics["equity_curve"]
        
        # Also include legacy field names in metrics dict for backward compatibility
        metrics["sharpe"] = sharpe
        metrics["drawdown"] = max_dd
        metrics["returns"] = total_return
        metrics["calmar"] = metrics.get("calmar_ratio")


        
        # 7. Generate chart if requested
        chart_path = None
        if task.generate_chart and task.chart_save_path:
            try:
                save_path = Path(task.chart_save_path)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                plt.ioff()
                figures = cerebro.plot(style="candlestick", iplot=False)
                first_fig = figures[0][0] if figures and figures[0] else None
                if first_fig:
                    first_fig.set_size_inches(18, 10)
                    first_fig.savefig(save_path, bbox_inches="tight", dpi=150)
                    plt.close(first_fig)
                    chart_path = str(save_path)
                plt.close("all")
            except Exception as e:
                logger.warning(f"Chart generation failed: {e}")
                plt.close("all")
        
        # 8. Build result
        logger.info(f"Backtest {task_id} completed: final_value={final_value:.2f}")
        
        return BacktestResult(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            final_value=final_value,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            total_return=total_return,
            metrics=metrics,
            trade_details=trade_details,
            equity_curve=equity_curve,
            annual_returns=annual_returns,
            chart_path=chart_path,
        )
    
    except Exception as e:
        logger.exception(f"Backtest {task_id} failed: {e}")
        return BacktestResult.error_result(task_id, str(e), type(e).__name__)


def _serialize_trade_analysis(analysis: Dict) -> Dict[str, Any]:
    """Recursively serialize trade analysis to JSON-compatible format."""
    result = {}
    for key, value in analysis.items():
        if isinstance(value, dict):
            result[key] = _serialize_trade_analysis(value)
        elif hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
            try:
                result[key] = list(value)
            except:
                result[key] = str(value)
        elif isinstance(value, (int, float, str, bool, type(None))):
            result[key] = value
        else:
            result[key] = str(value)
    return result


__all__ = ["execute_backtest_task"]
