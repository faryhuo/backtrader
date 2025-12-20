from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import (
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_ORIGINS,
    CORS_ALLOW_ORIGIN_REGEX,
    DEBUG,
    ensure_resource_dirs,
)
from src.routes.ai_routes import router as ai_router
from src.routes.strategy_routes import router as strategy_router
from src.routes.backtest_routes import router as backtest_router
from src.routes.market_data_routes import router as market_data_router
from src.routes.live_routes import router as live_router
from src.routes.portfolio_routes import router as portfolio_router
from src.routes.settings_routes import router as settings_router
from src.routes.walkforward_routes import router as walkforward_router
from src.routes.websocket_routes import router as websocket_router
from src.routes.frontend_routes import mount_frontend
from src.utils.exception_handlers import create_exception_handlers

ensure_resource_dirs()

app = FastAPI()

# Register global exception handlers
for exc_class, handler in create_exception_handlers(debug=DEBUG).items():
    app.add_exception_handler(exc_class, handler)

cors_allow_credentials = CORS_ALLOW_CREDENTIALS
if cors_allow_credentials and ("*" in CORS_ALLOW_ORIGINS or CORS_ALLOW_ORIGIN_REGEX == ".*"):
    cors_allow_credentials = False

# Configure CORS via environment (safe by default).
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_origin_regex=CORS_ALLOW_ORIGIN_REGEX,
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(strategy_router, prefix="/api")
app.include_router(backtest_router, prefix="/api")
app.include_router(market_data_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(live_router, prefix="/api")
app.include_router(portfolio_router)  # Portfolio routes (includes /api/portfolio prefix)
app.include_router(settings_router, prefix="/api")
app.include_router(walkforward_router)  # Walk-forward routes (includes /api prefix)
app.include_router(websocket_router)  # WebSocket routes (no prefix)
mount_frontend(app)

__all__ = ["app"]
