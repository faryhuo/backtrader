"""
Settings Routes - API endpoints for user settings and credentials management.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.db import SettingsStorage
from src.routes.common.dependencies import get_settings_storage
from src.routes.common.auth_dependencies import get_optional_user_id
from src.utils.encryption import mask_credential
from src.utils.credential_validator import validate_credential

logger = logging.getLogger(__name__)
router = APIRouter()


def _resolve_masked_credential_value(
    storage: SettingsStorage,
    credential_key: str,
    incoming_value: Any,
    user_id: Optional[str],
) -> Any:
    """Keep the current secret when the client submits a masked placeholder."""
    if not isinstance(incoming_value, str) or not incoming_value:
        return incoming_value

    current_value, _ = storage.get_credential_with_fallback(credential_key, user_id)
    if isinstance(current_value, str) and incoming_value == mask_credential(current_value):
        return current_value

    return incoming_value


def _resolve_masked_ai_provider_value(
    storage: SettingsStorage,
    provider: str,
    field: str,
    incoming_value: Optional[str],
    user_id: Optional[str],
) -> Optional[str]:
    """Keep nested AI provider secrets when the client submits masked placeholders."""
    if not incoming_value:
        return incoming_value

    current_value = None
    try:
        if hasattr(storage, "get_ai_provider_config"):
            current_config, _ = storage.get_ai_provider_config(
                provider,
                user_id=user_id,
                mask_sensitive=False,
            )
            current_value = current_config.get(field)
    except Exception:
        current_value = None

    if current_value is None and provider == "openai" and field == "api_key":
        current_value, _ = storage.get_credential_with_fallback("openai_api_key", user_id)

    if isinstance(current_value, str) and incoming_value == mask_credential(current_value):
        return current_value

    return incoming_value


def _resolve_masked_ccxt_value(
    storage: SettingsStorage,
    exchange: str,
    mode: str,
    field: str,
    incoming_value: Optional[str],
    user_id: Optional[str],
) -> Optional[str]:
    """Keep the current CCXT secret when the client submits a masked placeholder."""
    if not incoming_value:
        return incoming_value

    all_credentials, _ = storage.get_ccxt_credentials_all(user_id=user_id, mask_sensitive=False)
    current_value = all_credentials.get(exchange, {}).get(mode, {}).get(field)
    if isinstance(current_value, str) and incoming_value == mask_credential(current_value):
        return current_value

    return incoming_value


def _resolve_masked_data_source_value(
    storage: SettingsStorage,
    field: str,
    incoming_value: Optional[str],
    user_id: Optional[str],
) -> Optional[str]:
    """Keep the current data-source secret when the client submits a masked placeholder."""
    if not incoming_value:
        return incoming_value

    if field == "eodhd_api_key":
        current_value = storage.get_eodhd_api_key(user_id=user_id)
        if isinstance(current_value, str) and incoming_value == mask_credential(current_value):
            return current_value

    return incoming_value


class UserSettingsRequest(BaseModel):
    """Request model for updating user settings."""
    selected_models: Optional[List[str]] = Field(None, min_length=1, description="Legacy hidden list of AI model names")
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
    storage = get_settings_storage()

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
    ai_provider: Optional[str] = None
    ai_provider_priority: Optional[List[str]] = None
    ai_provider_configs: Optional[Dict[str, Dict[str, Optional[str]]]] = None
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
    credential_type: str = Field(..., description="Type: ai_model, openai, ccxt, logto, proxy")
    provider: Optional[str] = None
    # For AI providers
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
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
        "ai_provider": credentials_nested["ai_models"]["active_provider"],
        "ai_provider_priority": credentials_nested["ai_models"]["provider_priority"],
        "ai_provider_configs": credentials_nested["ai_models"]["providers"],
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
        "ai_provider": credentials_nested["ai_models"]["active_provider_source"],
        "ai_provider_priority": credentials_nested["ai_models"]["provider_priority_source"],
        "ai_provider_configs": credentials_nested["ai_models"]["provider_sources"],
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

    # Backward-compatible legacy OpenAI fields
    payload = request.dict(exclude_unset=True)
    legacy_openai = {}
    if "openai_api_key" in payload:
        legacy_openai["api_key"] = _resolve_masked_credential_value(
            storage, "openai_api_key", payload.pop("openai_api_key"), user_id
        )
    if "openai_base_url" in payload:
        legacy_openai["base_url"] = payload.pop("openai_base_url")
    if legacy_openai:
        payload.setdefault("ai_provider_configs", {})
        payload["ai_provider_configs"].setdefault("openai", {}).update(legacy_openai)

    updated_fields = []
    for key, value in payload.items():
        if key == "ai_provider" and value:
            if storage.save_ai_provider(value.lower(), user_id):
                updated_fields.append(key)
            continue

        if key == "ai_provider_priority" and value is not None:
            if storage.save_ai_provider_priority(value, user_id):
                updated_fields.append(key)
            continue

        if key == "ai_provider_configs" and value:
            for provider, provider_config in value.items():
                resolved_config = dict(provider_config or {})
                if "api_key" in resolved_config:
                    resolved_config["api_key"] = _resolve_masked_ai_provider_value(
                        storage,
                        provider,
                        "api_key",
                        resolved_config.get("api_key"),
                        user_id,
                    )
                success = storage.save_ai_provider_config(
                    provider.lower(),
                    resolved_config,
                    user_id=user_id,
                )
                if success:
                    updated_fields.append(f"ai_provider_configs.{provider}")
            continue

        if value is not None:  # Allow empty string to clear a value
            value = _resolve_masked_credential_value(storage, key, value, user_id)
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
        credentials["api_key"] = _resolve_masked_ccxt_value(
            storage, request.exchange, request.mode, "api_key", request.api_key, user_id
        )
    if request.secret is not None:
        credentials["secret"] = _resolve_masked_ccxt_value(
            storage, request.exchange, request.mode, "secret", request.secret, user_id
        )
    if request.passphrase is not None:
        credentials["passphrase"] = _resolve_masked_ccxt_value(
            storage, request.exchange, request.mode, "passphrase", request.passphrase, user_id
        )

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

    if credential_key.startswith("ai_provider:"):
        try:
            _, provider, field = credential_key.split(":", 2)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid AI provider credential key") from exc

        success = storage.save_ai_provider_config(
            provider,
            {field: None},
            user_id=user_id,
        )
    else:
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
        storage = get_settings_storage()
        credential_type = request.credential_type.lower()

        # Prepare kwargs based on credential type
        if credential_type in {'openai', 'ai_model'}:
            provider = (request.provider or "openai").lower()
            kwargs = {
                'api_key': _resolve_masked_ai_provider_value(
                    storage, provider, 'api_key', request.api_key, user_id
                ),
                'base_url': request.base_url,
                'model': request.model,
            }
            if credential_type == 'ai_model':
                kwargs['provider'] = provider
        elif credential_type == 'ccxt':
            kwargs = {
                'exchange': request.exchange,
                'mode': request.mode,
                'api_key': _resolve_masked_ccxt_value(
                    storage, request.exchange or '', request.mode or '', 'api_key', request.api_key, user_id
                ),
                'secret': _resolve_masked_ccxt_value(
                    storage, request.exchange or '', request.mode or '', 'secret', request.secret, user_id
                ),
                'passphrase': _resolve_masked_ccxt_value(
                    storage, request.exchange or '', request.mode or '', 'passphrase', request.passphrase, user_id
                )
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
        eodhd_api_key=_resolve_masked_data_source_value(
            storage, "eodhd_api_key", request.eodhd_api_key, user_id
        ),
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

