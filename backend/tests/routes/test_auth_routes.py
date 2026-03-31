"""Unit tests for auth routes."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.routes.auth_routes import (
    SystemLoginRequest,
    SystemRegisterRequest,
    SystemUserCreateRequest,
    SystemUserPasswordResetRequest,
    create_system_user,
    get_auth_public_config,
    get_current_authenticated_user,
    list_system_users,
    login_system_user,
    register_system_user,
    reset_system_user_password,
    set_system_user_active,
)
from src.service.auth_service import (
    InvalidCredentialsError,
    RegistrationDisabledError,
    UnsupportedAuthProviderError,
    UserAlreadyExistsError,
)


class TestAuthRequests:
    def test_login_request(self):
        request = SystemLoginRequest(email="user@example.com", password="password123")
        assert request.email == "user@example.com"

    def test_register_request(self):
        request = SystemRegisterRequest(
            email="user@example.com",
            password="password123",
            display_name="User",
        )
        assert request.display_name == "User"


@patch("src.routes.auth_routes.AuthService")
def test_get_auth_public_config(mock_service_cls):
    mock_service_cls.return_value.get_auth_config.return_value = {
        "enable_login": True,
        "auth_provider": "system",
        "registration_enabled": True,
    }

    response = get_auth_public_config()

    assert response["status"] == "ok"
    assert response["config"]["auth_provider"] == "system"


@patch("src.routes.auth_routes.AuthService")
def test_login_system_user_success(mock_service_cls):
    mock_service_cls.return_value.login_user.return_value = SimpleNamespace(
        access_token="token",
        token_type="bearer",
        expires_in=3600,
        user={"email": "user@example.com"},
    )

    response = login_system_user(SystemLoginRequest(email="user@example.com", password="password123"))

    assert response["status"] == "ok"
    assert response["access_token"] == "token"


@patch("src.routes.auth_routes.AuthService")
def test_login_system_user_invalid_credentials(mock_service_cls):
    mock_service_cls.return_value.login_user.side_effect = InvalidCredentialsError("Invalid email or password")

    with pytest.raises(Exception) as excinfo:
        login_system_user(SystemLoginRequest(email="user@example.com", password="password123"))

    assert excinfo.value.status_code == 401


@patch("src.routes.auth_routes.AuthService")
def test_register_system_user_success(mock_service_cls):
    mock_service_cls.return_value.register_user.return_value = SimpleNamespace(
        access_token="token",
        token_type="bearer",
        expires_in=3600,
        user={"email": "user@example.com"},
    )

    response = register_system_user(
        SystemRegisterRequest(
            email="user@example.com",
            password="password123",
            display_name="User",
        )
    )

    assert response["status"] == "ok"
    assert response["user"]["email"] == "user@example.com"


@patch("src.routes.auth_routes.AuthService")
def test_register_system_user_conflict(mock_service_cls):
    mock_service_cls.return_value.register_user.side_effect = UserAlreadyExistsError("Email already exists")

    with pytest.raises(Exception) as excinfo:
        register_system_user(
            SystemRegisterRequest(
                email="user@example.com",
                password="password123",
                display_name="User",
            )
        )

    assert excinfo.value.status_code == 409


@patch("src.routes.auth_routes.AuthService")
def test_register_system_user_disabled(mock_service_cls):
    mock_service_cls.return_value.register_user.side_effect = RegistrationDisabledError("Registration is disabled")

    with pytest.raises(Exception) as excinfo:
        register_system_user(
            SystemRegisterRequest(
                email="user@example.com",
                password="password123",
            )
        )

    assert excinfo.value.status_code == 403


@patch("src.routes.auth_routes.AuthService")
def test_register_system_user_unsupported_provider(mock_service_cls):
    mock_service_cls.return_value.register_user.side_effect = UnsupportedAuthProviderError("System authentication is not enabled")

    with pytest.raises(Exception) as excinfo:
        register_system_user(
            SystemRegisterRequest(
                email="user@example.com",
                password="password123",
            )
        )

    assert excinfo.value.status_code == 400


def test_get_current_authenticated_user():
    user = {"sub": "system:1", "email": "user@example.com"}
    response = get_current_authenticated_user(user=user)
    assert response == {"status": "ok", "user": user}


@patch("src.routes.auth_routes.AuthService")
def test_list_system_users(mock_service_cls):
    mock_service_cls.return_value.list_users.return_value = [{"id": 1, "email": "admin@example.com"}]

    response = list_system_users(_={"id": 1, "auth_provider": "system", "is_superuser": True})

    assert response == {"status": "ok", "users": [{"id": 1, "email": "admin@example.com"}]}


@patch("src.routes.auth_routes.AuthService")
def test_create_system_user_success(mock_service_cls):
    mock_service_cls.return_value.create_user.return_value = {"id": 2, "email": "user@example.com"}

    response = create_system_user(
        SystemUserCreateRequest(
            email="user@example.com",
            password="password123",
            display_name="User",
            is_superuser=False,
        ),
        _={"id": 1, "auth_provider": "system", "is_superuser": True},
    )

    assert response == {"status": "ok", "user": {"id": 2, "email": "user@example.com"}}


@patch("src.routes.auth_routes.AuthService")
def test_set_system_user_active_success(mock_service_cls):
    mock_service_cls.return_value.set_user_active.return_value = {"id": 2, "email": "user@example.com", "is_active": False}

    response = set_system_user_active(
        2,
        False,
        admin_user={"id": 1, "auth_provider": "system", "is_superuser": True},
    )

    assert response == {"status": "ok", "user": {"id": 2, "email": "user@example.com", "is_active": False}}


def test_set_system_user_active_rejects_self_deactivate():
    with pytest.raises(Exception) as excinfo:
        set_system_user_active(
            1,
            False,
            admin_user={"id": 1, "auth_provider": "system", "is_superuser": True},
        )

    assert excinfo.value.status_code == 400


@patch("src.routes.auth_routes.AuthService")
def test_reset_system_user_password_success(mock_service_cls):
    mock_service_cls.return_value.reset_password.return_value = {"id": 2, "email": "user@example.com"}

    response = reset_system_user_password(
        2,
        SystemUserPasswordResetRequest(password="newpassword123"),
        _={"id": 1, "auth_provider": "system", "is_superuser": True},
    )

    assert response == {"status": "ok", "user": {"id": 2, "email": "user@example.com"}}
