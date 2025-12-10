from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import ensure_resource_dirs
from src.service.routes.ai_routes import router as ai_router
from src.service.routes.api_routes import router as api_router
from src.service.routes.frontend_routes import mount_frontend

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
mount_frontend(app)
