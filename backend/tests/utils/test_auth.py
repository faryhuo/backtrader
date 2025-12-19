import types

import pytest
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError

from src.utils import auth


def test_get_auth_token_missing_header():
    with pytest.raises(auth.AuthError) as excinfo:
        auth.get_auth_token(None)
    assert excinfo.value.detail["code"] == "auth.authorization_header_missing"


def test_get_auth_token_wrong_scheme():
    credentials = types.SimpleNamespace(scheme="Basic", credentials="x")
    with pytest.raises(auth.AuthError) as excinfo:
        auth.get_auth_token(credentials)
    assert excinfo.value.detail["code"] == "auth.authorization_token_type_not_supported"


def test_get_auth_token_empty_token():
    credentials = types.SimpleNamespace(scheme="Bearer", credentials="")
    with pytest.raises(auth.AuthError) as excinfo:
        auth.get_auth_token(credentials)
    assert excinfo.value.detail["code"] == "auth.authorization_token_invalid_format"


def test_get_auth_token_success():
    credentials = types.SimpleNamespace(scheme="Bearer", credentials="token")
    assert auth.get_auth_token(credentials) == "token"


def test_validate_scopes_allows_when_not_configured(monkeypatch):
    monkeypatch.setattr(auth, "get_logto_config", lambda: {"required_scopes": ""})
    auth.validate_scopes({"scope": ""})


def test_validate_scopes_requires_configured_scopes(monkeypatch):
    monkeypatch.setattr(auth, "get_logto_config", lambda: {"required_scopes": "read write"})
    with pytest.raises(auth.AuthError) as excinfo:
        auth.validate_scopes({"scope": "read"})
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail["code"] == "auth.insufficient_scope"


def test_get_signing_key_finds_matching_kid(monkeypatch):
    monkeypatch.setattr(auth.jwt, "get_unverified_header", lambda token: {"kid": "k1"})
    monkeypatch.setattr(auth, "fetch_jwks", lambda: {"keys": [{"kid": "k1", "kty": "RSA"}]})
    assert auth.get_signing_key("t") == {"kid": "k1", "kty": "RSA"}


def test_get_signing_key_missing_kid(monkeypatch):
    monkeypatch.setattr(auth.jwt, "get_unverified_header", lambda token: {})
    with pytest.raises(auth.AuthError) as excinfo:
        auth.get_signing_key("t")
    assert excinfo.value.detail["code"] == "auth.invalid_token"


@pytest.mark.parametrize(
    "exc,code",
    [
        (ExpiredSignatureError("expired"), "auth.token_expired"),
        (JWTClaimsError("bad claims"), "auth.invalid_claims"),
        (JWTError("bad token"), "auth.invalid_token"),
    ],
)
def test_verify_token_maps_jose_exceptions(monkeypatch, exc, code):
    monkeypatch.setattr(auth, "get_logto_config", lambda: {"audience": "a", "issuer": "i", "required_scopes": ""})
    monkeypatch.setattr(auth, "get_signing_key", lambda token: {"kid": "k1"})
    monkeypatch.setattr(auth.jwt, "get_unverified_header", lambda token: {"alg": "RS256"})
    monkeypatch.setattr(auth.jwt, "decode", lambda *args, **kwargs: (_ for _ in ()).throw(exc))

    with pytest.raises(auth.AuthError) as excinfo:
        auth.verify_token("t")
    assert excinfo.value.detail["code"] == code

