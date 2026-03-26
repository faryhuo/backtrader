"""
Unified AI service with provider-priority fallback.
"""

import base64
import logging
from typing import Optional

import httpx
from openai import AsyncOpenAI

from src.config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


def _encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def _build_anthropic_messages_url(base_url: str) -> str:
    """Build the Anthropic-compatible messages endpoint from a base URL."""
    normalized = (base_url or "https://api.anthropic.com/v1").rstrip("/")
    if normalized.endswith("/v1"):
        return f"{normalized}/messages"
    return f"{normalized}/v1/messages"


def _supports_image_input(provider: str, model: str | None, base_url: str | None) -> bool:
    """Best-effort capability check to avoid sending images to text-only models."""
    provider_name = (provider or "").lower()
    model_name = (model or "").lower()
    normalized_base_url = (base_url or "").rstrip("/").lower()

    # MiniMax anthropic-compatible endpoint in this project is treated as text-only.
    if provider_name == "minimax" and "/anthropic" in normalized_base_url:
        return False

    # Common text-only model hints across OpenAI-compatible providers.
    text_only_markers = (
        "mini",
        "nano",
        "text",
        "chat",
        "coder",
        "instruct",
        "reasoner",
        "m2.7",
    )
    if any(marker in model_name for marker in text_only_markers):
        if any(marker in model_name for marker in ("vision", "vl", "omni", "4o", "sonnet", "opus", "gemini")):
            return True
        if provider_name in {"openai", "minimax"}:
            return False

    # Gemini multimodal models generally support image input.
    if provider_name == "gemini":
        return True

    # Claude 3+/4 models support image input.
    if provider_name == "claude":
        return True

    # OpenAI-compatible default: allow unless model name strongly indicates text-only.
    return True


async def _call_openai_compatible(
    api_key: str,
    base_url: str,
    model: str,
    message: str,
    image_bytes: bytes | None,
    proxy: str | None,
) -> str:
    content: list[dict] = [{"type": "text", "text": message}]
    if image_bytes is not None:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{_encode_image(image_bytes)}"},
            }
        )

    messages = [{"role": "user", "content": content}]

    if proxy:
        async with httpx.AsyncClient(proxy=proxy, timeout=900) as http_client:
            client = AsyncOpenAI(api_key=api_key, base_url=base_url, http_client=http_client)
            response = await client.chat.completions.create(model=model, messages=messages)
    else:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        response = await client.chat.completions.create(model=model, messages=messages)

    return response.choices[0].message.content


async def _call_gemini(
    api_key: str,
    base_url: str,
    model: str,
    message: str,
    image_bytes: bytes | None,
    proxy: str | None,
) -> str:
    parts: list[dict] = [{"text": message}]
    if image_bytes is not None:
        parts.append(
            {
                "inline_data": {
                    "mime_type": "image/png",
                    "data": _encode_image(image_bytes),
                }
            }
        )

    kwargs = {"timeout": 900}
    if proxy:
        kwargs["proxy"] = proxy

    async with httpx.AsyncClient(**kwargs) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/models/{model}:generateContent",
            params={"key": api_key},
            json={"contents": [{"parts": parts}]},
        )
        response.raise_for_status()
        payload = response.json()

    texts = []
    for candidate in payload.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if part.get("text"):
                texts.append(part["text"])
    return "\n".join(texts).strip()


async def _call_claude(
    api_key: str,
    base_url: str,
    model: str,
    message: str,
    image_bytes: bytes | None,
    proxy: str | None,
) -> str:
    content: list[dict] = []
    if image_bytes is not None:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": _encode_image(image_bytes),
                },
            }
        )
    content.append({"type": "text", "text": message})

    kwargs = {
        "timeout": 900,
        "headers": {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    }
    if proxy:
        kwargs["proxy"] = proxy

    async with httpx.AsyncClient(**kwargs) as client:
        response = await client.post(
            _build_anthropic_messages_url(base_url),
            json={
                "model": model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": content}],
            },
        )
        response.raise_for_status()
        payload = response.json()

    texts = [
        block.get("text", "")
        for block in payload.get("content", [])
        if block.get("type") == "text"
    ]
    return "\n".join(texts).strip()


async def call_ai(
    message: str,
    *,
    user_id: Optional[str] = None,
    model: Optional[str] = None,
    image_bytes: bytes | None = None,
) -> dict:
    """
    Call AI using configured provider priority with automatic fallback.
    """
    config_manager = ConfigManager(user_id=user_id)
    proxy_config = config_manager.get_proxy_config()
    proxy = proxy_config.get("https_proxy") or proxy_config.get("http_proxy")
    priority = config_manager.get_ai_provider_priority()
    settings = config_manager.settings_storage.get_settings(user_id=user_id)
    legacy_default_model = (settings.get("selected_models") or [None])[0]

    errors: list[str] = []

    for provider in priority:
        provider_config = config_manager.get_ai_model_config(provider)
        api_key = provider_config.get("api_key")
        base_url = provider_config.get("base_url")
        resolved_model = model or provider_config.get("default_model") or legacy_default_model
        normalized_base_url = (base_url or "").rstrip("/").lower()
        effective_image_bytes = image_bytes

        if not api_key or not base_url:
            errors.append(f"{provider}: missing credentials")
            continue
        if not resolved_model:
            errors.append(f"{provider}: missing runtime model")
            continue

        if effective_image_bytes is not None and not _supports_image_input(provider, resolved_model, base_url):
            logger.info(
                "AI provider '%s' model '%s' does not support image input, sending text-only request",
                provider,
                resolved_model,
            )
            effective_image_bytes = None

        try:
            if provider == "gemini":
                analysis = await _call_gemini(api_key, base_url, resolved_model, message, effective_image_bytes, proxy)
            elif provider == "minimax" and "/anthropic" in normalized_base_url:
                analysis = await _call_claude(api_key, base_url, resolved_model, message, effective_image_bytes, proxy)
            elif provider == "claude":
                analysis = await _call_claude(api_key, base_url, resolved_model, message, effective_image_bytes, proxy)
            else:
                analysis = await _call_openai_compatible(
                    api_key,
                    base_url,
                    resolved_model,
                    message,
                    effective_image_bytes,
                    proxy,
                )

            return {
                "analysis": analysis,
                "provider": provider,
                "model": resolved_model,
                "provider_priority": priority,
            }
        except Exception as exc:
            logger.warning(f"AI provider '{provider}' failed, trying next provider: {exc}")
            errors.append(f"{provider}: {exc}")

    raise RuntimeError("All AI providers failed: " + " | ".join(errors))
