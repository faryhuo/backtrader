import os
import pytest
from cryptography.fernet import Fernet

from src.utils.encryption import (
    decrypt_value,
    encrypt_value,
    is_encryption_enabled,
    mask_credential,
)


@pytest.fixture
def encryption_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY", key)
    return key


def test_encrypt_decrypt_round_trip(encryption_key):
    plaintext = "my-secret-value"

    encrypted = encrypt_value(plaintext)
    assert encrypted and encrypted != plaintext

    decrypted = decrypt_value(encrypted)
    assert decrypted == plaintext


def test_decrypt_with_wrong_key_raises(monkeypatch, encryption_key):
    encrypted = encrypt_value("another-secret")
    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())

    with pytest.raises(ValueError):
        decrypt_value(encrypted)


def test_invalid_encryption_key(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY", "invalid-key")

    with pytest.raises(ValueError):
        encrypt_value("should-fail")

    assert is_encryption_enabled() is False


def test_encrypt_decrypt_handles_empty(encryption_key):
    assert encrypt_value("") is None
    assert encrypt_value(None) is None
    assert decrypt_value("") is None
    assert decrypt_value(None) is None


def test_is_encryption_enabled(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    assert is_encryption_enabled() is True

    monkeypatch.setenv("ENCRYPTION_KEY", "bad-key")
    assert is_encryption_enabled() is False


def test_mask_credential_variants(encryption_key):
    assert mask_credential("sk-abc123def456ghi789") == "sk-xxxxxxxxxxxxxxx-789"
    assert mask_credential("short") == "xxxxx"
    assert mask_credential(None) == ""

