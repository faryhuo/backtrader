from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backtest_engine import ensure_resource_files
from routes.api_routes import router as api_router
from routes.ai_routes import router as ai_router
from routes.frontend_routes import mount_frontend
from auth import get_logto_config

ensure_resource_files()

app = FastAPI()

# Initialize Logto M2M configuration on startup
@app.on_event("startup")
async def startup_event():
    """Initialize M2M authentication configuration"""
    try:
        config = get_logto_config()
        print(f"Logto M2M authentication initialized: {config.endpoint}")
        print(f"API Resource: {config.resource}")
        print("M2M authentication is ready for backend-to-backend API calls")
    except ValueError as e:
        print(f"Warning: Logto M2M configuration not set - {e}")
        print("M2M authentication is disabled. Please configure LOGTO_M2M_* environment variables.")

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
