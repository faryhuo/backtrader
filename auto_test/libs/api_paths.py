"""
API Path Constants for E2E Testing.

Centralized API endpoint definitions to ensure tests match backend routes.
All paths should NOT include the '/api' prefix as that's added by the backend router.
"""

# ========== Strategy Endpoints ==========
# Note: /strategies is for listing, /strategy is for CRUD
STRATEGIES_LIST = "/api/strategies"  # GET - list all strategies
STRATEGY = "/api/strategy"           # GET/POST - get/save strategy

def strategy_params(name: str) -> str:
    """Get strategy parameters endpoint."""
    return f"/api/strategy/{name}/params"

def strategy_versions(name: str) -> str:
    """List strategy versions endpoint."""
    return f"/api/strategy/{name}/versions"

def strategy_version(name: str, version: int) -> str:
    """Get specific strategy version endpoint."""
    return f"/api/strategy/{name}/versions/{version}"

def strategy_version_latest(name: str) -> str:
    """Get latest strategy version endpoint."""
    return f"/api/strategy/{name}/versions/latest"

def strategy_version_compare(name: str) -> str:
    """Compare strategy versions endpoint."""
    return f"/api/strategy/{name}/versions/compare"

def strategy_version_rollback(name: str, version: int) -> str:
    """Rollback to strategy version endpoint."""
    return f"/api/strategy/{name}/versions/{version}/rollback"


# ========== Template Endpoints ==========
TEMPLATES_LIST = "/api/templates"
TEMPLATES_IMPORT = "/api/templates/import"

def template_detail(template_id: str) -> str:
    """Get template detail endpoint."""
    return f"/api/templates/{template_id}"


# ========== Backtest Endpoints ==========
BACKTEST = "/api/backtest"
BACKTEST_HISTORY = "/api/backtest/history"

def backtest_detail(backtest_id: str) -> str:
    """Get backtest detail endpoint."""
    return f"/api/backtest/history/{backtest_id}"

def backtest_ai_analysis(backtest_id: str) -> str:
    """Update AI analysis for backtest endpoint."""
    return f"/api/backtest/history/{backtest_id}/ai-analysis"

def backtest_deep_analysis(backtest_id: str) -> str:
    """Get/compute deep analysis for backtest endpoint."""
    return f"/api/backtest/history/{backtest_id}/deep-analysis"


# ========== Task Endpoints ==========
TASKS = "/api/tasks"
TASKS_STATS = "/api/tasks/stats"

def task_detail(task_id: str) -> str:
    """Get task detail endpoint."""
    return f"/api/tasks/{task_id}"

def task_cancel(task_id: str) -> str:
    """Cancel task endpoint."""
    return f"/api/tasks/{task_id}/cancel"

def task_retry(task_id: str) -> str:
    """Retry task endpoint."""
    return f"/api/tasks/{task_id}/retry"


# ========== Market Data Endpoints ==========
DATA = "/api/data"  # Legacy endpoint
ANALYZE = "/api/analyze"

def ticker_info(ticker: str) -> str:
    """Get ticker info endpoint."""
    return f"/api/ticker/{ticker}/info"

def ticker_prices(ticker: str) -> str:
    """Get ticker prices endpoint."""
    return f"/api/ticker/{ticker}/prices"


# ========== Cache Endpoints ==========
CACHE_STATS = "/api/cache/stats"
CACHE_TICKERS = "/api/cache/tickers"
CACHE_WARMUP = "/api/cache/warmup"
CACHE_CLEANUP = "/api/cache/cleanup"

def cache_ticker(ticker: str) -> str:
    """Get/delete cache for specific ticker endpoint."""
    return f"/api/cache/{ticker}"


# ========== Resample Endpoints ==========
RESAMPLE = "/api/resample"
RESAMPLE_TIMEFRAMES = "/api/resample/timeframes"

def resample_targets(source_timeframe: str) -> str:
    """Get valid target timeframes for source endpoint."""
    return f"/api/resample/targets/{source_timeframe}"


# ========== Settings Endpoints ==========
SETTINGS = "/api/settings"
SETTINGS_RESET = "/api/settings/reset"
SETTINGS_CREDENTIALS = "/api/settings/credentials"
SETTINGS_CREDENTIALS_CCXT = "/api/settings/credentials/ccxt"
SETTINGS_CREDENTIALS_TEST = "/api/settings/credentials/test"
SETTINGS_DATA_SOURCE = "/api/settings/data-source"
SETTINGS_DATA_SOURCE_RESET = "/api/settings/data-source/reset"

def settings_credential_reset(credential_key: str) -> str:
    """Reset specific credential endpoint."""
    return f"/api/settings/credentials/{credential_key}"


# ========== Portfolio Endpoints ==========
# Portfolio routes have /api/portfolio prefix
PORTFOLIO = "/api/portfolio/backtest"
PORTFOLIO_HISTORY = "/api/portfolio/history"

def portfolio_detail(portfolio_id: str) -> str:
    """Get portfolio detail endpoint."""
    return f"/api/portfolio/{portfolio_id}"

def portfolio_delete(portfolio_id: str) -> str:
    """Delete portfolio endpoint."""
    return f"/api/portfolio/{portfolio_id}"


# ========== Walk-forward Endpoints ==========
# Walkforward routes are at /api/walkforward
WALKFORWARD = "/api/walkforward"
WALKFORWARD_START = "/api/walkforward/start"
WALKFORWARD_LIST = "/api/walkforward/list"

def walkforward_detail(optimization_id: str) -> str:
    """Get walkforward detail endpoint."""
    return f"/api/walkforward/{optimization_id}"

def walkforward_status(optimization_id: str) -> str:
    """Get walkforward status endpoint."""
    return f"/api/walkforward/{optimization_id}/status"

def walkforward_delete(optimization_id: str) -> str:
    """Delete walkforward optimization endpoint."""
    return f"/api/walkforward/{optimization_id}"


# ========== Live Trading Endpoints ==========
LIVE_START = "/api/live/start"
LIVE_STOP = "/api/live/stop"
LIVE_SESSIONS = "/api/live/sessions"
LIVE_EXCHANGES = "/api/live/exchanges"
LIVE_HEALTH = "/api/live/health"

def live_session(session_id: str) -> str:
    """Get live session detail endpoint."""
    return f"/api/live/status/{session_id}"

def live_orders(session_id: str) -> str:
    """Get live session orders endpoint."""
    return f"/api/live/orders/{session_id}"
