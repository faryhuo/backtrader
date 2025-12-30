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
        assert callable(get_optional_user_id)

    def test_get_user_id_import(self):
        """Test that get_user_id can be imported."""
        from src.routes.common.auth_dependencies import get_user_id
        assert get_user_id is not None
        assert callable(get_user_id)


class TestGetOptionalUserId:
    """Tests for get_optional_user_id dependency."""

    def test_returns_none_when_user_none(self):
        """Test that None is returned when user is None."""
        from src.routes.common.auth_dependencies import get_optional_user_id
        result = get_optional_user_id(None)
        assert result is None

    def test_returns_sub_when_user_present(self):
        """Test that sub is returned when user is present."""
        from src.routes.common.auth_dependencies import get_optional_user_id
        user = {"sub": "user123", "email": "test@example.com"}
        result = get_optional_user_id(user)
        assert result == "user123"


class TestGetUserId:
    """Tests for get_user_id dependency."""

    def test_returns_sub_from_user(self):
        """Test that sub is returned from user dict."""
        from src.routes.common.auth_dependencies import get_user_id
        user = {"sub": "user456", "email": "test@example.com"}
        result = get_user_id(user)
        assert result == "user456"
