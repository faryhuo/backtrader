import pandas as pd
import pytest

from src.db.storage import market_data
from src.db.storage import ticker_metadata


def test_validate_ticker_info():
    ok, err = ticker_metadata._validate_ticker_info({})
    assert ok is False
    assert "No data" in err

    ok, err = ticker_metadata._validate_ticker_info({"longName": "X"})
    assert ok is False
    assert "No price" in err

    ok, err = ticker_metadata._validate_ticker_info({"symbol": "AAPL", "currentPrice": 1})
    assert ok is True
    assert err is None


def test_parse_ticker_info():
    info = {"longName": "Apple", "regularMarketPrice": 123.0, "exchange": "NMS", "currency": "USD"}
    parsed = ticker_metadata._parse_ticker_info("aapl", info, True, None)
    assert parsed["ticker"] == "AAPL"
    assert parsed["is_valid"] is True
    assert parsed["current_price"] == 123.0
    assert parsed["additional_info"]["currency"] == "USD"


def test_get_raw_data_json_formats_dataframe(monkeypatch):
    df = pd.DataFrame(
        {
            "Open": [1.0],
            "High": [2.0],
            "Low": [0.5],
            "Close": [1.5],
            "Volume": [10],
        },
        index=pd.to_datetime(["2024-01-01"]),
    )
    df.index.name = "Date"

    monkeypatch.setattr(market_data, "get_data", lambda *args, **kwargs: df)
    result = market_data.get_raw_data_json("AAPL", "2024-01-01", "2024-01-02")
    assert result == [
        {"time": "2024-01-01", "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 10}
    ]


def test_get_data_raises_when_no_data(monkeypatch):
    import yfinance as yf
    monkeypatch.setattr(yf, "download", lambda *args, **kwargs: pd.DataFrame())
    monkeypatch.setattr(market_data, "get_data_from_db", lambda *args, **kwargs: None)

    with pytest.raises(market_data.DataLoadError):
        market_data.get_data("AAPL", "2024-01-01", "2024-01-02")
