"""
Live Trading REST API Routes — Binance Spot only.

Endpoints:
- POST /api/live/start                            — Start new trading session
- POST /api/live/stop                             — Stop running session
- POST /api/live/orders/{session_id}/cancel/{oid} — Cancel open order
- GET  /api/live/status/{session_id}              — Get session status
- GET  /api/live/sessions                         — List sessions
- GET  /api/live/orders/{session_id}              — Get session orders
- GET  /api/live/ticker/{session_id}              — Get current price
- GET  /api/live/health                           — Health check
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.config.settings import LIVE_TRADING_ENABLED
from src.routes.common.auth_dependencies import get_optional_user_id
from src.service import live_engine
from src.service.live_engine import LiveTradingError
from src.service.session_manager import SessionStatus, get_session_manager
from src.utils.config_loader import (
    list_enabled_exchanges,
    load_broker_config,
    validate_symbol,
    validate_timeframe,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ──────────────────────────── Request / Response models ────────────────────────────


class StartLiveRequest(BaseModel):
    """Start a Binance Spot trading session."""
    strategy_name: str = Field(..., description="Strategy file name (without .py)")
    symbol: str = Field(..., description="Trading pair (e.g., 'BTC/USDT')")
    mode: str = Field(default="paper", description="'paper' (testnet) or 'live'")
    timeframe: str = Field(default="1m", description="Bar timeframe")
    initial_cash: float = Field(default=10000.0, ge=100, le=10_000_000)
    commission: float = Field(default=0.001, ge=0, le=0.1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "strategy_name": "sma_cross",
                "symbol": "BTC/USDT",
                "mode": "paper",
                "timeframe": "1m",
                "initial_cash": 10000.0,
                "commission": 0.001,
            }
        }
    }


class StopLiveRequest(BaseModel):
    session_id: str = Field(..., description="Session ID to stop")


class SessionResponse(BaseModel):
    session_id: str
    status: str
    feed_status: str = "warming_up"
    strategy_name: str
    symbol: str
    exchange: str
    mode: str
    timeframe: str
    start_time: str
    end_time: Optional[str] = None
    initial_cash: float
    current_pnl: float = 0.0
    total_trades: int = 0
    positions: List[dict] = []
    open_orders: List[dict] = []
    error_message: Optional[str] = None
    ws_token: Optional[str] = None
    user_id: Optional[str] = None


class ExchangeInfo(BaseModel):
    id: str
    name: str
    adapter: str = "binance"
    binance_id: Optional[str] = None
    markets: List[str]
    default_market: str
    paper_mode_available: bool


# ──────────────────────────── Endpoints ────────────────────────────


@router.post("/live/start", tags=["Live Trading"])
async def start_live_trading(
    request: StartLiveRequest,
    user_id: str = Depends(get_optional_user_id),
):
    """Start a new Binance Spot live/paper trading session."""
    if request.mode not in ('paper', 'live'):
        raise HTTPException(400, f"Invalid mode: '{request.mode}'. Must be 'paper' or 'live'")

    if request.mode == 'live' and not LIVE_TRADING_ENABLED:
        raise HTTPException(
            403,
            "Live trading is disabled. Set LIVE_TRADING_ENABLED=true in .env to enable.",
        )

    try:
        config = load_broker_config()
        validate_symbol(request.symbol, 'binance', config)
        validate_timeframe(request.timeframe, config)

        session = live_engine.start_session(
            strategy_name=request.strategy_name,
            symbol=request.symbol,
            mode=request.mode,
            timeframe=request.timeframe,
            initial_cash=request.initial_cash,
            commission=request.commission,
            user_id=user_id,
        )

        logger.info(f"Session {session['session_id']} started")
        return session

    except ValueError as e:
        raise HTTPException(400, str(e))
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except LiveTradingError as e:
        raise HTTPException(500, str(e))
    except Exception as e:
        logger.exception(f"Failed to start live trading: {e}")
        raise HTTPException(500, f"Failed to start session: {e}")


@router.post("/live/stop", tags=["Live Trading"])
async def stop_live_trading(request: StopLiveRequest):
    """Stop a running live trading session."""
    try:
        result = live_engine.stop_session(request.session_id)
        return result
    except LiveTradingError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.exception(f"Failed to stop session: {e}")
        raise HTTPException(500, str(e))


@router.post("/live/orders/{session_id}/cancel/{order_id}", tags=["Live Trading"])
async def cancel_order(session_id: str, order_id: str):
    """Cancel an open order within a session."""
    try:
        result = live_engine.cancel_order(session_id, order_id)
        return result
    except LiveTradingError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.exception(f"Failed to cancel order: {e}")
        raise HTTPException(500, str(e))


@router.get("/live/status/{session_id}", tags=["Live Trading"])
async def get_live_status(session_id: str):
    """Get current status of a trading session."""
    try:
        return live_engine.get_session_status(session_id)
    except LiveTradingError as e:
        raise HTTPException(404, str(e))


@router.get("/live/sessions", tags=["Live Trading"])
async def list_live_sessions(
    status: Optional[str] = Query(None),
    active_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=1000),
):
    """List trading sessions with optional filters."""
    session_manager = get_session_manager()

    status_filter = None
    if status:
        try:
            status_filter = SessionStatus(status.lower())
        except ValueError:
            raise HTTPException(
                400,
                f"Invalid status: '{status}'. Valid: starting, running, stopping, stopped, error",
            )

    sessions = session_manager.list_sessions(
        status_filter=status_filter, active_only=active_only
    )
    return {'sessions': [s.to_dict() for s in sessions[:limit]]}


@router.get("/live/orders/{session_id}", tags=["Live Trading"])
async def get_session_orders(session_id: str):
    """Get orders for a session."""
    try:
        orders = live_engine.get_session_orders(session_id)
        return {'orders': orders}
    except LiveTradingError as e:
        raise HTTPException(404, str(e))


@router.get("/live/ticker/{session_id}", tags=["Live Trading"])
async def get_ticker_price(session_id: str):
    """Get current ticker price for the session's symbol."""
    try:
        return live_engine.get_ticker_price(session_id)
    except LiveTradingError as e:
        # Return structured error so frontend can handle gracefully
        raise HTTPException(404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch ticker: {e}")
        raise HTTPException(503, detail=f"Ticker unavailable: {e}")


@router.get("/live/ohlcv/{session_id}", tags=["Live Trading"])
async def get_ohlcv(session_id: str, limit: int = 100):
    """Get historical OHLCV bars for the session's symbol (REST fallback)."""
    try:
        return live_engine.get_ohlcv(session_id, limit=limit)
    except LiveTradingError as e:
        raise HTTPException(404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch OHLCV: {e}")
        raise HTTPException(503, detail=f"OHLCV unavailable: {e}")


@router.get("/live/logs/{session_id}", tags=["Live Trading"])
async def get_strategy_logs(session_id: str, limit: int = 100):
    """Get recent strategy log entries for a session."""
    try:
        return live_engine.get_strategy_logs(session_id, limit=limit)
    except LiveTradingError as e:
        raise HTTPException(404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch logs: {e}")
        raise HTTPException(503, detail=f"Logs unavailable: {e}")


@router.get("/live/exchanges", tags=["Live Trading"])
async def get_exchanges():
    """Get list of available exchanges."""
    exchanges = list_enabled_exchanges()
    return [ExchangeInfo(**ex) for ex in exchanges]


@router.get("/live/health", tags=["Live Trading"])
async def health_check():
    """Health check for live trading system."""
    try:
        session_manager = get_session_manager()
        config = load_broker_config()

        return {
            'status': 'healthy',
            'live_trading_enabled': LIVE_TRADING_ENABLED,
            'active_sessions': session_manager.get_active_session_count(),
            'session_counts': session_manager.get_session_count(),
            'enabled_exchanges': [ex for ex, cfg in config.exchanges.items() if cfg.enabled],
        }
    except Exception as e:
        logger.exception("Health check failed")
        return {'status': 'unhealthy', 'error': str(e)}
