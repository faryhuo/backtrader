"""
Share Token Utilities - HMAC-based signed URL generation for report sharing.

Provides secure, time-limited share tokens without external dependencies.
Token format: {report_id}:{expiry_timestamp}:{hmac_signature}
"""

import hmac
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple

from src.config.settings import REPORT_SHARE_SECRET


def generate_share_token(report_id: str, expires_at: datetime) -> str:
    """
    Generate an HMAC-signed share token.

    Args:
        report_id: The report UUID to share
        expires_at: When the share link should expire

    Returns:
        Token string in format: {report_id}:{expiry_timestamp}:{signature}
    """
    expiry_ts = int(expires_at.timestamp())
    message = f"{report_id}:{expiry_ts}"

    signature = hmac.new(
        REPORT_SHARE_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()[:16]  # Use first 16 chars for shorter URLs

    return f"{report_id}:{expiry_ts}:{signature}"


def verify_share_token(token: str) -> Optional[str]:
    """
    Verify a share token and return the report_id if valid.

    Args:
        token: The share token to verify

    Returns:
        The report_id if token is valid and not expired, None otherwise
    """
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None

        report_id, expiry_ts_str, signature = parts

        # Validate expiry timestamp format
        try:
            expiry_ts = int(expiry_ts_str)
        except ValueError:
            return None

        # Check expiry
        if expiry_ts < time.time():
            return None

        # Verify signature
        message = f"{report_id}:{expiry_ts}"
        expected_signature = hmac.new(
            REPORT_SHARE_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:16]

        if not hmac.compare_digest(signature, expected_signature):
            return None

        return report_id

    except Exception:
        return None


def parse_share_token(token: str) -> Optional[Tuple[str, datetime]]:
    """
    Parse a share token and return report_id and expiry datetime.

    Does not validate signature - use verify_share_token for security checks.

    Args:
        token: The share token to parse

    Returns:
        Tuple of (report_id, expires_at) or None if invalid format
    """
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None

        report_id, expiry_ts_str, _ = parts
        expiry_ts = int(expiry_ts_str)
        expires_at = datetime.fromtimestamp(expiry_ts)

        return report_id, expires_at

    except Exception:
        return None


def generate_random_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Useful for one-time tokens or additional entropy.

    Args:
        length: Token length in characters

    Returns:
        Random hex string
    """
    return secrets.token_hex(length // 2)


def create_share_link(base_url: str, report_id: str, expires_in_hours: int = 168) -> Tuple[str, datetime]:
    """
    Create a complete share link with token.

    Args:
        base_url: The base URL of the application (e.g., "https://example.com")
        report_id: The report UUID to share
        expires_in_hours: Hours until link expires (default 7 days)

    Returns:
        Tuple of (share_url, expires_at)
    """
    expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    token = generate_share_token(report_id, expires_at)

    # Remove trailing slash from base_url if present
    base_url = base_url.rstrip("/")
    share_url = f"{base_url}/report/shared/{token}"

    return share_url, expires_at


__all__ = [
    "generate_share_token",
    "verify_share_token",
    "parse_share_token",
    "generate_random_token",
    "create_share_link",
]
