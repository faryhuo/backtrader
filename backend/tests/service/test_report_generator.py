"""
Unit tests for report generator service.
"""
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from src.db.models import ReportStatus
from src.service.report_generator import ReportGenerator, get_report_generator
from src.utils.report_i18n import DEFAULT_LANGUAGE


class TestReportGenerator:
    """Tests for ReportGenerator class."""

    @pytest.fixture
    def mock_config(self):
        """Mock report configuration."""
        return {
            "version": "1.0",
            "report": {
                "output_directory": "backend/resources/reports"
            }
        }

    @pytest.fixture
    def mock_storages(self):
        """Mock all storage backends."""
        with patch("src.service.report_generator.BacktestStorage") as backtest, \
             patch("src.service.report_generator.PortfolioStorage") as portfolio, \
             patch("src.service.report_generator.WalkForwardStorage") as walkforward, \
             patch("src.service.report_generator.get_report_storage") as report:
            yield {
                "backtest": backtest,
                "portfolio": portfolio,
                "walkforward": walkforward,
                "report": report
            }

    @pytest.fixture
    def report_generator(self, mock_config, mock_storages):
        """Create ReportGenerator instance with mocked dependencies."""
        with patch("src.service.report_generator.load_report_config", return_value=mock_config), \
             patch("src.service.report_generator.Environment") as mock_env:
            generator = ReportGenerator()
            # Mock template environment
            generator.template_env = MagicMock()
            yield generator

    @pytest.mark.asyncio
    async def test_generate_backtest_report(self, report_generator):
        """Test generating a backtest report."""
        # Mock backtest data
        backtest_data = {
            "backtest_id": "test-123",
            "strategy_name": "SMA Strategy",
            "ticker": "AAPL",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_cash": 100000,
            "final_value": 120000,
            "total_return": 20.0,
            "sharpe_ratio": 1.5,
            "max_drawdown": -5.0,
            "metrics": {
                "trade_details": {
                    "total_trades": 50,
                    "winning_trades": 30,
                    "losing_trades": 20,
                    "trades": []
                }
            },
            "plot_url": "/images/test.png"
        }

        # Configure mocks
        report_generator.backtest_storage.get_backtest = MagicMock(return_value=backtest_data)
        report_generator.report_storage.update_status = MagicMock()
        report_generator.report_storage.save_content = MagicMock()

        # Mock template rendering
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Test Report</html>"
        report_generator.template_env.get_template = MagicMock(return_value=mock_template)

        # Mock file writing
        with patch("builtins.open", mock_open()):
            result = await report_generator.generate_report(
                report_id="test-report-123",
                report_type="backtest",
                source_ids=["test-123"],
                language="en"
            )

        assert result["report_id"] == "test-report-123"
        assert "html_filename" in result
        assert "metrics_summary" in result

        # Verify status updates
        report_generator.report_storage.update_status.assert_called()
        report_generator.report_storage.save_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_comparison_report(self, report_generator):
        """Test generating a comparison report with multiple results."""
        # Mock multiple backtest data
        backtest_data_1 = {
            "backtest_id": "test-1",
            "strategy_name": "Strategy A",
            "ticker": "AAPL",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "total_return": 20.0,
            "sharpe_ratio": 1.5,
            "max_drawdown": -5.0,
            "metrics": {"trade_details": {"total_trades": 50, "winning_trades": 30}}
        }

        backtest_data_2 = {
            "backtest_id": "test-2",
            "strategy_name": "Strategy B",
            "ticker": "AAPL",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "total_return": 15.0,
            "sharpe_ratio": 1.2,
            "max_drawdown": -3.0,
            "metrics": {"trade_details": {"total_trades": 40, "winning_trades": 25}}
        }

        report_generator.backtest_storage.get_backtest = MagicMock(
            side_effect=[backtest_data_1, backtest_data_2]
        )
        report_generator.report_storage.update_status = MagicMock()
        report_generator.report_storage.save_content = MagicMock()

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Comparison Report</html>"
        report_generator.template_env.get_template = MagicMock(return_value=mock_template)

        with patch("builtins.open", mock_open()):
            result = await report_generator.generate_report(
                report_id="comparison-123",
                report_type="comparison",
                source_ids=["test-1", "test-2"],
                language="en"
            )

        assert result["report_id"] == "comparison-123"
        # Verify template was called with comparison template
        report_generator.template_env.get_template.assert_called_with("comparison.html")

    @pytest.mark.asyncio
    async def test_generate_report_with_progress_callback(self, report_generator):
        """Test report generation with progress updates."""
        backtest_data = {
            "backtest_id": "test-123",
            "strategy_name": "Test",
            "ticker": "AAPL",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "metrics": {"trade_details": {"total_trades": 10, "winning_trades": 6}}
        }

        report_generator.backtest_storage.get_backtest = MagicMock(return_value=backtest_data)
        report_generator.report_storage.update_status = MagicMock()
        report_generator.report_storage.save_content = MagicMock()

        mock_template = MagicMock()
        mock_template.render.return_value = "<html>Test</html>"
        report_generator.template_env.get_template = MagicMock(return_value=mock_template)

        # Track progress updates
        progress_updates = []

        async def progress_callback(progress, message):
            progress_updates.append((progress, message))

        with patch("builtins.open", mock_open()):
            await report_generator.generate_report(
                report_id="test-123",
                report_type="backtest",
                source_ids=["test-123"],
                progress_callback=progress_callback,
                language="en"
            )

        # Verify progress updates were called
        assert len(progress_updates) > 0
        assert progress_updates[-1][0] == 100  # Final progress should be 100%

    @pytest.mark.asyncio
    async def test_generate_report_error_handling(self, report_generator):
        """Test error handling during report generation."""
        report_generator.backtest_storage.get_backtest = MagicMock(
            side_effect=Exception("Database error")
        )
        report_generator.report_storage.update_status = MagicMock()

        with pytest.raises(Exception) as exc_info:
            await report_generator.generate_report(
                report_id="test-123",
                report_type="backtest",
                source_ids=["test-123"],
                language="en"
            )

        # Verify error was recorded
        report_generator.report_storage.update_status.assert_called()
        update_call = report_generator.report_storage.update_status.call_args_list[-1]
        assert update_call[0][1] == ReportStatus.FAILED.value

    @pytest.mark.asyncio
    async def test_fetch_source_data_no_data(self, report_generator):
        """Test error when no source data found."""
        report_generator.backtest_storage.get_backtest = MagicMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            await report_generator._fetch_source_data(
                report_type="backtest",
                source_ids=["nonexistent"],
                user_id=None
            )

        assert "No source data found" in str(exc_info.value)

    def test_prepare_backtest_context(self, report_generator):
        """Test preparing context for backtest report."""
        backtest_data = {
            "backtest_id": "test-123",
            "strategy_name": "SMA Strategy",
            "ticker": "AAPL",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_cash": 100000,
            "final_value": 120000,
            "total_return": 20.0,
            "sharpe_ratio": 1.5,
            "max_drawdown": -5.0,
            "metrics": {
                "trade_details": {
                    "total_trades": 50,
                    "winning_trades": 30,
                    "losing_trades": 20,
                    "trades": []
                }
            }
        }

        context = report_generator._prepare_backtest_context(
            data=backtest_data,
            config={},
            translations={"lang": "en", "tab_overview": "Overview"}
        )

        assert context["strategy_name"] == "SMA Strategy"
        assert context["ticker"] == "AAPL"
        assert context["total_return"] == 20.0
        assert context["win_rate"] == 60.0  # 30/50 * 100
        assert context["report_type"] == "backtest"

    def test_prepare_comparison_context(self, report_generator):
        """Test preparing context for comparison report."""
        source_data = [
            {
                "strategy_name": "Strategy A",
                "ticker": "AAPL",
                "total_return": 20.0,
                "sharpe_ratio": 1.5,
                "max_drawdown": -5.0,
                "metrics": {"trade_details": {"total_trades": 50, "winning_trades": 30}}
            },
            {
                "strategy_name": "Strategy B",
                "ticker": "AAPL",
                "total_return": 15.0,
                "sharpe_ratio": 1.2,
                "max_drawdown": -3.0,
                "metrics": {"trade_details": {"total_trades": 40, "winning_trades": 25}}
            }
        ]

        context = report_generator._prepare_comparison_context(
            source_data=source_data,
            config={},
            translations={"lang": "en"}
        )

        assert context["report_type"] == "comparison"
        assert len(context["results"]) == 2
        assert "comparison_metrics" in context
        assert context["comparison_metrics"]["best_return"]["value"] == 20.0

    def test_calculate_comparison_metrics(self, report_generator):
        """Test calculating comparison metrics."""
        results = [
            {"name": "A", "total_return": 20.0, "sharpe_ratio": 1.5, "max_drawdown": -5.0, "win_rate": 60},
            {"name": "B", "total_return": 15.0, "sharpe_ratio": 1.8, "max_drawdown": -3.0, "win_rate": 55},
        ]

        metrics = report_generator._calculate_comparison_metrics(results)

        assert metrics["best_return"]["name"] == "A"
        assert metrics["best_sharpe"]["name"] == "B"
        assert metrics["lowest_drawdown"]["name"] == "B"
        assert metrics["best_win_rate"]["name"] == "A"

    def test_format_trades(self, report_generator):
        """Test trade formatting."""
        trades = [
            {
                "entry_date": "2024-01-01",
                "exit_date": "2024-01-05",
                "type": "LONG",
                "size": 100,
                "entry_price": 150.0,
                "exit_price": 155.0,
                "pnl": 500.0,
                "return_pct": 3.33
            }
            for _ in range(100)  # Create 100 trades
        ]

        formatted = report_generator._format_trades(trades)

        # Should limit to 50 trades
        assert len(formatted) <= 50
        assert formatted[0]["type"] == "LONG"
        assert formatted[0]["pnl"] == 500.0

    def test_embed_image_as_base64(self, report_generator):
        """Test image embedding as base64."""
        mock_image_data = b"fake_png_data"

        with patch("src.service.report_generator.IMAGES_DIR", Path("/fake/images")), \
             patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_image_data)):
            result = report_generator._embed_image_as_base64("/images/test.png")

            assert result.startswith("data:image/png;base64,")
            assert "fake_png_data" in result or len(result) > 30

    def test_embed_image_not_found(self, report_generator):
        """Test image embedding when image doesn't exist."""
        with patch("src.service.report_generator.IMAGES_DIR", Path("/fake/images")), \
             patch("pathlib.Path.exists", return_value=False):
            result = report_generator._embed_image_as_base64("/images/nonexistent.png")

            assert result is None


class TestGetReportGenerator:
    """Tests for get_report_generator singleton."""

    def test_get_report_generator_singleton(self):
        """Test that get_report_generator returns singleton instance."""
        with patch("src.service.report_generator.load_report_config", return_value={}), \
             patch("src.service.report_generator.Environment"), \
             patch("src.service.report_generator.BacktestStorage"), \
             patch("src.service.report_generator.PortfolioStorage"), \
             patch("src.service.report_generator.WalkForwardStorage"), \
             patch("src.service.report_generator.get_report_storage"):
            gen1 = get_report_generator()
            gen2 = get_report_generator()

            assert gen1 is gen2
