"""
Soft Strategy Sandbox (DEPRECATED)

This module provides a soft sandbox for executing user strategy code.
It restricts imports and builtins but CANNOT protect against malicious code.

WARNING: This sandbox can be bypassed through:
- pandas/numpy file I/O operations
- Python reflection (__class__.__bases__, etc.)
- Object graph traversal

For secure execution of untrusted code, use IsolatedSandbox instead.

Example:
    # Secure (recommended):
    from src.service.isolated_sandbox import IsolatedSandbox
    sandbox = IsolatedSandbox()
    result = sandbox.execute_strategy(source, "my_strategy", "my_strategy.py")
    
    # Insecure (only for trusted code):
    from src.service.strategy_sandbox import execute_strategy_code
    result = execute_strategy_code(source, module_name="my_strategy", filename="my_strategy.py")
"""

import builtins as py_builtins
import importlib
import sys
import warnings
from types import ModuleType
from typing import Any, Dict

import backtrader as bt
import pandas as pd

# Security warning for soft sandbox mode
SOFT_SANDBOX_WARNING = (
    "Using soft sandbox mode which cannot protect against malicious code. "
    "For untrusted strategy code, use IsolatedSandbox instead (set SANDBOX_MODE=subprocess)."
)


class StrategySandboxError(Exception):
    """Raised when user strategy code violates sandbox constraints."""


# Modules that user-provided strategy code is allowed to import
ALLOWED_IMPORTS = {
    "backtrader",
    "math",
    "statistics",
    "random",
    "datetime",
    "decimal",
    "fractions",
    "collections",
    "itertools",
    "functools",
    "typing",
    "operator",
    "bisect",
    "heapq",
    "pandas",
    "numpy",
}


def _strip_module_builtins(module: ModuleType) -> ModuleType:
    """Remove the __builtins__ reference from modules we expose."""
    module_dict = getattr(module, "__dict__", None)
    if module_dict is not None:
        module_dict.pop("__builtins__", None)
    return module


def _safe_import(name: str, globals=None, locals=None, fromlist=(), level: int = 0):
    if level != 0:
        raise StrategySandboxError("Relative imports are not allowed in strategy code")
    root = name.split(".", 1)[0]
    if root not in ALLOWED_IMPORTS:
        raise StrategySandboxError(f"Import of module '{root}' is not permitted")
    try:
        module = importlib.import_module(name)
    except ImportError as exc:
        raise StrategySandboxError(f"Failed to import module '{name}': {exc}") from exc
    _strip_module_builtins(module)
    return module


def _build_base_builtins() -> Dict[str, Any]:
    allowed = {
        "abs": py_builtins.abs,
        "all": py_builtins.all,
        "any": py_builtins.any,
        "bin": py_builtins.bin,
        "bool": py_builtins.bool,
        "bytearray": py_builtins.bytearray,
        "bytes": py_builtins.bytes,
        "callable": py_builtins.callable,
        "chr": py_builtins.chr,
        "complex": py_builtins.complex,
        "dict": py_builtins.dict,
        "divmod": py_builtins.divmod,
        "enumerate": py_builtins.enumerate,
        "filter": py_builtins.filter,
        "float": py_builtins.float,
        "format": py_builtins.format,
        "frozenset": py_builtins.frozenset,
        "getattr": py_builtins.getattr,
        "hasattr": py_builtins.hasattr,
        "hash": py_builtins.hash,
        "hex": py_builtins.hex,
        "id": py_builtins.id,
        "int": py_builtins.int,
        "isinstance": py_builtins.isinstance,
        "issubclass": py_builtins.issubclass,
        "iter": py_builtins.iter,
        "len": py_builtins.len,
        "list": py_builtins.list,
        "map": py_builtins.map,
        "max": py_builtins.max,
        "memoryview": py_builtins.memoryview,
        "min": py_builtins.min,
        "next": py_builtins.next,
        "oct": py_builtins.oct,
        "ord": py_builtins.ord,
        "pow": py_builtins.pow,
        "print": py_builtins.print,
        "property": py_builtins.property,
        "range": py_builtins.range,
        "repr": py_builtins.repr,
        "reversed": py_builtins.reversed,
        "round": py_builtins.round,
        "set": py_builtins.set,
        "setattr": py_builtins.setattr,
        "slice": py_builtins.slice,
        "sorted": py_builtins.sorted,
        "staticmethod": py_builtins.staticmethod,
        "str": py_builtins.str,
        "sum": py_builtins.sum,
        "super": py_builtins.super,
        "tuple": py_builtins.tuple,
        "type": py_builtins.type,
        "vars": py_builtins.vars,
        "zip": py_builtins.zip,
        "__build_class__": py_builtins.__build_class__,
        "BaseException": py_builtins.BaseException,
        "Exception": py_builtins.Exception,
        "ValueError": py_builtins.ValueError,
        "RuntimeError": py_builtins.RuntimeError,
        "KeyError": py_builtins.KeyError,
        "NotImplementedError": py_builtins.NotImplementedError,
        "StopIteration": py_builtins.StopIteration,
        "object": py_builtins.object,
        "classmethod": py_builtins.classmethod,
    }
    return allowed


_BASE_SAFE_BUILTINS = _build_base_builtins()


def _build_safe_globals() -> Dict[str, Any]:
    safe_globals = {
        "bt": _strip_module_builtins(bt),
        "pd": _strip_module_builtins(pd),
    }
    return safe_globals


_BASE_SAFE_GLOBALS = _build_safe_globals()


def _make_builtins() -> Dict[str, Any]:
    safe = dict(_BASE_SAFE_BUILTINS)
    safe["__import__"] = _safe_import
    return safe


def execute_strategy_code(source: str, *, module_name: str, filename: str) -> Dict[str, Any]:
    """
    Compile and execute user strategy code inside the sandbox environment.
    Returns the globals dict produced by executing the code.
    """
    sandbox_globals = dict(_BASE_SAFE_GLOBALS)
    sandbox_globals.update(
        {
            "__name__": module_name,
            "__package__": None,
            "__doc__": None,
            "__builtins__": _make_builtins(),
            "__file__": filename,
        }
    )

    try:
        bytecode = compile(source, filename, "exec")
    except SyntaxError as exc:
        raise StrategySandboxError(f"Strategy contains syntax errors: {exc}") from exc

    try:
        exec(bytecode, sandbox_globals)
    except Exception as exc:
        raise StrategySandboxError(f"Strategy execution failed: {exc}") from exc

    module = ModuleType(module_name)
    module.__dict__.update(sandbox_globals)
    sys.modules[module_name] = module

    return sandbox_globals


__all__ = ["StrategySandboxError", "execute_strategy_code"]
