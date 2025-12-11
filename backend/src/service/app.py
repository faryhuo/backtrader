import warnings

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import ensure_resource_dirs
from src.routes.ai_routes import router as ai_router
from src.routes.api_routes import router as api_router
from src.routes.live_routes import router as live_router
from src.routes.websocket_routes import router as websocket_router
from src.routes.frontend_routes import mount_frontend

# Suppress noisy protobuf gencode/runtime mismatch warnings emitted by third-party
# generated stubs. Keep one notice at most to avoid log spam.
warnings.filterwarnings(
    "once",
    message=r"Protobuf gencode version .*runtime version .*",
    category=UserWarning,
    module=r"google\.protobuf\.runtime_version"
)

ensure_resource_dirs()

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(live_router, prefix="/api")
app.include_router(websocket_router)  # WebSocket routes (no prefix)
mount_frontend(app)
