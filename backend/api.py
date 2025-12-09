from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backtest_engine import ensure_resource_files
from routes.api_routes import router as api_router
from routes.frontend_routes import mount_frontend

ensure_resource_files()

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
mount_frontend(app)
