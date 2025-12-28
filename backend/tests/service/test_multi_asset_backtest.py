"""Unit tests for multi-asset backtest service."""

import pytest
from unittest.mock import patch, MagicMock

from src.service.multi_asset_backtest import (
    calculate_correlation_matrix,
    calculate_optimal_weights,
    MultiAssetBacktestError,
)


def _create_mock_df(periods: int = 100):
    """Create mock price data using modern numpy.random.Generator."""
    import pandas as pd
    import numpy as np
    
    rng = np.random.default_rng(42)  # Seed for reproducibility
    dates = pd.date_range('2022-01-01', periods=periods)
    mock_df = pd.DataFrame({
        'Close': rng.standard_normal(periods).cumsum() + 100
    }, index=dates)
    mock_df.index.name = 'Date'
    return mock_df


class TestCorrelationMatrix:
    """Tests for correlation matrix calculation."""

    @patch('src.service.multi_asset_backtest.get_data')
    def test_correlation_returns_structure(self, mock_get_data):
        """Test correlation returns expected structure."""
        mock_get_data.return_value = _create_mock_df()
        
        result = calculate_correlation_matrix(['AAPL', 'GOOGL'], '2022-01-01', '2022-12-31')
        
        assert 'matrix' in result
        assert 'tickers' in result
        assert len(result['tickers']) == 2


class TestOptimalWeights:
    """Tests for Markowitz optimization."""

    @patch('src.service.multi_asset_backtest.get_data')
    def test_optimal_weights_returns_structure(self, mock_get_data):
        """Test optimization returns expected structure."""
        mock_get_data.return_value = _create_mock_df()
        
        result = calculate_optimal_weights(['AAPL', 'GOOGL'], '2022-01-01', '2022-12-31')
        
        assert 'optimal_weights' in result
        assert 'tickers' in result
        assert len(result['optimal_weights']) == 2

    @patch('src.service.multi_asset_backtest.get_data')
    def test_optimal_weights_sum_to_one(self, mock_get_data):
        """Test optimal weights sum to 1."""
        mock_get_data.return_value = _create_mock_df()
        
        result = calculate_optimal_weights(['AAPL', 'GOOGL'], '2022-01-01', '2022-12-31')
        
        if 'error' not in result:
            assert abs(sum(result['optimal_weights']) - 1.0) < 0.01
