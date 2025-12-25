"""
Unit tests for ECharts theme module.
"""
import pytest

from src.service.echarts_theme import (
    COLORS,
    get_tooltip_config,
    get_axis_label_config,
    get_axis_line_config,
    get_split_line_config,
    get_grid_config,
    get_data_zoom_config,
    build_equity_chart,
    build_comparison_bar_chart,
)


class TestColors:
    """Tests for theme color constants."""

    def test_colors_has_accent(self):
        """Test that accent color matches base.html CSS."""
        assert COLORS["accent"] == "#22d3ee"

    def test_colors_has_success(self):
        """Test that success color is defined."""
        assert COLORS["success"] == "#22c55e"

    def test_colors_has_text_colors(self):
        """Test that text colors are defined."""
        assert "text_primary" in COLORS
        assert "text_secondary" in COLORS
        assert "text_muted" in COLORS


class TestComponentConfigs:
    """Tests for reusable component configuration functions."""

    def test_get_tooltip_config(self):
        """Test tooltip configuration generation."""
        config = get_tooltip_config()
        
        assert config["trigger"] == "axis"
        assert "backgroundColor" in config
        assert "textStyle" in config

    def test_get_axis_label_config_default(self):
        """Test default axis label configuration."""
        config = get_axis_label_config()
        
        assert config["color"] == COLORS["text_secondary"]
        assert config["fontSize"] == 11
        assert "rotate" not in config
        assert "interval" not in config

    def test_get_axis_label_config_with_options(self):
        """Test axis label configuration with rotation and interval."""
        config = get_axis_label_config(rotate=45, interval=10)
        
        assert config["rotate"] == 45
        assert config["interval"] == 10

    def test_get_grid_config_default(self):
        """Test default grid configuration."""
        config = get_grid_config()
        
        assert config["left"] == "3%"
        assert config["right"] == "4%"
        assert config["containLabel"] is True

    def test_get_grid_config_custom(self):
        """Test custom grid configuration."""
        config = get_grid_config(left="5%", bottom="15%")
        
        assert config["left"] == "5%"
        assert config["bottom"] == "15%"

    def test_get_data_zoom_config_with_slider(self):
        """Test data zoom configuration with slider."""
        config = get_data_zoom_config(has_slider=True)
        
        assert len(config) == 2
        assert config[0]["type"] == "inside"
        assert config[1]["type"] == "slider"

    def test_get_data_zoom_config_without_slider(self):
        """Test data zoom configuration without slider."""
        config = get_data_zoom_config(has_slider=False)
        
        assert len(config) == 1
        assert config[0]["type"] == "inside"


class TestChartBuilders:
    """Tests for chart builder functions."""

    def test_build_equity_chart_basic(self):
        """Test building a basic equity chart."""
        dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
        values = [100000, 101000, 102000]
        
        chart = build_equity_chart(dates, values)
        
        assert "tooltip" in chart
        assert "xAxis" in chart
        assert "yAxis" in chart
        assert "series" in chart
        assert "grid" in chart
        assert "dataZoom" in chart
        
        # Check data is passed correctly
        assert chart["xAxis"]["data"] == dates
        assert chart["series"][0]["data"] == values

    def test_build_equity_chart_styling(self):
        """Test that equity chart has correct styling."""
        chart = build_equity_chart(["2024-01-01"], [100000])
        
        # Check line styling
        series = chart["series"][0]
        assert series["type"] == "line"
        assert series["smooth"] is True
        assert series["lineStyle"]["color"] == COLORS["accent"]
        assert "areaStyle" in series

    def test_build_equity_chart_custom_color(self):
        """Test equity chart with custom color."""
        custom_color = "#ff0000"
        chart = build_equity_chart(["2024-01-01"], [100000], color=custom_color)
        
        assert chart["series"][0]["lineStyle"]["color"] == custom_color

    def test_build_equity_chart_label_interval(self):
        """Test that label interval is calculated for many data points."""
        dates = [f"2024-01-{i:02d}" for i in range(1, 32)]  # 31 dates
        values = [100000 + i * 100 for i in range(31)]
        
        chart = build_equity_chart(dates, values)
        
        # Should have a non-zero interval for >15 data points
        assert chart["xAxis"]["axisLabel"]["interval"] > 0

    def test_build_comparison_bar_chart_basic(self):
        """Test building a basic comparison bar chart."""
        categories = ["Strategy A", "Strategy B"]
        returns = [20.0, 15.0]
        sharpes = [1.5, 1.2]
        
        chart = build_comparison_bar_chart(categories, returns, sharpes)
        
        assert "tooltip" in chart
        assert "legend" in chart
        assert "xAxis" in chart
        assert "yAxis" in chart
        assert "series" in chart
        assert "grid" in chart
        
        # Check data is passed correctly
        assert chart["xAxis"]["data"] == categories
        assert len(chart["series"]) == 2
        assert chart["series"][0]["data"] == returns
        assert chart["series"][1]["data"] == sharpes

    def test_build_comparison_bar_chart_dual_axis(self):
        """Test that comparison chart has dual y-axes."""
        chart = build_comparison_bar_chart(["A"], [10], [1])
        
        assert isinstance(chart["yAxis"], list)
        assert len(chart["yAxis"]) == 2
        assert chart["yAxis"][0]["name"] == "Return %"
        assert chart["yAxis"][1]["name"] == "Sharpe"
        
        # Second series should use second y-axis
        assert chart["series"][1]["yAxisIndex"] == 1

    def test_build_comparison_bar_chart_styling(self):
        """Test that comparison chart uses correct colors."""
        chart = build_comparison_bar_chart(["A"], [10], [1])
        
        assert chart["series"][0]["itemStyle"]["color"] == COLORS["accent"]
        assert chart["series"][1]["itemStyle"]["color"] == COLORS["success"]
