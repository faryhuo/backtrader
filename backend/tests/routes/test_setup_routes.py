"""Unit tests for setup wizard routes."""

from unittest.mock import patch

import pytest

from src.routes.setup_routes import (
    _require_setup_write_access,
    get_setup_wizard,
    router,
)


class TestSetupRouter:
    def test_router_exists(self):
        assert router is not None
        assert len(router.routes) > 0

    @patch("src.routes.setup_routes.SetupWizardService")
    def test_get_setup_wizard_allows_anonymous_when_ready_and_login_required(self, mock_service_cls):
        mock_service_cls.return_value.get_wizard_state.return_value = {
            "status": {"is_ready": True, "setup_completed": True, "requires_login": True},
            "meta": {"has_system_users": True},
        }

        response = get_setup_wizard()

        assert response["status"]["is_ready"] is True
        mock_service_cls.return_value.get_wizard_state.assert_called_once()

    @patch("src.routes.setup_routes.SetupWizardService")
    def test_save_setup_wizard_requires_authenticated_user_when_ready_and_login_required(self, mock_service_cls):
        mock_service_cls.return_value.get_wizard_state.return_value = {
            "status": {"is_ready": True, "setup_completed": True, "requires_login": True},
            "meta": {"has_system_users": True},
        }

        with pytest.raises(Exception) as excinfo:
            _require_setup_write_access(user=None)

        assert excinfo.value.status_code == 401

    @patch("src.routes.setup_routes.SetupWizardService")
    def test_save_setup_wizard_allows_anonymous_bootstrap_when_no_system_users(self, mock_service_cls):
        mock_service_cls.return_value.get_wizard_state.return_value = {
            "status": {"is_ready": False, "setup_completed": False, "requires_login": True},
            "meta": {"has_system_users": False},
        }

        assert _require_setup_write_access(user=None) is None
