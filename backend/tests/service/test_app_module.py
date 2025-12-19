from fastapi import FastAPI


def test_service_app_exports_fastapi_app():
    from src.service.app import app

    assert isinstance(app, FastAPI)

