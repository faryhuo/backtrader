from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import (
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_ORIGINS,
    CORS_ALLOW_ORIGIN_REGEX,
    DEBUG,
    ensure_database_dir,
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
from src.routes.task_routes import router as task_router
from src.routes.site_config_routes import router as site_config_router
from src.routes.report_routes import router as report_router
from src.routes.setup_routes import router as setup_router
from src.routes.frontend_routes import mount_frontend
from src.utils.exception_handlers import create_exception_handlers
from src.utils.request_context import RequestContextMiddleware
from src.service.worker.worker_pool import get_worker_pool, shutdown_worker_pool

prefix = "/api"


@asynccontextmanager
async def app_lifespan(_app: FastAPI):
    """
    Application startup handler - Initialize resources and warmup worker pool.

    1. Ensures required resource directories exist
    2. Ensures database directory exists
    3. Pre-initializes the worker pool to eliminate cold start delays
    4. Captures the main asyncio event loop for live trading WebSocket broadcasts
    """
    import logging
    logger = logging.getLogger(__name__)

    # Capture the main event loop for live trading WebSocket broadcasts
    from src.service.live_engine import set_main_event_loop
    set_main_event_loop(asyncio.get_event_loop())
    logger.info("Main event loop captured for live trading")
    
    # Ensure resource directories exist
    try:
        logger.info("Ensuring resource directories exist...")
        ensure_resource_dirs()
        logger.info("Resource directories initialized successfully")
    except Exception as e:
        logger.error(f"Failed to create resource directories: {e}")
        raise RuntimeError(f"Application startup failed: Cannot create required directories. {e}")

    # Ensure database directory exists
    try:
        logger.info("Ensuring database directory exists...")
        ensure_database_dir()
        logger.info("Database directory initialized successfully")
    except Exception as e:
        logger.error(f"Failed to create database directory: {e}")
        raise RuntimeError(f"Application startup failed: Cannot create database directory. {e}")

    try:
        logger.info("Warming up worker pool...")
        pool = get_worker_pool()
        
        if pool.is_enabled:
            pool.start()
            logger.info(f"Worker pool warmed up: {pool.get_stats()}")
        else:
            logger.info("Worker pool disabled, skipping warmup")
    except Exception as e:
        logger.error(f"Worker pool warmup failed: {e}")
        # Don't fail startup if worker pool fails
    try:
        yield
    finally:
        """
        Application shutdown handler - Cleanup worker pool.

        Gracefully shutdown worker processes on app shutdown.
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            logger.info("Shutting down worker pool...")
            shutdown_worker_pool()
            logger.info("Worker pool shutdown complete")
        except Exception as e:
            logger.error(f"Worker pool shutdown failed: {e}")


app = FastAPI(lifespan=app_lifespan)

# Request context middleware (must be added first for proper request_id propagation)
app.add_middleware(RequestContextMiddleware)

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

app.include_router(strategy_router, prefix=prefix)
app.include_router(backtest_router, prefix=prefix)
app.include_router(market_data_router, prefix=prefix)
app.include_router(ai_router, prefix=prefix)
app.include_router(live_router, prefix=prefix)
app.include_router(portfolio_router, prefix=prefix)
app.include_router(settings_router, prefix=prefix)
app.include_router(walkforward_router, prefix=prefix) 
app.include_router(websocket_router)  # WebSocket routes (no prefix)
app.include_router(task_router, prefix=prefix)
app.include_router(site_config_router, prefix=prefix)  # Site config (public, no auth)
app.include_router(report_router, prefix=prefix)  
app.include_router(setup_router, prefix=prefix)
mount_frontend(app)

__all__ = ["app"]
