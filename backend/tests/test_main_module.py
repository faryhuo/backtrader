import types


def test_backend_main_creates_daphne_server(monkeypatch):
    captured = {}

    class StubServer:
        def __init__(self, application, endpoints, signal_handlers, verbosity):
            captured["application"] = application
            captured["endpoints"] = endpoints
            captured["signal_handlers"] = signal_handlers
            captured["verbosity"] = verbosity

        def run(self):
            captured["ran"] = True

    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "8123")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    import main as main_module

    monkeypatch.setattr(main_module, "Server", StubServer)
    main_module.main()

    assert captured["ran"] is True
    assert captured["endpoints"] == ["tcp:port=8123:interface=127.0.0.1"]

