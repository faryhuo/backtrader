"""Standalone basis arbitrage trading service."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, Optional

import ccxt

from src.config.config_manager import get_user_config_manager

logger = logging.getLogger(__name__)

class BasisTradingError(Exception):
    """Raised when basis trading actions fail."""


def _safe_close_client(client: Any) -> None:
    """Close a client when the installed ccxt version exposes a close method."""
    close_method = getattr(client, "close", None)
    if callable(close_method):
        try:
            close_method()
        except Exception:
            logger.debug("Failed to close ccxt client cleanly", exc_info=True)


def _normalize_symbol(symbol: str) -> str:
    raw = str(symbol or "").strip().upper().replace("-", "/")
    if "/" in raw:
        return raw
    if raw.endswith("USDT"):
        return f"{raw[:-4]}/USDT"
    raise BasisTradingError(f"Unsupported symbol format: {symbol}")


def _to_okx_swap_symbol(symbol: str) -> str:
    normalized = _normalize_symbol(symbol)
    base, quote = normalized.split("/")
    return f"{base}/{quote}:{quote}"


def _split_symbol(symbol: str) -> tuple[str, str]:
    normalized = _normalize_symbol(symbol)
    base, quote = normalized.split("/")
    return base, quote


def _get_exchange_credentials(exchange: str, mode: str, user_id: Optional[str]) -> Dict[str, Optional[str]]:
    manager = get_user_config_manager(user_id) if user_id else get_user_config_manager("")
    creds = manager.get_ccxt_credentials(exchange.lower(), mode.lower())
    if not creds.get("api_key") or not creds.get("secret"):
        raise BasisTradingError(f"Missing {exchange} {mode} credentials")
    return creds


def _round_quantity(raw_quantity: float, *, precision: int = 6) -> float:
    quantity = float(raw_quantity or 0)
    if quantity <= 0:
        raise BasisTradingError("Calculated quantity must be positive")
    return round(quantity, precision)


def _fetch_binance_snapshot(symbol: str) -> Dict[str, float]:
    spot_client = ccxt.binance({"enableRateLimit": True})
    futures_client = ccxt.binanceusdm({"enableRateLimit": True})
    try:
        normalized = _normalize_symbol(symbol)
        spot_ticker = spot_client.fetch_ticker(normalized)
        perp_ticker = futures_client.fetch_ticker(normalized)
        spot_price = float(spot_ticker.get("last") or 0)
        perp_price = float(perp_ticker.get("last") or 0)
        return {
            "spot_price": spot_price,
            "perp_price": perp_price,
            "basis": perp_price - spot_price,
        }
    finally:
        _safe_close_client(spot_client)
        _safe_close_client(futures_client)


def _fetch_okx_snapshot(symbol: str) -> Dict[str, float]:
    spot_client = ccxt.okx({"enableRateLimit": True, "options": {"defaultType": "spot"}})
    swap_client = ccxt.okx({"enableRateLimit": True, "options": {"defaultType": "swap"}})
    try:
        normalized = _normalize_symbol(symbol)
        swap_symbol = _to_okx_swap_symbol(symbol)
        spot_ticker = spot_client.fetch_ticker(normalized)
        perp_ticker = swap_client.fetch_ticker(swap_symbol)
        spot_price = float(spot_ticker.get("last") or 0)
        perp_price = float(perp_ticker.get("last") or 0)
        return {
            "spot_price": spot_price,
            "perp_price": perp_price,
            "basis": perp_price - spot_price,
        }
    finally:
        _safe_close_client(spot_client)
        _safe_close_client(swap_client)


def get_market_snapshot(exchange: str, symbol: str) -> Dict[str, float]:
    normalized_exchange = str(exchange or "").strip().lower()
    if normalized_exchange == "binance":
        return _fetch_binance_snapshot(symbol)
    if normalized_exchange == "okx":
        return _fetch_okx_snapshot(symbol)
    raise BasisTradingError(f"Unsupported exchange: {exchange}")


def _extract_currency_balance(balance: Dict[str, Any], currency: str) -> Dict[str, float]:
    upper_currency = str(currency or "").upper()
    entry = balance.get(upper_currency) or {}
    free_value = entry.get("free")
    total_value = entry.get("total")
    used_value = entry.get("used")
    if free_value is None and isinstance(balance.get("free"), dict):
        free_value = balance["free"].get(upper_currency)
    if total_value is None and isinstance(balance.get("total"), dict):
        total_value = balance["total"].get(upper_currency)
    if used_value is None and isinstance(balance.get("used"), dict):
        used_value = balance["used"].get(upper_currency)
    return {
        "free": float(free_value or 0),
        "used": float(used_value or 0),
        "total": float(total_value or 0),
    }


def _find_position_for_symbol(positions: list[Dict[str, Any]], symbol: str) -> Optional[Dict[str, Any]]:
    normalized = _normalize_symbol(symbol)
    swap_symbol = _to_okx_swap_symbol(symbol)
    for position in positions or []:
        position_symbol = position.get("symbol")
        if position_symbol in {normalized, swap_symbol}:
            contracts = float(position.get("contracts") or 0)
            if abs(contracts) > 0:
                return position
    return None


def calculate_trade_preview(
    *,
    exchange: str,
    symbol: str,
    capital: float,
    spot_ratio: float,
    funding_rate: float,
    entry_price: Optional[float],
    cycles_per_month: int,
    round_trip_fees: float,
) -> Dict[str, Any]:
    normalized_symbol = _normalize_symbol(symbol)
    snapshot = get_market_snapshot(exchange, normalized_symbol)
    price = float(entry_price or snapshot["spot_price"] or 0)
    if price <= 0:
        raise BasisTradingError("Entry price must be positive")

    total_capital = float(capital or 0)
    spot_capital = total_capital * (float(spot_ratio or 0) / 100.0)
    margin_capital = total_capital - spot_capital
    quantity = _round_quantity(spot_capital / price)
    perp_notional = quantity * price
    income_per_8h = perp_notional * float(funding_rate or 0)
    income_per_day = income_per_8h * 3
    income_per_month = income_per_day * 30
    income_per_year = income_per_day * 365
    net_yearly_income = income_per_year - float(round_trip_fees or 0) * max(1, int(cycles_per_month or 1))
    annualized_net = net_yearly_income / total_capital if total_capital > 0 else 0
    single_cycle_volume = spot_capital * 2 + perp_notional * 2
    monthly_volume = single_cycle_volume * max(1, int(cycles_per_month or 1))

    return {
        "exchange": exchange.lower(),
        "symbol": normalized_symbol,
        "spot_capital": spot_capital,
        "margin_capital": margin_capital,
        "entry_price": price,
        "quantity": quantity,
        "perp_notional": perp_notional,
        "income_per_8h": income_per_8h,
        "income_per_day": income_per_day,
        "income_per_month": income_per_month,
        "income_per_year": income_per_year,
        "net_yearly_income": net_yearly_income,
        "annualized_net": annualized_net,
        "single_cycle_volume": single_cycle_volume,
        "monthly_volume": monthly_volume,
        "snapshot": snapshot,
    }


def get_credentials_status(exchange: str, user_id: Optional[str]) -> Dict[str, Any]:
    normalized_exchange = str(exchange or "").strip().lower()
    manager = get_user_config_manager(user_id) if user_id else get_user_config_manager("")
    paper = manager.get_ccxt_credentials(normalized_exchange, "paper")
    live = manager.get_ccxt_credentials(normalized_exchange, "live")
    needs_passphrase = normalized_exchange == "okx"
    return {
        "exchange": normalized_exchange,
        "paper": {
            "configured": bool(paper.get("api_key") and paper.get("secret") and (paper.get("passphrase") if needs_passphrase else True)),
            "has_passphrase": bool(paper.get("passphrase")),
        },
        "live": {
            "configured": bool(live.get("api_key") and live.get("secret") and (live.get("passphrase") if needs_passphrase else True)),
            "has_passphrase": bool(live.get("passphrase")),
        },
        "requires_passphrase": needs_passphrase,
    }


def _create_binance_spot_client(mode: str, creds: Dict[str, Optional[str]]) -> ccxt.binance:
    client = ccxt.binance({
        "apiKey": creds.get("api_key"),
        "secret": creds.get("secret"),
        "enableRateLimit": True,
    })
    if mode == "paper":
        client.set_sandbox_mode(True)
    return client


def _create_binance_futures_client(mode: str, creds: Dict[str, Optional[str]]) -> ccxt.binanceusdm:
    client = ccxt.binanceusdm({
        "apiKey": creds.get("api_key"),
        "secret": creds.get("secret"),
        "enableRateLimit": True,
    })
    if mode == "paper":
        client.set_sandbox_mode(True)
    return client


def _execute_binance_open(
    *,
    mode: str,
    symbol: str,
    quantity: float,
    user_id: Optional[str],
) -> Dict[str, Any]:
    creds = _get_exchange_credentials("binance", mode, user_id)
    spot_client = _create_binance_spot_client(mode, creds)
    futures_client = _create_binance_futures_client(mode, creds)
    try:
        normalized_symbol = _normalize_symbol(symbol)
        spot_order = spot_client.create_order(normalized_symbol, "market", "buy", quantity)
        futures_order = futures_client.create_order(
            normalized_symbol,
            "market",
            "sell",
            quantity,
            None,
            {"positionSide": "BOTH"},
        )
        return {
            "spot_order": spot_order,
            "perp_order": futures_order,
        }
    finally:
        _safe_close_client(spot_client)
        _safe_close_client(futures_client)


def _execute_binance_close(
    *,
    mode: str,
    symbol: str,
    spot_quantity: float,
    perp_quantity: float,
    user_id: Optional[str],
) -> Dict[str, Any]:
    creds = _get_exchange_credentials("binance", mode, user_id)
    spot_client = _create_binance_spot_client(mode, creds)
    futures_client = _create_binance_futures_client(mode, creds)
    try:
        normalized_symbol = _normalize_symbol(symbol)
        spot_order = spot_client.create_order(normalized_symbol, "market", "sell", spot_quantity)
        futures_order = futures_client.create_order(
            normalized_symbol,
            "market",
            "buy",
            perp_quantity,
            None,
            {"reduceOnly": True, "positionSide": "BOTH"},
        )
        return {
            "spot_order": spot_order,
            "perp_order": futures_order,
        }
    finally:
        _safe_close_client(spot_client)
        _safe_close_client(futures_client)


def _create_okx_spot_client(mode: str, creds: Dict[str, Optional[str]]) -> ccxt.okx:
    client = ccxt.okx({
        "apiKey": creds.get("api_key"),
        "secret": creds.get("secret"),
        "password": creds.get("passphrase"),
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    })
    if mode == "paper":
        client.set_sandbox_mode(True)
    return client


def _create_okx_swap_client(mode: str, creds: Dict[str, Optional[str]]) -> ccxt.okx:
    client = ccxt.okx({
        "apiKey": creds.get("api_key"),
        "secret": creds.get("secret"),
        "password": creds.get("passphrase"),
        "enableRateLimit": True,
        "options": {"defaultType": "swap"},
    })
    if mode == "paper":
        client.set_sandbox_mode(True)
    return client


def _get_okx_account_config(client: ccxt.okx) -> Dict[str, Any]:
    response = client.privateGetAccountConfig()
    data = response.get("data") or []
    return data[0] if data else {}


def _convert_okx_base_to_contracts(client: ccxt.okx, symbol: str, base_amount: float) -> float:
    client.load_markets()
    market = client.market(symbol)
    contract_size = float(market.get("contractSize") or 1)
    if contract_size <= 0:
        raise BasisTradingError(f"Invalid OKX contract size for {symbol}")
    contracts = float(base_amount or 0) / contract_size
    return float(client.amount_to_precision(symbol, contracts))


def get_trade_precheck(
    *,
    exchange: str,
    mode: str,
    symbol: str,
    capital: float,
    spot_ratio: float,
    leverage: int,
    funding_rate: float,
    entry_price: Optional[float],
    cycles_per_month: int,
    round_trip_fees: float,
    user_id: Optional[str],
) -> Dict[str, Any]:
    normalized_exchange = str(exchange or "").strip().lower()
    normalized_mode = str(mode or "").strip().lower()
    normalized_symbol = _normalize_symbol(symbol)

    preview = calculate_trade_preview(
        exchange=normalized_exchange,
        symbol=normalized_symbol,
        capital=capital,
        spot_ratio=spot_ratio,
        funding_rate=funding_rate,
        entry_price=entry_price,
        cycles_per_month=cycles_per_month,
        round_trip_fees=round_trip_fees,
    )

    result = {
        "exchange": normalized_exchange,
        "mode": normalized_mode,
        "symbol": normalized_symbol,
        "plan": {
            "spot_capital": preview["spot_capital"],
            "margin_capital": preview["margin_capital"],
            "quantity": preview["quantity"],
            "entry_price": preview["entry_price"],
            "perp_notional": preview["perp_notional"],
            "single_cycle_volume": preview["single_cycle_volume"],
            "monthly_volume": preview["monthly_volume"],
            "funding_rate": funding_rate,
            "leverage": leverage,
        },
        "snapshot": preview["snapshot"],
        "balances": None,
        "submit_preview": None,
    }

    try:
        creds = _get_exchange_credentials(normalized_exchange, normalized_mode, user_id)
    except BasisTradingError:
        return {
            **result,
            "balances": {
                "configured": False,
                "message": f"Missing {normalized_exchange} {normalized_mode} credentials",
            },
        }

    if normalized_exchange == "okx":
        spot_client = _create_okx_spot_client(normalized_mode, creds)
        swap_client = _create_okx_swap_client(normalized_mode, creds)
        try:
            account_config = _get_okx_account_config(swap_client)
            spot_balance = spot_client.fetch_balance({"type": "trading"})
            swap_balance = swap_client.fetch_balance({"type": "trading"})
            swap_contracts = _convert_okx_base_to_contracts(swap_client, _to_okx_swap_symbol(normalized_symbol), preview["quantity"])
            result["balances"] = {
                "configured": True,
                "spot_usdt": _extract_currency_balance(spot_balance, "USDT"),
                "swap_usdt": _extract_currency_balance(swap_balance, "USDT"),
            }
            result["account_config"] = {
                "acctLv": account_config.get("acctLv"),
                "posMode": account_config.get("posMode"),
                "autoLoan": account_config.get("autoLoan"),
                "greeksType": account_config.get("greeksType"),
            }
            result["submit_preview"] = {
                "spot_order": {
                    "symbol": normalized_symbol,
                    "side": "buy",
                    "type": "market",
                    "amount": preview["spot_capital"],
                    "params": {
                        "tdMode": "cash",
                        "tgtCcy": "quote_ccy",
                    },
                },
                "perp_order": {
                    "symbol": _to_okx_swap_symbol(normalized_symbol),
                    "side": "sell",
                    "type": "market",
                    "amount": swap_contracts,
                    "base_amount": preview["quantity"],
                    "params": (
                        {
                            "tdMode": "isolated",
                            "posSide": "short",
                        }
                        if account_config.get("posMode") == "long_short_mode"
                        else {
                            "tdMode": "isolated",
                        }
                    ),
                },
            }
        finally:
            _safe_close_client(spot_client)
            _safe_close_client(swap_client)
    elif normalized_exchange == "binance":
        spot_client = _create_binance_spot_client(normalized_mode, creds)
        futures_client = _create_binance_futures_client(normalized_mode, creds)
        try:
            spot_balance = spot_client.fetch_balance({"type": "spot"})
            futures_balance = futures_client.fetch_balance({"type": "future"})
            result["balances"] = {
                "configured": True,
                "spot_usdt": _extract_currency_balance(spot_balance, "USDT"),
                "swap_usdt": _extract_currency_balance(futures_balance, "USDT"),
            }
            result["submit_preview"] = {
                "spot_order": {
                    "symbol": normalized_symbol,
                    "side": "buy",
                    "type": "market",
                    "amount": preview["quantity"],
                    "params": {},
                },
                "perp_order": {
                    "symbol": normalized_symbol,
                    "side": "sell",
                    "type": "market",
                    "amount": preview["quantity"],
                    "params": {
                        "positionSide": "BOTH",
                    },
                },
            }
        finally:
            _safe_close_client(spot_client)
            _safe_close_client(futures_client)
    else:
        raise BasisTradingError(f"Unsupported exchange: {exchange}")

    return result


def _execute_okx_open(
    *,
    mode: str,
    symbol: str,
    quantity: float,
    spot_capital: float,
    leverage: int,
    user_id: Optional[str],
) -> Dict[str, Any]:
    creds = _get_exchange_credentials("okx", mode, user_id)
    spot_client = _create_okx_spot_client(mode, creds)
    swap_client = _create_okx_swap_client(mode, creds)
    try:
        normalized_symbol = _normalize_symbol(symbol)
        swap_symbol = _to_okx_swap_symbol(symbol)
        account_config = _get_okx_account_config(swap_client)
        acct_lv = str(account_config.get("acctLv") or "")
        pos_mode = str(account_config.get("posMode") or "")
        contract_amount = _convert_okx_base_to_contracts(swap_client, swap_symbol, quantity)
        if acct_lv == "1":
            raise BasisTradingError("OKX account mode is Spot mode (acctLv=1). Switch demo account mode to Futures, Multi-currency margin, or Portfolio margin before opening the perpetual short leg.")

        leverage_params = {"mgnMode": "isolated"}
        if pos_mode == "long_short_mode":
            leverage_params["posSide"] = "short"
        swap_client.set_leverage(leverage, swap_symbol, leverage_params)
        spot_order = spot_client.create_order(
            normalized_symbol,
            "market",
            "buy",
            spot_capital,
            None,
            {
                "tdMode": "cash",
                "tgtCcy": "quote_ccy",
            },
        )
        perp_params = {"tdMode": "isolated"}
        if pos_mode == "long_short_mode":
            perp_params["posSide"] = "short"
        futures_order = swap_client.create_order(
            swap_symbol,
            "market",
            "sell",
            contract_amount,
            None,
            perp_params,
        )
        return {
            "spot_order": spot_order,
            "perp_order": futures_order,
            "debug": {
                "account_config": {
                    "acctLv": acct_lv,
                    "posMode": pos_mode,
                },
                "spot_submit": {
                    "symbol": normalized_symbol,
                    "side": "buy",
                    "type": "market",
                    "amount": spot_capital,
                    "params": {
                        "tdMode": "cash",
                        "tgtCcy": "quote_ccy",
                    },
                },
                "perp_submit": {
                    "symbol": swap_symbol,
                    "side": "sell",
                    "type": "market",
                    "amount": contract_amount,
                    "base_amount": quantity,
                    "params": perp_params,
                },
            },
        }
    finally:
        _safe_close_client(spot_client)
        _safe_close_client(swap_client)


def _execute_okx_close(
    *,
    mode: str,
    symbol: str,
    spot_quantity: float,
    perp_quantity: float,
    user_id: Optional[str],
) -> Dict[str, Any]:
    creds = _get_exchange_credentials("okx", mode, user_id)
    spot_client = _create_okx_spot_client(mode, creds)
    swap_client = _create_okx_swap_client(mode, creds)
    try:
        normalized_symbol = _normalize_symbol(symbol)
        swap_symbol = _to_okx_swap_symbol(symbol)
        account_config = _get_okx_account_config(swap_client)
        pos_mode = str(account_config.get("posMode") or "")
        contract_amount = _convert_okx_base_to_contracts(swap_client, swap_symbol, perp_quantity)
        spot_order = spot_client.create_order(normalized_symbol, "market", "sell", spot_quantity)
        perp_params = {"tdMode": "isolated", "reduceOnly": True}
        if pos_mode == "long_short_mode":
            perp_params["posSide"] = "short"
        futures_order = swap_client.create_order(
            swap_symbol,
            "market",
            "buy",
            contract_amount,
            None,
            perp_params,
        )
        return {
            "spot_order": spot_order,
            "perp_order": futures_order,
        }
    finally:
        _safe_close_client(spot_client)
        _safe_close_client(swap_client)


def open_basis_trade(
    *,
    exchange: str,
    mode: str,
    symbol: str,
    capital: float,
    spot_ratio: float,
    leverage: int,
    funding_rate: float,
    user_id: Optional[str],
    confirm_live: bool = False,
) -> Dict[str, Any]:
    normalized_exchange = str(exchange or "").strip().lower()
    normalized_mode = str(mode or "").strip().lower()
    normalized_symbol = _normalize_symbol(symbol)
    if normalized_mode == "live" and not confirm_live:
        raise BasisTradingError("Live mode requires confirm_live=true")

    preview = calculate_trade_preview(
        exchange=normalized_exchange,
        symbol=normalized_symbol,
        capital=capital,
        spot_ratio=spot_ratio,
        funding_rate=funding_rate,
        entry_price=None,
        cycles_per_month=1,
        round_trip_fees=0,
    )
    quantity = preview["quantity"]
    if normalized_exchange == "binance":
        orders = _execute_binance_open(mode=normalized_mode, symbol=normalized_symbol, quantity=quantity, user_id=user_id)
    elif normalized_exchange == "okx":
        orders = _execute_okx_open(
            mode=normalized_mode,
            symbol=normalized_symbol,
            quantity=quantity,
            spot_capital=preview["spot_capital"],
            leverage=leverage,
            user_id=user_id,
        )
    else:
        raise BasisTradingError(f"Unsupported exchange: {exchange}")

    return {
        "status": "ok",
        "mode": normalized_mode,
        "exchange": normalized_exchange,
        "symbol": normalized_symbol,
        "action": "open",
        "paper": normalized_mode == "paper",
        "quantity": quantity,
        "orders": orders,
        "snapshot": preview["snapshot"],
        "execution_id": str(uuid.uuid4()),
        "executed_at": int(time.time() * 1000),
    }


def close_basis_trade(
    *,
    exchange: str,
    mode: str,
    symbol: str,
    quantity: Optional[float],
    spot_quantity: Optional[float],
    perp_quantity: Optional[float],
    user_id: Optional[str],
    confirm_live: bool = False,
) -> Dict[str, Any]:
    normalized_exchange = str(exchange or "").strip().lower()
    normalized_mode = str(mode or "").strip().lower()
    normalized_symbol = _normalize_symbol(symbol)
    if normalized_mode == "live" and not confirm_live:
        raise BasisTradingError("Live mode requires confirm_live=true")

    fallback_quantity = _round_quantity(quantity or 0)
    closing_spot_quantity = _round_quantity(spot_quantity or fallback_quantity)
    closing_perp_quantity = _round_quantity(perp_quantity or fallback_quantity)
    if normalized_exchange == "binance":
        orders = _execute_binance_close(
            mode=normalized_mode,
            symbol=normalized_symbol,
            spot_quantity=closing_spot_quantity,
            perp_quantity=closing_perp_quantity,
            user_id=user_id,
        )
    elif normalized_exchange == "okx":
        orders = _execute_okx_close(
            mode=normalized_mode,
            symbol=normalized_symbol,
            spot_quantity=closing_spot_quantity,
            perp_quantity=closing_perp_quantity,
            user_id=user_id,
        )
    else:
        raise BasisTradingError(f"Unsupported exchange: {exchange}")

    return {
        "status": "ok",
        "mode": normalized_mode,
        "exchange": normalized_exchange,
        "symbol": normalized_symbol,
        "action": "close",
        "paper": normalized_mode == "paper",
        "quantity": fallback_quantity,
        "spot_quantity": closing_spot_quantity,
        "perp_quantity": closing_perp_quantity,
        "orders": orders,
        "execution_id": str(uuid.uuid4()),
        "executed_at": int(time.time() * 1000),
    }


def get_trade_state(*, exchange: str, mode: str, symbol: str, user_id: Optional[str]) -> Dict[str, Any]:
    normalized_exchange = str(exchange or "").strip().lower()
    normalized_mode = str(mode or "").strip().lower()
    normalized_symbol = _normalize_symbol(symbol)
    snapshot = get_market_snapshot(normalized_exchange, normalized_symbol)
    base_currency, quote_currency = _split_symbol(normalized_symbol)

    try:
        creds = _get_exchange_credentials(normalized_exchange, normalized_mode, user_id)
    except BasisTradingError:
        return {
            "exchange": normalized_exchange,
            "mode": normalized_mode,
            "symbol": normalized_symbol,
            "status": "credentials_missing",
            "trade": None,
            "snapshot": {
                "spot_price": snapshot["spot_price"],
                "perp_price": snapshot["perp_price"],
                "basis": snapshot["basis"],
            },
            "message": f"Missing {normalized_exchange} {normalized_mode} credentials",
        }

    if normalized_exchange == "okx":
        spot_client = _create_okx_spot_client(normalized_mode, creds)
        swap_client = _create_okx_swap_client(normalized_mode, creds)
        try:
            spot_balance = spot_client.fetch_balance({"type": "trading"})
            positions = swap_client.fetch_positions([_to_okx_swap_symbol(normalized_symbol)], {"instType": "SWAP"})
            account_config = _get_okx_account_config(swap_client)
            swap_market = swap_client.market(_to_okx_swap_symbol(normalized_symbol))
        finally:
            _safe_close_client(spot_client)
            _safe_close_client(swap_client)
    elif normalized_exchange == "binance":
        spot_client = _create_binance_spot_client(normalized_mode, creds)
        futures_client = _create_binance_futures_client(normalized_mode, creds)
        try:
            spot_balance = spot_client.fetch_balance({"type": "spot"})
            positions = futures_client.fetch_positions([normalized_symbol])
            account_config = {}
            swap_market = None
        finally:
            _safe_close_client(spot_client)
            _safe_close_client(futures_client)
    else:
        raise BasisTradingError(f"Unsupported exchange: {exchange}")

    spot_asset = _extract_currency_balance(spot_balance, base_currency)
    quote_asset = _extract_currency_balance(spot_balance, quote_currency)
    position = _find_position_for_symbol(positions, normalized_symbol)

    spot_quantity = float(spot_asset["total"] or 0)
    perp_contracts = float(position.get("contracts") or 0) if position else 0.0
    contract_size = float((swap_market or {}).get("contractSize") or 1)
    perp_base_quantity = perp_contracts * contract_size if normalized_exchange == "okx" else perp_contracts
    entry_price = float(position.get("entryPrice") or 0) if position else 0.0
    unrealized_pnl = float(position.get("unrealizedPnl") or 0) if position else 0.0
    perp_side = position.get("side") if position else None

    status = "idle"
    if spot_quantity > 0 or abs(perp_contracts) > 0:
        status = "open"

    return {
        "exchange": normalized_exchange,
        "mode": normalized_mode,
        "symbol": normalized_symbol,
        "status": status,
        "trade": {
            "spot_quantity": spot_quantity,
            "spot_notional": spot_quantity * float(snapshot["spot_price"]),
            "perp_contracts": perp_contracts,
            "perp_base_quantity": perp_base_quantity,
            "contract_size": contract_size if normalized_exchange == "okx" else None,
            "perp_side": perp_side,
            "entry_price": entry_price,
            "base_currency": base_currency,
            "quote_currency": quote_currency,
        },
        "snapshot": {
            "spot_price": snapshot["spot_price"],
            "perp_price": snapshot["perp_price"],
            "basis": snapshot["basis"],
        },
        "balances": {
            "spot_base": spot_asset,
            "spot_quote": quote_asset,
        },
        "account_config": {
            "acctLv": account_config.get("acctLv"),
            "posMode": account_config.get("posMode"),
        },
        "unrealized_pnl": unrealized_pnl,
    }
