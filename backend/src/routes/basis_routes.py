"""Standalone basis arbitrage trading routes."""

from __future__ import annotations

import logging
from typing import Optional

from ccxt.base.errors import AccountNotEnabled, InsufficientFunds
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from src.routes.common.auth_dependencies import get_optional_user_id
from src.service.basis_trading_service import (
    BasisTradingError,
    calculate_trade_preview,
    close_basis_trade,
    get_credentials_status,
    get_trade_precheck,
    get_trade_state,
    open_basis_trade,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class BasisPreviewRequest(BaseModel):
    exchange: str = Field(..., description="Exchange id: okx or binance")
    symbol: str = Field(..., description="Trading symbol, e.g. ETH/USDT")
    capital: float = Field(..., gt=0)
    spot_ratio: float = Field(..., gt=0, le=100)
    funding_rate: float = Field(..., description="Funding rate as decimal, e.g. 0.0001")
    entry_price: Optional[float] = Field(default=None, gt=0)
    cycles_per_month: int = Field(default=4, ge=1, le=60)
    round_trip_fees: float = Field(default=12, ge=0)

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"okx", "binance"}:
            raise ValueError("exchange must be okx or binance")
        return normalized


class BasisOpenRequest(BaseModel):
    exchange: str = Field(..., description="Exchange id: okx or binance")
    mode: str = Field(default="paper", description="paper or live")
    symbol: str = Field(..., description="Trading symbol, e.g. ETH/USDT")
    capital: float = Field(..., gt=0)
    spot_ratio: float = Field(..., gt=0, le=100)
    leverage: int = Field(default=1, ge=1, le=3)
    funding_rate: float = Field(default=0, description="Funding rate as decimal")
    confirm_live: bool = Field(default=False)

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"okx", "binance"}:
            raise ValueError("exchange must be okx or binance")
        return normalized

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"paper", "live"}:
            raise ValueError("mode must be paper or live")
        return normalized


class BasisCloseRequest(BaseModel):
    exchange: str = Field(..., description="Exchange id: okx or binance")
    mode: str = Field(default="paper", description="paper or live")
    symbol: str = Field(..., description="Trading symbol, e.g. ETH/USDT")
    quantity: Optional[float] = Field(default=None, gt=0)
    spot_quantity: Optional[float] = Field(default=None, gt=0)
    perp_quantity: Optional[float] = Field(default=None, gt=0)
    confirm_live: bool = Field(default=False)

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"okx", "binance"}:
            raise ValueError("exchange must be okx or binance")
        return normalized

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"paper", "live"}:
            raise ValueError("mode must be paper or live")
        return normalized


class BasisPrecheckRequest(BaseModel):
    exchange: str = Field(..., description="Exchange id: okx or binance")
    mode: str = Field(default="paper", description="paper or live")
    symbol: str = Field(..., description="Trading symbol, e.g. ETH/USDT")
    capital: float = Field(..., gt=0)
    spot_ratio: float = Field(..., gt=0, le=100)
    leverage: int = Field(default=1, ge=1, le=3)
    funding_rate: float = Field(default=0, description="Funding rate as decimal")
    entry_price: Optional[float] = Field(default=None, gt=0)
    cycles_per_month: int = Field(default=4, ge=1, le=60)
    round_trip_fees: float = Field(default=12, ge=0)

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"okx", "binance"}:
            raise ValueError("exchange must be okx or binance")
        return normalized

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        normalized = str(value or "").strip().lower()
        if normalized not in {"paper", "live"}:
            raise ValueError("mode must be paper or live")
        return normalized


@router.get("/basis/credentials-status", tags=["Basis Arbitrage"])
async def basis_credentials_status(
    exchange: str,
    user_id: str = Depends(get_optional_user_id),
):
    try:
        return get_credentials_status(exchange, user_id)
    except BasisTradingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/basis/preview", tags=["Basis Arbitrage"])
async def preview_basis_trade(request: BasisPreviewRequest):
    try:
        return calculate_trade_preview(
            exchange=request.exchange,
            symbol=request.symbol,
            capital=request.capital,
            spot_ratio=request.spot_ratio,
            funding_rate=request.funding_rate,
            entry_price=request.entry_price,
            cycles_per_month=request.cycles_per_month,
            round_trip_fees=request.round_trip_fees,
        )
    except BasisTradingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/basis/precheck", tags=["Basis Arbitrage"])
async def precheck_basis_trade(
    request: BasisPrecheckRequest,
    user_id: str = Depends(get_optional_user_id),
):
    try:
        return get_trade_precheck(
            exchange=request.exchange,
            mode=request.mode,
            symbol=request.symbol,
            capital=request.capital,
            spot_ratio=request.spot_ratio,
            leverage=request.leverage,
            funding_rate=request.funding_rate,
            entry_price=request.entry_price,
            cycles_per_month=request.cycles_per_month,
            round_trip_fees=request.round_trip_fees,
            user_id=user_id,
        )
    except BasisTradingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/basis/trade/state", tags=["Basis Arbitrage"])
async def basis_trade_state(
    exchange: str,
    mode: str,
    symbol: str,
    user_id: str = Depends(get_optional_user_id),
):
    try:
        return get_trade_state(exchange=exchange, mode=mode, symbol=symbol, user_id=user_id)
    except BasisTradingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/basis/trade/open", tags=["Basis Arbitrage"])
async def open_basis_trade_route(
    request: BasisOpenRequest,
    user_id: str = Depends(get_optional_user_id),
):
    try:
        return open_basis_trade(
            exchange=request.exchange,
            mode=request.mode,
            symbol=request.symbol,
            capital=request.capital,
            spot_ratio=request.spot_ratio,
            leverage=request.leverage,
            funding_rate=request.funding_rate,
            user_id=user_id,
            confirm_live=request.confirm_live,
        )
    except BasisTradingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InsufficientFunds as exc:
        raise HTTPException(status_code=400, detail=f"Insufficient exchange balance: {exc}") from exc
    except AccountNotEnabled as exc:
        raise HTTPException(status_code=400, detail=f"Exchange account mode rejected this request: {exc}") from exc
    except Exception as exc:
        logger.exception(f"Failed to open basis trade: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to open basis trade: {exc}") from exc


@router.post("/basis/trade/close", tags=["Basis Arbitrage"])
async def close_basis_trade_route(
    request: BasisCloseRequest,
    user_id: str = Depends(get_optional_user_id),
):
    try:
        return close_basis_trade(
            exchange=request.exchange,
            mode=request.mode,
            symbol=request.symbol,
            quantity=request.quantity,
            spot_quantity=request.spot_quantity,
            perp_quantity=request.perp_quantity,
            user_id=user_id,
            confirm_live=request.confirm_live,
        )
    except BasisTradingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InsufficientFunds as exc:
        raise HTTPException(status_code=400, detail=f"Insufficient exchange balance: {exc}") from exc
    except AccountNotEnabled as exc:
        raise HTTPException(status_code=400, detail=f"Exchange account mode rejected this request: {exc}") from exc
    except Exception as exc:
        logger.exception(f"Failed to close basis trade: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to close basis trade: {exc}") from exc
