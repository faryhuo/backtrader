"""
Unit tests for market_data storage module.

Tests for market data fetching, caching, and integration with multiple data sources
including Yahoo Finance, EODHD, and local database storage.
"""
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch, call

import pandas as pd
import pytest
import backtrader as bt

from src.contracts.exceptions import DataLoadError
from src.db.storage.market_data import (
    save_to_db,
    get_data_from_db,
    get_data_from_yahoo,
    get_data_from_eodhd,
    get_data,
    get_bt_feed,
    get_raw_data_json,
)


@pytest.fixture
def sample_dataframe():
    """Sample OHLCV DataFrame for testing."""
    dates = pd.date_range('2024-01-01', periods=5, freq='D')
    data = pd.DataFrame({
        'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
        'High': [105.0, 106.0, 107.0, 108.0, 109.0],
        'Low': [95.0, 96.0, 97.0, 98.0, 99.0],
        'Close': [102.0, 103.0, 104.0, 105.0, 106.0],
        'Volume': [1000000, 1100000, 1200000, 1300000, 1400000],
        'Adj Close': [102.0, 103.0, 104.0, 105.0, 106.0],
    }, index=dates)
    data.index.name = 'Date'
    return data


@pytest.fixture
def mock_session_factory():
    """Mock database session factory."""
    session = MagicMock()
    session.get_bind.return_value.dialect.name = "sqlite"
    session.begin.return_value.__enter__ = MagicMock()
    session.begin.return_value.__exit__ = MagicMock()
    session.execute.return_value.rowcount = 5
    return session


class TestSaveToDb:
    """Tests for save_to_db function."""

    @patch('src.db.storage.market_data._get_engine_and_session')
    def test_save_to_db_success_sqlite(self, mock_get_engine, sample_dataframe, mock_session_factory):
        """Test successfully saving data to SQLite database."""
        mock_get_engine.return_value = (MagicMock(), lambda: mock_session_factory)

        result = save_to_db("AAPL", sample_dataframe, source="yfinance")

        assert result is True
        assert mock_session_factory.execute.called
        assert mock_session_factory.close.called

    @patch('src.db.storage.market_data._get_engine_and_session')
    def test_save_to_db_with_date_column(self, mock_get_engine, mock_session_factory):
        """Test saving data when Date is a regular column (not index)."""
        mock_get_engine.return_value = (MagicMock(), lambda: mock_session_factory)

        data = pd.DataFrame({
            'Date': ['2024-01-01', '2024-01-02'],
            'Open': [100.0, 101.0],
            'High': [105.0, 106.0],
            'Low': [95.0, 96.0],
            'Close': [102.0, 103.0],
            'Volume': [1000000, 1100000],
        })

        result = save_to_db("AAPL", data)

        assert result is True

    @patch('src.db.storage.market_data._get_engine_and_session')
    def test_save_to_db_lowercase_columns(self, mock_get_engine, mock_session_factory):
        """Test saving data with lowercase column names."""
        mock_get_engine.return_value = (MagicMock(), lambda: mock_session_factory)

        data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=2),
            'open': [100.0, 101.0],
            'high': [105.0, 106.0],
            'low': [95.0, 96.0],
            'close': [102.0, 103.0],
            'volume': [1000000, 1100000],
            'adj_close': [102.0, 103.0],
        })

        result = save_to_db("AAPL", data)

        assert result is True

    @patch('src.db.storage.market_data._get_engine_and_session')
    def test_save_to_db_missing_date_column(self, mock_get_engine, mock_session_factory):
        """Test saving data without Date column raises error."""
        mock_get_engine.return_value = (MagicMock(), lambda: mock_session_factory)

        data = pd.DataFrame({
            'Open': [100.0],
            'Close': [102.0],
        })

        result = save_to_db("AAPL", data)

        assert result is False

    @patch('src.db.storage.market_data._get_engine_and_session')
    def test_save_to_db_empty_dataframe(self, mock_get_engine, mock_session_factory):
        """Test saving empty DataFrame returns False."""
        mock_get_engine.return_value = (MagicMock(), lambda: mock_session_factory)

        data = pd.DataFrame()

        result = save_to_db("AAPL", data)

        assert result is False

    @patch('src.db.storage.market_data._get_engine_and_session')
    def test_save_to_db_exception_handling(self, mock_get_engine):
        """Test exception handling during save."""
        mock_get_engine.side_effect = Exception("Database connection failed")

        result = save_to_db("AAPL", pd.DataFrame({'Date': ['2024-01-01']}))

        assert result is False

    @patch('src.db.storage.market_data._get_engine_and_session')
    def test_save_to_db_non_sqlite_dialect(self, mock_get_engine, sample_dataframe):
        """Test saving with non-SQLite database (PostgreSQL/MySQL)."""
        mock_session = MagicMock()
        mock_session.get_bind.return_value.dialect.name = "postgresql"
        mock_session.execute.return_value.all.return_value = []
        mock_session.begin.return_value.__enter__ = MagicMock()
        mock_session.begin.return_value.__exit__ = MagicMock()

        mock_get_engine.return_value = (MagicMock(), lambda: mock_session)

        result = save_to_db("AAPL", sample_dataframe)

        assert result is True


class TestGetDataFromDb:
    """Tests for get_data_from_db function."""

    @patch('src.db.storage.market_data._get_engine_and_session')
    @patch('pandas.read_sql')
    def test_get_data_from_db_success(self, mock_read_sql, mock_get_engine):
        """Test successfully fetching data from database."""
        mock_engine = MagicMock()
        mock_get_engine.return_value = (mock_engine, MagicMock())

        # Mock data returned from database
        db_data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=3),
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [95.0, 96.0, 97.0],
            'close': [102.0, 103.0, 104.0],
            'volume': [1000000, 1100000, 1200000],
            'adj_close': [102.0, 103.0, 104.0],
        })
        mock_read_sql.return_value = db_data

        result = get_data_from_db("AAPL", "2024-01-01", "2024-01-03")

        assert result is not None
        assert len(result) == 3
        assert 'Open' in result.columns
        assert 'High' in result.columns
        assert 'Close' in result.columns
        assert result.index.name == 'Date'

    @patch('src.db.storage.market_data._get_engine_and_session')
    @patch('pandas.read_sql')
    def test_get_data_from_db_empty_result(self, mock_read_sql, mock_get_engine):
        """Test fetching data when database returns empty result."""
        mock_engine = MagicMock()
        mock_get_engine.return_value = (mock_engine, MagicMock())

        mock_read_sql.return_value = pd.DataFrame()

        result = get_data_from_db("AAPL", "2024-01-01", "2024-01-03")

        assert result is None

    @patch('src.db.storage.market_data._get_engine_and_session')
    def test_get_data_from_db_exception(self, mock_get_engine):
        """Test exception handling when database fetch fails."""
        mock_get_engine.side_effect = Exception("Connection error")

        result = get_data_from_db("AAPL", "2024-01-01", "2024-01-03")

        assert result is None

    @patch('src.db.storage.market_data._get_engine_and_session')
    @patch('pandas.read_sql')
    def test_get_data_from_db_missing_adj_close(self, mock_read_sql, mock_get_engine):
        """Test handling missing Adj Close column."""
        mock_engine = MagicMock()
        mock_get_engine.return_value = (mock_engine, MagicMock())

        db_data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=2),
            'open': [100.0, 101.0],
            'high': [105.0, 106.0],
            'low': [95.0, 96.0],
            'close': [102.0, 103.0],
            'volume': [1000000, 1100000],
            'adj_close': [None, None],  # Missing adj_close
        })
        mock_read_sql.return_value = db_data

        result = get_data_from_db("AAPL", "2024-01-01", "2024-01-02")

        assert result is not None
        assert 'Adj Close' in result.columns
        # Should fall back to Close values
        assert (result['Adj Close'] == result['Close']).all()


class TestGetDataFromYahoo:
    """Tests for get_data_from_yahoo function."""

    @patch('src.db.storage.market_data.save_to_db')
    @patch('yfinance.download')
    def test_get_data_from_yahoo_success(self, mock_download, mock_save, sample_dataframe):
        """Test successfully fetching data from Yahoo Finance."""
        mock_download.return_value = sample_dataframe
        mock_save.return_value = True

        result = get_data_from_yahoo("AAPL", "2024-01-01", "2024-01-05")

        assert result is not None
        assert len(result) == 5
        mock_download.assert_called_once_with("AAPL", start="2024-01-01", end="2024-01-05",
                                              progress=False, auto_adjust=False)
        mock_save.assert_called_once()

    @patch('yfinance.download')
    def test_get_data_from_yahoo_empty_result(self, mock_download):
        """Test Yahoo Finance returns empty data."""
        mock_download.return_value = pd.DataFrame()

        result = get_data_from_yahoo("INVALID", "2024-01-01", "2024-01-05")

        assert result is None

    @patch('yfinance.download')
    def test_get_data_from_yahoo_none_result(self, mock_download):
        """Test Yahoo Finance returns None."""
        mock_download.return_value = None

        result = get_data_from_yahoo("INVALID", "2024-01-01", "2024-01-05")

        assert result is None

    @patch('yfinance.download')
    def test_get_data_from_yahoo_exception(self, mock_download):
        """Test exception handling when Yahoo Finance fails."""
        mock_download.side_effect = Exception("Network error")

        result = get_data_from_yahoo("AAPL", "2024-01-01", "2024-01-05")

        assert result is None

    @patch('src.db.storage.market_data.save_to_db')
    @patch('yfinance.download')
    def test_get_data_from_yahoo_multiindex_columns(self, mock_download, mock_save):
        """Test handling MultiIndex columns from Yahoo Finance."""
        # Create data with MultiIndex columns (happens with multiple tickers)
        dates = pd.date_range('2024-01-01', periods=3)
        data = pd.DataFrame({
            ('Open', 'AAPL'): [100.0, 101.0, 102.0],
            ('Close', 'AAPL'): [102.0, 103.0, 104.0],
        }, index=dates)
        data.columns = pd.MultiIndex.from_tuples(data.columns)

        mock_download.return_value = data
        mock_save.return_value = True

        result = get_data_from_yahoo("AAPL", "2024-01-01", "2024-01-03")

        assert result is not None
        # Should flatten MultiIndex to single level
        assert not isinstance(result.columns, pd.MultiIndex)


class TestGetDataFromEodhd:
    """Tests for get_data_from_eodhd function."""

    @patch('src.db.storage.market_data.save_to_db')
    @patch('src.db.storage.eodhd_data.fetch_from_eodhd')
    def test_get_data_from_eodhd_success(self, mock_fetch, mock_save, sample_dataframe):
        """Test successfully fetching data from EODHD."""
        mock_fetch.return_value = sample_dataframe
        mock_save.return_value = True

        result = get_data_from_eodhd("AAPL", "2024-01-01", "2024-01-05", api_key="test_key")

        assert result is not None
        assert len(result) == 5
        mock_fetch.assert_called_once_with("AAPL", "2024-01-01", "2024-01-05", "test_key")
        mock_save.assert_called_once()

    @patch('src.db.storage.settings.SettingsStorage')
    @patch('src.db.storage.eodhd_data.fetch_from_eodhd')
    def test_get_data_from_eodhd_with_settings_api_key(self, mock_fetch, mock_settings_class, sample_dataframe):
        """Test EODHD fetch using API key from settings."""
        mock_settings = MagicMock()
        mock_settings.get_eodhd_api_key.return_value = "settings_key"
        mock_settings_class.return_value = mock_settings

        mock_fetch.return_value = sample_dataframe

        result = get_data_from_eodhd("AAPL", "2024-01-01", "2024-01-05")

        assert result is not None
        mock_fetch.assert_called_once_with("AAPL", "2024-01-01", "2024-01-05", "settings_key")

    @patch('src.db.storage.settings.SettingsStorage')
    def test_get_data_from_eodhd_no_api_key(self, mock_settings_class):
        """Test EODHD fetch when no API key is configured."""
        mock_settings = MagicMock()
        mock_settings.get_eodhd_api_key.return_value = None
        mock_settings_class.return_value = mock_settings

        result = get_data_from_eodhd("AAPL", "2024-01-01", "2024-01-05")

        assert result is None

    @patch('src.db.storage.eodhd_data.fetch_from_eodhd')
    def test_get_data_from_eodhd_exception(self, mock_fetch):
        """Test exception handling when EODHD fetch fails."""
        mock_fetch.side_effect = Exception("API error")

        result = get_data_from_eodhd("AAPL", "2024-01-01", "2024-01-05", api_key="test_key")

        assert result is None


class TestGetData:
    """Tests for get_data function (main entry point with priority)."""

    @patch('src.db.storage.market_data.get_data_from_yahoo')
    def test_get_data_success_first_source(self, mock_yahoo, sample_dataframe):
        """Test successful data fetch from first priority source."""
        mock_yahoo.return_value = sample_dataframe

        result = get_data("AAPL", "2024-01-01", "2024-01-05", priority=["yahoo"])

        assert result is not None
        assert len(result) == 5
        mock_yahoo.assert_called_once()

    @patch('src.db.storage.market_data.get_data_from_db')
    @patch('src.db.storage.market_data.get_data_from_yahoo')
    def test_get_data_fallback_to_second_source(self, mock_yahoo, mock_db, sample_dataframe):
        """Test fallback when first source fails."""
        mock_yahoo.return_value = None  # First source fails
        mock_db.return_value = sample_dataframe  # Second source succeeds

        result = get_data("AAPL", "2024-01-01", "2024-01-05", priority=["yahoo", "database"])

        assert result is not None
        mock_yahoo.assert_called_once()
        mock_db.assert_called_once()

    @patch('src.db.storage.market_data.get_data_from_yahoo')
    @patch('src.db.storage.market_data.get_data_from_eodhd')
    def test_get_data_all_sources_fail(self, mock_eodhd, mock_yahoo):
        """Test DataLoadError when all sources fail."""
        mock_yahoo.return_value = None
        mock_eodhd.return_value = None

        with pytest.raises(DataLoadError) as exc_info:
            get_data("AAPL", "2024-01-01", "2024-01-05", priority=["yahoo", "eodhd"])

        assert "All data sources failed" in str(exc_info.value)
        assert "AAPL" in str(exc_info.value)

    @patch('src.db.storage.market_data.get_data_from_yahoo')
    def test_get_data_unknown_source_skipped(self, mock_yahoo, sample_dataframe):
        """Test unknown data sources are skipped."""
        mock_yahoo.return_value = sample_dataframe

        result = get_data("AAPL", "2024-01-01", "2024-01-05",
                         priority=["unknown_source", "yahoo"])

        assert result is not None
        # Should skip unknown source and use yahoo

    @patch('src.db.storage.settings.SettingsStorage')
    @patch('src.db.storage.market_data.get_data_from_yahoo')
    def test_get_data_uses_settings_priority(self, mock_yahoo, mock_settings_class, sample_dataframe):
        """Test using priority from settings when not provided."""
        mock_settings = MagicMock()
        mock_settings.get_data_source_priority.return_value = ["yahoo", "database"]
        mock_settings_class.return_value = mock_settings

        mock_yahoo.return_value = sample_dataframe

        result = get_data("AAPL", "2024-01-01", "2024-01-05")  # No priority arg

        assert result is not None
        mock_settings.get_data_source_priority.assert_called_once()

    @patch('src.db.storage.settings.SettingsStorage')
    @patch('src.db.storage.market_data.get_data_from_yahoo')
    def test_get_data_settings_load_fails_uses_default(self, mock_yahoo, mock_settings_class, sample_dataframe):
        """Test fallback to default priority when settings load fails."""
        mock_settings_class.side_effect = Exception("Settings error")
        mock_yahoo.return_value = sample_dataframe

        result = get_data("AAPL", "2024-01-01", "2024-01-05")

        assert result is not None
        # Should use default ["yahoo", "database"]

    @patch('src.db.storage.market_data.get_data_from_yahoo')
    def test_get_data_source_returns_empty_dataframe(self, mock_yahoo):
        """Test when source returns empty DataFrame (not None)."""
        mock_yahoo.return_value = pd.DataFrame()  # Empty but not None

        with pytest.raises(DataLoadError):
            get_data("AAPL", "2024-01-01", "2024-01-05", priority=["yahoo"])


class TestGetBtFeed:
    """Tests for get_bt_feed function."""

    @patch('src.db.storage.market_data.get_data')
    def test_get_bt_feed_success(self, mock_get_data, sample_dataframe):
        """Test creating Backtrader feed from data."""
        mock_get_data.return_value = sample_dataframe

        result = get_bt_feed("AAPL", "2024-01-01", "2024-01-05")

        assert isinstance(result, bt.feeds.PandasData)
        mock_get_data.assert_called_once_with("AAPL", "2024-01-01", "2024-01-05")

    @patch('src.db.storage.market_data.get_data')
    def test_get_bt_feed_propagates_exception(self, mock_get_data):
        """Test exception propagates when get_data fails."""
        mock_get_data.side_effect = DataLoadError("Failed to load data")

        with pytest.raises(DataLoadError):
            get_bt_feed("AAPL", "2024-01-01", "2024-01-05")


class TestGetRawDataJson:
    """Tests for get_raw_data_json function."""

    @patch('src.db.storage.market_data.get_data')
    def test_get_raw_data_json_success(self, mock_get_data, sample_dataframe):
        """Test converting data to JSON format for frontend."""
        mock_get_data.return_value = sample_dataframe

        result = get_raw_data_json("AAPL", "2024-01-01", "2024-01-05")

        assert isinstance(result, list)
        assert len(result) == 5

        # Check first record structure
        first_record = result[0]
        assert "time" in first_record
        assert "open" in first_record
        assert "high" in first_record
        assert "low" in first_record
        assert "close" in first_record
        assert "volume" in first_record

        # Verify values
        assert first_record["time"] == "2024-01-01"
        assert first_record["open"] == 100.0
        assert first_record["close"] == 102.0

    @patch('src.db.storage.market_data.get_data')
    def test_get_raw_data_json_with_index(self, mock_get_data):
        """Test conversion when Date is in index."""
        dates = pd.date_range('2024-01-01', periods=2)
        data = pd.DataFrame({
            'Open': [100.0, 101.0],
            'High': [105.0, 106.0],
            'Low': [95.0, 96.0],
            'Close': [102.0, 103.0],
            'Volume': [1000000, 1100000],
        }, index=dates)
        data.index.name = 'Date'

        mock_get_data.return_value = data

        result = get_raw_data_json("AAPL", "2024-01-01", "2024-01-02")

        assert len(result) == 2
        assert result[0]["time"] == "2024-01-01"

    @patch('src.db.storage.market_data.get_data')
    def test_get_raw_data_json_skips_invalid_dates(self, mock_get_data):
        """Test that rows with invalid dates are skipped."""
        data = pd.DataFrame({
            'Date': [pd.NaT, pd.Timestamp('2024-01-01')],
            'Open': [100.0, 101.0],
            'High': [105.0, 106.0],
            'Low': [95.0, 96.0],
            'Close': [102.0, 103.0],
            'Volume': [1000000, 1100000],
        })

        mock_get_data.return_value = data

        result = get_raw_data_json("AAPL", "2024-01-01", "2024-01-02")

        # Should only have 1 valid record
        assert len(result) == 1
        assert result[0]["time"] == "2024-01-01"

    @patch('src.db.storage.market_data.get_data')
    def test_get_raw_data_json_exception_returns_empty(self, mock_get_data):
        """Test exception handling returns empty list."""
        mock_get_data.side_effect = Exception("Data fetch failed")

        result = get_raw_data_json("AAPL", "2024-01-01", "2024-01-05")

        assert result == []

    @patch('src.db.storage.market_data.get_data')
    def test_get_raw_data_json_handles_null_volume(self, mock_get_data):
        """Test handling of null volume values."""
        dates = pd.date_range('2024-01-01', periods=1)
        data = pd.DataFrame({
            'Open': [100.0],
            'High': [105.0],
            'Low': [95.0],
            'Close': [102.0],
            'Volume': [None],  # Null volume
        }, index=dates)
        data.index.name = 'Date'

        mock_get_data.return_value = data

        result = get_raw_data_json("AAPL", "2024-01-01", "2024-01-01")

        assert len(result) == 1
        assert result[0]["volume"] == 0  # Should convert null to 0
