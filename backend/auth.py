"""
Logto Authentication Module

This module provides JWT token verification and user authentication
for the Backtrader platform using Logto as the identity provider.
"""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from functools import lru_cache

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
    """Logto configuration loaded from environment variables"""

    def __init__(self):
        self.endpoint = os.getenv("LOGTO_ENDPOINT")
        self.app_id = os.getenv("LOGTO_APP_ID")
        self.app_secret = os.getenv("LOGTO_APP_SECRET")
        self.audience = os.getenv("LOGTO_AUDIENCE", "http://localhost:8000")

        # Validate required configuration
        if not all([self.endpoint, self.app_id, self.app_secret]):
            raise ValueError(
                "Missing required Logto configuration. "
                "Please set LOGTO_ENDPOINT, LOGTO_APP_ID, and LOGTO_APP_SECRET in .env file"
            )

    @property
    def jwks_uri(self) -> str:
        """Get JWKS URI for token verification"""
        return f"{self.endpoint}/oidc/jwks"

    @property
    def issuer(self) -> str:
        """Get issuer URI"""
        return f"{self.endpoint}/oidc"


# Global config instance
_config: Optional[LogtoConfig] = None


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


def verify_token(token: str, config: LogtoConfig) -> Dict[str, Any]:
    """
    Verify and decode JWT token from Logto.

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
            audience=config.audience,
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


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user.

    This dependency can be used in route handlers to enforce authentication:

    @router.get("/protected")
    async def protected_route(user: dict = Depends(get_current_user)):
        return {"user_id": user["sub"]}

    Args:
        credentials: HTTP Authorization credentials (Bearer token)

    Returns:
        User information from token claims containing:
        - sub: User ID (subject)
        - aud: Audience
        - iss: Issuer
        - exp: Expiration timestamp
        - iat: Issued at timestamp
        - Other custom claims

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
    user_claims = verify_token(token, config)

    return user_claims


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(optional_security)
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency to get current user if authenticated, None otherwise.

    Useful for endpoints that have optional authentication.

    Args:
        credentials: HTTP Authorization credentials (Bearer token)

    Returns:
        User claims if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        config = get_logto_config()
        return verify_token(credentials.credentials, config)
    except HTTPException:
        return None


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
