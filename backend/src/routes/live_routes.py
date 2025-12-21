"""
Live Trading REST API Routes

This module provides REST API endpoints for managing live/paper trading sessions:
- POST /api/live/start - Start new trading session
- POST /api/live/stop - Stop running session
- GET  /api/live/status/{session_id} - Get session status
- GET  /api/live/sessions - List all sessions
- GET  /api/live/exchanges - List available exchanges
- GET  /api/live/orders/{session_id} - Get session orders
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.config.settings import LIVE_TRADING_ENABLED
from src.service.live_engine import run_live, stop_live, get_session_status
from src.service.session_manager import SessionStatus, get_session_manager
from src.utils.auth import get_current_user
from src.utils.config_loader import list_enabled_exchanges, load_broker_config, validate_symbol, validate_timeframe

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models


class StartLiveRequest(BaseModel):
    """Request model for starting live trading session."""
    strategy_name: str = Field(..., description="Strategy file name (without .py)")
    symbol: str = Field(..., description="Trading pair (e.g., 'BTC/USDT')")
    exchange: str = Field(default="binance", description="Exchange ID")
    mode: str = Field(default="paper", description="Trading mode: 'paper' or 'live'")
    timeframe: str = Field(default="1m", description="Bar timeframe (e.g., '1m', '5m', '1h')")
    initial_cash: float = Field(default=10000.0, description="Initial cash for paper trading")
    commission: float = Field(default=0.001, description="Commission rate (0.001 = 0.1%)")

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_name": "sma_cross",
                "symbol": "BTC/USDT",
                "exchange": "binance",
                "mode": "paper",
                "timeframe": "1m",
                "initial_cash": 10000.0,
                "commission": 0.001
            }
        }


class StopLiveRequest(BaseModel):
    """Request model for stopping live trading session."""
    session_id: str = Field(..., description="Session ID to stop")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "12345678-1234-1234-1234-123456789abc"
            }
        }


class SessionResponse(BaseModel):
    """Response model for session information."""
    session_id: str
    status: str
    strategy_name: str
    symbol: str
    exchange: str
    mode: str
    timeframe: str
    start_time: str
    end_time: Optional[str] = None
    initial_cash: float
    current_pnl: float
    total_trades: int
    positions: List[dict] = []
    open_orders: List[dict] = []
    error_message: Optional[str] = None


class ExchangeInfo(BaseModel):
    """Exchange information model."""
    id: str
    name: str
    adapter: str = Field(default="ccxt", description="Underlying adapter (ccxt/ibkr)")
    ccxt_id: Optional[str] = Field(default=None, description="CCXT exchange id if applicable")
    markets: List[str]
    default_market: str
    paper_mode_available: bool


# API Endpoints


@router.post("/live/start", response_model=dict, tags=["Live Trading"])
async def start_live_trading(
    request: StartLiveRequest,
    user: dict = Depends(get_current_user)
):
    """
    Start a new live/paper trading session.

    This endpoint:
    1. Validates configuration
    2. Creates new trading session
    3. Starts Cerebro with CCXT broker and data feed
    4. Returns session information

    **Permissions:**
    - Paper mode (mode='paper') is always available
    - Live mode (mode='live') requires LIVE_TRADING_ENABLED=true in .env

    **Rate Limits:**
    - Maximum 5 concurrent sessions per user (Phase 3+)

    **Returns:**
    - Session ID for tracking
    - Session status and configuration
    """
    # Extract user ID for credential lookup
    user_id = user.get("sub") if user else None
    
    # Validate mode first
    if request.mode not in ['paper', 'live']:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: '{request.mode}'. Must be 'paper' or 'live'"
        )
    
    # Check if live trading is enabled (only required for 'live' mode, paper mode is always allowed)
    if request.mode == 'live' and not LIVE_TRADING_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="Live trading is disabled. Set LIVE_TRADING_ENABLED=true in .env to enable real trading."
        )

    try:
        # Validate configuration
        config = load_broker_config()

        # Validate exchange
        from src.utils.config_loader import get_exchange_config
        ex_config = get_exchange_config(request.exchange, config)

        # Validate symbol format
        validate_symbol(request.symbol, request.exchange, config)

        # Validate timeframe
        validate_timeframe(request.timeframe, config)

        # Start live trading session
        logger.info(
            f"Starting {request.mode} trading: {request.strategy_name} on "
            f"{request.symbol} ({request.exchange})"
        )

        session = run_live(
            strategy_name=request.strategy_name,
            symbol=request.symbol,
            exchange=request.exchange,
            mode=request.mode,
            timeframe=request.timeframe,
            initial_cash=request.initial_cash,
            commission=request.commission,
            user_id=user_id  # Pass user_id for database credential lookup
        )

        logger.info(f"Session {session['session_id']} started successfully")

        return session

    except ValueError as e:
        # Configuration or validation error
        raise HTTPException(status_code=400, detail=str(e))

    except FileNotFoundError as e:
        # Strategy not found
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        # Unexpected error
        logger.exception(f"Failed to start live trading: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/live/stop", response_model=dict, tags=["Live Trading"])
async def stop_live_trading(request: StopLiveRequest):
    """
    Stop a running live trading session.

    This endpoint:
    1. Validates session exists
    2. Gracefully stops Cerebro execution
    3. Closes CCXT connection
    4. Saves final session state to database

    **Behavior:**
    - Cancels all open orders (optional, Phase 4+)
    - Closes all positions (optional, configurable)
    - Saves session history

    **Returns:**
    - Session ID
    - Final status
    - Final P&L
    """
    try:
        session_manager = get_session_manager()

        # Check session exists
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found"
            )

        # Check session is active
        if not session.is_active():
            return {
                'session_id': request.session_id,
                'status': session.status.value,
                'message': f'Session already {session.status.value}',
                'final_pnl': session.current_pnl
            }

        # Stop session
        logger.info(f"Stopping session {request.session_id}")

        success = session_manager.stop_session(request.session_id, timeout=10.0)

        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to stop session {request.session_id}. Check logs for details."
            )

        # Return updated session info
        session = session_manager.get_session(request.session_id)

        return {
            'session_id': request.session_id,
            'status': session.status.value,
            'message': 'Session stopped successfully',
            'final_pnl': session.current_pnl,
            'total_trades': session.total_trades,
            'end_time': session.end_time.isoformat() if session.end_time else None
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Failed to stop session {request.session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop session: {str(e)}")


@router.get("/live/status/{session_id}", response_model=SessionResponse, tags=["Live Trading"])
async def get_live_status(session_id: str):
    """
    Get current status of a trading session.

    **Returns:**
    - Session configuration
    - Current status (starting, running, stopped, error)
    - Financial metrics (P&L, trades)
    - Current positions
    - Open orders
    """
    try:
        session_manager = get_session_manager()

        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        return SessionResponse(**session.to_dict())

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Failed to get status for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/live/sessions", response_model=List[SessionResponse], tags=["Live Trading"])
async def list_live_sessions(
    status: Optional[str] = Query(None, description="Filter by status"),
    active_only: bool = Query(False, description="Only return active sessions"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results")
):
    """
    List all trading sessions.

    **Query Parameters:**
    - status: Filter by status (starting, running, stopped, error)
    - active_only: If true, only return starting/running sessions
    - limit: Maximum number of results (default: 100)

    **Returns:**
    - List of sessions with full details
    - Ordered by start time (newest first)
    """
    try:
        session_manager = get_session_manager()

        # Parse status filter
        status_filter = None
        if status:
            try:
                status_filter = SessionStatus(status.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: '{status}'. Valid: starting, running, stopping, stopped, error"
                )

        # Get sessions
        sessions = session_manager.list_sessions(
            status_filter=status_filter,
            active_only=active_only
        )

        # Limit results
        sessions = sessions[:limit]

        # Convert to response models
        return [SessionResponse(**s.to_dict()) for s in sessions]

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.get("/live/exchanges", response_model=List[ExchangeInfo], tags=["Live Trading"])
async def get_exchanges():
    """
    Get list of available exchanges.

    **Returns:**
    - Exchange ID and name
    - Supported markets (spot, futures, etc.)
    - Paper mode availability
    """
    try:
        exchanges = list_enabled_exchanges()
        return [ExchangeInfo(**ex) for ex in exchanges]

    except Exception as e:
        logger.exception(f"Failed to get exchanges: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get exchanges: {str(e)}")


@router.get("/live/orders/{session_id}", response_model=List[dict], tags=["Live Trading"])
async def get_session_orders(session_id: str):
    """
    Get all orders for a session.

    **Returns:**
    - Order ID
    - Symbol, side, type, size, price
    - Status (submitted, filled, canceled, rejected)
    - Fill details (filled size, price, commission)
    - Timestamps
    """
    try:
        session_manager = get_session_manager()

        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        # Return orders from session
        return session.orders

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Failed to get orders for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get orders: {str(e)}")


@router.get("/live/health", response_model=dict, tags=["Live Trading"])
async def health_check():
    """
    Health check endpoint for live trading system.

    **Returns:**
    - System status
    - Active session count
    - Configuration loaded
    """
    try:
        session_manager = get_session_manager()
        config = load_broker_config()

        active_count = session_manager.get_active_session_count()
        session_counts = session_manager.get_session_count()

        return {
            'status': 'healthy',
            'live_trading_enabled': LIVE_TRADING_ENABLED,
            'active_sessions': active_count,
            'session_counts': session_counts,
            'enabled_exchanges': [ex for ex, cfg in config.exchanges.items() if cfg.enabled]
        }

    except Exception as e:
        logger.exception("Health check failed")
        return {
            'status': 'unhealthy',
            'error': str(e)
        }
