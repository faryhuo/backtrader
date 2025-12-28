"""
Multi-Asset Backtest Service - True multi-asset portfolio backtesting engine.

This module provides functionality for:
- Single Cerebro instance with multiple data feeds
- Portfolio-level position sizing and cash management
- Periodic rebalancing with multiple optimization methods
- Unified portfolio equity curve generation
- Per-asset strategy parameter configuration

Unlike the old parallel backtest approach,
this module runs a single unified backtest with portfolio-level logic.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import backtrader as bt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config.settings import IMAGES_DIR
from src.contracts.exceptions import BacktestError
from src.db.storage.market_data import get_bt_feed, get_data, DataLoadError
from src.service.multi_asset_strategy_wrapper import (
    MultiAssetPortfolioStrategy,
    BuyAndHoldPortfolioStrategy,
)
from src.service.portfolio_analyzers import (
    PortfolioValueAnalyzer,
    RebalancingEventAnalyzer,
    AssetContributionAnalyzer,
    PortfolioMetricsAnalyzer,
)

logger = logging.getLogger(__name__)


class MultiAssetBacktestError(Exception):
    """Raised when multi-asset backtest fails."""


class DataAlignmentError(Exception):
    """Raised when data feeds cannot be properly aligned."""


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

def _load_returns_data(tickers: list[str], start_date: str, end_date: str) -> tuple[dict, str]:
    """Load and calculate daily returns for all tickers."""
    returns_data = {}
    
    for ticker in tickers:
        try:
            data = get_data(ticker, start_date, end_date)
            close_prices = data['Close'] if 'Close' in data.columns else data['close']
            returns = close_prices.pct_change().dropna()
            returns_data[ticker] = returns
        except Exception as e:
            logger.warning(f"Failed to get data for {ticker}: {e}")
            return {}, f"Failed to get data for {ticker}: {e}"
    
    return returns_data, ""


def _run_markowitz_optimization(
    mean_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    n_assets: int,
    risk_free_rate: float
) -> dict:
    """Run Markowitz mean-variance optimization using scipy."""
    from scipy.optimize import minimize
    
    def neg_sharpe_ratio(weights):
        portfolio_return = np.sum(mean_returns * weights)
        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        if portfolio_std == 0:
            return 0
        return -(portfolio_return - risk_free_rate) / portfolio_std
    
    constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
    bounds = tuple((0, 1) for _ in range(n_assets))
    initial_weights = np.array([1.0 / n_assets] * n_assets)
    
    result = minimize(
        neg_sharpe_ratio,
        initial_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )
    
    if not result.success:
        return {}
    
    optimal_weights = result.x.tolist()
    portfolio_return = np.sum(mean_returns * result.x)
    portfolio_std = np.sqrt(np.dot(result.x.T, np.dot(cov_matrix, result.x)))
    sharpe = (portfolio_return - risk_free_rate) / portfolio_std if portfolio_std > 0 else 0
    
    return {
        "optimal_weights": [round(w, 4) for w in optimal_weights],
        "expected_return": round(portfolio_return, 4),
        "expected_volatility": round(portfolio_std, 4),
        "sharpe_ratio": round(sharpe, 4)
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
    n_assets = len(tickers)
    equal_weights_fallback = {
        "optimal_weights": [1.0 / n_assets] * n_assets,
        "tickers": tickers,
    }
    
    # Load returns data
    returns_data, error = _load_returns_data(tickers, start_date, end_date)
    if error:
        return {**equal_weights_fallback, "error": error}
    
    # Align all series
    returns_df = pd.DataFrame(returns_data).dropna()
    
    if returns_df.empty or len(returns_df) < 10:
        return {**equal_weights_fallback, "error": "Insufficient data for optimization"}
    
    # Calculate expected returns and covariance matrix (annualized)
    mean_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252
    
    # Try scipy optimization
    try:
        result = _run_markowitz_optimization(mean_returns, cov_matrix, n_assets, risk_free_rate)
        if result:
            return {"tickers": tickers, **result}
    except ImportError:
        logger.warning("scipy not available, using equal weights")
    except Exception as e:
        logger.warning(f"Optimization failed: {e}")
    
    return {**equal_weights_fallback, "error": "Optimization failed, returning equal weights"}

def align_data_feeds(
    tickers: list[str],
    start_date: str,
    end_date: str,
    timeframe: str = "1d",
    min_overlap: float = 0.8
) -> dict[str, bt.feeds.PandasData]:
    """
    Load and align multiple data feeds to common trading dates.

    Strategy: Use intersection of trading dates to ensure all assets have data
    on the same days. This prevents lookahead bias and ensures fair portfolio
    rebalancing.

    Args:
        tickers: List of ticker symbols to load
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        timeframe: Data timeframe ('1d', '1h', '15m', '5m', '1m')
        min_overlap: Minimum required overlap ratio (default 0.8 = 80%)

    Returns:
        Dictionary mapping tickers to aligned Backtrader data feeds

    Raises:
        DataAlignmentError: If data overlap is insufficient
        DataLoadError: If data cannot be loaded for any ticker
    """
    logger.info(f"Aligning data feeds for {len(tickers)} tickers: {tickers}")

    # Step 1: Load raw data for all tickers
    raw_data = {}
    for ticker in tickers:
        try:
            feed = get_bt_feed(ticker, start_date, end_date, timeframe)
            if feed is None:
                raise DataLoadError(f"Failed to load data for {ticker}")
            raw_data[ticker] = feed
        except Exception as e:
            logger.error(f"Failed to load data for {ticker}: {e}")
            raise DataLoadError(f"Cannot load {ticker}: {str(e)}") from e

    logger.info(f"Successfully loaded data for {len(raw_data)} tickers")

    # Step 2: Extract date indices from each feed's dataname (pandas DataFrame)
    # Note: Backtrader feeds wrap pandas DataFrames accessible via feed._dataname
    date_sets = {}
    for ticker, feed in raw_data.items():
        try:
            # Access the underlying pandas DataFrame
            df = feed._dataname if hasattr(feed, '_dataname') else feed.p.dataname
            if df is None or df.empty:
                raise DataAlignmentError(f"Empty data for {ticker}")

            # Get the index (should be DatetimeIndex)
            dates = set(df.index)
            date_sets[ticker] = dates
            logger.debug(f"{ticker}: {len(dates)} trading days")
        except Exception as e:
            logger.error(f"Failed to extract dates for {ticker}: {e}")
            raise DataAlignmentError(f"Cannot extract dates for {ticker}: {str(e)}") from e

    # Step 3: Find intersection of all trading dates
    common_dates = set.intersection(*date_sets.values())

    if not common_dates:
        raise DataAlignmentError(
            f"No common trading dates found across {tickers}. "
            f"Check if tickers trade on same exchanges/calendars."
        )

    logger.info(f"Found {len(common_dates)} common trading dates")

    # Step 4: Check minimum overlap requirement
    max_dates = max(len(dates) for dates in date_sets.values())
    overlap_ratio = len(common_dates) / max_dates

    if overlap_ratio < min_overlap:
        logger.warning(
            f"Data overlap ({overlap_ratio:.1%}) below threshold ({min_overlap:.1%}). "
            f"Common dates: {len(common_dates)}, Max dates: {max_dates}"
        )
        raise DataAlignmentError(
            f"Insufficient data overlap ({overlap_ratio:.1%}). "
            f"Need at least {min_overlap:.1%} overlap. "
            f"Consider adjusting date range or removing tickers with limited data."
        )

    logger.info(f"Data overlap: {overlap_ratio:.1%} (meets {min_overlap:.1%} threshold)")

    # Step 5: Filter each feed to common dates
    # We'll create new Backtrader feeds with aligned data
    aligned_feeds = {}
    common_dates_sorted = sorted(common_dates)

    for ticker, feed in raw_data.items():
        try:
            df = feed._dataname if hasattr(feed, '_dataname') else feed.p.dataname
            # Filter to common dates
            aligned_df = df.loc[df.index.isin(common_dates_sorted)].sort_index()

            if aligned_df.empty:
                raise DataAlignmentError(f"No data remaining for {ticker} after alignment")

            # Create new Backtrader feed with aligned data
            aligned_feed = bt.feeds.PandasData(
                dataname=aligned_df,
                datetime=None,  # Use index
                open='open' if 'open' in aligned_df.columns else 'Open',
                high='high' if 'high' in aligned_df.columns else 'High',
                low='low' if 'low' in aligned_df.columns else 'Low',
                close='close' if 'close' in aligned_df.columns else 'Close',
                volume='volume' if 'volume' in aligned_df.columns else 'Volume',
                openinterest=-1
            )
            aligned_feeds[ticker] = aligned_feed
            logger.debug(f"{ticker}: Aligned to {len(aligned_df)} dates")

        except Exception as e:
            logger.error(f"Failed to align data for {ticker}: {e}")
            raise DataAlignmentError(f"Cannot align {ticker}: {str(e)}") from e

    logger.info(f"Successfully aligned {len(aligned_feeds)} data feeds")
    return aligned_feeds


def run_multi_asset_backtest(
    tickers: list[str],
    weights: list[float],
    start_date: str,
    end_date: str,
    initial_cash: float = 100000.0,
    commission: float = 0.0005,
    strategy_name: Optional[str] = None,
    rebalance_config: Optional[dict] = None,
    optimization_method: str = "equal_weight",
    timeframe: str = "1d",
    save_path: Optional[Path] = None,
) -> dict:
    """
    Run a true multi-asset portfolio backtest with unified Cerebro instance.

    This function creates a single Backtrader Cerebro with multiple data feeds,
    allowing portfolio-level position sizing, rebalancing, and equity curve tracking.

    Args:
        tickers: List of ticker symbols (e.g., ['AAPL', 'GOOGL', 'MSFT'])
        weights: Initial allocation weights (must sum to ~1.0)
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
        initial_cash: Starting portfolio cash (default: 100000.0)
        commission: Commission rate per trade (default: 0.0005 = 0.05%)
        strategy_name: Strategy file name (without .py). If None, uses buy-and-hold.
        rebalance_config: Rebalancing configuration
            Example: {"frequency": "monthly", "method": "risk_parity"}
        optimization_method: Optimization method for rebalancing
            Options: "equal_weight", "risk_parity", "min_variance", "markowitz"
        timeframe: Data timeframe (default: "1d")
        save_path: Optional path to save chart image

    Returns:
        Dictionary containing backtest results:
        {
            "final_value": float,
            "total_return": float,
            "sharpe_ratio": float,
            "max_drawdown": float,
            "equity_curve": {date: value},
            "rebalancing_events": [{date, weights, orders}],
            "asset_contributions": {ticker: contribution},
            "metrics": {...}  # All other metrics
        }

    Raises:
        MultiAssetBacktestError: If backtest execution fails
        DataAlignmentError: If data cannot be aligned
        ValueError: If input validation fails
    """
    # Validation
    if not tickers:
        raise ValueError("Must provide at least one ticker")

    if len(tickers) > 20:
        raise ValueError("Maximum 20 tickers allowed (memory limit)")

    if len(weights) != len(tickers):
        raise ValueError(f"Weights length ({len(weights)}) must match tickers length ({len(tickers)})")

    weight_sum = sum(weights)
    if not (0.99 <= weight_sum <= 1.01):
        logger.warning(f"Weights sum to {weight_sum:.3f}, normalizing to 1.0")
        weights = [w / weight_sum for w in weights]

    if any(w < 0 for w in weights):
        raise ValueError("All weights must be non-negative")

    logger.info(f"Starting multi-asset backtest: {len(tickers)} assets, ${initial_cash:,.2f} capital")
    logger.info(f"Tickers: {tickers}")
    logger.info(f"Weights: {[f'{w:.2%}' for w in weights]}")
    logger.info(f"Period: {start_date} to {end_date}")

    try:
        # Step 1: Align data feeds
        logger.info("Step 1: Aligning data feeds...")
        aligned_feeds = align_data_feeds(tickers, start_date, end_date, timeframe)

        # Step 2: Create Cerebro instance
        logger.info("Step 2: Creating Cerebro instance...")
        cerebro = bt.Cerebro()

        # Set initial cash
        cerebro.broker.setcash(initial_cash)

        # Set commission
        cerebro.broker.setcommission(commission=commission)

        # Step 3: Add all data feeds to Cerebro
        logger.info("Step 3: Adding data feeds to Cerebro...")
        for ticker in tickers:
            feed = aligned_feeds[ticker]
            cerebro.adddata(feed, name=ticker)
            logger.debug(f"Added data feed: {ticker}")

        # Step 4: Add strategy
        logger.info("Step 4: Adding multi-asset portfolio strategy...")
        cerebro.addstrategy(
            BuyAndHoldPortfolioStrategy,  # Simple buy-and-hold for Phase 1
            tickers=tickers,
            initial_weights=weights,
            rebalance_config=rebalance_config,
            optimization_method=optimization_method,
        )
        logger.info("Strategy added: BuyAndHoldPortfolioStrategy")

        # Step 5: Add custom portfolio analyzers
        logger.info("Step 5: Adding portfolio analyzers...")
        cerebro.addanalyzer(PortfolioValueAnalyzer, _name="portfolio_value")
        cerebro.addanalyzer(RebalancingEventAnalyzer, _name="rebalancing")
        cerebro.addanalyzer(AssetContributionAnalyzer, _name="asset_contribution")
        cerebro.addanalyzer(PortfolioMetricsAnalyzer, _name="portfolio_metrics")

        # Add standard Backtrader analyzers for compatibility
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")

        # Step 6: Run backtest
        logger.info("Step 6: Running backtest...")
        results = cerebro.run()
        strat = results[0]

        # Step 7: Extract metrics from analyzers
        logger.info("Step 7: Extracting metrics from analyzers...")
        final_value = cerebro.broker.getvalue()
        total_return = ((final_value - initial_cash) / initial_cash) * 100

        # Extract from standard analyzers
        sharpe_ratio = strat.analyzers.sharpe.get_analysis().get('sharperatio', 0)
        if sharpe_ratio is None:
            sharpe_ratio = 0.0

        drawdown_analysis = strat.analyzers.drawdown.get_analysis()
        max_drawdown = drawdown_analysis.get('max', {}).get('drawdown', 0)

        returns_analysis = strat.analyzers.returns.get_analysis()

        # Extract from custom portfolio analyzers
        portfolio_value_analysis = strat.analyzers.portfolio_value.get_analysis()
        rebalancing_analysis = strat.analyzers.rebalancing.get_analysis()
        asset_contribution_analysis = strat.analyzers.asset_contribution.get_analysis()
        portfolio_metrics_analysis = strat.analyzers.portfolio_metrics.get_analysis()

        # Calculate correlation matrix and optimization suggestions
        logger.info("Calculating correlation matrix...")
        correlation = calculate_correlation_matrix(tickers, start_date, end_date)

        logger.info("Calculating optimization suggestions...")
        optimization = calculate_optimal_weights(tickers, start_date, end_date)

        # Build individual results from asset contributions
        contributions = asset_contribution_analysis.get("contributions", {})
        individual_results = []
        for i, ticker in enumerate(tickers):
            contrib = contributions.get(ticker, {})
            individual_results.append({
                "ticker": ticker,
                "weight": weights[i],
                "success": True,
                "initial_cash": initial_cash * weights[i],
                "final_value": contrib.get("end_value", initial_cash * weights[i]),
                "total_return": contrib.get("return_pct", 0),
                "sharpe": None,  # Not available per-asset in unified backtest
                "max_drawdown": None,
                "total_trades": 0,
            })

        # Build result dictionary
        result = {
            "final_value": final_value,
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "initial_cash": initial_cash,
            "num_assets": len(tickers),
            "tickers": tickers,
            "weights": weights,
            # From custom analyzers
            "equity_curve": portfolio_value_analysis.get("equity_curve", {}),
            "rebalancing_events": rebalancing_analysis.get("events", []),
            "asset_contributions": contributions,
            # Individual asset results (for UI compatibility)
            "individual_results": individual_results,
            # Correlation and optimization
            "correlation": correlation,
            "optimization": optimization,
            # Comprehensive metrics
            "metrics": {
                "returns": returns_analysis,
                "drawdown": drawdown_analysis,
                "portfolio_metrics": portfolio_metrics_analysis,
                "optimization_method": optimization_method,
                "rebalance_frequency": rebalance_config.get("frequency") if rebalance_config else None,
                "total_transaction_costs": rebalancing_analysis.get("total_transaction_costs", 0.0),
                "rebalancing_count": rebalancing_analysis.get("total_events", 0),
            }
        }

        logger.info(f"Backtest complete! Final value: ${final_value:,.2f}")
        logger.info(f"Total return: {total_return:.2f}%, Sharpe: {sharpe_ratio:.2f}, Max DD: {max_drawdown:.2f}%")
        logger.info(f"Equity curve: {len(portfolio_value_analysis.get('equity_curve', {}))} days")
        logger.info(f"Asset contributions: {len(asset_contribution_analysis.get('contributions', {}))} assets")

        # Step 8: Generate chart (optional)
        if save_path:
            logger.info("Step 8: Generating chart...")
            try:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                # Force non-interactive backend to prevent popup
                import matplotlib
                matplotlib.use('Agg', force=True)
                import matplotlib.pyplot as plt
                plt.ioff()
                plt.switch_backend('Agg')

                figures = cerebro.plot(style='candlestick', volume=False, iplot=False)
                first_fig = figures[0][0] if figures and figures[0] else None
                if first_fig:
                    first_fig.set_size_inches(18, 10)
                    first_fig.savefig(save_path, bbox_inches='tight', dpi=150)
                    plt.close(first_fig)
                    logger.info(f"Chart saved to {save_path}")
                    # Add plot_url to result for UI access
                    result["plot_url"] = f"/images/{save_path.name}"
                plt.close('all')
            except Exception as e:
                logger.warning(f"Failed to generate chart: {e}")
                plt.close('all')

        return result

    except DataAlignmentError:
        raise
    except Exception as e:
        logger.error(f"Multi-asset backtest failed: {e}", exc_info=True)
        raise MultiAssetBacktestError(f"Backtest execution failed: {str(e)}") from e

__all__ = [
    "run_multi_asset_backtest",
    "align_data_feeds",
    "calculate_correlation_matrix",
    "calculate_optimal_weights",
    "MultiAssetBacktestError",
    "DataAlignmentError",
]
