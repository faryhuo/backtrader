import types


def test_backend_main_uses_uvicorn_server(monkeypatch):
    """Test that main() runs the server using Uvicorn."""
    captured = {}

    def stub_uvicorn_run(app, host, port, log_level, access_log):
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port
        captured["log_level"] = log_level
        captured["access_log"] = access_log
        captured["ran"] = True

    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "8123")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    import uvicorn
    import main as main_module

    monkeypatch.setattr(uvicorn, "run", stub_uvicorn_run)
    main_module.main()

    assert captured["ran"] is True
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 8123
    assert captured["log_level"] == "info"

