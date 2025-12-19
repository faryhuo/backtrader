import pytest

from src.service.strategy_sandbox import StrategySandboxError, execute_strategy_code


def test_strategy_sandbox_allows_whitelisted_import():
    code = "import math\nx = math.sqrt(9)\n"
    g = execute_strategy_code(code, module_name="strategy_test_ok", filename="strategy_test_ok.py")
    assert g["x"] == 3.0


def test_strategy_sandbox_blocks_non_whitelisted_import():
    code = "import os\n"
    with pytest.raises(StrategySandboxError) as excinfo:
        execute_strategy_code(code, module_name="strategy_test_bad", filename="strategy_test_bad.py")
    assert "not permitted" in str(excinfo.value)


def test_strategy_sandbox_blocks_relative_import():
    code = "from . import something\n"
    with pytest.raises(StrategySandboxError) as excinfo:
        execute_strategy_code(code, module_name="strategy_test_rel", filename="strategy_test_rel.py")
    assert "Relative imports are not allowed" in str(excinfo.value)


def test_strategy_sandbox_missing_builtin_is_blocked():
    code = "open('x', 'w')\n"
    with pytest.raises(StrategySandboxError) as excinfo:
        execute_strategy_code(code, module_name="strategy_test_open", filename="strategy_test_open.py")
    assert "Strategy execution failed" in str(excinfo.value)


def test_strategy_sandbox_syntax_error_is_wrapped():
    code = "def f(:\n  pass\n"
    with pytest.raises(StrategySandboxError) as excinfo:
        execute_strategy_code(code, module_name="strategy_test_syntax", filename="strategy_test_syntax.py")
    assert "syntax errors" in str(excinfo.value).lower()

