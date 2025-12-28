"""
Portfolio Optimizer - Portfolio optimization algorithms for dynamic weight allocation.

This module provides multiple portfolio optimization algorithms:
- EqualWeightOptimizer: Simple 1/N allocation (benchmark)
- RiskParityOptimizer: Equal risk contribution from each asset
- MinimumVarianceOptimizer: Minimize portfolio volatility
- MarkowitzOptimizer: Maximum Sharpe ratio (mean-variance optimization)

Usage:
    from src.service.portfolio_optimizer import get_optimizer

    optimizer = get_optimizer("risk_parity")
    result = optimizer.optimize(returns_df)
    weights = result["weights"]
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

import numpy as np
import pandas as pd
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


class PortfolioOptimizer(ABC):
    """
    Base class for portfolio optimization algorithms.

    All optimizers implement the optimize() method which takes a DataFrame
    of historical returns and outputs optimal portfolio weights.
    """

    @abstractmethod
    def optimize(self, returns: pd.DataFrame) -> dict:
        """
        Calculate optimal portfolio weights.

        Args:
            returns: Daily returns DataFrame (columns = tickers, rows = dates)
                    Example: DataFrame with columns ['AAPL', 'GOOGL', 'MSFT']
                    and rows containing daily return values

        Returns:
            dict with:
                - weights: List of optimal weights (same order as returns.columns)
                - tickers: List of ticker names
                - method: String identifying the optimization method
                - success: Boolean indicating if optimization converged
                - Additional method-specific metrics (expected_return, etc.)

        Raises:
            ValueError: If returns DataFrame is empty or has insufficient data
        """
        pass

    def _validate_returns(self, returns: pd.DataFrame, min_periods: int = 20) -> None:
        """
        Validate returns DataFrame has sufficient data.

        Args:
            returns: Returns DataFrame
            min_periods: Minimum number of periods required

        Raises:
            ValueError: If validation fails
        """
        if returns.empty:
            raise ValueError("Returns DataFrame is empty")

        if len(returns) < min_periods:
            raise ValueError(
                f"Insufficient data: {len(returns)} periods, "
                f"minimum {min_periods} required"
            )

        if returns.isnull().any().any():
            logger.warning("Returns contain NaN values, will be forward-filled")


class EqualWeightOptimizer(PortfolioOptimizer):
    """
    Equal weight (1/N) portfolio optimizer.

    Allocates equal weight to all assets regardless of their
    risk or return characteristics.

    Benefits:
    - No estimation error (robust)
    - Simple and transparent
    - Surprisingly competitive with sophisticated methods

    When to use:
    - As a benchmark
    - When no strong views on assets
    - When simplicity is preferred
    """

    def optimize(self, returns: pd.DataFrame) -> dict:
        """
        Calculate equal weights for all assets.

        Args:
            returns: Daily returns DataFrame

        Returns:
            dict with equal weights and portfolio statistics
        """
        self._validate_returns(returns, min_periods=2)

        n_assets = len(returns.columns)
        tickers = returns.columns.tolist()

        # Equal weight for all assets
        weight = 1.0 / n_assets
        weights = np.ones(n_assets) * weight

        # Calculate portfolio statistics for reference
        mean_returns = returns.mean() * 252  # Annualized
        cov_matrix = returns.cov() * 252

        # Ensure cov_matrix is a numpy array for dot product
        cov_values = cov_matrix.values

        portfolio_return = float(np.dot(weights, mean_returns.values))
        portfolio_vol = float(np.sqrt(weights.T @ cov_values @ weights))

        logger.info(f"Equal weight optimizer: {weight:.2%} per asset")

        return {
            "weights": weights.tolist(),
            "tickers": tickers,
            "method": "equal_weight",
            "success": True,
            "expected_return": portfolio_return,
            "expected_volatility": portfolio_vol,
        }


class RiskParityOptimizer(PortfolioOptimizer):
    """
    Risk parity portfolio optimizer.

    Allocates weights so that each asset contributes equally
    to the total portfolio risk (volatility).

    Key concept:
    - Risk contribution = weight × marginal risk contribution
    - Each asset should contribute 1/N to total risk

    Benefits:
    - True diversification (balances risk, not capital)
    - Ignores return estimation (more robust)
    - Good for long-term strategic allocation

    Trade-offs:
    - May over-allocate to low-volatility assets
    - Ignores expected return differences
    """

    def __init__(self, max_iterations: int = 1000, tolerance: float = 1e-10):
        """
        Initialize risk parity optimizer.

        Args:
            max_iterations: Maximum optimization iterations
            tolerance: Convergence tolerance
        """
        self.max_iterations = max_iterations
        self.tolerance = tolerance

    def optimize(self, returns: pd.DataFrame) -> dict:
        """
        Calculate risk parity weights.

        Args:
            returns: Daily returns DataFrame

        Returns:
            dict with risk parity weights and metrics
        """
        self._validate_returns(returns, min_periods=20)

        n_assets = len(returns.columns)
        tickers = returns.columns.tolist()

        # Annualized covariance matrix
        cov_matrix = returns.cov().values * 252

        # Target risk contribution: equal for all assets
        target_risk_contrib = np.ones(n_assets) / n_assets

        def risk_contribution(weights):
            """Calculate each asset's contribution to total portfolio risk."""
            portfolio_var = weights.T @ cov_matrix @ weights
            if portfolio_var <= 0:
                return np.zeros(n_assets)
            portfolio_vol = np.sqrt(portfolio_var)
            marginal_contrib = cov_matrix @ weights
            risk_contrib = weights * marginal_contrib / portfolio_vol
            return risk_contrib

        def objective(weights):
            """
            Minimize squared difference between actual and target risk contribution.
            """
            rc = risk_contribution(weights)
            # Normalize to percentage of total risk
            rc_pct = rc / np.sum(rc) if np.sum(rc) > 0 else rc
            return np.sum((rc_pct - target_risk_contrib) ** 2)

        # Constraints: weights sum to 1
        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

        # Bounds: 0 < weight <= 1 (no shorting, no zero weights)
        bounds = tuple((0.001, 1.0) for _ in range(n_assets))

        # Initial guess: equal weights
        initial_weights = np.ones(n_assets) / n_assets

        try:
            result = minimize(
                objective,
                initial_weights,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={"maxiter": self.max_iterations, "ftol": self.tolerance},
            )

            if not result.success:
                logger.warning(f"Risk parity optimization did not converge: {result.message}")

            weights = result.x

            # Normalize weights to ensure they sum to exactly 1
            weights = weights / np.sum(weights)

            # Calculate final risk contributions
            final_rc = risk_contribution(weights)
            final_rc_pct = final_rc / np.sum(final_rc) if np.sum(final_rc) > 0 else final_rc

            # Calculate portfolio metrics
            mean_returns = returns.mean().values * 252
            portfolio_return = float(np.dot(weights, mean_returns))
            portfolio_vol = float(np.sqrt(weights.T @ cov_matrix @ weights))

            logger.info(
                f"Risk parity optimizer converged: {result.success}, "
                f"risk contribution spread: {final_rc_pct.max() - final_rc_pct.min():.4f}"
            )

            return {
                "weights": weights.tolist(),
                "tickers": tickers,
                "method": "risk_parity",
                "success": result.success,
                "expected_return": portfolio_return,
                "expected_volatility": portfolio_vol,
                "risk_contributions": final_rc_pct.tolist(),
                "iterations": result.nit if hasattr(result, "nit") else None,
            }

        except Exception as e:
            logger.error(f"Risk parity optimization failed: {e}")
            # Fallback to equal weights
            equal_weights = np.ones(n_assets) / n_assets
            return {
                "weights": equal_weights.tolist(),
                "tickers": tickers,
                "method": "risk_parity",
                "success": False,
                "error": str(e),
            }


class MinimumVarianceOptimizer(PortfolioOptimizer):
    """
    Minimum variance portfolio optimizer.

    Finds the portfolio with the lowest possible volatility
    (leftmost point on the efficient frontier).

    Benefits:
    - Conservative, low-risk allocation
    - Doesn't require return estimation
    - Good for risk-averse investors

    Trade-offs:
    - Ignores expected returns completely
    - May concentrate in few low-volatility assets
    - Can be sensitive to covariance estimation errors
    """

    def __init__(self, max_iterations: int = 1000, tolerance: float = 1e-10):
        """
        Initialize minimum variance optimizer.

        Args:
            max_iterations: Maximum optimization iterations
            tolerance: Convergence tolerance
        """
        self.max_iterations = max_iterations
        self.tolerance = tolerance

    def optimize(self, returns: pd.DataFrame) -> dict:
        """
        Calculate minimum variance weights.

        Args:
            returns: Daily returns DataFrame

        Returns:
            dict with minimum variance weights and metrics
        """
        self._validate_returns(returns, min_periods=20)

        n_assets = len(returns.columns)
        tickers = returns.columns.tolist()

        # Annualized covariance matrix
        cov_matrix = returns.cov().values * 252

        def portfolio_variance(weights):
            """Calculate portfolio variance."""
            return weights.T @ cov_matrix @ weights

        # Constraints: weights sum to 1
        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

        # Bounds: 0 <= weight <= 1 (no shorting)
        bounds = tuple((0, 1) for _ in range(n_assets))

        # Initial guess: equal weights
        initial_weights = np.ones(n_assets) / n_assets

        try:
            result = minimize(
                portfolio_variance,
                initial_weights,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={"maxiter": self.max_iterations, "ftol": self.tolerance},
            )

            if not result.success:
                logger.warning(f"Minimum variance optimization did not converge: {result.message}")

            weights = result.x

            # Normalize weights
            weights = weights / np.sum(weights)

            # Calculate portfolio metrics
            mean_returns = returns.mean().values * 252
            portfolio_return = float(np.dot(weights, mean_returns))
            portfolio_vol = float(np.sqrt(result.fun))

            logger.info(
                f"Minimum variance optimizer: volatility = {portfolio_vol:.2%}, "
                f"converged = {result.success}"
            )

            return {
                "weights": weights.tolist(),
                "tickers": tickers,
                "method": "min_variance",
                "success": result.success,
                "expected_return": portfolio_return,
                "expected_volatility": portfolio_vol,
                "iterations": result.nit if hasattr(result, "nit") else None,
            }

        except Exception as e:
            logger.error(f"Minimum variance optimization failed: {e}")
            # Fallback to equal weights
            equal_weights = np.ones(n_assets) / n_assets
            return {
                "weights": equal_weights.tolist(),
                "tickers": tickers,
                "method": "min_variance",
                "success": False,
                "error": str(e),
            }


class MarkowitzOptimizer(PortfolioOptimizer):
    """
    Markowitz mean-variance optimizer (Maximum Sharpe Ratio).

    Finds the portfolio that maximizes the Sharpe ratio
    (risk-adjusted return) on the efficient frontier.

    Key concept:
    - Sharpe ratio = (return - risk_free_rate) / volatility
    - Maximize Sharpe = best risk-adjusted return

    Benefits:
    - Optimal risk-adjusted return
    - Industry-standard approach
    - Balances risk and return

    Trade-offs:
    - Sensitive to input estimates (garbage in, garbage out)
    - Requires return estimation (can be noisy)
    - May produce extreme weights with poor estimates
    """

    def __init__(
        self,
        risk_free_rate: float = 0.02,
        max_iterations: int = 1000,
        tolerance: float = 1e-10,
    ):
        """
        Initialize Markowitz optimizer.

        Args:
            risk_free_rate: Annual risk-free rate (default 2%)
            max_iterations: Maximum optimization iterations
            tolerance: Convergence tolerance
        """
        self.risk_free_rate = risk_free_rate
        self.max_iterations = max_iterations
        self.tolerance = tolerance

    def optimize(self, returns: pd.DataFrame) -> dict:
        """
        Calculate maximum Sharpe ratio weights.

        Args:
            returns: Daily returns DataFrame

        Returns:
            dict with optimal weights and metrics
        """
        self._validate_returns(returns, min_periods=20)

        n_assets = len(returns.columns)
        tickers = returns.columns.tolist()

        # Annualized statistics
        mean_returns = returns.mean().values * 252
        cov_matrix = returns.cov().values * 252

        def negative_sharpe(weights):
            """Negative Sharpe ratio (minimize this = maximize Sharpe)."""
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_vol = np.sqrt(weights.T @ cov_matrix @ weights)
            if portfolio_vol <= 0:
                return 0
            sharpe = (portfolio_return - self.risk_free_rate) / portfolio_vol
            return -sharpe  # Minimize negative = maximize positive

        # Constraints: weights sum to 1
        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

        # Bounds: 0 <= weight <= 1 (no shorting)
        bounds = tuple((0, 1) for _ in range(n_assets))

        # Initial guess: equal weights
        initial_weights = np.ones(n_assets) / n_assets

        try:
            result = minimize(
                negative_sharpe,
                initial_weights,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={"maxiter": self.max_iterations, "ftol": self.tolerance},
            )

            if not result.success:
                logger.warning(f"Markowitz optimization did not converge: {result.message}")

            weights = result.x

            # Normalize weights
            weights = weights / np.sum(weights)

            # Calculate portfolio metrics
            portfolio_return = float(np.dot(weights, mean_returns))
            portfolio_vol = float(np.sqrt(weights.T @ cov_matrix @ weights))
            sharpe = (
                (portfolio_return - self.risk_free_rate) / portfolio_vol
                if portfolio_vol > 0
                else 0
            )

            logger.info(
                f"Markowitz optimizer: Sharpe = {sharpe:.4f}, "
                f"return = {portfolio_return:.2%}, vol = {portfolio_vol:.2%}"
            )

            return {
                "weights": weights.tolist(),
                "tickers": tickers,
                "method": "markowitz",
                "success": result.success,
                "expected_return": portfolio_return,
                "expected_volatility": portfolio_vol,
                "sharpe_ratio": sharpe,
                "risk_free_rate": self.risk_free_rate,
                "iterations": result.nit if hasattr(result, "nit") else None,
            }

        except Exception as e:
            logger.error(f"Markowitz optimization failed: {e}")
            # Fallback to equal weights
            equal_weights = np.ones(n_assets) / n_assets
            return {
                "weights": equal_weights.tolist(),
                "tickers": tickers,
                "method": "markowitz",
                "success": False,
                "error": str(e),
            }


# Optimizer registry
_OPTIMIZER_REGISTRY: dict[str, type[PortfolioOptimizer]] = {
    "equal_weight": EqualWeightOptimizer,
    "risk_parity": RiskParityOptimizer,
    "min_variance": MinimumVarianceOptimizer,
    "markowitz": MarkowitzOptimizer,
}


def get_optimizer(method: str, **kwargs) -> PortfolioOptimizer:
    """
    Factory function to create optimizer instances.

    Args:
        method: Optimization method name. Supported:
            - "equal_weight": Simple 1/N allocation
            - "risk_parity": Equal risk contribution
            - "min_variance": Minimum portfolio volatility
            - "markowitz": Maximum Sharpe ratio
        **kwargs: Optional parameters for optimizer constructor
            - risk_free_rate: For Markowitz (default 0.02)
            - max_iterations: For iterative optimizers (default 1000)
            - tolerance: Convergence tolerance (default 1e-10)

    Returns:
        PortfolioOptimizer instance

    Raises:
        ValueError: If method is not supported

    Example:
        >>> optimizer = get_optimizer("markowitz", risk_free_rate=0.03)
        >>> result = optimizer.optimize(returns_df)
        >>> print(result["weights"])
        [0.3, 0.4, 0.3]
    """
    if method not in _OPTIMIZER_REGISTRY:
        supported = ", ".join(_OPTIMIZER_REGISTRY.keys())
        raise ValueError(
            f"Unsupported optimization method: '{method}'. Supported: {supported}"
        )

    optimizer_class = _OPTIMIZER_REGISTRY[method]

    # Filter kwargs to only those accepted by the constructor
    import inspect

    sig = inspect.signature(optimizer_class.__init__)
    valid_params = set(sig.parameters.keys()) - {"self"}
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}

    logger.info(f"Creating optimizer: {method} with params: {filtered_kwargs}")

    return optimizer_class(**filtered_kwargs)


def get_supported_methods() -> list[str]:
    """
    Get list of supported optimization methods.

    Returns:
        List of method names
    """
    return list(_OPTIMIZER_REGISTRY.keys())


__all__ = [
    "PortfolioOptimizer",
    "EqualWeightOptimizer",
    "RiskParityOptimizer",
    "MinimumVarianceOptimizer",
    "MarkowitzOptimizer",
    "get_optimizer",
    "get_supported_methods",
]
