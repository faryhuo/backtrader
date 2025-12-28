"""Unit tests for portfolio optimizer module."""

import pytest
import numpy as np
import pandas as pd

from src.service.portfolio_optimizer import (
    PortfolioOptimizer,
    EqualWeightOptimizer,
    RiskParityOptimizer,
    MinimumVarianceOptimizer,
    MarkowitzOptimizer,
    get_optimizer,
    get_supported_methods,
)


def create_mock_returns(n_assets: int = 3, n_periods: int = 252, seed: int = 42) -> pd.DataFrame:
    """
    Create mock daily returns DataFrame for testing.

    Args:
        n_assets: Number of assets
        n_periods: Number of trading days
        seed: Random seed for reproducibility

    Returns:
        DataFrame with daily returns
    """
    np.random.seed(seed)

    # Create returns with different characteristics
    # Asset 0: Low volatility, moderate return
    # Asset 1: High volatility, high return
    # Asset 2: Medium volatility, medium return
    volatilities = [0.01, 0.03, 0.02][:n_assets]
    means = [0.0003, 0.0008, 0.0005][:n_assets]

    returns_data = {}
    tickers = [f"ASSET_{i}" for i in range(n_assets)]

    for i, ticker in enumerate(tickers):
        vol = volatilities[i] if i < len(volatilities) else 0.02
        mean = means[i] if i < len(means) else 0.0005
        returns_data[ticker] = np.random.normal(mean, vol, n_periods)

    return pd.DataFrame(returns_data)


class TestEqualWeightOptimizer:
    """Tests for EqualWeightOptimizer."""

    def test_weights_sum_to_one(self):
        """Equal weights should sum to 1.0."""
        optimizer = EqualWeightOptimizer()
        returns = create_mock_returns(n_assets=4)

        result = optimizer.optimize(returns)

        assert abs(sum(result["weights"]) - 1.0) < 1e-10

    def test_equal_distribution(self):
        """All weights should be equal."""
        optimizer = EqualWeightOptimizer()
        returns = create_mock_returns(n_assets=5)

        result = optimizer.optimize(returns)

        expected_weight = 1.0 / 5
        for weight in result["weights"]:
            assert abs(weight - expected_weight) < 1e-10

    def test_success_flag(self):
        """Equal weight always succeeds."""
        optimizer = EqualWeightOptimizer()
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        assert result["success"] is True

    def test_method_name(self):
        """Method name should be 'equal_weight'."""
        optimizer = EqualWeightOptimizer()
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        assert result["method"] == "equal_weight"

    def test_tickers_preserved(self):
        """Ticker names should be preserved in output."""
        optimizer = EqualWeightOptimizer()
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        assert result["tickers"] == list(returns.columns)

    def test_includes_portfolio_stats(self):
        """Result should include expected return and volatility."""
        optimizer = EqualWeightOptimizer()
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        assert "expected_return" in result
        assert "expected_volatility" in result
        assert isinstance(result["expected_return"], float)
        assert isinstance(result["expected_volatility"], float)

    def test_insufficient_data_raises(self):
        """Should raise ValueError with insufficient data."""
        optimizer = EqualWeightOptimizer()
        returns = pd.DataFrame({"A": [0.01]})  # Only 1 period

        with pytest.raises(ValueError, match="Insufficient data"):
            optimizer.optimize(returns)

    def test_empty_dataframe_raises(self):
        """Should raise ValueError with empty DataFrame."""
        optimizer = EqualWeightOptimizer()
        returns = pd.DataFrame()

        with pytest.raises(ValueError, match="empty"):
            optimizer.optimize(returns)


class TestRiskParityOptimizer:
    """Tests for RiskParityOptimizer."""

    def test_weights_sum_to_one(self):
        """Risk parity weights should sum to 1.0."""
        optimizer = RiskParityOptimizer()
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        assert abs(sum(result["weights"]) - 1.0) < 1e-6

    def test_risk_contributions_exist(self):
        """Result should include risk contributions."""
        optimizer = RiskParityOptimizer()
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        if result["success"]:
            assert "risk_contributions" in result
            assert len(result["risk_contributions"]) == len(result["weights"])

    def test_risk_contributions_roughly_equal(self):
        """Risk contributions should be approximately equal."""
        optimizer = RiskParityOptimizer()
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        if result["success"]:
            rc = result["risk_contributions"]
            # Check that max - min spread is small
            spread = max(rc) - min(rc)
            assert spread < 0.1  # 10% tolerance

    def test_method_name(self):
        """Method name should be 'risk_parity'."""
        optimizer = RiskParityOptimizer()
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        assert result["method"] == "risk_parity"

    def test_low_vol_asset_gets_higher_weight(self):
        """Low volatility asset should get higher weight."""
        optimizer = RiskParityOptimizer()
        returns = create_mock_returns()  # ASSET_0 has lowest vol

        result = optimizer.optimize(returns)

        if result["success"]:
            # ASSET_0 (index 0) should have higher weight than ASSET_1 (index 1)
            assert result["weights"][0] > result["weights"][1]


class TestMinimumVarianceOptimizer:
    """Tests for MinimumVarianceOptimizer."""

    def test_weights_sum_to_one(self):
        """Minimum variance weights should sum to 1.0."""
        optimizer = MinimumVarianceOptimizer()
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        assert abs(sum(result["weights"]) - 1.0) < 1e-6

    def test_method_name(self):
        """Method name should be 'min_variance'."""
        optimizer = MinimumVarianceOptimizer()
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        assert result["method"] == "min_variance"

    def test_lower_volatility_than_equal_weight(self):
        """Min variance should have lower or equal volatility than equal weight."""
        returns = create_mock_returns()

        equal_weight = EqualWeightOptimizer().optimize(returns)
        min_var = MinimumVarianceOptimizer().optimize(returns)

        if min_var["success"]:
            # Min variance volatility should be <= equal weight volatility
            assert min_var["expected_volatility"] <= equal_weight["expected_volatility"] + 1e-6

    def test_includes_volatility(self):
        """Result should include expected volatility."""
        optimizer = MinimumVarianceOptimizer()
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        assert "expected_volatility" in result
        assert result["expected_volatility"] >= 0


class TestMarkowitzOptimizer:
    """Tests for MarkowitzOptimizer."""

    def test_weights_sum_to_one(self):
        """Markowitz weights should sum to 1.0."""
        optimizer = MarkowitzOptimizer()
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        assert abs(sum(result["weights"]) - 1.0) < 1e-6

    def test_method_name(self):
        """Method name should be 'markowitz'."""
        optimizer = MarkowitzOptimizer()
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        assert result["method"] == "markowitz"

    def test_includes_sharpe_ratio(self):
        """Result should include Sharpe ratio."""
        optimizer = MarkowitzOptimizer()
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        if result["success"]:
            assert "sharpe_ratio" in result
            assert isinstance(result["sharpe_ratio"], float)

    def test_custom_risk_free_rate(self):
        """Should respect custom risk-free rate."""
        optimizer = MarkowitzOptimizer(risk_free_rate=0.05)
        returns = create_mock_returns()

        result = optimizer.optimize(returns)

        if result["success"]:
            assert result["risk_free_rate"] == 0.05

    def test_higher_sharpe_than_equal_weight(self):
        """Markowitz should have higher or equal Sharpe than equal weight."""
        returns = create_mock_returns(seed=123)  # Use different seed

        equal_weight = EqualWeightOptimizer().optimize(returns)
        markowitz = MarkowitzOptimizer().optimize(returns)

        if markowitz["success"]:
            # Calculate equal weight Sharpe for comparison
            eq_return = equal_weight["expected_return"]
            eq_vol = equal_weight["expected_volatility"]
            eq_sharpe = (eq_return - 0.02) / eq_vol if eq_vol > 0 else 0

            # Markowitz should be >= equal weight Sharpe
            assert markowitz["sharpe_ratio"] >= eq_sharpe - 0.01  # Small tolerance


class TestOptimizerFactory:
    """Tests for get_optimizer factory function."""

    def test_get_equal_weight(self):
        """Factory should create EqualWeightOptimizer."""
        optimizer = get_optimizer("equal_weight")
        assert isinstance(optimizer, EqualWeightOptimizer)

    def test_get_risk_parity(self):
        """Factory should create RiskParityOptimizer."""
        optimizer = get_optimizer("risk_parity")
        assert isinstance(optimizer, RiskParityOptimizer)

    def test_get_min_variance(self):
        """Factory should create MinimumVarianceOptimizer."""
        optimizer = get_optimizer("min_variance")
        assert isinstance(optimizer, MinimumVarianceOptimizer)

    def test_get_markowitz(self):
        """Factory should create MarkowitzOptimizer."""
        optimizer = get_optimizer("markowitz")
        assert isinstance(optimizer, MarkowitzOptimizer)

    def test_markowitz_with_params(self):
        """Factory should pass kwargs to optimizer."""
        optimizer = get_optimizer("markowitz", risk_free_rate=0.05)
        assert optimizer.risk_free_rate == 0.05

    def test_invalid_method_raises(self):
        """Invalid method should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported optimization method"):
            get_optimizer("invalid_method")

    def test_invalid_method_lists_supported(self):
        """Error message should list supported methods."""
        with pytest.raises(ValueError) as exc_info:
            get_optimizer("unknown")

        error_msg = str(exc_info.value)
        assert "equal_weight" in error_msg
        assert "risk_parity" in error_msg
        assert "min_variance" in error_msg
        assert "markowitz" in error_msg


class TestGetSupportedMethods:
    """Tests for get_supported_methods function."""

    def test_returns_all_methods(self):
        """Should return all supported methods."""
        methods = get_supported_methods()

        assert "equal_weight" in methods
        assert "risk_parity" in methods
        assert "min_variance" in methods
        assert "markowitz" in methods

    def test_returns_list(self):
        """Should return a list."""
        methods = get_supported_methods()
        assert isinstance(methods, list)


class TestOptimizerConvergence:
    """Tests for optimizer convergence behavior."""

    def test_all_optimizers_converge(self):
        """All optimizers should converge on reasonable data."""
        returns = create_mock_returns(n_assets=3, n_periods=252)

        for method in get_supported_methods():
            optimizer = get_optimizer(method)
            result = optimizer.optimize(returns)

            # All should succeed
            assert result["success"], f"{method} failed to converge"

            # All weights should sum to 1
            assert abs(sum(result["weights"]) - 1.0) < 1e-6, f"{method} weights don't sum to 1"

            # All weights should be non-negative
            assert all(w >= -1e-6 for w in result["weights"]), f"{method} has negative weights"

    def test_handles_high_correlation(self):
        """Optimizers should handle highly correlated assets."""
        np.random.seed(42)
        base_returns = np.random.normal(0.0005, 0.02, 252)

        # Create highly correlated returns
        returns = pd.DataFrame({
            "A": base_returns,
            "B": base_returns + np.random.normal(0, 0.001, 252),  # Highly correlated
            "C": base_returns + np.random.normal(0, 0.001, 252),  # Highly correlated
        })

        for method in get_supported_methods():
            optimizer = get_optimizer(method)
            result = optimizer.optimize(returns)

            # Should still produce valid weights
            assert abs(sum(result["weights"]) - 1.0) < 1e-4, f"{method} failed with correlated assets"

    def test_handles_many_assets(self):
        """Optimizers should handle portfolios with many assets."""
        returns = create_mock_returns(n_assets=20, n_periods=500)

        for method in get_supported_methods():
            optimizer = get_optimizer(method)
            result = optimizer.optimize(returns)

            assert len(result["weights"]) == 20, f"{method} wrong number of weights"
            assert abs(sum(result["weights"]) - 1.0) < 1e-4, f"{method} weights don't sum to 1"


class TestOptimizerEdgeCases:
    """Tests for edge cases and error handling."""

    def test_single_asset(self):
        """Single asset should get 100% weight."""
        returns = create_mock_returns(n_assets=1, n_periods=100)

        for method in get_supported_methods():
            optimizer = get_optimizer(method)
            result = optimizer.optimize(returns)

            assert len(result["weights"]) == 1
            assert abs(result["weights"][0] - 1.0) < 1e-6

    def test_two_assets(self):
        """Two assets should work correctly."""
        returns = create_mock_returns(n_assets=2, n_periods=100)

        for method in get_supported_methods():
            optimizer = get_optimizer(method)
            result = optimizer.optimize(returns)

            assert len(result["weights"]) == 2
            assert abs(sum(result["weights"]) - 1.0) < 1e-6

    def test_minimum_periods(self):
        """Should work with minimum required periods."""
        # Most optimizers need at least 20 periods
        returns = create_mock_returns(n_assets=3, n_periods=25)

        optimizer = EqualWeightOptimizer()
        result = optimizer.optimize(returns)
        assert result["success"]

    def test_nan_handling(self):
        """Should handle NaN values gracefully."""
        returns = create_mock_returns()
        returns.iloc[0, 0] = np.nan  # Add a NaN

        # Equal weight should still work (just logs warning)
        optimizer = EqualWeightOptimizer()
        result = optimizer.optimize(returns)
        assert result["success"]
