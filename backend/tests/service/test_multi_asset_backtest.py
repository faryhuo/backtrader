"""Unit tests for multi-asset backtest service."""

import pytest
from unittest.mock import patch, MagicMock

from src.service.multi_asset_backtest import (
    MultiAssetBacktestError,
    DataAlignmentError,
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


class TestMultiAssetBacktestExceptions:
    """Tests for multi-asset backtest exceptions."""

    def test_multi_asset_backtest_error(self):
        """Test MultiAssetBacktestError can be raised."""
        with pytest.raises(MultiAssetBacktestError):
            raise MultiAssetBacktestError("Test error")

    def test_data_alignment_error(self):
        """Test DataAlignmentError can be raised."""
        with pytest.raises(DataAlignmentError):
            raise DataAlignmentError("Test alignment error")
