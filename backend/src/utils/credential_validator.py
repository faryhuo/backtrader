"""
Credential Validator - Test and validate API credentials.

Provides utilities to test API credentials by making actual API calls
to verify they are valid and have proper permissions.

Example usage:
    from src.utils.credential_validator import validate_ai_provider_key, validate_ccxt_credentials

    # Test OpenAI key
    is_valid, message = validate_ai_provider_key("openai", "sk-...", "https://api.openai.com/v1")
    if is_valid:
        print(f"OpenAI credentials valid: {message}")

    # Test CCXT credentials
    is_valid, message = validate_ccxt_credentials("binance", "paper", "api_key", "secret")
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def validate_openai_key(api_key: str, base_url: str = "https://api.openai.com/v1") -> Tuple[bool, str]:
    """
    Validate OpenAI API key by attempting to list models.

    Args:
        api_key: OpenAI API key to test
        base_url: OpenAI API base URL

    Returns:
        Tuple of (is_valid, message)
        - is_valid: True if credentials are valid
        - message: Success message or error description
    """
    if not api_key:
        return False, "API key is empty"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url, timeout=10.0)

        # Try to list models
        models = client.models.list()
        model_count = len(models.data) if hasattr(models, 'data') else 0

        return True, f"Valid - {model_count} models available"

    except Exception as e:
        error_msg = str(e)
        # Extract useful error message
        if "401" in error_msg or "Unauthorized" in error_msg:
            return False, "Invalid API key (401 Unauthorized)"
        elif "403" in error_msg or "Forbidden" in error_msg:
            return False, "API key lacks permissions (403 Forbidden)"
        elif "timeout" in error_msg.lower():
            return False, "Connection timeout - check base_url and network"
        elif "connection" in error_msg.lower():
            return False, f"Connection error: {error_msg}"
        else:
            return False, f"Validation failed: {error_msg[:100]}"


def validate_gemini_key(
    api_key: str,
    base_url: str = "https://generativelanguage.googleapis.com/v1beta",
) -> Tuple[bool, str]:
    """Validate Gemini API key with a lightweight generateContent call."""
    if not api_key:
        return False, "API key is empty"

    try:
        import requests

        response = requests.post(
            f"{base_url.rstrip('/')}/models/gemini-2.0-flash:generateContent",
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": "ping"}]}]},
            timeout=10,
        )
        if response.status_code == 200:
            return True, "Valid - Gemini request succeeded"
        if response.status_code in {401, 403}:
            return False, f"Invalid API key ({response.status_code})"
        return False, f"Validation failed: HTTP {response.status_code}"
    except Exception as exc:
        return False, f"Validation failed: {str(exc)[:100]}"


def validate_claude_key(
    api_key: str,
    base_url: str = "https://api.anthropic.com/v1",
) -> Tuple[bool, str]:
    """Validate Claude API key using the Messages API."""
    if not api_key:
        return False, "API key is empty"

    try:
        import requests

        response = requests.post(
            f"{base_url.rstrip('/')}/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-3-5-haiku-latest",
                "max_tokens": 16,
                "messages": [{"role": "user", "content": "ping"}],
            },
            timeout=10,
        )
        if response.status_code == 200:
            return True, "Valid - Claude request succeeded"
        if response.status_code in {401, 403}:
            return False, f"Invalid API key ({response.status_code})"
        return False, f"Validation failed: HTTP {response.status_code}"
    except Exception as exc:
        return False, f"Validation failed: {str(exc)[:100]}"


def validate_ai_provider_key(
    provider: str,
    api_key: str,
    base_url: Optional[str] = None,
) -> Tuple[bool, str]:
    """Validate a configured AI provider key."""
    provider_name = (provider or "openai").lower()
    if provider_name == "gemini":
        return validate_gemini_key(api_key, base_url or "https://generativelanguage.googleapis.com/v1beta")
    if provider_name == "claude":
        return validate_claude_key(api_key, base_url or "https://api.anthropic.com/v1")
    return validate_openai_key(api_key, base_url or "https://api.openai.com/v1")


def validate_ccxt_credentials(
    exchange: str,
    mode: str,
    api_key: str,
    secret: str,
    passphrase: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Validate CCXT exchange credentials by fetching account balance.

    Args:
        exchange: Exchange ID (e.g., "binance", "okx", "bybit")
        mode: Trading mode ("paper" or "live")
        api_key: Exchange API key
        secret: Exchange API secret
        passphrase: Optional passphrase (for OKX, KuCoin, etc.)

    Returns:
        Tuple of (is_valid, message)
    """
    if not api_key or not secret:
        return False, "API key or secret is empty"

    try:
        import ccxt

        # Get exchange class
        exchange_class = getattr(ccxt, exchange, None)
        if not exchange_class:
            return False, f"Unsupported exchange: {exchange}"

        # Initialize exchange
        config = {
            'apiKey': api_key,
            'secret': secret,
            'timeout': 10000,  # 10 second timeout
            'enableRateLimit': True
        }

        if passphrase:
            config['password'] = passphrase

        ex = exchange_class(config)

        # Enable sandbox mode for paper trading
        if mode == 'paper':
            if hasattr(ex, 'set_sandbox_mode'):
                ex.set_sandbox_mode(True)
            else:
                logger.warning(f"{exchange} may not support sandbox mode")

        # Try to fetch balance (requires authentication)
        balance = ex.fetch_balance()

        # Success - credentials are valid
        total_balance = balance.get('total', {})
        currency_count = len([k for k, v in total_balance.items() if v > 0])

        return True, f"Valid - Connected to {exchange} ({mode}), {currency_count} currencies with balance"

    except ccxt.AuthenticationError as e:
        return False, f"Authentication failed: Invalid API key or secret ({str(e)[:100]})"
    except ccxt.PermissionDenied as e:
        return False, f"Permission denied: API key lacks required permissions ({str(e)[:100]})"
    except ccxt.InvalidNonce as e:
        return False, f"Invalid nonce: Check system time synchronization ({str(e)[:100]})"
    except ccxt.NetworkError as e:
        if mode == 'paper':
            return False, f"Network error: Check if {exchange} testnet is accessible ({str(e)[:100]})"
        else:
            return False, f"Network error: {str(e)[:100]}"
    except ccxt.ExchangeError as e:
        return False, f"Exchange error: {str(e)[:100]}"
    except AttributeError as e:
        return False, f"Exchange '{exchange}' not found in CCXT library"
    except Exception as e:
        return False, f"Validation failed: {type(e).__name__}: {str(e)[:100]}"


async def validate_ccxt_credentials_async(
    exchange: str,
    mode: str,
    api_key: str,
    secret: str,
    passphrase: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Async version of validate_ccxt_credentials.

    Useful for FastAPI async endpoints.

    Args:
        exchange: Exchange ID
        mode: Trading mode
        api_key: Exchange API key
        secret: Exchange API secret
        passphrase: Optional passphrase

    Returns:
        Tuple of (is_valid, message)
    """
    if not api_key or not secret:
        return False, "API key or secret is empty"

    try:
        import ccxt.async_support as ccxt_async

        # Get exchange class
        exchange_class = getattr(ccxt_async, exchange, None)
        if not exchange_class:
            return False, f"Unsupported exchange: {exchange}"

        # Initialize exchange
        config = {
            'apiKey': api_key,
            'secret': secret,
            'timeout': 10000,
            'enableRateLimit': True
        }

        if passphrase:
            config['password'] = passphrase

        ex = exchange_class(config)

        try:
            # Enable sandbox mode for paper trading
            if mode == 'paper':
                if hasattr(ex, 'set_sandbox_mode'):
                    ex.set_sandbox_mode(True)

            # Try to fetch balance
            balance = await ex.fetch_balance()

            # Success
            total_balance = balance.get('total', {})
            currency_count = len([k for k, v in total_balance.items() if v > 0])

            return True, f"Valid - Connected to {exchange} ({mode}), {currency_count} currencies with balance"

        finally:
            await ex.close()

    except Exception as e:
        # Handle errors similar to sync version
        error_type = type(e).__name__
        error_msg = str(e)[:100]

        if "Authentication" in error_type:
            return False, f"Authentication failed: Invalid API key or secret ({error_msg})"
        elif "PermissionDenied" in error_type:
            return False, f"Permission denied: API key lacks required permissions ({error_msg})"
        elif "InvalidNonce" in error_type:
            return False, f"Invalid nonce: Check system time synchronization ({error_msg})"
        elif "Network" in error_type:
            if mode == 'paper':
                return False, f"Network error: Check if {exchange} testnet is accessible ({error_msg})"
            else:
                return False, f"Network error: {error_msg}"
        elif "Exchange" in error_type:
            return False, f"Exchange error: {error_msg}"
        else:
            return False, f"Validation failed: {error_type}: {error_msg}"


def validate_logto_config(issuer: str, jwks_uri: str) -> Tuple[bool, str]:
    """
    Validate Logto configuration by checking JWKS endpoint.

    Args:
        issuer: Logto issuer URL
        jwks_uri: Logto JWKS URI

    Returns:
        Tuple of (is_valid, message)
    """
    if not issuer or not jwks_uri:
        return False, "Issuer or JWKS URI is empty"

    try:
        import requests

        # Try to fetch JWKS
        response = requests.get(jwks_uri, timeout=10)

        if response.status_code == 200:
            jwks = response.json()
            key_count = len(jwks.get('keys', []))
            return True, f"Valid - JWKS endpoint accessible ({key_count} keys)"
        else:
            return False, f"JWKS endpoint returned {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "Connection timeout - check JWKS URI"
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection error: {str(e)[:100]}"
    except Exception as e:
        return False, f"Validation failed: {str(e)[:100]}"


def validate_proxy(proxy_url: str) -> Tuple[bool, str]:
    """
    Validate HTTP/HTTPS proxy by making a test request.

    Args:
        proxy_url: Proxy URL (e.g., "http://proxy.example.com:8080")

    Returns:
        Tuple of (is_valid, message)
    """
    if not proxy_url:
        return False, "Proxy URL is empty"

    try:
        import requests

        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }

        # Try to fetch a lightweight endpoint
        response = requests.get(
            'https://httpbin.org/ip',
            proxies=proxies,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            origin = data.get('origin', 'unknown')
            return True, f"Valid - Proxy working (origin IP: {origin})"
        else:
            return False, f"Proxy test returned {response.status_code}"

    except requests.exceptions.ProxyError as e:
        return False, f"Proxy error: {str(e)[:100]}"
    except requests.exceptions.Timeout:
        return False, "Connection timeout - check proxy URL"
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection error: {str(e)[:100]}"
    except Exception as e:
        return False, f"Validation failed: {str(e)[:100]}"


# Convenience function for testing all credential types
def validate_credential(
    credential_type: str,
    **kwargs
) -> Tuple[bool, str]:
    """
    Validate credentials based on type.

    Args:
        credential_type: One of 'openai', 'ccxt', 'logto', 'proxy'
        **kwargs: Type-specific parameters

    Returns:
        Tuple of (is_valid, message)

    Examples:
        >>> validate_credential('openai', api_key='sk-...', base_url='...')
        >>> validate_credential('ccxt', exchange='binance', mode='paper', api_key='...', secret='...')
        >>> validate_credential('logto', issuer='...', jwks_uri='...')
        >>> validate_credential('proxy', proxy_url='http://...')
    """
    if credential_type in {'openai', 'ai_model'}:
        return validate_ai_provider_key(
            kwargs.get('provider', 'openai'),
            kwargs.get('api_key'),
            kwargs.get('base_url')
        )

    elif credential_type == 'ccxt':
        return validate_ccxt_credentials(
            kwargs.get('exchange'),
            kwargs.get('mode'),
            kwargs.get('api_key'),
            kwargs.get('secret'),
            kwargs.get('passphrase')
        )

    elif credential_type == 'logto':
        return validate_logto_config(
            kwargs.get('issuer'),
            kwargs.get('jwks_uri')
        )

    elif credential_type == 'proxy':
        return validate_proxy(kwargs.get('proxy_url'))

    else:
        return False, f"Unknown credential type: {credential_type}"
