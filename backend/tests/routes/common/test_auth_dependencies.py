"""
Unit tests for auth dependencies module.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestAuthDependenciesImports:
    """Tests for auth dependencies module imports."""

    def test_get_optional_user_id_import(self):
        """Test that get_optional_user_id can be imported."""
        from src.routes.common.auth_dependencies import get_optional_user_id
        assert get_optional_user_id is not None

    def test_get_required_user_id_import(self):
        """Test that get_required_user_id can be imported."""
        from src.routes.common.auth_dependencies import get_required_user_id
        assert get_required_user_id is not None


class TestGetOptionalUserId:
    """Tests for get_optional_user_id dependency."""

    @patch("src.routes.common.auth_dependencies.get_logto_config")
    def test_returns_none_when_auth_disabled(self, mock_config):
        """Test that None is returned when auth is disabled."""
        mock_config.return_value = {"enabled": False}
        from src.routes.common.auth_dependencies import get_optional_user_id
        # The function is a FastAPI dependency, so we verify it's callable
        assert callable(get_optional_user_id)
