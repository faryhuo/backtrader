"""
Backtest Models - SQLAlchemy models for backtest results persistence.

This module defines database tables for storing:
- Backtest history
- Portfolio results
- Walk-forward optimization results
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from src.db.models.base import Base, SafeJSON


class BacktestHistoryModel(Base):
    """
    Backtest History Model - Stores historical backtest results.

    Stores all backtest configurations, metrics, AI analysis, and plot references
    for historical tracking and comparison.
    """
    __tablename__ = "backtest_history"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique identifier for the backtest run
    backtest_id = Column(String(36), unique=True, nullable=False, index=True)

    # User identification (optional, for multi-user support)
    user_id = Column(String(255), nullable=True, index=True)

    # Configuration parameters
    ticker = Column(String(50), nullable=False, index=True)
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)    # YYYY-MM-DD
    initial_cash = Column(Float, nullable=False)
    commission = Column(Float, default=0.0005)
    stake = Column(Integer, default=100)
    strategy_name = Column(String(255), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Key performance metrics (denormalized for fast filtering/sorting)
    final_value = Column(Float, nullable=True)
    total_return = Column(Float, nullable=True, index=True)  # For sorting
    sharpe_ratio = Column(Float, nullable=True, index=True)  # For sorting
    max_drawdown = Column(Float, nullable=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)

    # Complete metrics JSON (all metrics from backtest engine)
    metrics = Column(SafeJSON, nullable=False)

    # AI Analysis - JSON format: {"model_name": "gpt-4o", "analysis_content": "..."}
    # Can store multiple analyses as a dict: {"gpt-4o": "...", "deepseek-v3.1": "..."}
    ai_analysis = Column(SafeJSON, nullable=True)

    # Strategy code snapshot (saved at backtest runtime)
    strategy_code = Column(Text, nullable=True)

    # Plot image reference
    plot_filename = Column(String(255), nullable=True)  # UUID.png

    # Strategy parameter overrides (JSON format)
    # e.g., {"fast_period": 10, "slow_period": 30}
    params = Column(SafeJSON, nullable=True)

    # Deep analysis results (computed on-demand, cached)
    # Contains: monthly_returns, rolling_sharpe, returns_distribution,
    # drawdown_distribution, consecutive_losses, benchmark_comparison
    deep_analysis = Column(SafeJSON, nullable=True)

    def __repr__(self):
        return (
            f"<BacktestHistory(id={self.backtest_id}, "
            f"ticker={self.ticker}, "
            f"strategy={self.strategy_name}, "
            f"return={self.total_return:.2f}% if self.total_return else 'N/A')>"
        )


class PortfolioResultModel(Base):
    """
    Portfolio Result Model - Stores multi-asset portfolio backtest results.

    Stores portfolio configuration, combined metrics, individual asset metrics,
    correlation analysis, and Markowitz optimization suggestions.
    """
    __tablename__ = "portfolio_results"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique identifier for the portfolio backtest run
    portfolio_id = Column(String(36), unique=True, nullable=False, index=True)

    # User identification (optional, for multi-user support)
    user_id = Column(String(255), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Portfolio configuration
    tickers = Column(SafeJSON, nullable=False)  # ["AAPL", "GOOGL", "MSFT"]
    weights = Column(SafeJSON, nullable=False)  # [0.4, 0.3, 0.3]
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)    # YYYY-MM-DD
    initial_cash = Column(Float, nullable=False)
    commission = Column(Float, default=0.0005)
    stake = Column(Integer, default=100)
    strategy_name = Column(String(255), nullable=True, index=True)

    # Key combined portfolio metrics (denormalized for fast querying)
    final_value = Column(Float, nullable=True)
    total_return = Column(Float, nullable=True, index=True)
    weighted_sharpe = Column(Float, nullable=True, index=True)
    max_drawdown = Column(Float, nullable=True)
    num_assets = Column(Integer, default=0)
    successful_backtests = Column(Integer, default=0)
    failed_backtests = Column(Integer, default=0)

    # Complete results (JSON format)
    portfolio_metrics = Column(SafeJSON, nullable=True)  # Combined metrics
    individual_results = Column(SafeJSON, nullable=True)  # Per-ticker metrics
    correlation_matrix = Column(SafeJSON, nullable=True)  # Correlation data
    optimization_suggestion = Column(SafeJSON, nullable=True)  # Optimal weights

    # Multi-asset backtest specific fields
    equity_curve = Column(SafeJSON, nullable=True)  # Time-series portfolio value {date: value}
    rebalancing_events = Column(SafeJSON, nullable=True)  # [{date, weights, orders, cost}]
    asset_contributions = Column(SafeJSON, nullable=True)  # {ticker: {return%, weight, contribution%}}
    optimization_history = Column(SafeJSON, nullable=True)  # [{date, weights, method}] for dynamic optimization

    # Configuration fields for multi-asset
    rebalance_frequency = Column(String(50), nullable=True)  # monthly, quarterly, etc.
    optimization_method = Column(String(50), nullable=True)  # equal_weight, risk_parity, min_variance, markowitz
    per_asset_params = Column(SafeJSON, nullable=True)  # {ticker: {param: value}}

    # Strategy parameters used (existing, kept for backward compatibility)
    params = Column(SafeJSON, nullable=True)

    # Plot image reference
    plot_filename = Column(String(255), nullable=True)

    def __repr__(self):
        tickers_str = ",".join(self.tickers[:3]) if self.tickers else "N/A"
        if self.tickers and len(self.tickers) > 3:
            tickers_str += "..."
        return (
            f"<PortfolioResult(id={self.portfolio_id}, "
            f"tickers=[{tickers_str}], "
            f"return={self.total_return:.2f}% if self.total_return else 'N/A')>"
        )


class WalkForwardOptimizationModel(Base):
    """
    Walk-Forward Optimization Model - Stores walk-forward analysis results.

    Stores parameter optimization results with train/validation split,
    including overfitting detection metrics.
    """
    __tablename__ = "walkforward_optimizations"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Unique identifier for the optimization run
    optimization_id = Column(String(36), unique=True, nullable=False, index=True)

    # User identification (optional, for multi-user support)
    user_id = Column(String(255), nullable=True, index=True)

    # Configuration parameters
    strategy_name = Column(String(255), nullable=False, index=True)
    ticker = Column(String(50), nullable=False, index=True)
    start_date = Column(String(10), nullable=False)
    end_date = Column(String(10), nullable=False)

    # Walk-forward configuration
    train_period_days = Column(Integer, nullable=False)
    test_period_days = Column(Integer, nullable=False)
    anchored = Column(Integer, default=0)  # 0 for rolling, 1 for anchored
    optimization_metric = Column(String(50), default="sharpe_ratio")

    # Backtest configuration
    initial_cash = Column(Float, nullable=False)
    commission = Column(Float, default=0.0005)
    stake = Column(Integer, default=100)

    # Parameter grid (JSON format)
    # e.g., {"fast_period": [5, 10, 20], "slow_period": [20, 30, 50]}
    param_grid = Column(SafeJSON, nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Status
    status = Column(String(20), default="pending", index=True)  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)

    # Results summary (denormalized for fast querying)
    num_windows = Column(Integer, default=0)
    avg_train_performance = Column(Float, nullable=True)
    avg_test_performance = Column(Float, nullable=True)
    avg_degradation_pct = Column(Float, nullable=True)
    train_test_correlation = Column(Float, nullable=True)
    consistency_score = Column(Float, nullable=True)
    overfitting_detected = Column(Integer, default=0)  # 0 for False, 1 for True

    # Complete results (JSON format)
    # Stores all windows with train/test metrics, best params for each window
    windows = Column(SafeJSON, nullable=True)

    # Overfitting metrics (JSON format)
    overfitting_metrics = Column(SafeJSON, nullable=True)

    # Combined test metrics (JSON format)
    combined_test_metrics = Column(SafeJSON, nullable=True)

    def __repr__(self):
        return (
            f"<WalkForwardOptimization(id={self.optimization_id}, "
            f"strategy={self.strategy_name}, "
            f"ticker={self.ticker}, "
            f"status={self.status})>"
        )


__all__ = [
    "BacktestHistoryModel",
    "PortfolioResultModel",
    "WalkForwardOptimizationModel",
]
