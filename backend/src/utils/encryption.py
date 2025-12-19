"""
Encryption utilities for securing sensitive credentials in the database.

Uses Fernet symmetric encryption (AES-128 in CBC mode with HMAC authentication).
Encryption key must be set in ENCRYPTION_KEY environment variable.

Example usage:
    from src.utils.encryption import encrypt_value, decrypt_value

    # Encrypt a value before storing
    encrypted = encrypt_value("my-api-key-12345")

    # Decrypt when retrieving
    plaintext = decrypt_value(encrypted)
"""

from cryptography.fernet import Fernet, InvalidToken
import os
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_encryption_key() -> bytes:
    """
    Get encryption key from environment variable.

    Returns:
        bytes: The encryption key (32-byte base64 encoded)

    Raises:
        ValueError: If ENCRYPTION_KEY is not set or invalid

    Note:
        Generate a new key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError(
            "ENCRYPTION_KEY not set in environment. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

    try:
        # Validate it's proper base64 and correct length
        decoded = base64.b64decode(key)
        if len(decoded) != 32:
            raise ValueError("ENCRYPTION_KEY must be 32 bytes when decoded")
        return key.encode() if isinstance(key, str) else key
    except Exception as e:
        raise ValueError(f"Invalid ENCRYPTION_KEY format: {e}")


def encrypt_value(plaintext: Optional[str]) -> Optional[str]:
    """
    Encrypt a credential value for secure storage.

    Args:
        plaintext: The value to encrypt (e.g., API key, password)

    Returns:
        str: The encrypted value (base64 encoded), or None if input is None/empty

    Example:
        >>> encrypted = encrypt_value("sk-my-secret-api-key")
        >>> print(encrypted)
        gAAAAABh... (base64 encoded ciphertext)
    """
    if not plaintext:
        return None

    try:
        f = Fernet(get_encryption_key())
        encrypted_bytes = f.encrypt(plaintext.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise ValueError(f"Failed to encrypt value: {e}")


def decrypt_value(ciphertext: Optional[str]) -> Optional[str]:
    """
    Decrypt a credential value from storage.

    Args:
        ciphertext: The encrypted value (base64 encoded)

    Returns:
        str: The decrypted plaintext value, or None if input is None/empty

    Raises:
        ValueError: If decryption fails (wrong key, corrupted data, etc.)

    Example:
        >>> plaintext = decrypt_value("gAAAAABh...")
        >>> print(plaintext)
        sk-my-secret-api-key
    """
    if not ciphertext:
        return None

    try:
        f = Fernet(get_encryption_key())
        decrypted_bytes = f.decrypt(ciphertext.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except InvalidToken:
        logger.error("Decryption failed: Invalid token (wrong key or corrupted data)")
        raise ValueError("Failed to decrypt value: Invalid encryption key or corrupted data")
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise ValueError(f"Failed to decrypt value: {e}")


def mask_credential(value: Optional[str]) -> str:
    """
    Mask sensitive credential values for display purposes.

    Shows prefix (up to first dash), masks middle, shows last few characters.
    For API keys like 'sk-123456789', returns 'sk-xxxxxxx-789'

    Args:
        value: The credential value to mask

    Returns:
        str: Masked value suitable for display

    Examples:
        >>> mask_credential("sk-abc123def456ghi789")
        'sk-xxxxxxxxxxx-789'

        >>> mask_credential("short")
        'xxxxx'

        >>> mask_credential(None)
        ''
    """
    if not value:
        return ""

    if len(value) < 8:
        return "x" * len(value)

    # Handle keys with prefix (like sk-, pk-, etc.)
    if '-' in value and value.index('-') < 5:
        prefix_end = value.index('-') + 1
        prefix = value[:prefix_end]
        rest = value[prefix_end:]

        if len(rest) <= 6:
            return prefix + "x" * len(rest)
        else:
            # Show last 3 characters
            return prefix + "x" * (len(rest) - 3) + "-" + rest[-3:]

    # For values without prefix, show first 4 and last 3
    return value[:4] + "x" * (len(value) - 7) + value[-3:]


def is_encryption_enabled() -> bool:
    """
    Check if encryption is properly configured.

    Returns:
        bool: True if ENCRYPTION_KEY is set and valid, False otherwise
    """
    try:
        get_encryption_key()
        return True
    except ValueError:
        return False


def generate_encryption_key() -> str:
    """
    Generate a new encryption key.

    Returns:
        str: A new Fernet encryption key (32-byte base64 encoded)

    Note:
        This is a utility function for initial setup. The key should be
        stored in the ENCRYPTION_KEY environment variable and kept secure.
    """
    return Fernet.generate_key().decode('utf-8')


if __name__ == "__main__":
    # Utility script for generating encryption keys
    print("Generated new encryption key:")
    print(generate_encryption_key())
    print("\nAdd this to your .env file as:")
    print("ENCRYPTION_KEY=<the-key-above>")
