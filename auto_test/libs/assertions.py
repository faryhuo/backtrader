"""
Custom Assertion Helpers

Provides reusable assertion functions for:
- API response validation
- Schema validation
- Error message matching
- Metric validation
"""

from typing import Any, Dict, List, Optional
import httpx


def assert_api_response(
    response: httpx.Response,
    expected_status: int = 200,
    expected_keys: Optional[List[str]] = None,
):
    """
    Assert API response is valid.

    Args:
        response: httpx Response object
        expected_status: Expected HTTP status code
        expected_keys: Expected keys in JSON response

    Raises:
        AssertionError: If response doesn't match expectations
    """
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}. "
        f"Response: {response.text}"
    )
    
    if expected_keys:
        try:
            data = response.json()
        except Exception as e:
            raise AssertionError(f"Failed to parse JSON response: {e}")
        
        for key in expected_keys:
            assert key in data, f"Expected key '{key}' not found in response: {data}"


def assert_api_error(
    response: httpx.Response,
    expected_status: int,
    expected_error_substring: Optional[str] = None,
):
    """
    Assert API returns expected error.

    Args:
        response: httpx Response object
        expected_status: Expected error status code
        expected_error_substring: Expected substring in error message

    Raises:
        AssertionError: If error response doesn't match expectations
    """
    assert response.status_code == expected_status, (
        f"Expected error status {expected_status}, got {response.status_code}"
    )
    
    if expected_error_substring:
        response_text = response.text.lower()
        try:
            error_data = response.json()
            detail = error_data.get("detail", "").lower()
        except:
            detail = response_text
        
        assert expected_error_substring.lower() in detail, (
            f"Expected error substring '{expected_error_substring}' not found in: {detail}"
        )


def assert_backtest_metrics(metrics: Dict[str, Any]):
    """
    Assert backtest metrics have expected structure and reasonable values.

    Args:
        metrics: Metrics dictionary

    Raises:
        AssertionError: If metrics are invalid
    """
    required_keys = [
        "total_return",
        "sharpe_ratio",
        "max_drawdown",
        "total_trades",
    ]
    
    for key in required_keys:
        assert key in metrics, f"Missing required metric: {key}"
    
    # Validate value types and ranges
    assert isinstance(metrics["total_trades"], (int, float)), (
        "total_trades should be numeric"
    )
    assert metrics["total_trades"] >= 0, "total_trades should be non-negative"
    
    # Max drawdown should be negative or zero
    if "max_drawdown" in metrics and metrics["max_drawdown"] is not None:
        assert metrics["max_drawdown"] <= 0, "max_drawdown should be <= 0"


def assert_strategy_params(params: List[Dict[str, Any]]):
    """
    Assert strategy parameters have expected structure.

    Args:
        params: List of parameter dictionaries

    Raises:
        AssertionError: If parameters are invalid
    """
    for param in params:
        assert "name" in param, "Parameter missing 'name' field"
        assert "value" in param, "Parameter missing 'value' field"
        assert "type" in param, "Parameter missing 'type' field"
        
        # Validate type is one of expected values
        valid_types = ["int", "float", "str", "bool"]
        assert param["type"] in valid_types, (
            f"Parameter type '{param['type']}' not in {valid_types}"
        )


def assert_session_response(session: Dict[str, Any]):
    """
    Assert live trading session response has expected structure.

    Args:
        session: Session dictionary

    Raises:
        AssertionError: If session structure is invalid
    """
    required_keys = [
        "session_id",
        "status",
        "strategy_name",
        "symbol",
        "exchange",
        "mode",
    ]
    
    for key in required_keys:
        assert key in session, f"Missing required session field: {key}"
    
    # Validate status
    valid_statuses = ["starting", "running", "stopped", "error"]
    assert session["status"] in valid_statuses, (
        f"Invalid session status: {session['status']}"
    )
    
    # Validate mode
    valid_modes = ["paper", "live"]
    assert session["mode"] in valid_modes, (
        f"Invalid trading mode: {session['mode']}"
    )


def assert_portfolio_result(result: Dict[str, Any]):
    """
    Assert portfolio backtest result has expected structure.

    Args:
        result: Portfolio result dictionary

    Raises:
        AssertionError: If result structure is invalid
    """
    assert "portfolio_metrics" in result, "Missing portfolio_metrics"
    assert "symbol_results" in result, "Missing symbol_results"
    
    # Validate symbol results is a dict or list
    assert isinstance(result["symbol_results"], (dict, list)), (
        "symbol_results should be dict or list"
    )


def assert_walkforward_result(result: Dict[str, Any]):
    """
    Assert walk-forward optimization result has expected structure.

    Args:
        result: Walk-forward result dictionary

    Raises:
        AssertionError: If result structure is invalid
    """
    required_keys = [
        "optimization_id",
        "status",
        "best_params",
    ]
    
    for key in required_keys:
        assert key in result, f"Missing required field: {key}"
    
    # If completed, should have results
    if result["status"] == "completed":
        assert "all_train_results" in result or "metrics" in result, (
            "Completed optimization should have results"
        )


def assert_list_response(
    response_data: Dict[str, Any],
    expected_total_key: str = "total",
    expected_items_key: str = "items",
):
    """
    Assert paginated list response has expected structure.

    Args:
        response_data: Response data dictionary
        expected_total_key: Key for total count
        expected_items_key: Key for items list

    Raises:
        AssertionError: If list response is invalid
    """
    assert expected_total_key in response_data, (
        f"Missing {expected_total_key} in list response"
    )
    assert expected_items_key in response_data, (
        f"Missing {expected_items_key} in list response"
    )

    assert isinstance(response_data[expected_items_key], list), (
        f"{expected_items_key} should be a list"
    )

    total = response_data[expected_total_key]
    items_count = len(response_data[expected_items_key])

    assert total >= items_count, (
        f"Total ({total}) should be >= items count ({items_count})"
    )


def assert_task_response(task: Dict[str, Any]):
    """
    Assert task response has expected structure.

    Args:
        task: Task dictionary

    Raises:
        AssertionError: If task structure is invalid
    """
    required_keys = [
        "task_id",
        "task_type",
        "status",
    ]

    for key in required_keys:
        assert key in task, f"Missing required task field: {key}"

    # Validate task_type
    valid_types = ["backtest", "portfolio", "walkforward", "deep_analysis"]
    assert task["task_type"] in valid_types, (
        f"Invalid task type: {task['task_type']}"
    )

    # Validate status
    valid_statuses = ["pending", "running", "completed", "failed", "cancelled"]
    assert task["status"] in valid_statuses, (
        f"Invalid task status: {task['status']}"
    )


def assert_settings_response(settings: Dict[str, Any]):
    """
    Assert settings response has expected structure.

    Args:
        settings: Settings dictionary

    Raises:
        AssertionError: If settings structure is invalid
    """
    expected_keys = [
        "selected_models",
        "code_analysis_prompt",
        "code_rewrite_prompt",
        "full_strategy_analysis_prompt",
    ]

    for key in expected_keys:
        assert key in settings, f"Missing settings field: {key}"

    assert isinstance(settings["selected_models"], list), (
        "selected_models should be a list"
    )
    assert len(settings["selected_models"]) > 0, (
        "selected_models should not be empty"
    )


def assert_cache_stats_response(stats: Dict[str, Any]):
    """
    Assert cache stats response has expected structure.

    Args:
        stats: Cache stats dictionary

    Raises:
        AssertionError: If stats structure is invalid
    """
    # Should be a dictionary with cache information
    assert isinstance(stats, dict), "Cache stats should be a dictionary"
