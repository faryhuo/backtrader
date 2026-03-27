"""
Strategy data requirement helpers.

This module estimates how many historical bars a strategy needs before its
indicators can be initialized safely. The estimate is intentionally heuristic:
it uses AST parsing only and never executes user strategy code.
"""

from __future__ import annotations

import ast
from typing import Any, Mapping


def estimate_strategy_min_bars(
    source: str,
    runtime_params: Mapping[str, Any] | None = None,
) -> int | None:
    """
    Estimate the minimum bar count required by a strategy.

    The estimate is based on `UserStrategy.params` defaults plus any runtime
    parameter overrides. If the strategy does not expose enough structure for a
    reliable estimate, returns ``None``.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    strategy_class = _find_user_strategy_class(tree)
    if strategy_class is None:
        return None

    effective_params = _extract_param_defaults(strategy_class)
    for key, value in (runtime_params or {}).items():
        if value is not None:
            effective_params[key] = value

    estimates: list[int] = []
    for node in ast.walk(strategy_class):
        if not isinstance(node, ast.Call):
            continue

        indicator_name = _get_called_name(node.func)
        if not indicator_name:
            continue

        estimate = _estimate_indicator_min_bars(node, indicator_name, effective_params)
        if estimate is not None:
            estimates.append(estimate)

    if not estimates:
        return None
    return max(estimates)


def count_data_bars(data_feed: Any) -> int | None:
    """
    Count the number of rows available to a Backtrader data feed.
    """
    dataname = getattr(getattr(data_feed, "p", None), "dataname", None)
    if dataname is None:
        return None

    try:
        return len(dataname)
    except TypeError:
        return None


def format_insufficient_data_error(
    *,
    strategy_name: str,
    ticker: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    available_bars: int,
    required_bars: int | None = None,
) -> str:
    """
    Build a user-facing insufficient-data message.
    """
    available_label = "bar" if available_bars == 1 else "bars"
    if required_bars is None:
        requirement_text = "the strategy indicators need more historical bars"
    else:
        requirement_label = "bar" if required_bars == 1 else "bars"
        requirement_text = (
            f"the strategy indicators need at least {required_bars} {requirement_label}"
        )

    return (
        f"Insufficient market data for strategy '{strategy_name}' on {ticker} "
        f"at {timeframe} timeframe: the requested range {start_date} to {end_date} "
        f"returned {available_bars} {available_label}, but {requirement_text}. "
        "Extend the start date or reduce the indicator periods."
    )


def _find_user_strategy_class(tree: ast.AST) -> ast.ClassDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "UserStrategy":
            return node
    return None


def _extract_param_defaults(strategy_class: ast.ClassDef) -> dict[str, Any]:
    defaults: dict[str, Any] = {}

    for item in strategy_class.body:
        if not isinstance(item, ast.Assign):
            continue

        if not any(
            isinstance(target, ast.Name) and target.id == "params"
            for target in item.targets
        ):
            continue

        if not isinstance(item.value, (ast.Tuple, ast.List)):
            continue

        for entry in item.value.elts:
            if not isinstance(entry, ast.Tuple) or len(entry.elts) < 2:
                continue

            name_node, value_node = entry.elts[0], entry.elts[1]
            if not isinstance(name_node, ast.Constant) or not isinstance(name_node.value, str):
                continue

            resolved = _resolve_value(value_node, defaults)
            if resolved is not None:
                defaults[name_node.value] = resolved

    return defaults


def _estimate_indicator_min_bars(
    node: ast.Call,
    indicator_name: str,
    effective_params: Mapping[str, Any],
) -> int | None:
    numeric_args = [_coerce_positive_int(_resolve_value(arg, effective_params)) for arg in node.args]
    numeric_kwargs = {
        keyword.arg: _coerce_positive_int(_resolve_value(keyword.value, effective_params))
        for keyword in node.keywords
        if keyword.arg
    }

    if indicator_name in {"Stochastic", "StochasticSlow"}:
        period = numeric_kwargs.get("period") or _first_numeric(numeric_args) or 14
        period_dfast = numeric_kwargs.get("period_dfast") or 3
        period_dslow = numeric_kwargs.get("period_dslow") or 3
        return period + period_dfast + period_dslow - 2

    if indicator_name == "StochasticFast":
        period = numeric_kwargs.get("period") or _first_numeric(numeric_args) or 14
        period_dfast = numeric_kwargs.get("period_dfast") or 3
        return period + period_dfast - 1

    if indicator_name == "MACD":
        period_me1 = numeric_kwargs.get("period_me1") or 12
        period_me2 = numeric_kwargs.get("period_me2") or 26
        period_signal = numeric_kwargs.get("period_signal") or 9
        return max(period_me1, period_me2) + period_signal - 1

    generic_periods = [
        value
        for key, value in numeric_kwargs.items()
        if value is not None and key.startswith("period")
    ]
    if generic_periods:
        return max(generic_periods)

    positional_period = _first_numeric(numeric_args)
    if positional_period is not None:
        return positional_period

    return None


def _get_called_name(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        chain = _attribute_chain(func)
        if chain:
            return chain[-1]
    return None


def _resolve_value(node: ast.AST, params: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        operand = _resolve_value(node.operand, params)
        if isinstance(operand, (int, float)):
            return -operand

    if isinstance(node, ast.Name):
        return params.get(node.id)

    if isinstance(node, ast.Attribute):
        chain = _attribute_chain(node)
        if not chain:
            return None
        if len(chain) >= 3 and chain[0] == "self" and chain[-2] in {"p", "params"}:
            return params.get(chain[-1])

    return None


def _attribute_chain(node: ast.Attribute) -> list[str] | None:
    chain: list[str] = []
    current: ast.AST = node

    while isinstance(current, ast.Attribute):
        chain.append(current.attr)
        current = current.value

    if isinstance(current, ast.Name):
        chain.append(current.id)
        chain.reverse()
        return chain

    return None


def _coerce_positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and value > 0:
        return int(value)
    return None


def _first_numeric(values: list[int | None]) -> int | None:
    for value in values:
        if value is not None:
            return value
    return None


__all__ = [
    "estimate_strategy_min_bars",
    "count_data_bars",
    "format_insufficient_data_error",
]
