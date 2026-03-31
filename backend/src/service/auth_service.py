"""Built-in email/password authentication service."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt

from src.db.storage.settings import SettingsStorage
from src.db.storage.user_auth import UserAuthStorage


class AuthServiceError(Exception):
    """Base error for built-in auth service."""


class InvalidCredentialsError(AuthServiceError):
    """Raised when email/password validation fails."""


class RegistrationDisabledError(AuthServiceError):
    """Raised when public registration is not allowed."""


class UserAlreadyExistsError(AuthServiceError):
    """Raised when the target email already exists."""


class UnsupportedAuthProviderError(AuthServiceError):
    """Raised when built-in auth is disabled by configuration."""


@dataclass(slots=True)
class AuthTokens:
    """JWT payload returned to the frontend."""

    access_token: str
    token_type: str
    expires_in: int
    user: dict[str, Any]


class AuthService:
    """Service for built-in system authentication."""

    def __init__(
        self,
        user_storage: UserAuthStorage | None = None,
        settings_storage: SettingsStorage | None = None,
    ) -> None:
        self.user_storage = user_storage or UserAuthStorage()
        self.settings_storage = settings_storage or SettingsStorage()

    def get_auth_config(self) -> dict[str, Any]:
        provider, _ = self.settings_storage.get_credential_with_fallback("auth_provider", None)
        enable_login, _ = self.settings_storage.get_credential_with_fallback("enable_login", None)
        allow_registration, _ = self.settings_storage.get_credential_with_fallback(
            "system_auth_allow_registration",
            None,
        )

        normalized_provider = (provider or "").strip().lower() or ("logto" if enable_login else "none")
        login_enabled = bool(enable_login) if enable_login is not None else normalized_provider != "none"
        if not login_enabled:
            normalized_provider = "none"

        if allow_registration is None:
            allow_registration = self.user_storage.count_users() == 0

        return {
            "enable_login": login_enabled,
            "auth_provider": normalized_provider,
            "registration_enabled": bool(allow_registration),
        }

    def ensure_system_auth_enabled(self) -> dict[str, Any]:
        config = self.get_auth_config()
        if not config["enable_login"] or config["auth_provider"] != "system":
            raise UnsupportedAuthProviderError("System authentication is not enabled")
        return config

    def register_user(
        self,
        email: str,
        password: str,
        display_name: str | None = None,
    ) -> AuthTokens:
        config = self.ensure_system_auth_enabled()
        normalized_email = self._normalize_email(email)
        if self.user_storage.get_by_email(normalized_email):
            raise UserAlreadyExistsError("Email already exists")

        existing_users = self.user_storage.count_users()
        if existing_users > 0 and not config["registration_enabled"]:
            raise RegistrationDisabledError("Registration is disabled")

        password_hash = self._hash_password(password)
        user = self.user_storage.create_user(
            normalized_email,
            password_hash=password_hash,
            display_name=display_name,
            is_superuser=existing_users == 0,
        )
        self.user_storage.update_last_login(user.id)
        return self._issue_tokens(user)

    def login_user(self, email: str, password: str) -> AuthTokens:
        self.ensure_system_auth_enabled()
        normalized_email = self._normalize_email(email)
        user = self.user_storage.get_by_email(normalized_email)
        if user is None or not user.is_active:
            raise InvalidCredentialsError("Invalid email or password")
        if not self._verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
        self.user_storage.update_last_login(user.id)
        refreshed_user = self.user_storage.get_by_id(user.id) or user
        return self._issue_tokens(refreshed_user)

    def get_current_user(self, user_id: int) -> dict[str, Any] | None:
        user = self.user_storage.get_by_id(user_id)
        if user is None or not user.is_active:
            return None
        return self._serialize_user(user)

    def list_users(self) -> list[dict[str, Any]]:
        return [self._serialize_user(user) for user in self.user_storage.list_users()]

    def create_user(
        self,
        email: str,
        password: str,
        display_name: str | None = None,
        is_superuser: bool = False,
    ) -> dict[str, Any]:
        normalized_email = self._normalize_email(email)
        if self.user_storage.get_by_email(normalized_email):
            raise UserAlreadyExistsError("Email already exists")
        user = self.user_storage.create_user(
            normalized_email,
            password_hash=self._hash_password(password),
            display_name=display_name,
            is_superuser=is_superuser,
        )
        return self._serialize_user(user)

    def set_user_active(self, user_id: int, is_active: bool) -> dict[str, Any] | None:
        user = self.user_storage.set_active(user_id, is_active)
        return self._serialize_user(user) if user else None

    def reset_password(self, user_id: int, password: str) -> dict[str, Any] | None:
        user = self.user_storage.update_password_hash(user_id, self._hash_password(password))
        return self._serialize_user(user) if user else None

    def decode_access_token(self, token: str) -> dict[str, Any]:
        secret = self._get_jwt_secret()
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer="backtrader-system-auth",
            audience="backtrader-api",
        )

    def _normalize_email(self, email: str) -> str:
        normalized = (email or "").strip().lower()
        if not normalized:
            raise InvalidCredentialsError("Email is required")
        return normalized

    def _hash_password(self, password: str) -> str:
        if len(password or "") < 8:
            raise InvalidCredentialsError("Password must be at least 8 characters")
        salt = secrets.token_bytes(16)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
        return f"pbkdf2_sha256$120000${base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        try:
            algorithm, iterations, salt_b64, hash_b64 = password_hash.split("$", 3)
        except ValueError:
            return False
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(hash_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)

    def _issue_tokens(self, user) -> AuthTokens:
        now = datetime.now(timezone.utc)
        expires_in = int(os.getenv("SYSTEM_AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", "480")) * 60
        payload = {
            "sub": f"system:{user.id}",
            "aud": "backtrader-api",
            "iss": "backtrader-system-auth",
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
            "auth_provider": "system",
            "user_id": user.id,
            "email": user.email,
            "name": user.display_name or user.email,
            "is_superuser": bool(user.is_superuser),
        }
        token = jwt.encode(payload, self._get_jwt_secret(), algorithm="HS256")
        return AuthTokens(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
            user=self._serialize_user(user),
        )

    def _serialize_user(self, user) -> dict[str, Any]:
        return {
            "id": user.id,
            "sub": f"system:{user.id}",
            "email": user.email,
            "name": user.display_name or user.email,
            "auth_provider": "system",
            "is_superuser": bool(user.is_superuser),
            "is_active": bool(user.is_active),
        }

    def _get_jwt_secret(self) -> str:
        secret = os.getenv("SYSTEM_AUTH_SECRET") or os.getenv("ENCRYPTION_KEY")
        if secret:
            return secret
        raise UnsupportedAuthProviderError("SYSTEM_AUTH_SECRET or ENCRYPTION_KEY must be configured")
