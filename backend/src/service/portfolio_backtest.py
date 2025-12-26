"""
Portfolio Backtest Service - Multi-asset portfolio backtesting with correlation analysis.

This module provides functionality for:
- Running parallel backtests for multiple tickers
- Portfolio weight allocation and normalization
- Correlation analysis between assets
- Markowitz mean-variance optimization suggestions
"""

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.db.storage.market_data import get_data, DataLoadError
from src.service.backtest_engine import (
    run_backtest,
    list_strategies,
    StrategyLoadError,
)

logger = logging.getLogger(__name__)


class PortfolioBacktestError(Exception):
    """Raised when portfolio backtest fails."""


def normalize_weights(weights: list[float]) -> list[float]:
    """
    Normalize weights to sum to 1.0.
    
    Args:
        weights: List of weights (can be any positive values)
        
    Returns:
        Normalized weights summing to 1.0
    """
    total = sum(weights)
    if total <= 0:
        raise PortfolioBacktestError("Weights must be positive")
    return [w / total for w in weights]


def calculate_correlation_matrix(
    tickers: list[str],
    start_date: str,
    end_date: str
) -> dict:
    """
    Calculate correlation matrix between asset daily returns.
    
    Args:
        tickers: List of ticker symbols
        start_date: Start date string
        end_date: End date string
        
    Returns:
        dict with 'matrix' (2D list) and 'tickers' (labels)
    """
    returns_data = {}
    
    for ticker in tickers:
        try:
            data = get_data(ticker, start_date, end_date)
            # Calculate daily returns
            close_prices = data['Close'] if 'Close' in data.columns else data['close']
            returns = close_prices.pct_change().dropna()
            returns_data[ticker] = returns
        except Exception as e:
            logger.warning(f"Failed to get data for {ticker}: {e}")
            returns_data[ticker] = pd.Series(dtype=float)
    
    # Align all series to common dates
    returns_df = pd.DataFrame(returns_data)
    returns_df = returns_df.dropna()
    
    if returns_df.empty or len(returns_df) < 2:
        return {
            "matrix": [[1.0] * len(tickers) for _ in tickers],
            "tickers": tickers,
            "error": "Insufficient data for correlation"
        }
    
    # Calculate correlation matrix
    corr_matrix = returns_df.corr()
    
    return {
        "matrix": corr_matrix.values.tolist(),
        "tickers": tickers
    }


def calculate_optimal_weights(
    tickers: list[str],
    start_date: str,
    end_date: str,
    risk_free_rate: float = 0.02
) -> dict:
    """
    Calculate optimal portfolio weights using mean-variance optimization (Markowitz).
    
    This is a simplified implementation that finds the maximum Sharpe ratio portfolio.
    
    Args:
        tickers: List of ticker symbols
        start_date: Start date string
        end_date: End date string
        risk_free_rate: Annual risk-free rate (default 2%)
        
    Returns:
        dict with optimal weights and metrics
    """
    returns_data = {}
    
    for ticker in tickers:
        try:
            data = get_data(ticker, start_date, end_date)
            close_prices = data['Close'] if 'Close' in data.columns else data['close']
            returns = close_prices.pct_change().dropna()
            returns_data[ticker] = returns
        except Exception as e:
            logger.warning(f"Failed to get data for {ticker}: {e}")
            return {
                "optimal_weights": [1.0 / len(tickers)] * len(tickers),
                "tickers": tickers,
                "error": f"Failed to get data for {ticker}: {e}"
            }
    
    # Align all series
    returns_df = pd.DataFrame(returns_data)
    returns_df = returns_df.dropna()
    
    if returns_df.empty or len(returns_df) < 10:
        return {
            "optimal_weights": [1.0 / len(tickers)] * len(tickers),
            "tickers": tickers,
            "error": "Insufficient data for optimization"
        }
    
    # Calculate expected returns and covariance matrix
    mean_returns = returns_df.mean() * 252  # Annualized
    cov_matrix = returns_df.cov() * 252  # Annualized
    
    n_assets = len(tickers)
    
    # Try to use scipy for optimization
    try:
        from scipy.optimize import minimize
        
        def neg_sharpe_ratio(weights):
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            if portfolio_std == 0:
                return 0
            return -(portfolio_return - risk_free_rate) / portfolio_std
        
        # Constraints: weights sum to 1
        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        # Bounds: 0 <= weight <= 1
        bounds = tuple((0, 1) for _ in range(n_assets))
        # Initial guess: equal weights
        initial_weights = np.array([1.0 / n_assets] * n_assets)
        
        result = minimize(
            neg_sharpe_ratio,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if result.success:
            optimal_weights = result.x.tolist()
            portfolio_return = np.sum(mean_returns * result.x)
            portfolio_std = np.sqrt(np.dot(result.x.T, np.dot(cov_matrix, result.x)))
            sharpe = (portfolio_return - risk_free_rate) / portfolio_std if portfolio_std > 0 else 0
            
            return {
                "optimal_weights": [round(w, 4) for w in optimal_weights],
                "tickers": tickers,
                "expected_return": round(portfolio_return, 4),
                "expected_volatility": round(portfolio_std, 4),
                "sharpe_ratio": round(sharpe, 4)
            }
    except ImportError:
        logger.warning("scipy not available, using equal weights")
    except Exception as e:
        logger.warning(f"Optimization failed: {e}")
    
    # Fallback: equal weights
    return {
        "optimal_weights": [1.0 / n_assets] * n_assets,
        "tickers": tickers,
        "error": "Optimization failed, returning equal weights"
    }


def _run_single_backtest(
    ticker: str,
    start_date: str,
    end_date: str,
    initial_cash: float,
    commission: float,
    stake: int,
    strategy_name: str,
    params: Optional[dict],
    sizer_type: str = "fixed_size",
    sizer_config: Optional[dict] = None,
    timeframe: str = "1d",
) -> dict:
    """
    Run backtest for a single ticker.
    
    Returns dict with ticker, metrics, and any error.
    """
    try:
        metrics = run_backtest(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            initial_cash=initial_cash,
            commission=commission,
            stake=stake,
            strategy_name=strategy_name,
            save_path=None,  # Don't save individual plots
            params=params,
            sizer_type=sizer_type,
            sizer_config=sizer_config,
            timeframe=timeframe,
        )
        return {
            "ticker": ticker,
            "success": True,
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Backtest failed for {ticker}: {e}")
        return {
            "ticker": ticker,
            "success": False,
            "error": str(e)
        }


def run_portfolio_backtest(
    tickers: list[str],
    weights: list[float],
    start_date: str,
    end_date: str,
    initial_cash: float = 100000.0,
    commission: float = 0.0005,
    stake: int = 100,
    strategy_name: Optional[str] = None,
    params: Optional[dict] = None,
    save_path: Optional[Path] = None,
    sizer_type: str = "fixed_size",
    sizer_config: Optional[dict] = None,
    timeframe: str = "1d",
) -> dict:
    """
    Run parallel backtests for multiple tickers and combine into portfolio.
    
    Args:
        tickers: List of ticker symbols
        weights: List of portfolio weights (will be normalized to sum to 1)
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        initial_cash: Total initial cash for portfolio
        commission: Broker commission rate
        stake: Fixed stake per trade
        strategy_name: Strategy to use for all tickers
        params: Strategy parameters
        save_path: Path to save combined portfolio chart
        
    Returns:
        dict with combined portfolio metrics, individual metrics,
        correlation matrix, and optimization suggestions
    """
    if not tickers:
        raise PortfolioBacktestError("At least one ticker is required")
    
    if len(tickers) != len(weights):
        raise PortfolioBacktestError("Number of tickers must match number of weights")
    
    # Normalize weights
    weights = normalize_weights(weights)
    
    # Select default strategy if not specified
    if not strategy_name:
        available = list_strategies()
        if not available:
            raise PortfolioBacktestError("No strategies available")
        strategy_name = available[0]
    
    # Allocate cash by weight
    cash_allocations = [initial_cash * w for w in weights]
    
    # Run backtests in parallel
    individual_results = []
    
    with ThreadPoolExecutor(max_workers=min(len(tickers), 5)) as executor:
        futures = {
            executor.submit(
                _run_single_backtest,
                ticker,
                start_date,
                end_date,
                cash_alloc,
                commission,
                stake,
                strategy_name,
                params,
                sizer_type,
                sizer_config,
                timeframe,
            ): (ticker, weight, cash_alloc)
            for ticker, weight, cash_alloc in zip(tickers, weights, cash_allocations)
        }
        
        for future in as_completed(futures):
            ticker, weight, cash_alloc = futures[future]
            result = future.result()
            result["weight"] = weight
            result["initial_cash"] = cash_alloc
            individual_results.append(result)
    
    # Sort by original ticker order
    ticker_order = {t: i for i, t in enumerate(tickers)}
    individual_results.sort(key=lambda x: ticker_order.get(x["ticker"], 999))
    
    # Calculate combined portfolio metrics
    successful_results = [r for r in individual_results if r["success"]]
    
    if not successful_results:
        raise PortfolioBacktestError("All backtests failed")
    
    # Calculate weighted portfolio performance
    total_final_value = 0
    total_initial_cash = 0
    weighted_sharpe = 0
    max_drawdown = 0
    
    for result in successful_results:
        weight = result["weight"]
        metrics = result["metrics"]
        final_value = metrics.get("final_value", result["initial_cash"])
        
        total_final_value += final_value
        total_initial_cash += result["initial_cash"]
        
        sharpe = metrics.get("sharpe")
        if sharpe is not None:
            weighted_sharpe += weight * sharpe
        
        dd = metrics.get("drawdown", 0)
        if dd > max_drawdown:
            max_drawdown = dd
    
    # Portfolio return
    portfolio_return = ((total_final_value - total_initial_cash) / total_initial_cash) * 100
    
    portfolio_metrics = {
        "initial_cash": initial_cash,
        "final_value": round(total_final_value, 2),
        "total_return": round(portfolio_return, 2),
        "weighted_sharpe": round(weighted_sharpe, 4) if weighted_sharpe else None,
        "max_drawdown": round(max_drawdown, 2),
        "num_assets": len(tickers),
        "successful_backtests": len(successful_results),
        "failed_backtests": len(tickers) - len(successful_results)
    }
    
    # Calculate correlation matrix
    correlation = calculate_correlation_matrix(tickers, start_date, end_date)
    
    # Calculate optimization suggestions
    optimization = calculate_optimal_weights(tickers, start_date, end_date)
    
    # Generate portfolio chart if save_path specified
    if save_path:
        try:
            _generate_portfolio_chart(
                individual_results,
                portfolio_metrics,
                save_path
            )
        except Exception as e:
            logger.warning(f"Failed to generate portfolio chart: {e}")
    
    return {
        "id": str(uuid.uuid4()),
        "tickers": tickers,
        "weights": [round(w, 4) for w in weights],
        "start_date": start_date,
        "end_date": end_date,
        "strategy_name": strategy_name,
        "portfolio_metrics": portfolio_metrics,
        "individual_results": [
            {
                "ticker": r["ticker"],
                "weight": r["weight"],
                "success": r["success"],
                "initial_cash": r["initial_cash"],
                "final_value": r["metrics"].get("final_value") if r["success"] else None,
                "total_return": round(
                    ((r["metrics"].get("final_value", r["initial_cash"]) - r["initial_cash"]) / r["initial_cash"]) * 100,
                    2
                ) if r["success"] else None,
                "sharpe_ratio": r["metrics"].get("sharpe") if r["success"] else None,
                "max_drawdown": r["metrics"].get("drawdown") if r["success"] else None,
                "total_trades": r["metrics"].get("trade_details", {}).get("total_trades", 0) if r["success"] else None,
                "error": r.get("error")
            }
            for r in individual_results
        ],
        "correlation": correlation,
        "optimization": optimization
    }


def _generate_portfolio_chart(
    individual_results: list[dict],
    portfolio_metrics: dict,
    save_path: Path
) -> None:
    """
    Generate a combined portfolio performance chart.
    """
    plt.ioff()
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Portfolio Backtest Results', fontsize=14, fontweight='bold')
    
    # Plot 1: Portfolio allocation (pie chart)
    ax1 = axes[0, 0]
    successful = [r for r in individual_results if r["success"]]
    if successful:
        labels = [r["ticker"] for r in successful]
        sizes = [r["weight"] for r in successful]
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Portfolio Allocation')
    
    # Plot 2: Individual returns (bar chart)
    ax2 = axes[0, 1]
    if successful:
        tickers = [r["ticker"] for r in successful]
        returns = [
            ((r["metrics"].get("final_value", r["initial_cash"]) - r["initial_cash"]) / r["initial_cash"]) * 100
            for r in successful
        ]
        colors = ['green' if r > 0 else 'red' for r in returns]
        ax2.bar(tickers, returns, color=colors)
        ax2.set_ylabel('Return (%)')
        ax2.set_title('Individual Asset Returns')
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Plot 3: Portfolio summary (text)
    ax3 = axes[1, 0]
    ax3.axis('off')
    summary_text = f"""
Portfolio Summary
─────────────────
Initial Cash: ${portfolio_metrics['initial_cash']:,.2f}
Final Value:  ${portfolio_metrics['final_value']:,.2f}
Total Return: {portfolio_metrics['total_return']:.2f}%

Weighted Sharpe: {portfolio_metrics['weighted_sharpe'] or 'N/A'}
Max Drawdown:    {portfolio_metrics['max_drawdown']:.2f}%

Assets: {portfolio_metrics['num_assets']}
Successful: {portfolio_metrics['successful_backtests']}
Failed: {portfolio_metrics['failed_backtests']}
"""
    ax3.text(0.1, 0.5, summary_text, transform=ax3.transAxes,
             fontsize=11, verticalalignment='center', fontfamily='monospace')
    ax3.set_title('Performance Metrics')
    
    # Plot 4: Sharpe ratios
    ax4 = axes[1, 1]
    if successful:
        tickers = [r["ticker"] for r in successful]
        sharpes = [r["metrics"].get("sharpe", 0) or 0 for r in successful]
        colors = ['green' if s > 0 else 'red' for s in sharpes]
        ax4.bar(tickers, sharpes, color=colors)
        ax4.set_ylabel('Sharpe Ratio')
        ax4.set_title('Sharpe Ratios by Asset')
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    plt.close('all')


__all__ = [
    "run_portfolio_backtest",
    "calculate_correlation_matrix",
    "calculate_optimal_weights",
    "normalize_weights",
    "PortfolioBacktestError",
]
