"""
ECharts Theme Configuration and Chart Builders.

Provides centralized theme constants and reusable chart configuration builders
to decouple styling from data shaping in report generation.

Theme colors are synchronized with CSS variables defined in base.html.
"""

from typing import Any, Dict, List, Optional


# =============================================================================
# Theme Color Constants (matching CSS variables in base.html)
# =============================================================================

COLORS = {
    # Primary colors
    "accent": "#22d3ee",
    "accent_hover": "#06b6d4",
    "success": "#22c55e",
    "danger": "#ef4444",
    "warning": "#f59e0b",
    # Text colors
    "text_primary": "#fafafa",
    "text_secondary": "#a1a1aa",
    "text_muted": "#71717a",
    # Background colors
    "bg_primary": "#09090b",
    "bg_secondary": "#18181b",
    "bg_tertiary": "#27272a",
    # Border and transparency
    "border": "rgba(255, 255, 255, 0.1)",
    "border_strong": "rgba(255, 255, 255, 0.12)",
    "bg_tooltip": "rgba(24, 24, 27, 0.95)",
}


# =============================================================================
# Reusable Component Configurations
# =============================================================================

def get_tooltip_config() -> Dict[str, Any]:
    """Get standard tooltip configuration for dark theme."""
    return {
        "trigger": "axis",
        "backgroundColor": COLORS["bg_tooltip"],
        "borderColor": COLORS["border"],
        "textStyle": {"color": COLORS["text_primary"]},
    }


def get_axis_label_config(rotate: int = 0, interval: int = 0) -> Dict[str, Any]:
    """Get standard axis label configuration."""
    config = {
        "color": COLORS["text_secondary"],
        "fontSize": 11,
    }
    if rotate:
        config["rotate"] = rotate
    if interval:
        config["interval"] = interval
    return config


def get_axis_line_config() -> Dict[str, Any]:
    """Get standard axis line configuration."""
    return {"lineStyle": {"color": COLORS["border"]}}


def get_split_line_config() -> Dict[str, Any]:
    """Get standard split line configuration."""
    return {"lineStyle": {"color": "rgba(255, 255, 255, 0.05)"}}


def get_grid_config(
    left: str = "3%",
    right: str = "4%",
    top: str = "10%",
    bottom: str = "18%",
    contain_label: bool = True,
) -> Dict[str, Any]:
    """Get standard grid configuration."""
    return {
        "left": left,
        "right": right,
        "top": top,
        "bottom": bottom,
        "containLabel": contain_label,
    }


def get_data_zoom_config(has_slider: bool = True) -> List[Dict[str, Any]]:
    """Get standard data zoom configuration."""
    config = [{"type": "inside", "start": 0, "end": 100}]
    
    if has_slider:
        config.append({
            "type": "slider",
            "start": 0,
            "end": 100,
            "height": 20,
            "bottom": 5,
            "borderColor": "transparent",
            "backgroundColor": "rgba(255, 255, 255, 0.05)",
            "fillerColor": f"rgba(34, 211, 238, 0.2)",  # accent with transparency
            "handleStyle": {"color": COLORS["accent"]},
            "textStyle": {"color": COLORS["text_secondary"]},
        })
    
    return config


# =============================================================================
# Chart Builder Functions
# =============================================================================

def build_equity_chart(
    dates: List[str],
    values: List[float],
    color: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build ECharts configuration for an equity curve chart.

    Args:
        dates: List of date strings for x-axis
        values: List of equity values for y-axis
        color: Optional override for line color (defaults to accent)

    Returns:
        Complete ECharts option configuration
    """
    line_color = color or COLORS["accent"]
    
    # Calculate label interval to avoid overcrowding
    label_interval = max(0, len(dates) // 15) if len(dates) > 15 else 0

    return {
        "tooltip": get_tooltip_config(),
        "xAxis": {
            "type": "category",
            "data": dates,
            "axisLabel": get_axis_label_config(rotate=45, interval=label_interval),
            "axisLine": get_axis_line_config(),
            "axisTick": get_axis_line_config(),
        },
        "yAxis": {
            "type": "value",
            "axisLabel": get_axis_label_config(),
            "axisLine": get_axis_line_config(),
            "splitLine": get_split_line_config(),
        },
        "series": [{
            "data": values,
            "type": "line",
            "smooth": True,
            "lineStyle": {"color": line_color, "width": 2},
            "areaStyle": {
                "color": {
                    "type": "linear",
                    "x": 0, "y": 0, "x2": 0, "y2": 1,
                    "colorStops": [
                        {"offset": 0, "color": f"rgba(34, 211, 238, 0.3)"},
                        {"offset": 1, "color": f"rgba(34, 211, 238, 0.02)"},
                    ],
                }
            },
            "symbol": "none",
        }],
        "grid": get_grid_config(),
        "dataZoom": get_data_zoom_config(has_slider=True),
    }


def build_comparison_bar_chart(
    categories: List[str],
    returns: List[float],
    sharpes: List[float],
) -> Dict[str, Any]:
    """
    Build ECharts configuration for a comparison bar chart.

    Args:
        categories: List of category names (e.g., result names)
        returns: List of return percentages
        sharpes: List of Sharpe ratios

    Returns:
        Complete ECharts option configuration
    """
    return {
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": ["Return %", "Sharpe"],
            "textStyle": {"color": COLORS["text_secondary"]},
        },
        "xAxis": {
            "type": "category",
            "data": categories,
            "axisLabel": get_axis_label_config(rotate=45),
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Return %",
                "axisLabel": get_axis_label_config(),
            },
            {
                "type": "value",
                "name": "Sharpe",
                "axisLabel": get_axis_label_config(),
            },
        ],
        "series": [
            {
                "name": "Return %",
                "type": "bar",
                "data": returns,
                "itemStyle": {"color": COLORS["accent"]},
            },
            {
                "name": "Sharpe",
                "type": "bar",
                "yAxisIndex": 1,
                "data": sharpes,
                "itemStyle": {"color": COLORS["success"]},
            },
        ],
        "grid": get_grid_config(bottom="15%"),
    }


__all__ = [
    "COLORS",
    "get_tooltip_config",
    "get_axis_label_config",
    "get_axis_line_config",
    "get_split_line_config",
    "get_grid_config",
    "get_data_zoom_config",
    "build_equity_chart",
    "build_comparison_bar_chart",
]
