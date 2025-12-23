"""
Strategy Parameter Extractor.

Extracts `params` from a user strategy with an AST-first approach and optional
subprocess fallback for complex definitions.
"""

from __future__ import annotations

import ast
import logging

from src.config.sandbox_config import get_config as get_sandbox_config
from src.service.isolated_sandbox import (
    IsolatedSandbox,
    SandboxError,
    SandboxExecutionError,
    SandboxTimeoutError,
)
from src.service.strategy_repo import read_user_strategy_source

logger = logging.getLogger(__name__)


def extract_strategy_params(name: str) -> list[dict[str, object]]:
    """
    Extract parameters from a strategy file safely.

    PERFORMANCE:
        - Fast path: static AST parsing (no code execution).
        - Slow path: subprocess sandbox execution only if AST finds no params.

    Args:
        name: Strategy name (without ".py").

    Returns:
        List of parameter objects with keys: name, value, type.
    """
    try:
        path, source = read_user_strategy_source(name)
    except FileNotFoundError:
        return []

    ast_params = _extract_params_from_source_ast(source)
    if ast_params:
        return ast_params

    sandbox_config = get_sandbox_config()

    if sandbox_config.mode != "subprocess":
        return []

    try:
        sandbox = IsolatedSandbox()
        result = sandbox.execute_strategy(
            source=source,
            module_name=f"user_strategy_{name}",
            filename=str(path),
        )
        strategy_params = result.get("strategy_params", [])
        return strategy_params or []
    except (SandboxError, SandboxExecutionError, SandboxTimeoutError) as exc:
        logger.warning("Isolated sandbox param extraction failed: %s", exc)
        return []


def _extract_params_from_source_ast(source: str) -> list[dict[str, object]]:
    """
    Extract strategy parameters using AST parsing (no code execution).

    This is a safe fallback that parses the source code without executing it.
    It looks for the `params` tuple in the UserStrategy class.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    params_list: list[dict[str, object]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != "UserStrategy":
            continue

        for item in node.body:
            if not isinstance(item, ast.Assign):
                continue

            for target in item.targets:
                if not isinstance(target, ast.Name) or target.id != "params":
                    continue

                if not isinstance(item.value, ast.Tuple):
                    continue

                for elt in item.value.elts:
                    if not isinstance(elt, ast.Tuple) or len(elt.elts) < 2:
                        continue

                    name_node, value_node = elt.elts[0], elt.elts[1]
                    if not isinstance(name_node, ast.Constant):
                        continue

                    param_name = name_node.value
                    if not param_name:
                        continue

                    param_value: object = None
                    param_type = "unknown"

                    if isinstance(value_node, ast.Constant):
                        param_value = value_node.value
                        param_type = type(param_value).__name__
                    elif isinstance(value_node, ast.UnaryOp) and isinstance(value_node.op, ast.USub):
                        if isinstance(value_node.operand, ast.Constant):
                            operand_val = value_node.operand.value
                            if isinstance(operand_val, (int, float)):
                                param_value = -operand_val
                                param_type = type(param_value).__name__

                    params_list.append(
                        {"name": str(param_name), "value": param_value, "type": param_type}
                    )

    return params_list
