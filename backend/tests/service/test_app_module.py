from fastapi import FastAPI
from types import SimpleNamespace

import pytest


def test_service_app_exports_fastapi_app():
    """Test that the main API module exports a FastAPI app."""
    from api import app

    assert isinstance(app, FastAPI)


@pytest.mark.asyncio
async def test_app_lifespan_bootstraps_system_admin(monkeypatch):
    from api import app_lifespan

    monkeypatch.setattr("api.ensure_resource_dirs", lambda: None)
    monkeypatch.setattr("api.ensure_database_dir", lambda: None)
    monkeypatch.setattr("api.bootstrap_system_admin_from_env", lambda: {"email": "admin@example.com"})
    monkeypatch.setattr("api.get_worker_pool", lambda: SimpleNamespace(is_enabled=False))
    monkeypatch.setattr("api.shutdown_worker_pool", lambda: None)
    monkeypatch.setattr("src.service.live_engine.set_main_event_loop", lambda loop: None)

    async with app_lifespan(FastAPI()):
        pass

