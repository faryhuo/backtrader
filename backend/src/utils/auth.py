"""
Token-based authentication helpers.

The backend no longer relies on the Logto SDK config; instead it validates
incoming Bearer tokens via Logto's JWKS endpoint using python-jose.

Authentication configuration is loaded from database first, then falls back
to environment variables for backward compatibility.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Optional

import requests
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError

from src.config.config_manager import get_global_config_manager

security = HTTPBearer(auto_error=False)
optional_security = HTTPBearer(auto_error=False)


class AuthError(HTTPException):
    """Standardized authentication error compatible with FastAPI."""

    def __init__(self, code: str, status_code: int = 401, message: Optional[str] = None):
        detail: Dict[str, Any] = {"code": code}
        if message:
            detail["message"] = message
        super().__init__(status_code=status_code, detail=detail)


def get_auth_token(credentials: Optional[HTTPAuthorizationCredentials]) -> str:
    """
    Extract and validate the Authorization header.
    """
    if not credentials:
        raise AuthError("auth.authorization_header_missing")

    if credentials.scheme.lower() != "bearer":
        raise AuthError("auth.authorization_token_type_not_supported")

    token = credentials.credentials
    if not token:
        raise AuthError("auth.authorization_token_invalid_format")

    return token


def get_logto_config() -> Dict[str, Any]:
    """
    Get Logto configuration from database or environment variables.
    """
    config_manager = get_global_config_manager()
    return config_manager.get_logto_config()


@lru_cache(maxsize=1)
def fetch_jwks() -> Dict[str, Any]:
    """
    Download JWKS metadata from Logto. Cached for efficiency.
    Configuration loaded from database first, then .env as fallback.
    """
    config = get_logto_config()
    proxy_config = get_global_config_manager().get_proxy_config()

    jwks_uri = config.get("jwks_uri")
    if not jwks_uri:
        raise HTTPException(status_code=500, detail="LOGTO_JWKS_URI not configured")

    proxies = {
        key: value
        for key, value in {
            "http": proxy_config.get("http_proxy"),
            "https": proxy_config.get("https_proxy")
        }.items()
        if value
    }
    try:
        response = requests.get(jwks_uri, timeout=10, proxies=proxies or None)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=500, detail=f"Unable to fetch JWKS: {exc}") from exc

    return response.json()


def get_signing_key(token: str) -> Dict[str, Any]:
    """
    Find the signing key in the JWKS that matches the JWT header.
    """
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise AuthError("auth.invalid_token_header", message=str(exc)) from exc

    kid = header.get("kid")
    if not kid:
        raise AuthError("auth.invalid_token", message="Missing key identifier (kid)")

    jwks = fetch_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    # JWKS may have rotated; invalidate the cache and retry once.
    fetch_jwks.cache_clear()
    jwks = fetch_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise AuthError("auth.invalid_token", message="Signing key not found")


def validate_scopes(claims: Dict[str, Any]) -> None:
    """
    Ensure the JWT contains the required scopes if configured.
    """
    config = get_logto_config()
    required_scopes_str = config.get("required_scopes", "")
    if not required_scopes_str:
        return

    required_scopes = required_scopes_str.split()
    token_scopes = set(str(claims.get("scope", "")).split())
    missing = [scope for scope in required_scopes if scope not in token_scopes]
    if missing:
        raise AuthError(
            "auth.insufficient_scope",
            status_code=403,
            message=f"Missing scopes: {', '.join(missing)}",
        )


def verify_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate the JWT using python-jose.
    """
    config = get_logto_config()
    key = get_signing_key(token)
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg")
    if not algorithm:
        raise AuthError("auth.invalid_token", message="Missing signing algorithm")

    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=[algorithm],
            audience=config.get("audience"),
            issuer=config.get("issuer"),
            options={"verify_at_hash": False},
        )
        validate_scopes(claims)
        return claims
    except ExpiredSignatureError as exc:
        raise AuthError("auth.token_expired", message="Token has expired") from exc
    except JWTClaimsError as exc:
        raise AuthError("auth.invalid_claims", message=str(exc)) from exc
    except JWTError as exc:
        raise AuthError("auth.invalid_token", message=str(exc)) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    FastAPI dependency to require authentication on an endpoint.
    """
    config = get_logto_config()
    if not config.get("enable_login"):
        # Authentication disabled; allow anonymous access.
        return {"sub": "anonymous"}

    token = get_auth_token(credentials)
    return verify_token(token)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication dependency.
    """
    config = get_logto_config()
    if not config.get("enable_login"):
        return {"sub": "anonymous"}

    if not credentials:
        return None

    try:
        token = get_auth_token(credentials)
        return verify_token(token)
    except HTTPException:
        return None


def require_user(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Dependency helper mirroring the previous interface.
    """
    return user
