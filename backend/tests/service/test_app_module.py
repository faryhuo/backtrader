from fastapi import FastAPI


def test_service_app_exports_fastapi_app():
    """Test that the main API module exports a FastAPI app."""
    from api import app

    assert isinstance(app, FastAPI)

