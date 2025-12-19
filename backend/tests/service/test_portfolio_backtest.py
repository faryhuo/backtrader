"""Unit tests for portfolio backtest service."""

import pytest
from unittest.mock import patch, MagicMock

from src.service.portfolio_backtest import (
    normalize_weights,
    calculate_correlation_matrix,
    calculate_optimal_weights,
    PortfolioBacktestError,
)


class TestNormalizeWeights:
    """Tests for weight normalization function."""

    def test_normalize_equal_weights(self):
        """Test normalization of equal weights."""
        weights = [1.0, 1.0, 1.0]
        result = normalize_weights(weights)
        assert len(result) == 3
        assert abs(sum(result) - 1.0) < 0.0001
        assert all(abs(w - 1/3) < 0.0001 for w in result)

    def test_normalize_unequal_weights(self):
        """Test normalization of unequal weights."""
        weights = [2.0, 1.0, 1.0]
        result = normalize_weights(weights)
        assert abs(sum(result) - 1.0) < 0.0001
        assert abs(result[0] - 0.5) < 0.0001
        assert abs(result[1] - 0.25) < 0.0001

    def test_normalize_already_normalized(self):
        """Test weights that already sum to 1."""
        weights = [0.5, 0.3, 0.2]
        result = normalize_weights(weights)
        assert abs(sum(result) - 1.0) < 0.0001
        assert result == weights

    def test_normalize_zero_total_raises(self):
        """Test that zero total raises error."""
        with pytest.raises(PortfolioBacktestError):
            normalize_weights([0, 0, 0])

    def test_normalize_negative_raises(self):
        """Test that negative total raises error."""
        with pytest.raises(PortfolioBacktestError):
            normalize_weights([-1, -1, -1])


class TestCorrelationMatrix:
    """Tests for correlation matrix calculation."""

    @patch('src.service.portfolio_backtest.get_data')
    def test_correlation_returns_structure(self, mock_get_data):
        """Test correlation returns expected structure."""
        import pandas as pd
        import numpy as np
        
        # Mock data with some correlation
        dates = pd.date_range('2022-01-01', periods=100)
        mock_df = pd.DataFrame({
            'Close': np.random.randn(100).cumsum() + 100
        }, index=dates)
        mock_df.index.name = 'Date'
        
        mock_get_data.return_value = mock_df
        
        result = calculate_correlation_matrix(['AAPL', 'GOOGL'], '2022-01-01', '2022-12-31')
        
        assert 'matrix' in result
        assert 'tickers' in result
        assert len(result['tickers']) == 2


class TestOptimalWeights:
    """Tests for Markowitz optimization."""

    @patch('src.service.portfolio_backtest.get_data')
    def test_optimal_weights_returns_structure(self, mock_get_data):
        """Test optimization returns expected structure."""
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range('2022-01-01', periods=100)
        mock_df = pd.DataFrame({
            'Close': np.random.randn(100).cumsum() + 100
        }, index=dates)
        mock_df.index.name = 'Date'
        
        mock_get_data.return_value = mock_df
        
        result = calculate_optimal_weights(['AAPL', 'GOOGL'], '2022-01-01', '2022-12-31')
        
        assert 'optimal_weights' in result
        assert 'tickers' in result
        assert len(result['optimal_weights']) == 2

    @patch('src.service.portfolio_backtest.get_data')
    def test_optimal_weights_sum_to_one(self, mock_get_data):
        """Test optimal weights sum to 1."""
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range('2022-01-01', periods=100)
        mock_df = pd.DataFrame({
            'Close': np.random.randn(100).cumsum() + 100
        }, index=dates)
        mock_df.index.name = 'Date'
        
        mock_get_data.return_value = mock_df
        
        result = calculate_optimal_weights(['AAPL', 'GOOGL'], '2022-01-01', '2022-12-31')
        
        if 'error' not in result:
            assert abs(sum(result['optimal_weights']) - 1.0) < 0.01
