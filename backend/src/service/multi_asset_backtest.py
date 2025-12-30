"""
Multi-Asset Backtest Service - True multi-asset portfolio backtesting engine.

This module provides functionality for:
- Single Cerebro instance with multiple data feeds
- Portfolio-level position sizing and cash management
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
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.config.settings import IMAGES_DIR
from src.contracts.exceptions import BacktestError
from src.db.storage.market_data import get_bt_feed, get_data, DataLoadError
from src.service.multi_asset_strategy_wrapper import (
    MultiAssetPortfolioStrategy,
    BuyAndHoldPortfolioStrategy,
)
from src.service.portfolio_analyzers import (
    PortfolioValueAnalyzer,
    AssetContributionAnalyzer,
    PortfolioMetricsAnalyzer,
    PortfolioTradeRecorder,
)
from src.service.portfolio.result_aggregator import PortfolioResultAggregator
from src.service.strategy_loader import load_user_strategy
from src.utils.backtrader_helpers import get_dataframe

logger = logging.getLogger(__name__)


class MultiAssetBacktestError(Exception):
    """Raised when multi-asset backtest fails."""


class DataAlignmentError(Exception):
    """Raised when data feeds cannot be properly aligned."""


def calculate_optimal_weights(
    tickers: list[str],
    start_date: str,
    end_date: str,
    timeframe: str = "1d",
    risk_free_rate: float = 0.02
) -> dict:
    """
    Calculate optimal portfolio weights using Modern Portfolio Theory (MPT).

    Uses mean-variance optimization to find weights that maximize the Sharpe ratio.

    Args:
        tickers: List of ticker symbols
        start_date: Start date for historical data
        end_date: End date for historical data
        timeframe: Data timeframe
        risk_free_rate: Annual risk-free rate (default: 2%)

    Returns:
        Dictionary containing:
        - optimal_weights: List of optimal weights
        - expected_return: Expected annual return
        - expected_volatility: Expected annual volatility
        - sharpe_ratio: Expected Sharpe ratio
        - tickers: List of tickers (for reference)
    """
    try:
        logger.info(f"Calculating optimal weights for {tickers}")

        # Load price data for all tickers
        returns_data = []
        valid_tickers = []

        for ticker in tickers:
            try:
                df = get_data(ticker, start_date, end_date, timeframe)
                if df is not None and not df.empty:
                    # Handle both lowercase and capitalized column names
                    close_col = 'close' if 'close' in df.columns else 'Close'
                    if close_col in df.columns:
                        # Calculate returns
                        returns = df[close_col].pct_change().dropna()
                        if len(returns) > 0:
                            returns_data.append(returns)
                            valid_tickers.append(ticker)
                    else:
                        logger.warning(f"No close column for {ticker}, skipping in optimization")
                else:
                    logger.warning(f"No data for {ticker}, skipping in optimization")
            except Exception as e:
                logger.warning(f"Failed to load data for {ticker}: {e}")

        if len(valid_tickers) < 2:
            logger.warning("Not enough valid tickers for optimization")
            return {
                "error": "Insufficient data for optimization",
                "tickers": tickers,
                "optimal_weights": [1.0 / len(tickers)] * len(tickers),  # Equal weights fallback
            }

        # Create returns DataFrame
        returns_df = pd.concat(returns_data, axis=1, keys=valid_tickers)
        returns_df = returns_df.dropna()

        if len(returns_df) < 10:
            logger.warning("Insufficient data points for optimization")
            return {
                "error": "Insufficient data points",
                "tickers": tickers,
                "optimal_weights": [1.0 / len(tickers)] * len(tickers),
            }

        # Calculate expected returns and covariance
        mean_returns = returns_df.mean() * 252  # Annualize
        cov_matrix = returns_df.cov() * 252  # Annualize

        num_assets = len(valid_tickers)

        # Objective function: negative Sharpe ratio (we minimize)
        def neg_sharpe(weights):
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            if portfolio_std == 0:
                return 1e10  # Avoid division by zero
            sharpe = (portfolio_return - risk_free_rate) / portfolio_std
            return -sharpe  # Negative because we minimize

        # Constraints
        constraints = (
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}  # Weights sum to 1
        )

        # Bounds: each weight between 0 and 1 (no short selling)
        bounds = tuple((0, 1) for _ in range(num_assets))

        # Initial guess: equal weights
        init_weights = np.array([1.0 / num_assets] * num_assets)

        # Optimize
        result = minimize(
            neg_sharpe,
            init_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )

        if not result.success:
            logger.warning(f"Optimization failed: {result.message}")
            # Return equal weights
            optimal_weights_dict = {ticker: 1.0 / num_assets for ticker in valid_tickers}
        else:
            optimal_weights_dict = {ticker: float(weight) for ticker, weight in zip(valid_tickers, result.x)}

        # Calculate expected metrics with optimal weights
        optimal_weights_array = np.array(list(optimal_weights_dict.values()))
        expected_return = np.dot(optimal_weights_array, mean_returns)
        expected_volatility = np.sqrt(np.dot(optimal_weights_array.T, np.dot(cov_matrix, optimal_weights_array)))
        sharpe_ratio = (expected_return - risk_free_rate) / expected_volatility if expected_volatility > 0 else 0

        # Map back to original tickers (fill missing with 0)
        optimal_weights_full = []
        for ticker in tickers:
            optimal_weights_full.append(optimal_weights_dict.get(ticker, 0.0))

        logger.info(f"Optimization complete. Sharpe ratio: {sharpe_ratio:.4f}")

        return {
            "tickers": tickers,
            "optimal_weights": optimal_weights_full,
            "expected_return": float(expected_return),
            "expected_volatility": float(expected_volatility),
            "sharpe_ratio": float(sharpe_ratio),
        }

    except Exception as e:
        logger.error(f"Failed to calculate optimal weights: {e}", exc_info=True)
        # Return equal weights on error
        return {
            "error": str(e),
            "tickers": tickers,
            "optimal_weights": [1.0 / len(tickers)] * len(tickers),
        }


def calculate_correlation_matrix(
    tickers: list[str],
    start_date: str,
    end_date: str,
    timeframe: str = "1d"
) -> dict:
    """
    Calculate correlation matrix between asset returns.

    Args:
        tickers: List of ticker symbols
        start_date: Start date for historical data
        end_date: End date for historical data
        timeframe: Data timeframe

    Returns:
        Dictionary containing:
        - matrix: 2D list of correlation values
        - tickers: List of tickers (for reference)
    """
    try:
        logger.info(f"Calculating correlation matrix for {tickers}")

        # Load price data for all tickers
        returns_data = []
        valid_tickers = []

        for ticker in tickers:
            try:
                df = get_data(ticker, start_date, end_date, timeframe)
                if df is not None and not df.empty:
                    # Handle both lowercase and capitalized column names
                    close_col = 'close' if 'close' in df.columns else 'Close'
                    if close_col in df.columns:
                        # Calculate returns
                        returns = df[close_col].pct_change().dropna()
                        if len(returns) > 0:
                            returns_data.append(returns)
                            valid_tickers.append(ticker)
                    else:
                        logger.warning(f"No close column for {ticker}, skipping in correlation")
                else:
                    logger.warning(f"No data for {ticker}, skipping in correlation")
            except Exception as e:
                logger.warning(f"Failed to load data for {ticker}: {e}")

        if len(valid_tickers) < 2:
            logger.warning("Not enough valid tickers for correlation matrix")
            return {
                "error": "Insufficient data for correlation",
                "tickers": tickers,
            }

        # Create returns DataFrame
        returns_df = pd.concat(returns_data, axis=1, keys=valid_tickers)
        returns_df = returns_df.dropna()

        if len(returns_df) < 10:
            logger.warning("Insufficient data points for correlation")
            return {
                "error": "Insufficient data points",
                "tickers": tickers,
            }

        # Calculate correlation matrix
        corr_matrix = returns_df.corr()
        
        # Convert to 2D list for JSON serialization (matches frontend expectation)
        matrix = []
        for ticker1 in valid_tickers:
            row = []
            for ticker2 in valid_tickers:
                row.append(float(corr_matrix.loc[ticker1, ticker2]))
            matrix.append(row)

        logger.info("Correlation matrix calculation complete")

        return {
            "tickers": valid_tickers,
            "matrix": matrix,
        }

    except Exception as e:
        logger.error(f"Failed to calculate correlation matrix: {e}", exc_info=True)
        return {
            "error": str(e),
            "tickers": tickers,
        }


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
    on the same days. This prevents lookahead bias.

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
    # Use helper function to safely access the underlying DataFrame
    date_sets = {}
    for ticker, feed in raw_data.items():
        try:
            # Access the underlying pandas DataFrame using helper function
            df = get_dataframe(feed)
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
            # Use helper function to access the underlying DataFrame
            df = get_dataframe(feed)
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
    strategy_name: str = ...,  # Required parameter
    params: Optional[dict] = None,
    timeframe: str = "1d",
    save_path: Optional[Path] = None,
) -> dict:
    """
    Run a true multi-asset portfolio backtest with unified Cerebro instance.

    This function creates a single Backtrader Cerebro with multiple data feeds,
    allowing portfolio-level position sizing and equity curve tracking.

    Args:
        tickers: List of ticker symbols (e.g., ['AAPL', 'GOOGL', 'MSFT'])
        weights: Initial allocation weights (must sum to ~1.0)
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
        initial_cash: Starting portfolio cash (default: 100000.0)
        commission: Commission rate per trade (default: 0.0005 = 0.05%)
        strategy_name: Strategy file name (without .py) - REQUIRED. Must be multi-data aware.
        params: Strategy parameters (dict) - passed to strategy's params
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
            "asset_contributions": {ticker: contribution},
            "all_trades": [{trade_info}],
            "metrics": {...}  # All other metrics
        }

    Raises:
        MultiAssetBacktestError: If backtest execution fails
        DataAlignmentError: If data cannot be aligned
        ValueError: If input validation fails or strategy not found
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

        # Step 4: Load and add user strategy
        logger.info(f"Step 4: Loading user strategy: {strategy_name}...")
        try:
            strategy_cls = load_user_strategy(strategy_name)
            logger.info(f"Successfully loaded strategy class: {strategy_cls.__name__}")

            # Add strategy to Cerebro with user params only
            # Don't pollute strategy params with portfolio metadata
            cerebro.addstrategy(
                strategy_cls,
                **(params or {})
            )
            logger.info(f"Strategy {strategy_name} added with params: {params}")

        except Exception as e:
            logger.error(f"Failed to load strategy {strategy_name}: {e}")
            raise MultiAssetBacktestError(f"Strategy load failed: {str(e)}") from e

        # Step 5: Add custom portfolio analyzers
        logger.info("Step 5: Adding portfolio analyzers...")
        cerebro.addanalyzer(PortfolioValueAnalyzer, _name="portfolio_value")
        cerebro.addanalyzer(
            AssetContributionAnalyzer,
            _name="asset_contribution",
            tickers=tickers,  # Pass portfolio metadata to analyzer
            initial_weights=weights
        )
        cerebro.addanalyzer(PortfolioMetricsAnalyzer, _name="portfolio_metrics")
        cerebro.addanalyzer(PortfolioTradeRecorder, _name="trade_recorder")

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
        asset_contribution_analysis = strat.analyzers.asset_contribution.get_analysis()
        portfolio_metrics_analysis = strat.analyzers.portfolio_metrics.get_analysis()
        trade_recorder_analysis = strat.analyzers.trade_recorder.get_analysis()

        # Build individual results from asset contributions
        contributions = asset_contribution_analysis.get("contributions", {})
        individual_results = []
        for i, ticker in enumerate(tickers):
            contrib = contributions.get(ticker, {})
            # Use start_value and end_value from contributions if available
            start_value = contrib.get("start_value", initial_cash * weights[i])
            end_value = contrib.get("end_value", initial_cash * weights[i])

            # Calculate return based on actual values
            asset_return = 0.0
            if start_value > 0:
                asset_return = ((end_value - start_value) / start_value) * 100

            individual_results.append({
                "ticker": ticker,
                "weight": weights[i],
                "success": True,
                "initial_cash": start_value,
                "final_value": end_value,
                "total_return": asset_return,
                "sharpe": None,  # Not available per-asset in unified backtest
                "max_drawdown": None,
                "total_trades": contrib.get("end_shares", 0),  # Use end_shares as proxy
            })

        # Calculate additional risk-adjusted metrics
        annual_return = portfolio_metrics_analysis.get("annual_return", 0.0)

        # Calmar Ratio - Annual Return / Max Drawdown
        calmar_ratio = 0.0
        if max_drawdown and abs(max_drawdown) > 0:
            calmar_ratio = annual_return / abs(max_drawdown)

        # Recovery Factor - Net Profit / Max Drawdown (in absolute terms)
        net_profit = final_value - initial_cash
        recovery_factor = 0.0
        if max_drawdown and abs(max_drawdown) > 0:
            # Convert max_drawdown percentage to dollar amount
            max_dd_dollars = (abs(max_drawdown) / 100) * drawdown_analysis.get('max', {}).get('moneydown', initial_cash * abs(max_drawdown) / 100)
            if max_dd_dollars > 0:
                recovery_factor = net_profit / max_dd_dollars

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
            "all_trades": trade_recorder_analysis.get("trades", []),  # All trades from TradeRecorder analyzer
            "asset_contributions": contributions,
            # Individual asset results (for UI compatibility)
            "individual_results": individual_results,
            # Comprehensive metrics
            "metrics": {
                "returns": returns_analysis,
                "drawdown": drawdown_analysis,
                "portfolio_metrics": portfolio_metrics_analysis,
            },
            # Additional calculated metrics
            "calmar_ratio": calmar_ratio,
            "recovery_factor": recovery_factor,
            # Trading cost metrics
            "total_commission": trade_recorder_analysis.get("total_commission", 0.0),
            "total_volume": trade_recorder_analysis.get("total_volume", 0.0),
            "total_trades": trade_recorder_analysis.get("total_trades", 0),
        }

        # Step 9: Calculate optimal portfolio weights using MPT
        logger.info("Step 9: Calculating optimal portfolio weights...")
        try:
            optimization_result = calculate_optimal_weights(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe,
                risk_free_rate=0.02  # 2% annual risk-free rate
            )
            result["optimization"] = optimization_result
            logger.info("Optimization calculation complete")
        except Exception as e:
            logger.warning(f"Failed to calculate optimization: {e}")
            # Add error result so frontend knows optimization was attempted
            result["optimization"] = {
                "error": f"Optimization failed: {str(e)}",
                "tickers": tickers,
            }

        # Step 10: Calculate correlation matrix
        logger.info("Step 10: Calculating correlation matrix...")
        try:
            correlation_result = calculate_correlation_matrix(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe,
            )
            result["correlation"] = correlation_result
            logger.info("Correlation matrix calculation complete")
        except Exception as e:
            logger.warning(f"Failed to calculate correlation matrix: {e}")
            result["correlation"] = {
                "error": f"Correlation calculation failed: {str(e)}",
                "tickers": tickers,
            }

        logger.info(f"Backtest complete! Final value: ${final_value:,.2f}")
        logger.info(f"Total return: {total_return:.2f}%, Sharpe: {sharpe_ratio:.2f}, Max DD: {max_drawdown:.2f}%")
        logger.info(f"Equity curve: {len(portfolio_value_analysis.get('equity_curve', {}))} days")
        logger.info(f"Asset contributions: {len(asset_contribution_analysis.get('contributions', {}))} assets")
        logger.info(f"All trades: {len(trade_recorder_analysis.get('trades', []))} trades")

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
                
                # Monkey-patch plt.show to prevent Backtrader from opening GUI
                # Backtrader's plot.py:821 calls self.mpyplot.show() which we need to suppress
                original_show = plt.show
                plt.show = lambda *args, **kwargs: None

                try:
                    figures = cerebro.plot(style='candlestick', volume=False, iplot=False)
                    first_fig = figures[0][0] if figures and figures[0] else None
                    if first_fig:
                        first_fig.set_size_inches(18, 10)
                        first_fig.savefig(save_path, bbox_inches='tight', dpi=150)
                        plt.close(first_fig)
                        logger.info(f"Chart saved to {save_path}")
                        # Add plot_url to result for UI access
                        result["plot_url"] = f"/images/{save_path.name}"
                finally:
                    # Restore original plt.show
                    plt.show = original_show
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
    "MultiAssetBacktestError",
    "DataAlignmentError",
]
