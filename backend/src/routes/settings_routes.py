"""
Settings Routes - API endpoints for user settings and credentials management.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.db import SettingsStorage
from src.routes.common.dependencies import get_settings_storage
from src.routes.common.auth_dependencies import get_optional_user_id
from src.utils.credential_validator import validate_credential

logger = logging.getLogger(__name__)
router = APIRouter()


class UserSettingsRequest(BaseModel):
    """Request model for updating user settings."""
    selected_models: List[str] = Field(..., min_length=1, description="List of AI model names")
    code_analysis_prompt: str = Field(..., min_length=1)
    code_rewrite_prompt: str = Field(..., min_length=1)
    full_strategy_analysis_prompt: str = Field(..., min_length=1)


@router.get("/settings")
def get_user_settings(user_id: str = Depends(get_optional_user_id)) -> dict:
    """
    Get user settings.

    Returns settings from database if found, otherwise returns defaults.
    Frontend will migrate from localStorage on first save.
    """
    storage = get_settings_storage()

    settings = storage.get_settings(user_id=user_id)

    return {
        "status": "ok",
        "settings": settings
    }


@router.put("/settings")
def update_user_settings(
    request: UserSettingsRequest,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Update user settings.

    Creates new settings if none exist, updates existing settings otherwise.
    Frontend should migrate localStorage data on first save.
    """
    from src.routes.common.error_utils import validate_list_not_empty

    storage = get_settings_storage()

    # Validate at least one model selected
    validate_list_not_empty(request.selected_models, "selected_models")

    settings = storage.save_settings(
        selected_models=request.selected_models,
        code_analysis_prompt=request.code_analysis_prompt,
        code_rewrite_prompt=request.code_rewrite_prompt,
        full_strategy_analysis_prompt=request.full_strategy_analysis_prompt,
        user_id=user_id
    )

    return {
        "status": "ok",
        "message": "Settings saved successfully",
        "settings": settings
    }


@router.post("/settings/reset")
def reset_user_settings(user_id: str = Depends(get_optional_user_id)) -> dict:
    """
    Reset user settings to defaults.

    Deletes user settings from database and returns default values.
    """
    storage = get_settings_storage()

    defaults = storage.reset_settings(user_id=user_id)

    return {
        "status": "ok",
        "message": "Settings reset to defaults",
        "settings": defaults
    }


@router.get("/settings/logto-config")
def get_logto_config(user_id: str = Depends(get_optional_user_id)) -> dict:
    """
    Get Logto frontend configuration.

    Returns Logto configuration for frontend initialization including
    endpoint, appId, redirect URIs, and login enablement status.
    Falls back to environment variables if not set in database.
    """
    storage = get_settings_storage()

    config = storage.get_logto_frontend_config(user_id=user_id)

    return {
        "status": "ok",
        "config": config
    }


# ========== CREDENTIAL MANAGEMENT ENDPOINTS ==========

class CredentialUpdate(BaseModel):
    """Request model for updating general credentials."""
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    # Server-side JWT validation settings
    logto_issuer: Optional[str] = None
    logto_jwks_uri: Optional[str] = None
    logto_audience: Optional[str] = None
    logto_required_scopes: Optional[str] = None
    enable_login: Optional[bool] = None
    # Frontend OAuth configuration
    logto_endpoint: Optional[str] = None
    logto_app_id: Optional[str] = None
    logto_redirect_uri: Optional[str] = None
    logto_post_logout_redirect_uri: Optional[str] = None
    # Proxy settings
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None



class CCXTCredentialUpdate(BaseModel):
    """Request model for updating CCXT exchange credentials."""
    exchange: str = Field(..., description="Exchange ID (binance, okx, bybit)")
    mode: str = Field(..., description="Trading mode (paper or live)")
    api_key: Optional[str] = None
    secret: Optional[str] = None
    passphrase: Optional[str] = None


class CredentialTestRequest(BaseModel):
    """Request model for testing credentials."""
    credential_type: str = Field(..., description="Type: openai, ccxt, logto, proxy")
    # For OpenAI
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    # For CCXT
    exchange: Optional[str] = None
    mode: Optional[str] = None
    secret: Optional[str] = None
    passphrase: Optional[str] = None
    # For Logto
    issuer: Optional[str] = None
    jwks_uri: Optional[str] = None
    # For Proxy
    proxy_url: Optional[str] = None


@router.get("/settings/credentials")
def get_credentials(user_id: str = Depends(get_optional_user_id)) -> dict:
    """
    Get all credentials with masked sensitive values.

    Returns credentials from database if found, otherwise falls back to .env.
    Sensitive values (API keys, secrets) are masked for security.
    """
    storage = get_settings_storage()

    credentials_nested = storage.get_all_credentials(user_id=user_id, mask_sensitive=True)

    # Flatten the structure to match frontend expectations
    credentials_flat = {
        "openai_api_key": credentials_nested["openai"]["api_key"],
        "openai_base_url": credentials_nested["openai"]["base_url"],
        # Server-side JWT validation
        "logto_issuer": credentials_nested["logto"]["issuer"],
        "logto_jwks_uri": credentials_nested["logto"]["jwks_uri"],
        "logto_audience": credentials_nested["logto"]["audience"],
        "logto_required_scopes": credentials_nested["logto"]["required_scopes"],
        "enable_login": credentials_nested["logto"]["enable_login"],
        # Frontend OAuth configuration
        "logto_endpoint": credentials_nested["logto"]["endpoint"],
        "logto_app_id": credentials_nested["logto"]["app_id"],
        "logto_redirect_uri": credentials_nested["logto"]["redirect_uri"],
        "logto_post_logout_redirect_uri": credentials_nested["logto"]["post_logout_redirect_uri"],
        # Proxy settings
        "http_proxy": credentials_nested["proxies"]["http_proxy"],
        "https_proxy": credentials_nested["proxies"]["https_proxy"],
        "ccxt": credentials_nested["exchanges"]
    }

    # Flatten sources as well
    sources = {
        "openai_api_key": credentials_nested["openai"]["api_key_source"],
        "openai_base_url": credentials_nested["openai"]["base_url_source"],
        # Server-side JWT validation sources
        "logto_issuer": credentials_nested["logto"]["issuer_source"],
        "logto_jwks_uri": credentials_nested["logto"]["jwks_uri_source"],
        "logto_audience": credentials_nested["logto"]["audience_source"],
        "logto_required_scopes": credentials_nested["logto"]["required_scopes_source"],
        "enable_login": credentials_nested["logto"]["enable_login_source"],
        # Frontend OAuth configuration sources
        "logto_endpoint": credentials_nested["logto"]["endpoint_source"],
        "logto_app_id": credentials_nested["logto"]["app_id_source"],
        "logto_redirect_uri": credentials_nested["logto"]["redirect_uri_source"],
        "logto_post_logout_redirect_uri": credentials_nested["logto"]["post_logout_redirect_uri_source"],
        # Proxy settings sources
        "http_proxy": credentials_nested["proxies"]["http_proxy_source"],
        "https_proxy": credentials_nested["proxies"]["https_proxy_source"],
    }

    return {
        "status": "ok",
        "credentials": credentials_flat,
        "sources": sources
    }


@router.put("/settings/credentials")
def update_credentials(
    request: CredentialUpdate,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Update general credentials (OpenAI, Logto, Proxies).

    Only updates fields that are explicitly set in the request.
    Values are encrypted before storage if they are sensitive fields.
    """
    storage = get_settings_storage()

    # Update each credential that was provided
    updated_fields = []
    for key, value in request.dict(exclude_unset=True).items():
        if value is not None:  # Allow empty string to clear a value
            success = storage.save_credential(key, value, user_id)
            if success:
                updated_fields.append(key)
            else:
                logger.warning(f"Failed to update credential: {key}")

    return {
        "status": "ok",
        "message": f"Updated {len(updated_fields)} credentials",
        "updated_fields": updated_fields
    }


@router.put("/settings/credentials/ccxt")
def update_ccxt_credentials(
    request: CCXTCredentialUpdate,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Update CCXT exchange credentials for a specific exchange and mode.

    Credentials are encrypted before storage.
    """
    from src.utils.exception_handlers import ValidationError, CredentialError

    storage = get_settings_storage()

    # Extract credentials dict
    credentials = {}
    if request.api_key is not None:
        credentials["api_key"] = request.api_key
    if request.secret is not None:
       credentials["secret"] = request.secret
    if request.passphrase is not None:
        credentials["passphrase"] = request.passphrase

    if not credentials:
        raise ValidationError("At least one credential field must be provided")

    success = storage.save_ccxt_credentials(
        exchange=request.exchange,
        mode=request.mode,
        credentials=credentials,
        user_id=user_id
    )

    if not success:
        raise CredentialError("Failed to save credentials")

    return {
        "status": "ok",
        "message": f"Updated {request.exchange} {request.mode} credentials"
    }


@router.delete("/settings/credentials/{credential_key}")
def reset_credential(
    credential_key: str,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Reset a credential to .env value by deleting it from database.

    After deletion, the credential will fall back to the value in .env file.
    """
    from src.utils.exception_handlers import CredentialError

    storage = get_settings_storage()

    success = storage.delete_credential(credential_key, user_id)

    if not success:
        raise CredentialError("Failed to delete credential")

    return {
        "status": "ok",
        "message": f"Credential '{credential_key}' reset to .env value"
    }


@router.post("/settings/credentials/test")
def test_credentials(
    request: CredentialTestRequest,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Test API credentials by making actual API calls.

    This validates that credentials are correct and have proper permissions.
    """
    try:
        credential_type = request.credential_type.lower()

        # Prepare kwargs based on credential type
        if credential_type == 'openai':
            kwargs = {
                'api_key': request.api_key,
                'base_url': request.base_url or 'https://api.openai.com/v1'
            }
        elif credential_type == 'ccxt':
            kwargs = {
                'exchange': request.exchange,
                'mode': request.mode,
                'api_key': request.api_key,
                'secret': request.secret,
                'passphrase': request.passphrase
            }
        elif credential_type == 'logto':
            kwargs = {
                'issuer': request.issuer,
                'jwks_uri': request.jwks_uri
            }
        elif credential_type == 'proxy':
            kwargs = {
                'proxy_url': request.proxy_url
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown credential type: {credential_type}"
            )

        # Validate credentials
        is_valid, message = validate_credential(credential_type, **kwargs)

        return {
            "status": "ok",
            "valid": is_valid,
            "message": message
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test credentials: {e}")
        return {
            "status": "error",
            "valid": False,
            "message": f"Test failed: {str(e)[:200]}"
        }


# ========== DATA SOURCE CONFIGURATION ENDPOINTS ==========

class DataSourceSettingsRequest(BaseModel):
    """Request model for updating data source settings."""
    data_source_priority: Optional[List[str]] = Field(
        None, description="List of data sources in priority order (yahoo, eodhd, database)"
    )
    eodhd_api_key: Optional[str] = Field(
        None, description="EODHD API key (will be encrypted)"
    )


@router.get("/settings/data-source")
def get_data_source_settings(user_id: str = Depends(get_optional_user_id)) -> dict:
    """
    Get data source configuration.

    Returns the priority order for fetching market data and EODHD API key status.
    """
    storage = get_settings_storage()

    settings = storage.get_data_source_settings(user_id=user_id)

    return {
        "status": "ok",
        "settings": settings
    }


@router.put("/settings/data-source")
def update_data_source_settings(
    request: DataSourceSettingsRequest,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Update data source configuration.

    Sets the priority order for fetching market data and/or EODHD API key.
    """
    from src.utils.exception_handlers import ValidationError, CredentialError

    storage = get_settings_storage()

    # Validate priority if provided
    valid_sources = {"yahoo", "eodhd", "database"}
    if request.data_source_priority:
        invalid = [s for s in request.data_source_priority if s not in valid_sources]
        if invalid:
            raise ValidationError(
                f"Invalid data sources: {invalid}. Valid options: {list(valid_sources)}"
            )

    success = storage.save_data_source_settings(
        data_source_priority=request.data_source_priority,
        eodhd_api_key=request.eodhd_api_key,
        user_id=user_id
    )

    if not success:
        raise CredentialError("Failed to save data source settings")

    return {
        "status": "ok",
        "message": "Data source settings saved successfully"
    }


@router.post("/settings/data-source/reset")
def reset_data_source_settings(user_id: str = Depends(get_optional_user_id)) -> dict:
    """
    Reset data source settings to defaults.

    Removes custom priority and EODHD API key from database.
    """
    from src.utils.exception_handlers import CredentialError

    storage = get_settings_storage()

    success = storage.reset_data_source_settings(user_id=user_id)

    if not success:
        raise CredentialError("Failed to reset data source settings")

    # Return new settings (defaults)
    settings = storage.get_data_source_settings(user_id=user_id)

    return {
        "status": "ok",
        "message": "Data source settings reset to defaults",
        "settings": settings
    }

