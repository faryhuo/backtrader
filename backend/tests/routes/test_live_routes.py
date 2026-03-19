"""
Unit tests for live trading routes module.
"""
import pytest

from src.routes.live_routes import (
    router,
    StartLiveRequest,
    StopLiveRequest,
    SessionResponse,
    ExchangeInfo,
)


class TestStartLiveRequest:
    """Tests for StartLiveRequest Pydantic model."""

    def test_valid_request(self):
        """Test creating valid StartLiveRequest (Binance Spot only, no exchange field)."""
        request = StartLiveRequest(
            strategy_name="sma_cross",
            symbol="BTC/USDT",
            mode="paper",
        )
        assert request.strategy_name == "sma_cross"
        assert request.symbol == "BTC/USDT"
        assert request.mode == "paper"

    def test_default_values(self):
        """Test default values in StartLiveRequest."""
        request = StartLiveRequest(
            strategy_name="test",
            symbol="BTC/USDT",
        )
        assert request.mode == "paper"
        assert request.timeframe == "1m"
        assert request.initial_cash == pytest.approx(10000.0)
        assert request.commission == pytest.approx(0.001)

    def test_custom_values(self):
        """Test custom values in StartLiveRequest."""
        request = StartLiveRequest(
            strategy_name="test",
            symbol="ETH/USDT",
            mode="live",
            timeframe="1s",
            initial_cash=50000.0,
            commission=0.0005,
        )
        assert request.timeframe == "1s"
        assert request.initial_cash == pytest.approx(50000.0)
        assert request.commission == pytest.approx(0.0005)

    def test_no_exchange_field(self):
        """StartLiveRequest should not have an exchange field (Binance-only)."""
        assert not hasattr(StartLiveRequest.model_fields, "exchange")


class TestStopLiveRequest:
    """Tests for StopLiveRequest Pydantic model."""

    def test_valid_request(self):
        """Test creating valid StopLiveRequest."""
        request = StopLiveRequest(session_id="test-session-123")
        assert request.session_id == "test-session-123"


class TestSessionResponse:
    """Tests for SessionResponse Pydantic model."""

    def test_session_response(self):
        """Test creating SessionResponse."""
        response = SessionResponse(
            session_id="test-123",
            status="running",
            strategy_name="sma_cross",
            symbol="BTC/USDT",
            exchange="binance",
            mode="paper",
            timeframe="1m",
            start_time="2024-01-01T00:00:00Z",
            initial_cash=10000.0,
            current_pnl=150.0,
            total_trades=5,
        )
        assert response.session_id == "test-123"
        assert response.status == "running"
        assert response.current_pnl == pytest.approx(150.0)

    def test_session_response_defaults(self):
        """Test SessionResponse default values."""
        response = SessionResponse(
            session_id="test-123",
            status="running",
            strategy_name="test",
            symbol="BTC/USDT",
            exchange="binance",
            mode="paper",
            timeframe="1m",
            start_time="2024-01-01T00:00:00Z",
            initial_cash=10000.0,
        )
        assert response.end_time is None
        assert response.positions == []
        assert response.open_orders == []
        assert response.error_message is None


class TestExchangeInfo:
    """Tests for ExchangeInfo Pydantic model."""

    def test_exchange_info(self):
        """Test creating ExchangeInfo."""
        info = ExchangeInfo(
            id="binance",
            name="Binance",
            markets=["spot"],
            default_market="spot",
            paper_mode_available=True,
        )
        assert info.id == "binance"
        assert info.adapter == "ccxt"
        assert info.paper_mode_available is True

    def test_exchange_info_with_ccxt_id(self):
        """Test ExchangeInfo with custom ccxt_id."""
        info = ExchangeInfo(
            id="binance",
            name="Binance",
            adapter="ccxt",
            ccxt_id="binance",
            markets=["spot"],
            default_market="spot",
            paper_mode_available=True,
        )
        assert info.ccxt_id == "binance"


class TestLiveRouter:
    """Tests for live trading router."""

    def test_router_exists(self):
        """Test that router is configured."""
        assert router is not None
        assert len(router.routes) > 0

    def test_router_has_start_endpoint(self):
        """Test that router has start trading endpoint."""
        route_paths = [route.path for route in router.routes if hasattr(route, 'path')]
        assert any("/start" in p for p in route_paths)

    def test_router_has_stop_endpoint(self):
        """Test that router has stop trading endpoint."""
        route_paths = [route.path for route in router.routes if hasattr(route, 'path')]
        assert any("/stop" in p for p in route_paths)

    def test_router_has_cancel_endpoint(self):
        """Test that router has cancel order endpoint."""
        route_paths = [route.path for route in router.routes if hasattr(route, 'path')]
        assert any("cancel" in p for p in route_paths)

    def test_router_has_ticker_endpoint(self):
        """Test that router has ticker price endpoint."""
        route_paths = [route.path for route in router.routes if hasattr(route, 'path')]
        assert any("ticker" in p for p in route_paths)
