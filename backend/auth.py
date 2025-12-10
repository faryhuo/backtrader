"""
Logto M2M Authentication Module

This module provides Machine-to-Machine (M2M) authentication using Logto.
It obtains access tokens via client credentials flow and uses them for API requests.
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
from fastapi import HTTPException, Request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LogtoM2MConfig:
    """Logto M2M configuration loaded from environment variables"""

    def __init__(self):
        self.endpoint = os.getenv("LOGTO_ENDPOINT")
        self.app_id = os.getenv("LOGTO_M2M_APP_ID")
        self.app_secret = os.getenv("LOGTO_M2M_APP_SECRET")
        self.resource = os.getenv("LOGTO_API_RESOURCE", "https://logto.fary.chat/api")

        # Validate required configuration
        if not all([self.endpoint, self.app_id, self.app_secret]):
            raise ValueError(
                "Missing required Logto M2M configuration. "
                "Please set LOGTO_ENDPOINT, LOGTO_M2M_APP_ID, and LOGTO_M2M_APP_SECRET in .env file"
            )

    @property
    def token_endpoint(self) -> str:
        """Get token endpoint for M2M authentication"""
        return f"{self.endpoint}/oidc/token"

    @property
    def jwks_uri(self) -> str:
        """Get JWKS URI for token verification"""
        return f"{self.endpoint}/oidc/jwks"

    @property
    def issuer(self) -> str:
        """Get issuer URI"""
        return f"{self.endpoint}/oidc"


# Global config instance
_config: Optional[LogtoM2MConfig] = None

# Token cache: stores access token and expiration time
_token_cache: Dict[str, Any] = {
    "access_token": None,
    "expires_at": 0
}


def get_logto_config() -> LogtoM2MConfig:
    """Get or initialize Logto M2M configuration"""
    global _config
    if _config is None:
        _config = LogtoM2MConfig()
    return _config


def obtain_m2m_token(config: LogtoM2MConfig) -> str:
    """
    Obtain access token using client credentials flow (M2M).

    This implements the OAuth 2.0 client credentials grant type,
    where the application authenticates itself to get an access token.

    Args:
        config: Logto M2M configuration

    Returns:
        Access token string

    Raises:
        HTTPException: If token request fails
    """
    global _token_cache

    # Check if we have a valid cached token
    current_time = time.time()
    if _token_cache["access_token"] and current_time < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    # Request new token using client credentials
    try:
        response = requests.post(
            config.token_endpoint,
            data={
                "grant_type": "client_credentials",
                "resource": config.resource,
                "scope": ""  # M2M apps typically don't need scopes, or use specific API scopes
            },
            auth=(config.app_id, config.app_secret),
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            timeout=10
        )
        response.raise_for_status()

        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour

        if not access_token:
            raise HTTPException(
                status_code=500,
                detail="Failed to obtain access token from Logto"
            )

        # Cache token with 5-minute buffer before expiration
        _token_cache["access_token"] = access_token
        _token_cache["expires_at"] = current_time + expires_in - 300

        return access_token

    except requests.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to obtain M2M token: {str(e)}"
        )


async def get_m2m_token() -> str:
    """
    FastAPI dependency to get M2M access token.

    This can be used in route handlers or service functions that need
    to authenticate with external APIs using M2M credentials.

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


def clear_token_cache():
    """
    Clear the cached M2M token.

    This is useful for testing or when token needs to be refreshed immediately.
    """
    global _token_cache
    _token_cache["access_token"] = None
    _token_cache["expires_at"] = 0
