from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backtest_engine import ensure_resource_files
from routes.api_routes import router as api_router
from routes.ai_routes import router as ai_router
from routes.frontend_routes import mount_frontend
from auth import get_logto_config

ensure_resource_files()

app = FastAPI()

# Initialize Logto configuration on startup
@app.on_event("startup")
async def startup_event():
    """Initialize authentication configuration"""
    try:
        config = get_logto_config()
        print(f"Logto authentication initialized: {config.endpoint}")
    except ValueError as e:
        print(f"Warning: Logto configuration not set - {e}")
        print("Authentication is disabled. Please configure LOGTO_* environment variables.")

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
