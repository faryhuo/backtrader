"""
Unit tests for walkforward routes module.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestWalkforwardRouterImports:
    """Tests for walkforward routes module imports."""

    def test_router_import(self):
        """Test that walkforward router can be imported."""
        from src.routes.walkforward_routes import router
        assert router is not None

    def test_router_has_routes(self):
        """Test that router has routes configured."""
        from src.routes.walkforward_routes import router
        assert len(router.routes) > 0


class TestWalkforwardRouterEndpoints:
    """Tests for walkforward router endpoint existence."""

    def test_has_run_endpoint(self):
        """Test that run/optimize endpoint exists."""
        from src.routes.walkforward_routes import router
        route_methods = []
        for route in router.routes:
            if hasattr(route, 'methods'):
                route_methods.extend(route.methods)
        # Should have POST for running walkforward
        assert 'POST' in route_methods

    def test_has_history_endpoint(self):
        """Test that history endpoint exists."""
        from src.routes.walkforward_routes import router
        route_methods = []
        for route in router.routes:
            if hasattr(route, 'methods'):
                route_methods.extend(route.methods)
        # Should have GET for listing history
        assert 'GET' in route_methods
