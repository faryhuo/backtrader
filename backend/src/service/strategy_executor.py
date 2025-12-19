#!/usr/bin/env python3
"""
Strategy Executor - Isolated Subprocess Worker

This script runs as a subprocess to execute user strategy code in isolation.
It communicates with the parent process via stdin/stdout using JSON protocol.

WARNING: This script should only be launched by IsolatedSandbox.
         Do not run directly.

Protocol:
    Input (JSON):  {"action": "execute"|"validate", "source": "...", ...}
    Output (JSON): {"success": true|false, "result": {...}, "error": "..."}
"""

import builtins as py_builtins
import importlib
import json
import os
import platform
import signal
import sys
import traceback
from types import ModuleType
from typing import Any, Dict, Optional


# ============================================================================
# Resource Limiting (Platform-Specific)
# ============================================================================

def apply_resource_limits(
    max_memory_mb: int = 512,
    max_cpu_percent: int = 100,
    allow_network: bool = False,
    allow_file_write: bool = False
) -> Dict[str, Any]:
    """
    Apply process-level resource limits.
    
    Args:
        max_memory_mb: Maximum memory in MB
        max_cpu_percent: Maximum CPU usage (not enforced on Windows)
        allow_network: Whether to allow network access
        allow_file_write: Whether to allow file write operations
    
    Returns:
        dict: Applied limits information
    """
    applied = {
        "platform": platform.system(),
        "memory_limit": None,
        "network_blocked": False,
        "file_write_blocked": False,
    }
    
    system = platform.system()
    
    if system == "Linux":
        try:
            import resource
            # Set memory limit (soft and hard)
            memory_bytes = max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            applied["memory_limit"] = max_memory_mb
            
            # Limit CPU time if not 100%
            if max_cpu_percent < 100:
                # Use RLIMIT_CPU for CPU seconds limit
                cpu_seconds = 30 * (max_cpu_percent / 100)
                resource.setrlimit(resource.RLIMIT_CPU, (int(cpu_seconds), int(cpu_seconds)))
            
            # Limit file descriptors to prevent resource leaks
            resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        except (ImportError, ValueError, OSError) as e:
            applied["resource_error"] = str(e)
    
    elif system == "Windows":
        # Windows: Use Job Objects via ctypes or psutil if available
        try:
            import psutil
            process = psutil.Process(os.getpid())
            # Note: Windows doesn't support hard memory limits easily
            # We can only monitor and terminate if exceeded
            applied["memory_limit"] = f"{max_memory_mb}MB (monitoring only)"
        except ImportError:
            applied["memory_limit"] = "psutil not available"
    
    return applied


# ============================================================================
# Sandbox Environment (Copied from strategy_sandbox.py with enhancements)
# ============================================================================

class SandboxExecutionError(Exception):
    """Raised when sandbox execution fails."""
    pass


# Modules allowed for import in strategy code
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

# Dangerous attributes to block via attribute access
BLOCKED_ATTRIBUTES = {
    "__subclasses__",
    "__bases__",
    "__mro__",
    "__globals__",
    "__code__",
    "__reduce__",
    "__reduce_ex__",
    "__class__",
    "__init_subclass__",
    "__set_name__",
}


def _safe_getattr(obj: Any, name: str, default: Any = None) -> Any:
    """Safe getattr that blocks dangerous attribute access."""
    if name in BLOCKED_ATTRIBUTES:
        raise SandboxExecutionError(f"Access to attribute '{name}' is blocked for security")
    return py_builtins.getattr(obj, name, default)


def _safe_import(name: str, globals=None, locals=None, fromlist=(), level: int = 0):
    """Safe import that only allows whitelisted modules."""
    if level != 0:
        raise SandboxExecutionError("Relative imports are not allowed in strategy code")
    root = name.split(".", 1)[0]
    if root not in ALLOWED_IMPORTS:
        raise SandboxExecutionError(f"Import of module '{root}' is not permitted")
    try:
        module = importlib.import_module(name)
        # Strip __builtins__ from imported modules
        if hasattr(module, "__dict__"):
            module.__dict__.pop("__builtins__", None)
        return module
    except ImportError as exc:
        raise SandboxExecutionError(f"Failed to import module '{name}': {exc}") from exc


def _build_safe_builtins(allow_file_write: bool = False) -> Dict[str, Any]:
    """Build restricted builtins for sandbox environment."""
    allowed = {
        # Safe functions
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
        "print": py_builtins.print,  # Will be redirected
        "property": py_builtins.property,
        "range": py_builtins.range,
        "repr": py_builtins.repr,
        "reversed": py_builtins.reversed,
        "round": py_builtins.round,
        "set": py_builtins.set,
        "slice": py_builtins.slice,
        "sorted": py_builtins.sorted,
        "staticmethod": py_builtins.staticmethod,
        "str": py_builtins.str,
        "sum": py_builtins.sum,
        "super": py_builtins.super,
        "tuple": py_builtins.tuple,
        "type": py_builtins.type,
        "zip": py_builtins.zip,
        "__build_class__": py_builtins.__build_class__,
        
        # Exceptions
        "BaseException": py_builtins.BaseException,
        "Exception": py_builtins.Exception,
        "ValueError": py_builtins.ValueError,
        "RuntimeError": py_builtins.RuntimeError,
        "KeyError": py_builtins.KeyError,
        "TypeError": py_builtins.TypeError,
        "AttributeError": py_builtins.AttributeError,
        "IndexError": py_builtins.IndexError,
        "NameError": py_builtins.NameError,
        "NotImplementedError": py_builtins.NotImplementedError,
        "StopIteration": py_builtins.StopIteration,
        "ZeroDivisionError": py_builtins.ZeroDivisionError,
        
        # Base types
        "object": py_builtins.object,
        "classmethod": py_builtins.classmethod,
        
        # Constants
        "True": True,
        "False": False,
        "None": None,
        
        # Safe attribute access
        "getattr": _safe_getattr,
        "hasattr": py_builtins.hasattr,
        "setattr": py_builtins.setattr,
        "delattr": py_builtins.delattr,
        "vars": py_builtins.vars,
        
        # Safe import
        "__import__": _safe_import,
    }
    
    # NOTE: 'open' is explicitly NOT included - file access blocked by default
    
    return allowed


def execute_in_sandbox(
    source: str,
    module_name: str,
    filename: str,
    allow_file_write: bool = False
) -> Dict[str, Any]:
    """
    Execute strategy code in sandboxed environment.
    
    Args:
        source: Strategy source code
        module_name: Module name for the strategy
        filename: Virtual filename for error messages
        allow_file_write: Whether to allow file operations
    
    Returns:
        dict: Execution result with globals and any strategy class found
    """
    # Pre-import allowed modules to make them available
    try:
        import backtrader as bt
        import pandas as pd
    except ImportError as e:
        raise SandboxExecutionError(f"Required module not available: {e}")
    
    # Build sandbox globals
    sandbox_globals: Dict[str, Any] = {
        "__name__": module_name,
        "__package__": None,
        "__doc__": None,
        "__builtins__": _build_safe_builtins(allow_file_write),
        "__file__": filename,
        "bt": bt,
        "pd": pd,
    }
    
    # Compile first to catch syntax errors
    try:
        bytecode = compile(source, filename, "exec")
    except SyntaxError as exc:
        raise SandboxExecutionError(f"Strategy contains syntax errors: {exc}") from exc
    
    # Execute in sandbox
    try:
        exec(bytecode, sandbox_globals)
    except SandboxExecutionError:
        raise
    except Exception as exc:
        raise SandboxExecutionError(f"Strategy execution failed: {exc}") from exc
    
    # Find UserStrategy class if present
    result = {
        "globals": {},
        "strategy_class": None,
        "strategy_params": [],
    }
    
    def is_json_serializable(val):
        """Check if a value is JSON serializable."""
        if val is None:
            return True
        if isinstance(val, (bool, int, float, str)):
            return True
        if isinstance(val, (list, tuple)):
            return all(is_json_serializable(item) for item in val)
        if isinstance(val, dict):
            return all(
                isinstance(k, str) and is_json_serializable(v) 
                for k, v in val.items()
            )
        return False
    
    # Extract serializable values from globals
    for key, value in sandbox_globals.items():
        if key.startswith("_"):
            continue
        if key in ("bt", "pd"):
            continue
        # Only include primitives that are definitely JSON serializable
        if isinstance(value, (int, float, str, bool)) or value is None:
            result["globals"][key] = value
        elif isinstance(value, (list, tuple)):
            # Only include if all items are serializable
            if is_json_serializable(value):
                result["globals"][key] = list(value) if isinstance(value, tuple) else value
        elif isinstance(value, dict):
            if is_json_serializable(value):
                result["globals"][key] = value
        elif isinstance(value, type):
            # Check if it's a strategy class
            try:
                import backtrader as bt_check
                if issubclass(value, bt_check.Strategy):
                    result["strategy_class"] = key
                    # Extract params - only include JSON-serializable values
                    params_cls = py_builtins.getattr(value, 'params', None)
                    if params_cls and py_builtins.hasattr(params_cls, '_getdefaults'):
                        try:
                            defaults = params_cls._getdefaults()
                            for param_name in defaults:
                                param_value = py_builtins.getattr(params_cls, param_name, None)
                                # Only include serializable param values
                                if is_json_serializable(param_value):
                                    result["strategy_params"].append({
                                        "name": str(param_name),
                                        "value": param_value,
                                        "type": type(param_value).__name__
                                    })
                        except Exception:
                            pass
            except Exception:
                pass
    
    return result


def validate_source(source: str) -> Dict[str, Any]:
    """
    Validate strategy source code without executing.
    
    Args:
        source: Strategy source code to validate
    
    Returns:
        dict: Validation result
    """
    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
    }
    
    # Check syntax
    try:
        compile(source, "<strategy>", "exec")
    except SyntaxError as e:
        result["errors"].append(f"Syntax error at line {e.lineno}: {e.msg}")
        return result
    
    # Check for dangerous patterns
    dangerous_patterns = [
        ("__subclasses__", "Accessing __subclasses__ is blocked"),
        ("__bases__", "Accessing __bases__ is blocked"),
        ("__globals__", "Accessing __globals__ is blocked"),
        ("__code__", "Accessing __code__ is blocked"),
        ("eval(", "eval() is not available"),
        ("exec(", "exec() is not available"),
        ("compile(", "compile() is not available"),
        ("__import__('os", "Module 'os' is not permitted"),
        ("__import__('sys", "Module 'sys' is not permitted"),
        ("__import__('subprocess", "Module 'subprocess' is not permitted"),
    ]
    
    for pattern, warning in dangerous_patterns:
        if pattern in source:
            result["warnings"].append(warning)
    
    # Check for required UserStrategy class
    if "class UserStrategy" not in source:
        result["warnings"].append("No 'UserStrategy' class found - strategy may not run")
    
    if "bt.Strategy" not in source and "backtrader.Strategy" not in source:
        result["warnings"].append("UserStrategy should inherit from bt.Strategy")
    
    result["valid"] = len(result["errors"]) == 0
    return result


# ============================================================================
# IPC Protocol Handler
# ============================================================================

def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming request from parent process.
    
    Args:
        request: Request dictionary with 'action' and other fields
    
    Returns:
        dict: Response dictionary
    """
    action = request.get("action")
    
    if action == "execute":
        source = request.get("source", "")
        module_name = request.get("module_name", "user_strategy")
        filename = request.get("filename", "<strategy>")
        allow_file_write = request.get("allow_file_write", False)
        
        try:
            result = execute_in_sandbox(
                source=source,
                module_name=module_name,
                filename=filename,
                allow_file_write=allow_file_write
            )
            return {
                "success": True,
                "result": result,
            }
        except SandboxExecutionError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "SandboxExecutionError",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
            }
    
    elif action == "validate":
        source = request.get("source", "")
        result = validate_source(source)
        return {
            "success": True,
            "result": result,
        }
    
    elif action == "ping":
        return {
            "success": True,
            "result": {"status": "alive"},
        }
    
    elif action == "shutdown":
        return {
            "success": True,
            "result": {"status": "shutting_down"},
        }
    
    else:
        return {
            "success": False,
            "error": f"Unknown action: {action}",
            "error_type": "ValueError",
        }


def main():
    """
    Main entry point for subprocess executor.
    
    Reads JSON requests from stdin, processes them, and writes JSON responses to stdout.
    """
    # Apply resource limits based on environment
    max_memory_mb = int(os.getenv("SANDBOX_MAX_MEMORY_MB", "512"))
    max_cpu_percent = int(os.getenv("SANDBOX_MAX_CPU_PERCENT", "100"))
    allow_network = os.getenv("SANDBOX_ALLOW_NETWORK", "false").lower() == "true"
    allow_file_write = os.getenv("SANDBOX_ALLOW_FILE_WRITE", "false").lower() == "true"
    
    limits = apply_resource_limits(
        max_memory_mb=max_memory_mb,
        max_cpu_percent=max_cpu_percent,
        allow_network=allow_network,
        allow_file_write=allow_file_write
    )
    
    # Signal ready
    startup_message = {
        "type": "ready",
        "pid": os.getpid(),
        "limits": limits,
    }
    sys.stdout.write(json.dumps(startup_message) + "\n")
    sys.stdout.flush()
    
    # Main loop - process requests
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            response = {
                "success": False,
                "error": f"Invalid JSON: {e}",
                "error_type": "JSONDecodeError",
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue
        
        # Handle request
        response = handle_request(request)
        
        # Send response
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
        
        # Check for shutdown
        if request.get("action") == "shutdown":
            break
    
    sys.exit(0)


if __name__ == "__main__":
    main()
