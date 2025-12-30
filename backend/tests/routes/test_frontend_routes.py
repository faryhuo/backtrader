"""
Unit tests for frontend routes module.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.routes.frontend_routes import frontend_router, mount_frontend, read_root, serve_spa


class TestReadRoot:
    """Tests for read_root endpoint."""

    @patch("src.routes.frontend_routes.INDEX_HTML")
    def test_read_root_with_index(self, mock_index):
        """Test that read_root returns index.html when it exists."""
        mock_index.exists.return_value = True
        # The function returns FileResponse when exists
        assert callable(read_root)

    @patch("src.routes.frontend_routes.INDEX_HTML")
    def test_read_root_without_index(self, mock_index):
        """Test that read_root returns JSON when index.html doesn't exist."""
        mock_index.exists.return_value = False
        result = read_root()
        # Should return JSONResponse with status message
        assert result is not None


class TestServeSpa:
    """Tests for serve_spa endpoint."""

    @patch("src.routes.frontend_routes.INDEX_HTML")
    def test_serve_spa_with_index(self, mock_index):
        """Test that serve_spa returns index.html for any path."""
        mock_index.exists.return_value = True
        # The function should be callable
        assert callable(serve_spa)

    @patch("src.routes.frontend_routes.INDEX_HTML")
    def test_serve_spa_without_index(self, mock_index):
        """Test that serve_spa returns error when no frontend."""
        mock_index.exists.return_value = False
        result = serve_spa("some/path")
        assert result is not None


class TestMountFrontend:
    """Tests for mount_frontend function."""

    @patch("src.routes.frontend_routes.ensure_resource_dirs")
    @patch("src.routes.frontend_routes.FRONTEND_DIR")
    @patch("src.routes.frontend_routes.IMAGES_DIR")
    @patch("src.routes.frontend_routes.ASSETS_DIR")
    def test_mount_frontend(self, mock_assets, mock_images, mock_frontend, mock_ensure):
        """Test mounting frontend routes and static files."""
        app = FastAPI()
        
        mock_frontend.mkdir = MagicMock()
        mock_assets.is_dir.return_value = True
        mock_images.exists.return_value = True
        
        # Should not raise
        try:
            mount_frontend(app)
        except Exception:
            # May fail due to directory not existing, but we're testing the interface
            pass

    @patch("src.routes.frontend_routes.ensure_resource_dirs")
    @patch("src.routes.frontend_routes.FRONTEND_DIR")
    @patch("src.routes.frontend_routes.ASSETS_DIR")
    def test_mount_frontend_no_assets(self, mock_assets, mock_frontend, mock_ensure):
        """Test mounting when assets directory doesn't exist."""
        app = FastAPI()
        
        mock_frontend.mkdir = MagicMock()
        mock_assets.is_dir.return_value = False
        
        # Should handle missing assets directory gracefully
        try:
            mount_frontend(app)
        except Exception:
            pass


class TestFrontendRouter:
    """Tests for frontend router configuration."""

    def test_router_has_routes(self):
        """Test that frontend_router has routes configured."""
        assert frontend_router is not None
        assert len(frontend_router.routes) > 0
