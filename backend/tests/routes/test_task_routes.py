"""
Unit tests for task routes module.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestTaskRouterImports:
    """Tests for task routes module imports."""

    def test_router_import(self):
        """Test that task router can be imported."""
        from src.routes.task_routes import router
        assert router is not None

    def test_router_has_routes(self):
        """Test that router has routes configured."""
        from src.routes.task_routes import router
        assert len(router.routes) > 0


class TestTaskRouterEndpoints:
    """Tests for task router endpoint existence."""

    def test_has_list_endpoint(self):
        """Test that list tasks endpoint exists."""
        from src.routes.task_routes import router
        route_methods = []
        for route in router.routes:
            if hasattr(route, 'methods'):
                route_methods.extend(route.methods)
        assert 'GET' in route_methods

    def test_has_status_endpoint(self):
        """Test that task status endpoint exists."""
        from src.routes.task_routes import router
        route_paths = [route.path for route in router.routes if hasattr(route, 'path')]
        # Should have something like /{task_id} or /status/{task_id}
        assert any("{task_id}" in p for p in route_paths) or any("task" in p for p in route_paths)

    def test_has_cancel_endpoint(self):
        """Test that cancel task endpoint exists or delete endpoint."""
        from src.routes.task_routes import router
        route_methods = []
        for route in router.routes:
            if hasattr(route, 'methods'):
                route_methods.extend(route.methods)
        # Should have POST for cancel or DELETE for delete
        assert 'POST' in route_methods or 'DELETE' in route_methods
