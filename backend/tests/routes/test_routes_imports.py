import importlib


def test_routes_modules_import_and_expose_router():
    modules = [
        "src.routes.auth_routes",
        "src.routes.ai_routes",
        "src.routes.backtest_routes",
        "src.routes.frontend_routes",
        "src.routes.live_routes",
        "src.routes.market_data_routes",
        "src.routes.portfolio_routes",
        "src.routes.report_routes",
        "src.routes.settings_routes",
        "src.routes.site_config_routes",
        "src.routes.strategy_routes",
        "src.routes.task_routes",
        "src.routes.walkforward_routes",
        "src.routes.websocket_routes",
    ]

    for name in modules:
        mod = importlib.import_module(name)
        if name.endswith("frontend_routes"):
            assert hasattr(mod, "mount_frontend")
        else:
            assert hasattr(mod, "router")
            assert len(getattr(mod, "router").routes) >= 1

