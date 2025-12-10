"""
Logto Authentication Module

This module provides both user authentication and M2M authentication:
- User authentication: Validates JWT tokens from frontend users
- M2M authentication: Obtains tokens for backend-to-backend API calls
"""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from functools import lru_cache
import time

import requests
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Security schemes for Bearer token
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


class LogtoConfig:
    """Unified Logto configuration for both user auth and M2M"""

    def __init__(self):
        self.endpoint = os.getenv("LOGTO_ENDPOINT")

        # User authentication (SPA)
        self.spa_app_id = os.getenv("LOGTO_SPA_APP_ID")

        # M2M authentication
        self.m2m_app_id = os.getenv("LOGTO_M2M_APP_ID")
        self.m2m_app_secret = os.getenv("LOGTO_M2M_APP_SECRET")

        # API resource
        self.api_resource = os.getenv("LOGTO_API_RESOURCE", "http://localhost:8000")

        # Validate required configuration for user auth
        if not all([self.endpoint, self.spa_app_id]):
            raise ValueError(
                "Missing required Logto configuration. "
                "Please set LOGTO_ENDPOINT and LOGTO_SPA_APP_ID in .env file"
            )

    @property
    def jwks_uri(self) -> str:
        """Get JWKS URI for token verification"""
        return f"{self.endpoint}/oidc/jwks"

    @property
    def issuer(self) -> str:
        """Get issuer URI"""
        return f"{self.endpoint}/oidc"

    @property
    def token_endpoint(self) -> str:
        """Get token endpoint for M2M authentication"""
        return f"{self.endpoint}/oidc/token"

    def has_m2m_config(self) -> bool:
        """Check if M2M configuration is available"""
        return bool(self.m2m_app_id and self.m2m_app_secret)


# Global config instance
_config: Optional[LogtoConfig] = None

# M2M token cache
_m2m_token_cache: Dict[str, Any] = {
    "access_token": None,
    "expires_at": 0
}


def get_logto_config() -> LogtoConfig:
    """Get or initialize Logto configuration"""
    global _config
    if _config is None:
        _config = LogtoConfig()
    return _config


@lru_cache(maxsize=1)
def get_jwks(jwks_uri: str) -> Dict[str, Any]:
    """
    Fetch JSON Web Key Set (JWKS) from Logto endpoint.
    Cached to avoid repeated requests.

    Args:
        jwks_uri: The JWKS endpoint URL

    Returns:
        Dictionary containing JWKS data

    Raises:
        HTTPException: If JWKS cannot be fetched
    """
    try:
        response = requests.get(jwks_uri, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch JWKS from Logto: {str(e)}"
        )


def get_signing_key(token: str, jwks_uri: str) -> str:
    """
    Get the signing key from JWKS for the given token.

    Args:
        token: JWT token to verify
        jwks_uri: JWKS endpoint URL

    Returns:
        The signing key as a string

    Raises:
        HTTPException: If signing key cannot be found
    """
    try:
        # Get unverified header to find the key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            raise HTTPException(
                status_code=401,
                detail="Token missing key ID (kid)"
            )

        # Fetch JWKS
        jwks = get_jwks(jwks_uri)

        # Find the matching key
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return json.dumps(key)

        raise HTTPException(
            status_code=401,
            detail="Unable to find matching signing key"
        )

    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token header: {str(e)}"
        )


def verify_user_token(token: str, config: LogtoConfig) -> Dict[str, Any]:
    """
    Verify and decode user JWT token from Logto (from frontend).

    Args:
        token: The JWT token to verify
        config: Logto configuration

    Returns:
        Decoded token claims as dictionary

    Raises:
        HTTPException: If token is invalid, expired, or verification fails
    """
    try:
        # Get signing key
        signing_key = get_signing_key(token, config.jwks_uri)

        # Verify and decode token
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=config.api_resource,
            issuer=config.issuer,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True,
            }
        )

        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except JWTClaimsError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token claims: {str(e)}"
        )
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token verification failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication error: {str(e)}"
        )


def obtain_m2m_token(config: LogtoConfig) -> str:
    """
    Obtain M2M access token using client credentials flow.

    This is used for backend-to-backend API calls, not for user authentication.

    Args:
        config: Logto configuration

    Returns:
        Access token string

    Raises:
        HTTPException: If token request fails or M2M is not configured
    """
    if not config.has_m2m_config():
        raise HTTPException(
            status_code=500,
            detail="M2M authentication not configured. Set LOGTO_M2M_APP_ID and LOGTO_M2M_APP_SECRET"
        )

    global _m2m_token_cache

    # Check if we have a valid cached token
    current_time = time.time()
    if _m2m_token_cache["access_token"] and current_time < _m2m_token_cache["expires_at"]:
        return _m2m_token_cache["access_token"]

    # Request new token using client credentials
    try:
        response = requests.post(
            config.token_endpoint,
            data={
                "grant_type": "client_credentials",
                "resource": config.api_resource,
                "scope": ""
            },
            auth=(config.m2m_app_id, config.m2m_app_secret),
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            timeout=10
        )
        response.raise_for_status()

        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)

        if not access_token:
            raise HTTPException(
                status_code=500,
                detail="Failed to obtain access token from Logto"
            )

        # Cache token with 5-minute buffer before expiration
        _m2m_token_cache["access_token"] = access_token
        _m2m_token_cache["expires_at"] = current_time + expires_in - 300

        return access_token

    except requests.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to obtain M2M token: {str(e)}"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user.

    This validates the JWT token from the frontend user.

    Usage:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["sub"]}

    Args:
        credentials: HTTP Authorization credentials (Bearer token)

    Returns:
        User information from token claims

    Raises:
        HTTPException 401: If token is missing or invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization credentials"
        )

    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing access token"
        )

    # Get config and verify token
    config = get_logto_config()
    user_claims = verify_user_token(token, config)

    return user_claims


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(optional_security)
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency to get current user if authenticated, None otherwise.

    Args:
        credentials: HTTP Authorization credentials (Bearer token)

    Returns:
        User claims if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        config = get_logto_config()
        return verify_user_token(credentials.credentials, config)
    except HTTPException:
        return None


async def get_m2m_token() -> str:
    """
    FastAPI dependency to get M2M access token.

    This is for backend services that need to call external protected APIs.

    Usage:
        @router.get("/external-api")
        async def call_external_api(token: str = Depends(get_m2m_token)):
            headers = {"Authorization": f"Bearer {token}"}
            # Make API call with token

    Returns:
        Valid M2M access token

    Raises:
        HTTPException: If token cannot be obtained
    """
    config = get_logto_config()
    return obtain_m2m_token(config)


def clear_m2m_token_cache():
    """Clear the cached M2M token (for testing or forced refresh)"""
    global _m2m_token_cache
    _m2m_token_cache["access_token"] = None
    _m2m_token_cache["expires_at"] = 0


def require_user(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Simplified dependency that just requires authentication.

    Usage:
        @router.get("/protected", dependencies=[Depends(require_user)])
        async def protected_route():
            return {"message": "authenticated"}

    Args:
        user: User claims from get_current_user

    Returns:
        User claims
    """
    return user
