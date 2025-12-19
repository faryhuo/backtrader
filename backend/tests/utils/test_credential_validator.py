import sys
import types
import asyncio

import pytest

from src.utils.credential_validator import (
    validate_ccxt_credentials,
    validate_ccxt_credentials_async,
    validate_logto_config,
    validate_openai_key,
    validate_proxy,
)


def test_validate_openai_key_success(monkeypatch):
    class FakeModels:
        def list(self):
            return types.SimpleNamespace(data=[object(), object(), object()])

    class FakeOpenAI:
        def __init__(self, api_key, base_url, timeout):
            self.api_key = api_key
            self.base_url = base_url
            self.timeout = timeout
            self.models = FakeModels()

    fake_openai_module = types.SimpleNamespace(OpenAI=FakeOpenAI)
    monkeypatch.setitem(sys.modules, "openai", fake_openai_module)

    ok, msg = validate_openai_key("sk-test", "https://example.com/v1")
    assert ok is True
    assert "3 models" in msg


@pytest.mark.parametrize(
    "error,expected",
    [
        (Exception("401 Unauthorized"), "Invalid API key"),
        (Exception("403 Forbidden"), "lacks permissions"),
        (Exception("timeout"), "Connection timeout"),
        (Exception("connection reset"), "Connection error"),
    ],
)
def test_validate_openai_key_error_mapping(monkeypatch, error, expected):
    class FakeOpenAI:
        def __init__(self, api_key, base_url, timeout):
            self.models = types.SimpleNamespace(list=lambda: (_ for _ in ()).throw(error))

    fake_openai_module = types.SimpleNamespace(OpenAI=FakeOpenAI)
    monkeypatch.setitem(sys.modules, "openai", fake_openai_module)

    ok, msg = validate_openai_key("sk-test", "https://example.com/v1")
    assert ok is False
    assert expected in msg


def test_validate_openai_key_empty():
    ok, msg = validate_openai_key("")
    assert ok is False
    assert "empty" in msg


def make_fake_ccxt(monkeypatch, *, balance_total=None, raise_exc=None, sandbox_supported=True):
    class AuthenticationError(Exception):
        pass

    class PermissionDenied(Exception):
        pass

    class InvalidNonce(Exception):
        pass

    class NetworkError(Exception):
        pass

    class ExchangeError(Exception):
        pass

    class FakeExchange:
        def __init__(self, config):
            self.config = config
            self.sandbox_enabled = False

        def set_sandbox_mode(self, enabled: bool):
            if not sandbox_supported:
                raise AttributeError("no set_sandbox_mode")
            self.sandbox_enabled = enabled

        def fetch_balance(self):
            if raise_exc:
                raise raise_exc
            return {"total": balance_total or {}}

    fake_ccxt = types.SimpleNamespace(
        AuthenticationError=AuthenticationError,
        PermissionDenied=PermissionDenied,
        InvalidNonce=InvalidNonce,
        NetworkError=NetworkError,
        ExchangeError=ExchangeError,
        binance=FakeExchange,
    )

    monkeypatch.setitem(sys.modules, "ccxt", fake_ccxt)
    return fake_ccxt, FakeExchange


def test_validate_ccxt_credentials_success(monkeypatch):
    make_fake_ccxt(monkeypatch, balance_total={"USDT": 1.0, "BTC": 0.0})

    ok, msg = validate_ccxt_credentials("binance", "paper", "k", "s")
    assert ok is True
    assert "Connected to binance (paper)" in msg


def test_validate_ccxt_credentials_unsupported_exchange(monkeypatch):
    make_fake_ccxt(monkeypatch)
    ok, msg = validate_ccxt_credentials("unknown", "paper", "k", "s")
    assert ok is False
    assert "Unsupported exchange" in msg


def test_validate_ccxt_credentials_auth_error(monkeypatch):
    fake_ccxt, fake_exchange = make_fake_ccxt(monkeypatch)
    monkeypatch.setattr(
        fake_exchange,
        "fetch_balance",
        lambda self: (_ for _ in ()).throw(fake_ccxt.AuthenticationError("bad")),
    )

    ok, msg = validate_ccxt_credentials("binance", "live", "k", "s")
    assert ok is False
    assert "Authentication failed" in msg


def test_validate_ccxt_credentials_empty_inputs():
    ok, msg = validate_ccxt_credentials("binance", "paper", "", "")
    assert ok is False
    assert "empty" in msg


def test_validate_ccxt_credentials_async_success(monkeypatch):
    class FakeExchangeAsync:
        def __init__(self, config):
            self.config = config
            self.sandbox_enabled = False

        def set_sandbox_mode(self, enabled: bool):
            self.sandbox_enabled = enabled

        async def fetch_balance(self):
            return {"total": {"USDT": 2.0, "BTC": 0.0}}

        async def close(self):
            return None

    fake_ccxt_async = types.SimpleNamespace(binance=FakeExchangeAsync)
    fake_ccxt_pkg = types.SimpleNamespace(async_support=fake_ccxt_async)
    monkeypatch.setitem(sys.modules, "ccxt", fake_ccxt_pkg)
    monkeypatch.setitem(sys.modules, "ccxt.async_support", fake_ccxt_async)

    ok, msg = asyncio.run(validate_ccxt_credentials_async("binance", "paper", "k", "s"))
    assert ok is True
    assert "Connected to binance (paper)" in msg


def test_validate_logto_config_requests(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {"keys": [{}, {}]}

    def fake_get(url, timeout):
        assert url == "https://issuer.example.com/.well-known/jwks.json"
        return FakeResponse()

    fake_requests = types.SimpleNamespace(get=fake_get, exceptions=types.SimpleNamespace(Timeout=Exception, ConnectionError=Exception))
    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    ok, msg = validate_logto_config("https://issuer.example.com", "https://issuer.example.com/.well-known/jwks.json")
    assert ok is True
    assert "2 keys" in msg


def test_validate_proxy_requests(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {"origin": "1.2.3.4"}

    def fake_get(url, proxies, timeout):
        assert url == "https://httpbin.org/ip"
        assert proxies["http"] == "http://proxy:8080"
        assert proxies["https"] == "http://proxy:8080"
        return FakeResponse()

    fake_requests = types.SimpleNamespace(
        get=fake_get,
        exceptions=types.SimpleNamespace(ProxyError=Exception, Timeout=Exception, ConnectionError=Exception),
    )
    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    ok, msg = validate_proxy("http://proxy:8080")
    assert ok is True
    assert "origin IP: 1.2.3.4" in msg
