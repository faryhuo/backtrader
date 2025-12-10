from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.config.settings import ASSETS_DIR, FRONTEND_DIR, IMAGES_DIR, ensure_resource_dirs

frontend_router = APIRouter()
INDEX_HTML = FRONTEND_DIR / "index.html"


@frontend_router.get("/", response_class=FileResponse)
def read_root():
    if INDEX_HTML.exists():
        return FileResponse(INDEX_HTML)
    return JSONResponse({"status": "ok", "message": "Backtrader API is running (no frontend build found)"})


# Catch-all route for SPA - must be last
@frontend_router.get("/{full_path:path}", response_class=FileResponse)
def serve_spa(full_path: str):
    """Serve index.html for all non-API routes to support client-side routing"""
    if INDEX_HTML.exists():
        return FileResponse(INDEX_HTML)
    return JSONResponse({"status": "error", "message": "Frontend not built"})


def mount_frontend(app: FastAPI):
    ensure_resource_dirs()
    FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")
    if ASSETS_DIR.is_dir():
        app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
    app.include_router(frontend_router)
