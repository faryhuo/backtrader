"""
Isolated Sandbox - Subprocess-based Strategy Execution

This module provides a secure sandbox for executing user strategy code in an
isolated subprocess with resource limits in place.

Example:
    from src.service.isolated_sandbox import IsolatedSandbox, SandboxError
    
    sandbox = IsolatedSandbox(timeout=30.0, max_memory_mb=512)
    try:
        result = sandbox.execute_strategy(source_code, "my_strategy", "my_strategy.py")
        strategy_class = result.get("strategy_class")
    except SandboxError as e:
        print(f"Sandbox error: {e}")
"""

import json
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import backtrader as bt

from src.config.sandbox_config import SandboxConfig, get_config
from src.service.strategy_sandbox import StrategySandboxError, execute_strategy_code

logger = logging.getLogger(__name__)

# Path to the executor script
EXECUTOR_SCRIPT = Path(__file__).parent / "strategy_executor.py"


def _is_frozen_app() -> bool:
    """Return True when running from a frozen executable."""
    return getattr(sys, "frozen", False)


def _build_in_process_result(module_globals: Dict[str, Any]) -> Dict[str, Any]:
    """Build an executor-compatible response for frozen-app fallback mode."""
    result = {
        "globals": {},
        "strategy_class": None,
        "strategy_params": [],
    }

    def is_json_serializable(val: Any) -> bool:
        if val is None:
            return True
        if isinstance(val, (bool, int, float, str)):
            return True
        if isinstance(val, (list, tuple)):
            return all(is_json_serializable(item) for item in val)
        if isinstance(val, dict):
            return all(isinstance(k, str) and is_json_serializable(v) for k, v in val.items())
        return False

    for key, value in module_globals.items():
        if key.startswith("_") or key in {"bt", "pd"}:
            continue
        if isinstance(value, (int, float, str, bool)) or value is None:
            result["globals"][key] = value
            continue
        if isinstance(value, (list, tuple)) and is_json_serializable(value):
            result["globals"][key] = list(value) if isinstance(value, tuple) else value
            continue
        if isinstance(value, dict) and is_json_serializable(value):
            result["globals"][key] = value
            continue
        if not isinstance(value, type):
            continue
        try:
            if not issubclass(value, bt.Strategy):
                continue
        except TypeError:
            continue

        result["strategy_class"] = key
        params_cls = getattr(value, "params", None)
        if not params_cls or not hasattr(params_cls, "_getdefaults"):
            continue
        try:
            defaults = params_cls._getdefaults()
        except Exception:
            continue
        for param_name in defaults:
            param_value = getattr(params_cls, param_name, None)
            if not is_json_serializable(param_value):
                continue
            result["strategy_params"].append(
                {
                    "name": str(param_name),
                    "value": param_value,
                    "type": type(param_value).__name__,
                }
            )

    return result


class SandboxError(Exception):
    """Base exception for sandbox errors."""
    pass


class SandboxTimeoutError(SandboxError):
    """Raised when strategy execution times out."""
    pass


class SandboxMemoryError(SandboxError):
    """Raised when strategy exceeds memory limit."""
    pass


class SandboxExecutionError(SandboxError):
    """Raised when strategy execution fails."""
    pass


class IsolatedSandbox:
    """
    Subprocess-based isolated sandbox for strategy execution.
    
    This sandbox runs user strategy code in a separate Python process with:
    - Memory limits
    - Execution timeout
    - Restricted imports
    - Blocked dangerous builtins
    
    Attributes:
        timeout: Maximum execution time in seconds
        max_memory_mb: Maximum memory usage in MB
        allow_network: Whether to allow network access
        allow_file_write: Whether to allow file write operations
    """
    
    def __init__(
        self,
        timeout: float = 30.0,
        max_memory_mb: int = 512,
        allow_network: bool = False,
        allow_file_write: bool = False,
        config: Optional[SandboxConfig] = None
    ):
        """
        Initialize the isolated sandbox.
        
        Args:
            timeout: Maximum execution time in seconds
            max_memory_mb: Maximum memory in MB
            allow_network: Whether to allow network access
            allow_file_write: Whether to allow file write operations
            config: Optional SandboxConfig to override individual settings
        """
        if config:
            self.timeout = config.timeout_seconds
            self.max_memory_mb = config.max_memory_mb
            self.allow_network = config.allow_network
            self.allow_file_write = config.allow_file_write
        else:
            self.timeout = timeout
            self.max_memory_mb = max_memory_mb
            self.allow_network = allow_network
            self.allow_file_write = allow_file_write
        
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
    
    def _start_executor(self) -> subprocess.Popen:
        """
        Start a new executor subprocess.
        
        Returns:
            Popen: The subprocess handle
        """
        env = os.environ.copy()
        env.update({
            "SANDBOX_MAX_MEMORY_MB": str(self.max_memory_mb),
            "SANDBOX_ALLOW_NETWORK": str(self.allow_network).lower(),
            "SANDBOX_ALLOW_FILE_WRITE": str(self.allow_file_write).lower(),
        })
        
        process = subprocess.Popen(
            [sys.executable, str(EXECUTOR_SCRIPT)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1,  # Line buffered
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        
        # Wait for ready message
        try:
            ready_line = process.stdout.readline()
            if ready_line:
                ready_msg = json.loads(ready_line)
                if ready_msg.get("type") == "ready":
                    logger.debug(
                        f"Executor started: PID={ready_msg.get('pid')}, "
                        f"limits={ready_msg.get('limits')}"
                    )
                    return process
        except (json.JSONDecodeError, TimeoutError) as e:
            process.kill()
            raise SandboxError(f"Failed to start executor: {e}")
        
        # If we get here, something went wrong
        stderr_output = process.stderr.read()
        process.kill()
        raise SandboxError(f"Executor failed to start: {stderr_output}")
    
    def _send_request(
        self,
        process: subprocess.Popen,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send a request to the executor and wait for response.
        
        Args:
            process: The executor subprocess
            request: Request dictionary
        
        Returns:
            dict: Response from executor
        """
        # Send request
        request_json = json.dumps(request) + "\n"
        process.stdin.write(request_json)
        process.stdin.flush()
        
        # Read response with timeout
        response_line = process.stdout.readline()
        if not response_line:
            stderr = process.stderr.read()
            raise SandboxError(f"Executor returned empty response. stderr: {stderr}")
        
        try:
            return json.loads(response_line)
        except json.JSONDecodeError as e:
            raise SandboxError(f"Invalid response from executor: {e}")
    
    def execute_strategy(
        self,
        source: str,
        module_name: str,
        filename: str
    ) -> Dict[str, Any]:
        """
        Execute strategy code in isolated subprocess.
        
        Args:
            source: Strategy source code
            module_name: Module name for the strategy
            filename: Virtual filename for error messages
        
        Returns:
            dict: Execution result containing:
                - globals: Serializable global values
                - strategy_class: Name of UserStrategy class if found
                - strategy_params: List of strategy parameters
        
        Raises:
            SandboxError: If execution fails
            SandboxTimeoutError: If execution times out
        """
        if _is_frozen_app():
            logger.warning(
                "Frozen executable detected; isolated subprocess sandbox is unavailable. "
                "Falling back to in-process strategy validation."
            )
            try:
                module_globals = execute_strategy_code(
                    source,
                    module_name=module_name,
                    filename=filename,
                )
            except StrategySandboxError as exc:
                raise SandboxExecutionError(str(exc)) from exc
            return _build_in_process_result(module_globals)

        with self._lock:
            process = None
            try:
                # Start executor
                process = self._start_executor()
                
                # Build request
                request = {
                    "action": "execute",
                    "source": source,
                    "module_name": module_name,
                    "filename": filename,
                    "allow_file_write": self.allow_file_write,
                }
                
                # Execute with timeout
                def execute():
                    return self._send_request(process, request)
                
                # Use threading for timeout on Windows
                result_container: List[Optional[Dict[str, Any]]] = [None]
                error_container: List[Optional[Exception]] = [None]
                
                def worker():
                    try:
                        result_container[0] = execute()
                    except Exception as e:
                        error_container[0] = e
                
                thread = threading.Thread(target=worker)
                thread.start()
                thread.join(timeout=self.timeout)
                
                if thread.is_alive():
                    # Timeout - kill the process
                    logger.warning(f"Strategy execution timed out after {self.timeout}s")
                    process.kill()
                    thread.join(timeout=1.0)
                    raise SandboxTimeoutError(
                        f"Strategy execution timed out after {self.timeout} seconds"
                    )
                
                if error_container[0]:
                    raise error_container[0]
                
                response = result_container[0]
                if response is None:
                    raise SandboxError("No response from executor")
                
                # Check response
                if not response.get("success"):
                    error_type = response.get("error_type", "SandboxError")
                    error_msg = response.get("error", "Unknown error")
                    
                    if "MemoryError" in error_type or "memory" in error_msg.lower():
                        raise SandboxMemoryError(error_msg)
                    
                    raise SandboxExecutionError(error_msg)
                
                return response.get("result", {})
            
            finally:
                # Cleanup
                if process:
                    try:
                        # Send shutdown
                        try:
                            process.stdin.write(json.dumps({"action": "shutdown"}) + "\n")
                            process.stdin.flush()
                            process.wait(timeout=1.0)
                        except Exception:
                            pass
                        
                        if process.poll() is None:
                            process.kill()
                            process.wait(timeout=1.0)
                    except Exception as e:
                        logger.debug(f"Error cleaning up executor: {e}")
    
    def validate_strategy(self, source: str) -> Dict[str, Any]:
        """
        Validate strategy source code without executing.
        
        Args:
            source: Strategy source code
        
        Returns:
            dict: Validation result with:
                - valid: bool
                - errors: List of error messages
                - warnings: List of warning messages
        """
        if _is_frozen_app():
            logger.warning(
                "Frozen executable detected; validating strategy in-process because the "
                "isolated subprocess sandbox is unavailable."
            )
            try:
                execute_strategy_code(
                    source,
                    module_name="strategy_validation",
                    filename="<strategy_validation>",
                )
            except StrategySandboxError as exc:
                return {"valid": False, "errors": [str(exc)], "warnings": []}
            return {
                "valid": True,
                "errors": [],
                "warnings": [
                    "PyInstaller executable mode uses in-process validation instead of the "
                    "isolated subprocess sandbox."
                ],
            }

        with self._lock:
            process = None
            try:
                process = self._start_executor()
                
                request = {
                    "action": "validate",
                    "source": source,
                }
                
                response = self._send_request(process, request)
                
                if not response.get("success"):
                    return {
                        "valid": False,
                        "errors": [response.get("error", "Validation failed")],
                        "warnings": [],
                    }
                
                return response.get("result", {"valid": False, "errors": [], "warnings": []})
            
            finally:
                if process:
                    try:
                        process.kill()
                        process.wait(timeout=1.0)
                    except Exception:
                        pass


# ============================================================================
# Convenience Functions
# ============================================================================

def execute_strategy_code_isolated(
    source: str,
    *,
    module_name: str,
    filename: str,
    timeout: Optional[float] = None,
    max_memory_mb: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute strategy code in isolated subprocess.
    
    This is a convenience function that creates a temporary IsolatedSandbox.
    For repeated executions, prefer creating a single IsolatedSandbox instance.
    
    Args:
        source: Strategy source code
        module_name: Module name for the strategy
        filename: Virtual filename for error messages
        timeout: Optional timeout override
        max_memory_mb: Optional memory limit override
    
    Returns:
        dict: Execution result
    
    Raises:
        SandboxError: If execution fails
    """
    config = get_config()
    
    sandbox = IsolatedSandbox(
        timeout=timeout or config.timeout_seconds,
        max_memory_mb=max_memory_mb or config.max_memory_mb,
        allow_network=config.allow_network,
        allow_file_write=config.allow_file_write,
    )
    
    return sandbox.execute_strategy(source, module_name, filename)


def validate_strategy_code(source: str) -> Dict[str, Any]:
    """
    Validate strategy source code.
    
    Args:
        source: Strategy source code
    
    Returns:
        dict: Validation result
    """
    sandbox = IsolatedSandbox()
    return sandbox.validate_strategy(source)


__all__ = [
    "IsolatedSandbox",
    "SandboxError",
    "SandboxTimeoutError",
    "SandboxMemoryError",
    "SandboxExecutionError",
    "execute_strategy_code_isolated",
    "validate_strategy_code",
]
