"""
Centralized Analyzer Configuration & Metrics Extraction.

This module provides standardized configuration of Backtrader analyzers
and extraction of metrics with canonical field names.

Usage:
    from src.service.analyzer_config import configure_analyzers, extract_metrics, AnalyzerMode

    # Configure analyzers
    configure_analyzers(cerebro, AnalyzerMode.BACKTEST)

    # After running, extract metrics
    metrics = extract_metrics(strat, cerebro.broker)
"""

from __future__ import annotations

import logging
import math
from enum import Enum
from typing import Any, Dict, Optional, Type

import backtrader as bt

logger = logging.getLogger(__name__)


class AnalyzerMode(Enum):
    """Execution mode determining which analyzers to add."""

    BACKTEST = "backtest"  # Full metrics for backtesting
    LIVE = "live"  # Minimal set for live/paper trading
    PORTFOLIO = "portfolio"  # Portfolio-specific analyzers


class SafeReturns(bt.analyzers.Returns):
    """Returns analyzer that tolerates zero bars (avoids ZeroDivisionError)."""

    def stop(self):
        try:
            super().stop()
        except ZeroDivisionError:
            logger.warning("Returns analyzer saw no bars; emitting neutral return metrics")
            self.rets["rtot"] = 0.0
            self.rets["ravg"] = 0.0
            self.rets["rnorm"] = 0.0
            self.rets["rnorm100"] = 0.0


def configure_analyzers(
    cerebro: bt.Cerebro,
    mode: AnalyzerMode = AnalyzerMode.BACKTEST,
    trade_recorder_cls: Optional[Type[bt.Analyzer]] = None,
) -> None:
    """
    Add appropriate analyzers to Cerebro based on execution mode.

    Args:
        cerebro: Backtrader Cerebro instance
        mode: Execution mode determining analyzer set
        trade_recorder_cls: Optional custom trade recorder class

    Analyzer sets by mode:
    - BACKTEST: Full set including Calmar, VWR, SQN, etc.
    - LIVE: Minimal set (Sharpe, DrawDown, Returns)
    - PORTFOLIO: Standard set (delegates to portfolio_analyzers)
    """
    # Core analyzers (all modes)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

    if mode == AnalyzerMode.LIVE:
        # Minimal set for live trading (performance-sensitive)
        cerebro.addanalyzer(SafeReturns, _name="returns")
        if trade_recorder_cls:
            cerebro.addanalyzer(trade_recorder_cls, _name="trade_recorder")
        logger.debug("Configured LIVE mode analyzers (minimal set)")

    elif mode == AnalyzerMode.BACKTEST:
        # Full set for backtesting
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="annual")
        cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="timereturns")
        cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name="timedraw")

        # Advanced metrics
        cerebro.addanalyzer(bt.analyzers.Calmar, _name="calmar")
        cerebro.addanalyzer(bt.analyzers.VWR, _name="vwr")

        # Custom trade recorder
        if trade_recorder_cls:
            cerebro.addanalyzer(trade_recorder_cls, _name="trade_recorder")

        logger.debug("Configured BACKTEST mode analyzers (full set)")

    elif mode == AnalyzerMode.PORTFOLIO:
        # Standard set for portfolio backtests (portfolio-specific added separately)
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        logger.debug("Configured PORTFOLIO mode analyzers (standard set)")


def extract_metrics(
    strat: bt.Strategy,
    broker: bt.brokers.BrokerBase,
    include_trade_details: bool = True,
) -> Dict[str, Any]:
    """
    Extract and normalize metrics from strategy analyzers.

    Uses canonical field names:
    - sharpe_ratio (not sharpe)
    - max_drawdown (not drawdown)
    - total_return (not returns)
    - calmar_ratio
    - vwr
    - sqn
    - annual_returns
    - trade_details
    - equity_curve
    - time_drawdown
    - trades

    Args:
        strat: Executed strategy instance with analyzers
        broker: Broker instance for final value
        include_trade_details: Whether to include trade_details

    Returns:
        Dictionary with canonical metric names
    """
    metrics: Dict[str, Any] = {}

    # Final portfolio value
    metrics["final_value"] = broker.getvalue()

    # Sharpe Ratio
    sharpe_analysis = _safe_get_analysis(strat, "sharpe")
    metrics["sharpe_ratio"] = sharpe_analysis.get("sharperatio") if sharpe_analysis else None

    # Maximum Drawdown
    dd_analysis = _safe_get_analysis(strat, "drawdown")
    if dd_analysis:
        max_dd = dd_analysis.get("max", {})
        metrics["max_drawdown"] = max_dd.get("drawdown", 0.0)
        metrics["max_drawdown_money"] = max_dd.get("moneydown", 0.0)
        metrics["max_drawdown_length"] = max_dd.get("len", 0)
    else:
        metrics["max_drawdown"] = 0.0
        metrics["max_drawdown_money"] = 0.0
        metrics["max_drawdown_length"] = 0

    # Returns
    returns_analysis = _safe_get_analysis(strat, "returns")
    if returns_analysis:
        metrics["total_return"] = returns_analysis.get("rnorm100", 0.0)
        metrics["total_return_raw"] = returns_analysis.get("rtot", 0.0)
    else:
        metrics["total_return"] = 0.0
        metrics["total_return_raw"] = 0.0

    # Annual Returns
    annual_analysis = _safe_get_analysis(strat, "annual")
    if annual_analysis:
        metrics["annual_returns"] = {
            str(k): float(v) for k, v in annual_analysis.items()
        }
    else:
        metrics["annual_returns"] = {}

    # SQN
    sqn_analysis = _safe_get_analysis(strat, "sqn")
    metrics["sqn"] = sqn_analysis.get("sqn") if sqn_analysis else None

    # Calmar Ratio (extract last non-NaN value from rolling series)
    calmar_analysis = _safe_get_analysis(strat, "calmar")
    metrics["calmar_ratio"] = _extract_last_valid(calmar_analysis)

    # VWR (Variability-Weighted Return)
    vwr_analysis = _safe_get_analysis(strat, "vwr")
    metrics["vwr"] = vwr_analysis.get("vwr") if vwr_analysis else None

    # Time-based Returns (equity curve)
    timereturns_analysis = _safe_get_analysis(strat, "timereturns")
    if timereturns_analysis:
        metrics["equity_curve"] = {
            dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt): float(ret)
            for dt, ret in timereturns_analysis.items()
        }
    else:
        metrics["equity_curve"] = {}

    # Time-based Drawdown
    timedraw_analysis = _safe_get_analysis(strat, "timedraw")
    metrics["time_drawdown"] = dict(timedraw_analysis) if timedraw_analysis else {}

    # Trade Analysis
    trades_analysis = _safe_get_analysis(strat, "trades")
    metrics["trades"] = _serialize_trade_analysis(trades_analysis) if trades_analysis else {}

    # Trade Recorder (custom detailed trades)
    if include_trade_details:
        trade_recorder_analysis = _safe_get_analysis(strat, "trade_recorder")
        metrics["trade_details"] = trade_recorder_analysis if trade_recorder_analysis else {}

    return metrics


def _safe_get_analysis(strat: bt.Strategy, analyzer_name: str) -> Optional[Dict]:
    """Safely get analyzer analysis, returning None if not present."""
    try:
        analyzer = getattr(strat.analyzers, analyzer_name, None)
        if analyzer is not None:
            return analyzer.get_analysis()
    except Exception as e:
        logger.debug(f"Could not get analysis for {analyzer_name}: {e}")
    return None


def _extract_last_valid(analysis: Optional[Dict]) -> Optional[float]:
    """Extract last non-NaN value from an OrderedDict (e.g., Calmar rolling values)."""
    if not analysis:
        return None
    for v in reversed(list(analysis.values())):
        if isinstance(v, (int, float)) and not math.isnan(v):
            return float(v)
    return None


def _serialize_trade_analysis(analysis: Dict) -> Dict[str, Any]:
    """Recursively serialize trade analysis to JSON-compatible format."""
    result = {}
    for key, value in analysis.items():
        if isinstance(value, dict):
            result[key] = _serialize_trade_analysis(value)
        elif hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
            try:
                result[key] = list(value)
            except Exception:
                result[key] = str(value)
        elif isinstance(value, (int, float, str, bool, type(None))):
            result[key] = value
        else:
            result[key] = str(value)
    return result


# Field name mapping for backward compatibility
LEGACY_TO_CANONICAL = {
    "sharpe": "sharpe_ratio",
    "drawdown": "max_drawdown",
    "returns": "total_return",
    "calmar": "calmar_ratio",
}

CANONICAL_TO_LEGACY = {v: k for k, v in LEGACY_TO_CANONICAL.items()}


def normalize_metric_names(metrics: Dict[str, Any], to_canonical: bool = True) -> Dict[str, Any]:
    """
    Convert metric names between legacy and canonical formats.

    Args:
        metrics: Dictionary of metrics
        to_canonical: If True, convert legacy -> canonical; else canonical -> legacy

    Returns:
        Dictionary with converted field names
    """
    mapping = LEGACY_TO_CANONICAL if to_canonical else CANONICAL_TO_LEGACY
    result = {}
    for key, value in metrics.items():
        new_key = mapping.get(key, key)
        result[new_key] = value
    return result


__all__ = [
    "AnalyzerMode",
    "SafeReturns",
    "configure_analyzers",
    "extract_metrics",
    "normalize_metric_names",
    "LEGACY_TO_CANONICAL",
    "CANONICAL_TO_LEGACY",
]
