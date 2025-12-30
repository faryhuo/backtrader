"""
Unit tests for site config routes module.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestSiteConfigRouterImports:
    """Tests for site config routes module imports."""

    def test_router_import(self):
        """Test that site config router can be imported."""
        from src.routes.site_config_routes import router
        assert router is not None

    def test_router_has_routes(self):
        """Test that router has routes configured."""
        from src.routes.site_config_routes import router
        assert len(router.routes) > 0


class TestSiteConfigRouterEndpoints:
    """Tests for site config router endpoint existence."""

    def test_has_get_config_endpoint(self):
        """Test that get config endpoint exists."""
        from src.routes.site_config_routes import router
        route_methods = []
        for route in router.routes:
            if hasattr(route, 'methods'):
                route_methods.extend(route.methods)
        assert 'GET' in route_methods
