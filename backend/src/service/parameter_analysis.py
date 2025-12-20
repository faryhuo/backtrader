"""
Parameter Analysis Module

Provides parameter sensitivity analysis and visualization data for walk-forward optimization:
- Parameter sensitivity scoring
- 2D heatmap matrix generation
- Overfitting score calculation (0-100 scale)
"""

import logging
from collections import defaultdict
from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_parameter_sensitivity(
    all_results: List[Dict[str, Any]],
    metric: str = "sharpe_ratio",
) -> Dict[str, float]:
    """
    Calculate sensitivity score for each parameter.
    
    Sensitivity is measured as the variance in performance when varying
    a single parameter while holding others constant.
    
    Args:
        all_results: List of backtest results with 'params' and metric values
        metric: The metric to analyze (e.g., 'sharpe_ratio', 'total_return')
    
    Returns:
        Dictionary mapping parameter names to sensitivity scores (0-100)
    """
    if not all_results:
        return {}
    
    # Extract all unique parameters
    param_names = set()
    for result in all_results:
        params = result.get("params", {})
        param_names.update(params.keys())
    
    if not param_names:
        return {}
    
    sensitivities = {}
    
    for param_name in param_names:
        # Group results by other parameters (excluding current one)
        other_params = param_names - {param_name}
        groups = defaultdict(list)
        
        for result in all_results:
            params = result.get("params", {})
            metric_value = result.get(metric)
            
            if metric_value is None:
                continue
            
            # Create key from other parameters
            key = tuple(sorted((k, params.get(k)) for k in other_params))
            groups[key].append(metric_value)
        
        # Calculate variance within each group
        variances = []
        for values in groups.values():
            if len(values) > 1:
                variances.append(np.var(values))
        
        # Sensitivity is the average variance
        if variances:
            sensitivities[param_name] = float(np.mean(variances))
        else:
            sensitivities[param_name] = 0.0
    
    # Normalize to 0-100 scale
    if sensitivities:
        max_sensitivity = max(sensitivities.values()) if max(sensitivities.values()) > 0 else 1
        sensitivities = {
            k: round((v / max_sensitivity) * 100, 2)
            for k, v in sensitivities.items()
        }
    
    return sensitivities


def build_parameter_grid_matrix(
    all_results: List[Dict[str, Any]],
    param1: str,
    param2: str,
    metric: str = "sharpe_ratio",
) -> Dict[str, Any]:
    """
    Build 2D matrix for heatmap visualization.
    
    Args:
        all_results: List of backtest results
        param1: Name of first parameter (X-axis)
        param2: Name of second parameter (Y-axis)
        metric: The metric to visualize
    
    Returns:
        Dictionary with:
        - x_values: List of param1 values
        - y_values: List of param2 values
        - matrix: 2D array of metric values
        - min_value: Minimum metric value
        - max_value: Maximum metric value
        - optimal: Dict with optimal param1, param2, and metric value
    """
    if not all_results:
        return {
            "x_values": [],
            "y_values": [],
            "matrix": [],
            "min_value": 0,
            "max_value": 0,
            "optimal": None,
        }
    
    # Extract unique values for each parameter
    x_values = sorted(set(
        r.get("params", {}).get(param1) 
        for r in all_results 
        if r.get("params", {}).get(param1) is not None
    ))
    y_values = sorted(set(
        r.get("params", {}).get(param2) 
        for r in all_results 
        if r.get("params", {}).get(param2) is not None
    ))
    
    if not x_values or not y_values:
        return {
            "x_values": [],
            "y_values": [],
            "matrix": [],
            "min_value": 0,
            "max_value": 0,
            "optimal": None,
        }
    
    # Build lookup dictionary
    lookup = {}
    for result in all_results:
        params = result.get("params", {})
        p1_val = params.get(param1)
        p2_val = params.get(param2)
        metric_val = result.get(metric)
        
        if p1_val is not None and p2_val is not None and metric_val is not None:
            lookup[(p1_val, p2_val)] = metric_val
    
    # Build matrix (rows = y_values, cols = x_values)
    matrix = []
    all_values = []
    optimal = {"value": float("-inf"), "param1": None, "param2": None}
    
    for y_val in y_values:
        row = []
        for x_val in x_values:
            val = lookup.get((x_val, y_val))
            if val is not None:
                row.append(round(val, 4))
                all_values.append(val)
                if val > optimal["value"]:
                    optimal = {
                        "value": round(val, 4),
                        "param1": x_val,
                        "param2": y_val,
                        "param1_name": param1,
                        "param2_name": param2,
                    }
            else:
                row.append(None)
        matrix.append(row)
    
    return {
        "x_values": [str(v) for v in x_values],
        "y_values": [str(v) for v in y_values],
        "x_param": param1,
        "y_param": param2,
        "matrix": matrix,
        "min_value": round(min(all_values), 4) if all_values else 0,
        "max_value": round(max(all_values), 4) if all_values else 0,
        "optimal": optimal if optimal["param1"] is not None else None,
    }


def calculate_overfitting_score(overfitting_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate a 0-100 overfitting score from existing metrics.
    
    Score interpretation:
    - 0-30: Low risk (green) - Strategy is robust
    - 31-60: Medium risk (yellow) - Some overfitting concerns
    - 61-100: High risk (red) - Significant overfitting detected
    
    Args:
        overfitting_metrics: Existing overfitting metrics from optimizer
    
    Returns:
        Dictionary with:
        - score: 0-100 overfitting score
        - level: 'low', 'medium', or 'high'
        - factors: List of contributing factors
    """
    if not overfitting_metrics:
        return {"score": 0, "level": "low", "factors": []}
    
    score = 0
    factors = []
    
    # Factor 1: Average degradation (0-40 points)
    avg_degradation = abs(overfitting_metrics.get("avg_degradation_pct", 0))
    if avg_degradation > 50:
        degradation_score = 40
        factors.append({"name": "high_degradation", "impact": 40, "value": avg_degradation})
    elif avg_degradation > 30:
        degradation_score = 30
        factors.append({"name": "moderate_degradation", "impact": 30, "value": avg_degradation})
    elif avg_degradation > 20:
        degradation_score = 20
        factors.append({"name": "mild_degradation", "impact": 20, "value": avg_degradation})
    elif avg_degradation > 10:
        degradation_score = 10
        factors.append({"name": "slight_degradation", "impact": 10, "value": avg_degradation})
    else:
        degradation_score = 0
    score += degradation_score
    
    # Factor 2: Consistency score (0-30 points, inverted)
    consistency = overfitting_metrics.get("consistency_score", 100)
    if consistency < 30:
        consistency_score = 30
        factors.append({"name": "low_consistency", "impact": 30, "value": consistency})
    elif consistency < 50:
        consistency_score = 20
        factors.append({"name": "poor_consistency", "impact": 20, "value": consistency})
    elif consistency < 70:
        consistency_score = 10
        factors.append({"name": "moderate_consistency", "impact": 10, "value": consistency})
    else:
        consistency_score = 0
    score += consistency_score
    
    # Factor 3: Train-Test correlation (0-20 points, inverted)
    correlation = overfitting_metrics.get("train_test_correlation", 1)
    if correlation is None or pd.isna(correlation):
        correlation = 0
    if correlation < 0:
        correlation_score = 20
        factors.append({"name": "negative_correlation", "impact": 20, "value": correlation})
    elif correlation < 0.3:
        correlation_score = 15
        factors.append({"name": "weak_correlation", "impact": 15, "value": correlation})
    elif correlation < 0.5:
        correlation_score = 10
        factors.append({"name": "low_correlation", "impact": 10, "value": correlation})
    else:
        correlation_score = 0
    score += correlation_score
    
    # Factor 4: Degradation volatility (0-10 points)
    degradation_std = overfitting_metrics.get("degradation_std", 0)
    if degradation_std > 30:
        std_score = 10
        factors.append({"name": "high_volatility", "impact": 10, "value": degradation_std})
    elif degradation_std > 20:
        std_score = 5
        factors.append({"name": "moderate_volatility", "impact": 5, "value": degradation_std})
    else:
        std_score = 0
    score += std_score
    
    # Determine level
    if score <= 30:
        level = "low"
    elif score <= 60:
        level = "medium"
    else:
        level = "high"
    
    return {
        "score": round(score, 0),
        "level": level,
        "factors": factors,
    }


def get_parameter_analysis(
    windows: List[Any],
    param_grid: Dict[str, List[Any]],
    optimization_metric: str,
    overfitting_metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate complete parameter analysis data.
    
    Args:
        windows: List of OptimizationWindow objects
        param_grid: Parameter grid used for optimization
        optimization_metric: The metric that was optimized
        overfitting_metrics: Existing overfitting metrics
    
    Returns:
        Complete parameter analysis data including:
        - sensitivity: Parameter sensitivity rankings
        - heatmap: 2D grid matrix (if 2+ parameters)
        - surface3d: 3D surface data (same as heatmap, for frontend)
        - overfitting_score: 0-100 score with breakdown
        - all_results_aggregated: Aggregated results across all windows
    """
    if not windows or not param_grid:
        return {
            "sensitivity_ranking": [],
            "heatmap": None,
            "surface3d": None,
            "overfitting_score": {"score": 0, "level": "low", "factors": []},
            "all_results_aggregated": [],
            "param_count": 0,
            "optimization_metric": optimization_metric,
        }
    
    # Aggregate all training results across windows
    all_results = []
    for window in windows:
        if hasattr(window, "all_train_results") and window.all_train_results:
            all_results.extend(window.all_train_results)
        elif isinstance(window, dict) and window.get("all_train_results"):
            all_results.extend(window["all_train_results"])
    
    # Fallback: if no all_train_results available (old data), 
    # use best_params and train_metrics from each window
    if not all_results:
        logger.info("No all_train_results found, using window best_params as fallback")
        for window in windows:
            if isinstance(window, dict):
                best_params = window.get("best_params", {})
                train_metrics = window.get("train_metrics", {})
            else:
                best_params = getattr(window, "best_params", {})
                train_metrics = getattr(window, "train_metrics", {})
            
            if best_params and train_metrics:
                result_entry = {
                    "params": best_params,
                    **train_metrics,
                }
                all_results.append(result_entry)
    
    # If still no results, return empty analysis
    if not all_results:
        logger.warning("No parameter results found for analysis")
        return {
            "sensitivity_ranking": [],
            "heatmap": None,
            "surface3d": None,
            "overfitting_score": calculate_overfitting_score(overfitting_metrics or {}),
            "all_results_aggregated": [],
            "param_count": len(param_grid),
            "optimization_metric": optimization_metric,
        }

    
    # Calculate parameter sensitivity
    sensitivity = calculate_parameter_sensitivity(all_results, optimization_metric)
    
    # Sort parameters by sensitivity
    sensitivity_ranking = sorted(
        sensitivity.items(),
        key=lambda x: x[1],
        reverse=True,
    )
    
    # Build heatmap for top 2 parameters (or only parameter pair)
    param_names = list(param_grid.keys())
    heatmap = None
    surface3d = None
    
    if len(param_names) >= 2:
        # Use top 2 most sensitive parameters
        if len(sensitivity_ranking) >= 2:
            top_params = [sensitivity_ranking[0][0], sensitivity_ranking[1][0]]
        else:
            top_params = param_names[:2]
        
        heatmap = build_parameter_grid_matrix(
            all_results,
            top_params[0],
            top_params[1],
            optimization_metric,
        )
        # Surface3D uses the same data structure
        surface3d = heatmap
    elif len(param_names) == 1:
        # Single parameter - create 1D data for line chart
        param_name = param_names[0]
        values = sorted(set(
            r.get("params", {}).get(param_name)
            for r in all_results
            if r.get("params", {}).get(param_name) is not None
        ))
        
        data_points = []
        for val in values:
            metrics = [
                r.get(optimization_metric)
                for r in all_results
                if r.get("params", {}).get(param_name) == val
                and r.get(optimization_metric) is not None
            ]
            if metrics:
                data_points.append({
                    "param_value": val,
                    "metric_value": round(np.mean(metrics), 4),
                    "metric_std": round(np.std(metrics), 4) if len(metrics) > 1 else 0,
                })
        
        heatmap = {
            "type": "line",
            "param_name": param_name,
            "data_points": data_points,
        }
    
    # Calculate overfitting score
    overfitting_score = calculate_overfitting_score(overfitting_metrics or {})
    
    # Aggregate results for table display (average across windows)
    param_combinations = {}
    for result in all_results:
        params = result.get("params", {})
        key = tuple(sorted(params.items()))
        
        if key not in param_combinations:
            param_combinations[key] = {
                "params": params,
                "metrics": [],
            }
        param_combinations[key]["metrics"].append({
            "sharpe_ratio": result.get("sharpe_ratio"),
            "total_return": result.get("total_return"),
            "max_drawdown": result.get("max_drawdown"),
            "profit_factor": result.get("profit_factor"),
            "win_rate": result.get("win_rate"),
        })
    
    aggregated_results = []
    for combo in param_combinations.values():
        metrics_df = pd.DataFrame(combo["metrics"])
        aggregated = {
            "params": combo["params"],
            "avg_sharpe_ratio": round(metrics_df["sharpe_ratio"].mean(), 4) if not metrics_df["sharpe_ratio"].isna().all() else None,
            "avg_total_return": round(metrics_df["total_return"].mean(), 2) if not metrics_df["total_return"].isna().all() else None,
            "avg_max_drawdown": round(metrics_df["max_drawdown"].mean(), 2) if not metrics_df["max_drawdown"].isna().all() else None,
            "avg_profit_factor": round(metrics_df["profit_factor"].mean(), 4) if not metrics_df["profit_factor"].isna().all() else None,
            "avg_win_rate": round(metrics_df["win_rate"].mean(), 2) if not metrics_df["win_rate"].isna().all() else None,
            "count": len(combo["metrics"]),
        }
        aggregated_results.append(aggregated)
    
    # Sort by optimization metric
    metric_key = f"avg_{optimization_metric}"
    aggregated_results.sort(
        key=lambda x: x.get(metric_key) if x.get(metric_key) is not None else float("-inf"),
        reverse=True,
    )
    
    return {
        "sensitivity": dict(sensitivity_ranking),
        "sensitivity_ranking": [
            {"param": k, "score": v} for k, v in sensitivity_ranking
        ],
        "heatmap": heatmap,
        "surface3d": surface3d,
        "overfitting_score": overfitting_score,
        "all_results_aggregated": aggregated_results[:50],  # Limit to top 50
        "optimization_metric": optimization_metric,
        "param_count": len(param_names),
    }


__all__ = [
    "calculate_parameter_sensitivity",
    "build_parameter_grid_matrix",
    "calculate_overfitting_score",
    "get_parameter_analysis",
]
