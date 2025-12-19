from fastapi import FastAPI


def test_backend_api_exports_app():
    from api import app

    assert isinstance(app, FastAPI)

