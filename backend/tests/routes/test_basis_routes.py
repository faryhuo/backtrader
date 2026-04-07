"""Unit tests for standalone basis trading routes."""

import asyncio
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.routes.basis_routes import BasisCloseRequest, BasisOpenRequest, BasisPreviewRequest, router


class TestBasisPreviewRequest:
    def test_valid_preview_request(self):
        request = BasisPreviewRequest(
            exchange="okx",
            symbol="ETH/USDT",
            capital=10000,
            spot_ratio=50,
            funding_rate=0.0002,
        )
        assert request.exchange == "okx"
        assert request.cycles_per_month == 4

    def test_invalid_exchange(self):
        with pytest.raises(ValidationError):
            BasisPreviewRequest(
                exchange="kraken",
                symbol="ETH/USDT",
                capital=10000,
                spot_ratio=50,
                funding_rate=0.0002,
            )


class TestBasisOpenRequest:
    def test_valid_open_request(self):
        request = BasisOpenRequest(
            exchange="binance",
            mode="paper",
            symbol="BTC/USDT",
            capital=20000,
            spot_ratio=55,
        )
        assert request.mode == "paper"
        assert request.leverage == 1

    def test_invalid_mode(self):
        with pytest.raises(ValidationError):
            BasisOpenRequest(
                exchange="binance",
                mode="demo",
                symbol="BTC/USDT",
                capital=20000,
                spot_ratio=55,
            )


class TestBasisCloseRequest:
    def test_valid_close_request(self):
        request = BasisCloseRequest(
            exchange="okx",
            mode="live",
            symbol="ETH/USDT",
            quantity=1.2,
            confirm_live=True,
        )
        assert request.exchange == "okx"
        assert request.confirm_live is True


class TestBasisRouter:
    def test_router_has_basis_endpoints(self):
        paths = [route.path for route in router.routes if hasattr(route, "path")]
        assert "/basis/preview" in paths
        assert "/basis/precheck" in paths
        assert "/basis/trade/open" in paths
        assert "/basis/trade/close" in paths
        assert "/basis/trade/state" in paths

    def test_open_route_delegates_to_service(self):
        payload = BasisOpenRequest(
            exchange="okx",
            mode="paper",
            symbol="ETH/USDT",
            capital=10000,
            spot_ratio=50,
        )
        with patch("src.routes.basis_routes.open_basis_trade", return_value={"status": "ok"}) as mocked:
            from src.routes.basis_routes import open_basis_trade_route

            result = asyncio.run(open_basis_trade_route(payload, user_id="u1"))
            assert result == {"status": "ok"}
            mocked.assert_called_once()
