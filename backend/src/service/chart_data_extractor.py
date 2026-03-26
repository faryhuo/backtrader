"""
Structured chart data extraction for single-asset backtests.

Converts Backtrader runtime state into JSON-serializable chart data so the
frontend can render charts without relying on PNG output from matplotlib.
"""

from __future__ import annotations

import math
from typing import Any

import backtrader as bt


def build_backtest_chart_data(
    strat: bt.Strategy,
    price_data: list[dict[str, Any]],
    metrics: dict[str, Any],
    initial_cash: float,
) -> dict[str, Any]:
    """Build a structured chart payload from a completed backtest."""
    normalized_price_data = _normalize_price_data(price_data)
    time_keys = [item["time"] for item in normalized_price_data]
    trade_details = metrics.get("trade_details", {}) or {}
    observer_payload = _extract_observers(strat, time_keys)

    return {
        "ohlcv": normalized_price_data,
        "markers": _merge_markers(
            observer_payload["markers"],
            _extract_trade_markers(trade_details),
        ),
        "equity_curve": _build_equity_curve(metrics.get("equity_curve", {}) or {}, initial_cash),
        "indicators": _extract_indicators(strat, time_keys) + observer_payload["indicators"],
    }


def _normalize_price_data(price_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []

    for item in price_data or []:
        time_key = item.get("time")
        if not time_key:
            continue

        normalized.append(
            {
                "time": str(time_key),
                "open": _safe_float(item.get("open")),
                "high": _safe_float(item.get("high")),
                "low": _safe_float(item.get("low")),
                "close": _safe_float(item.get("close")),
                "volume": _safe_float(item.get("volume")),
            }
        )

    normalized.sort(key=lambda item: item["time"])
    return normalized


def _extract_trade_markers(trade_details: dict[str, Any]) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []

    for trade in trade_details.get("trades", []) or []:
        trade_num = trade.get("trade_num")
        size = _safe_float(trade.get("size"))
        pnl = _safe_float(trade.get("net_pnl"))

        entry_date = trade.get("entry_date")
        entry_price = _safe_float(trade.get("entry_price"))
        if entry_date:
            markers.append(
                {
                    "time": str(entry_date),
                    "value": entry_price,
                    "side": "buy",
                    "label": f"BUY #{trade_num}" if trade_num else "BUY",
                    "size": size,
                }
            )

        exit_date = trade.get("exit_date")
        exit_price = _safe_float(trade.get("exit_price"))
        if exit_date:
            markers.append(
                {
                    "time": str(exit_date),
                    "value": exit_price,
                    "side": "sell",
                    "label": f"SELL #{trade_num}" if trade_num else "SELL",
                    "size": size,
                    "pnl": pnl,
                }
            )

    return markers


def _merge_markers(
    observer_markers: list[dict[str, Any]],
    trade_markers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not observer_markers:
        return trade_markers

    merged = [dict(marker) for marker in observer_markers]

    for trade_marker in trade_markers:
        matched = False
        for marker in merged:
            if marker.get("time") == trade_marker.get("time") and marker.get("side") == trade_marker.get("side"):
                for key, value in trade_marker.items():
                    if key not in marker or marker.get(key) in (None, "", 0.0):
                        marker[key] = value
                matched = True
                break

        if not matched:
            merged.append(dict(trade_marker))

    return sorted(merged, key=lambda item: (item.get("time", ""), item.get("side", "")))


def _build_equity_curve(
    equity_returns: dict[str, Any],
    initial_cash: float,
) -> list[dict[str, Any]]:
    if not equity_returns:
        return []

    current_value = float(initial_cash)
    curve: list[dict[str, Any]] = []

    for time_key in sorted(equity_returns):
        period_return = _safe_float(equity_returns[time_key])
        current_value *= 1 + period_return
        curve.append(
            {
                "time": str(time_key),
                "value": round(current_value, 6),
            }
        )

    return curve


def _extract_indicators(
    strat: bt.Strategy,
    time_keys: list[str],
) -> list[dict[str, Any]]:
    indicators: list[dict[str, Any]] = []

    for index, indicator in enumerate(getattr(strat, "getindicators", lambda: [])()):
        plotinfo = getattr(indicator, "plotinfo", None)
        if plotinfo is not None and getattr(plotinfo, "plot", True) is False:
            continue

        line_aliases = list(indicator.lines.getlinealiases())
        line_items: list[dict[str, Any]] = []

        for alias in line_aliases:
            line = getattr(indicator.lines, alias)
            line_series = _build_line_series(time_keys, list(line.array))
            if line_series:
                line_items.append(
                    {
                        "id": alias,
                        "name": alias.upper(),
                        "data": line_series,
                    }
                )

        if not line_items:
            continue

        indicator_name = ""
        if plotinfo is not None:
            indicator_name = getattr(plotinfo, "plotname", "") or ""

        indicators.append(
            {
                "id": f"{indicator.__class__.__name__.lower()}_{index}",
                "name": indicator_name or indicator.__class__.__name__,
                "subplot": bool(getattr(plotinfo, "subplot", False)) if plotinfo is not None else False,
                "lines": line_items,
            }
        )

    return indicators


def _extract_observers(
    strat: bt.Strategy,
    time_keys: list[str],
) -> dict[str, list[dict[str, Any]]]:
    markers: list[dict[str, Any]] = []
    indicators: list[dict[str, Any]] = []

    for observer in getattr(strat, "getobservers", lambda: [])():
        observer_name = observer.__class__.__name__
        line_aliases = list(observer.lines.getlinealiases())
        line_map = {
            alias: _build_line_series(time_keys, list(getattr(observer.lines, alias).array))
            for alias in line_aliases
        }

        if observer_name == "Broker":
            broker_lines = []
            for alias in ("cash", "value"):
                series = line_map.get(alias) or []
                if series:
                    broker_lines.append(
                        {
                            "id": alias,
                            "name": alias,
                            "data": series,
                        }
                    )
            if broker_lines:
                indicators.append(
                    {
                        "id": "observer_broker",
                        "name": "Broker",
                        "subplot": True,
                        "lines": broker_lines,
                    }
                )
            continue

        if observer_name == "BuySell":
            markers.extend(_build_buysell_markers(line_map))
            continue

        if observer_name == "Trades":
            trade_lines = []
            for alias in ("pnlplus", "pnlminus"):
                series = line_map.get(alias) or []
                if series:
                    trade_lines.append(
                        {
                            "id": alias,
                            "name": alias.upper(),
                            "data": series,
                            "series_type": "bar",
                        }
                    )
            if trade_lines:
                indicators.append(
                    {
                        "id": "observer_trades",
                        "name": "Trades",
                        "subplot": True,
                        "lines": trade_lines,
                    }
                )
            continue

    return {"markers": markers, "indicators": indicators}


def _build_buysell_markers(line_map: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []

    for side, label in (("buy", "BUY"), ("sell", "SELL")):
        for item in line_map.get(side, []):
            markers.append(
                {
                    "time": item["time"],
                    "value": item["value"],
                    "side": side,
                    "label": label,
                }
            )

    return markers


def _build_line_series(
    time_keys: list[str],
    values: list[Any],
) -> list[dict[str, Any]]:
    if not time_keys or not values:
        return []

    if len(values) > len(time_keys):
        # Backtrader observer/indicator buffers often keep the effective series
        # in the leading segment and pad the tail with NaN values.
        values = values[:len(time_keys)]
    elif len(values) < len(time_keys):
        time_keys = time_keys[-len(values):]

    series: list[dict[str, Any]] = []
    for time_key, value in zip(time_keys, values):
        numeric_value = _safe_float(value, default=None)
        if numeric_value is None or not math.isfinite(numeric_value):
            continue

        series.append(
            {
                "time": time_key,
                "value": round(numeric_value, 6),
            }
        )

    return series


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value is None:
            return default
        numeric_value = float(value)
        if math.isnan(numeric_value):
            return default
        return numeric_value
    except (TypeError, ValueError):
        return default
