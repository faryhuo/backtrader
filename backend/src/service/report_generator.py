"""
Report Generator Service - Generates HTML reports using Jinja2 templates.

Provides unified report generation for:
- Single backtest results
- Portfolio backtest results
- Walk-forward optimization results
- Comparison reports (multiple results)
"""

import base64
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.config.settings import TEMPLATES_DIR, REPORTS_DIR, IMAGES_DIR
from src.db.storage import BacktestStorage, PortfolioStorage, WalkForwardStorage, get_report_storage
from src.db.models import ReportStatus

logger = logging.getLogger(__name__)

# Ensure directories exist
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class ReportGenerator:
    """
    Generates HTML reports using Jinja2 templates.

    Features:
    - Template-based generation
    - ECharts configuration for interactive charts
    - Support for single and comparison reports
    - Progress callbacks for background task integration
    """

    def __init__(self):
        """Initialize the report generator with Jinja2 environment."""
        template_path = TEMPLATES_DIR / "reports"
        template_path.mkdir(parents=True, exist_ok=True)

        self.template_env = Environment(
            loader=FileSystemLoader(str(template_path)),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Add custom filters
        self.template_env.filters["enumerate"] = enumerate

        self.backtest_storage = BacktestStorage()
        self.portfolio_storage = PortfolioStorage()
        self.walkforward_storage = WalkForwardStorage()
        self.report_storage = get_report_storage()

    async def generate_report(
        self,
        report_id: str,
        report_type: str,
        source_ids: List[str],
        config: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a complete HTML report.

        Args:
            report_id: Unique report identifier
            report_type: Type of report (backtest, portfolio, walkforward, comparison)
            source_ids: List of source record IDs
            config: Optional configuration dict
            progress_callback: Optional async callback for progress updates
            user_id: Optional user ID for filtering

        Returns:
            Dict with report_id, html_filename, and metrics_summary
        """
        config = config or {}

        try:
            # Update status to generating
            self.report_storage.update_status(
                report_id, ReportStatus.GENERATING.value, progress=5, user_id=user_id
            )

            if progress_callback:
                await progress_callback(5, "Fetching source data...")

            # Fetch source data
            source_data = await self._fetch_source_data(
                report_type, source_ids, user_id
            )

            if progress_callback:
                await progress_callback(20, "Preparing report data...")

            # Determine template and prepare context
            if report_type == "comparison" or len(source_ids) > 1:
                template_name = "comparison.html"
                context = self._prepare_comparison_context(source_data, config)
            elif report_type == "backtest":
                template_name = "backtest.html"
                context = self._prepare_backtest_context(source_data[0], config)
            elif report_type == "portfolio":
                template_name = "backtest.html"  # Portfolio uses similar template
                context = self._prepare_portfolio_context(source_data[0], config)
            elif report_type == "walkforward":
                template_name = "backtest.html"  # Walkforward uses similar template
                context = self._prepare_walkforward_context(source_data[0], config)
            else:
                template_name = "backtest.html"
                context = self._prepare_backtest_context(source_data[0], config)

            if progress_callback:
                await progress_callback(40, "Generating charts...")

            # Generate chart configurations
            context = self._add_chart_configs(context, report_type, source_data)

            if progress_callback:
                await progress_callback(60, "Rendering template...")

            # Render template
            template = self.template_env.get_template(template_name)
            html_content = template.render(**context)

            if progress_callback:
                await progress_callback(80, "Saving report...")

            # Save to file
            html_filename = f"{report_id}.html"
            html_path = REPORTS_DIR / html_filename
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Extract metrics summary
            metrics_summary = self._extract_metrics_summary(context, report_type)

            # Save to database
            self.report_storage.save_content(
                report_id=report_id,
                html_content=html_content,
                html_filename=html_filename,
                metrics_summary=metrics_summary,
                user_id=user_id,
            )

            if progress_callback:
                await progress_callback(100, "Report generated successfully")

            logger.info(f"Generated report {report_id}")

            return {
                "report_id": report_id,
                "html_filename": html_filename,
                "metrics_summary": metrics_summary,
            }

        except Exception as e:
            logger.error(f"Failed to generate report {report_id}: {e}")
            self.report_storage.update_status(
                report_id,
                ReportStatus.FAILED.value,
                error_message=str(e),
                user_id=user_id,
            )
            raise

    async def _fetch_source_data(
        self,
        report_type: str,
        source_ids: List[str],
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch source data for all source IDs."""
        results = []

        for source_id in source_ids:
            if report_type in ["backtest", "comparison"]:
                data = self.backtest_storage.get_backtest(source_id, user_id=user_id)
            elif report_type == "portfolio":
                data = self.portfolio_storage.get_by_id(source_id, user_id=user_id)
            elif report_type == "walkforward":
                data = self.walkforward_storage.get_optimization(source_id, user_id=user_id)
            else:
                data = self.backtest_storage.get_backtest(source_id, user_id=user_id)

            if data:
                results.append(data)

        if not results:
            raise ValueError(f"No source data found for IDs: {source_ids}")

        return results

    def _prepare_backtest_context(
        self,
        data: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare context for backtest report template."""
        metrics = data.get("metrics", {})
        trade_details = metrics.get("trade_details", {})

        # Calculate win rate
        total_trades = trade_details.get("total_trades", 0)
        winning_trades = trade_details.get("winning_trades", 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else None

        # Determine sections
        sections = config.get("sections", ["overview", "charts", "trades", "parameters"])
        section_list = [{"id": s, "name": s.replace("_", " ").title()} for s in sections]

        # Add deep analysis section if available
        if data.get("deep_analysis") and "deep_analysis" not in sections:
            section_list.append({"id": "deep-analysis", "name": "Deep Analysis"})

        # Add AI analysis section if available
        if data.get("ai_analysis") and "ai_analysis" not in sections:
            section_list.append({"id": "ai-analysis", "name": "AI Analysis"})

        context = {
            "report_id": data.get("backtest_id", str(uuid.uuid4())),
            "title": f"{data.get('strategy_name', 'Strategy')} - {data.get('ticker', 'Unknown')}",
            "description": f"Backtest report for {data.get('ticker')} from {data.get('start_date')} to {data.get('end_date')}",
            "report_type": "backtest",
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "sections": section_list,

            # Metadata
            "strategy_name": data.get("strategy_name"),
            "ticker": data.get("ticker"),
            "date_range": f"{data.get('start_date')} - {data.get('end_date')}",
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date"),
            "initial_cash": data.get("initial_cash", 100000),
            "commission": data.get("commission", 0.0005),
            "stake": data.get("stake", 100),

            # Performance metrics
            "final_value": data.get("final_value"),
            "total_return": data.get("total_return"),
            "sharpe_ratio": data.get("sharpe_ratio"),
            "max_drawdown": data.get("max_drawdown"),
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": trade_details.get("losing_trades", 0),
            "win_rate": win_rate,
            "profit_factor": trade_details.get("profit_factor"),
            "sqn": metrics.get("sqn"),

            # Annual returns
            "annual_returns": metrics.get("annual_returns", {}),

            # Trade data
            "trades": self._format_trades(trade_details.get("trades", [])),

            # Strategy parameters
            "strategy_params": data.get("params", {}),

            # Plot URL - embed as base64 for standalone HTML reports
            "plot_url": self._embed_image_as_base64(data.get("plot_url")),

            # Deep analysis
            "deep_analysis": data.get("deep_analysis"),

            # AI analysis
            "ai_analysis": data.get("ai_analysis"),
        }

        return context

    def _prepare_portfolio_context(
        self,
        data: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare context for portfolio report template."""
        context = self._prepare_backtest_context(data, config)
        context["report_type"] = "portfolio"
        context["title"] = f"Portfolio - {', '.join(data.get('tickers', [])[:3])}..."
        context["ticker"] = ", ".join(data.get("tickers", []))
        return context

    def _prepare_walkforward_context(
        self,
        data: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare context for walk-forward report template."""
        context = {
            "report_id": data.get("optimization_id", str(uuid.uuid4())),
            "title": f"Walk-Forward - {data.get('strategy_name', 'Strategy')} - {data.get('ticker', 'Unknown')}",
            "description": f"Walk-forward optimization from {data.get('start_date')} to {data.get('end_date')}",
            "report_type": "walkforward",
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "sections": [
                {"id": "overview", "name": "Overview"},
                {"id": "charts", "name": "Charts"},
                {"id": "parameters", "name": "Parameters"},
            ],

            "strategy_name": data.get("strategy_name"),
            "ticker": data.get("ticker"),
            "date_range": f"{data.get('start_date')} - {data.get('end_date')}",
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date"),

            # Walk-forward specific
            "num_windows": data.get("num_windows", 0),
            "avg_train_performance": data.get("avg_train_performance"),
            "avg_test_performance": data.get("avg_test_performance"),
            "avg_degradation_pct": data.get("avg_degradation_pct"),
            "overfitting_detected": data.get("overfitting_detected", False),

            "windows": data.get("windows", []),
            "overfitting_metrics": data.get("overfitting_metrics", {}),
        }

        return context

    def _prepare_comparison_context(
        self,
        source_data: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare context for comparison report template."""
        results = []
        for i, data in enumerate(source_data):
            metrics = data.get("metrics", {})
            trade_details = metrics.get("trade_details", {})
            total_trades = trade_details.get("total_trades", 0)
            winning_trades = trade_details.get("winning_trades", 0)

            results.append({
                "name": data.get("name", f"Result {i + 1}"),
                "ticker": data.get("ticker"),
                "strategy_name": data.get("strategy_name"),
                "start_date": data.get("start_date"),
                "end_date": data.get("end_date"),
                "initial_cash": data.get("initial_cash", 100000),
                "total_return": data.get("total_return", 0),
                "sharpe_ratio": data.get("sharpe_ratio"),
                "max_drawdown": data.get("max_drawdown"),
                "total_trades": total_trades,
                "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else None,
            })

        # Calculate comparison metrics
        comparison_metrics = self._calculate_comparison_metrics(results)

        # Calculate statistics
        stats = self._calculate_statistics(results)

        context = {
            "report_id": str(uuid.uuid4()),
            "title": f"Comparison Report - {len(results)} Results",
            "description": f"Comparison of {len(results)} backtest results",
            "report_type": "comparison",
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "sections": [
                {"id": "overview", "name": "Overview"},
                {"id": "charts", "name": "Charts"},
                {"id": "details", "name": "Details"},
                {"id": "statistics", "name": "Statistics"},
            ],

            "results": results,
            "comparison_metrics": comparison_metrics,
            "stats": stats,
        }

        return context

    def _calculate_comparison_metrics(
        self,
        results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate best/worst metrics for comparison."""
        if not results:
            return {}

        metrics = {}

        # Best return
        returns = [(r.get("total_return", float("-inf")), r.get("name", "")) for r in results]
        best_return = max(returns, key=lambda x: x[0])
        if best_return[0] != float("-inf"):
            metrics["best_return"] = {"value": best_return[0], "name": best_return[1]}

        # Best Sharpe
        sharpes = [(r.get("sharpe_ratio") or float("-inf"), r.get("name", "")) for r in results]
        best_sharpe = max(sharpes, key=lambda x: x[0] if x[0] is not None else float("-inf"))
        if best_sharpe[0] != float("-inf"):
            metrics["best_sharpe"] = {"value": best_sharpe[0], "name": best_sharpe[1]}

        # Lowest drawdown (least negative)
        drawdowns = [(abs(r.get("max_drawdown") or float("inf")), r.get("name", "")) for r in results]
        lowest_dd = min(drawdowns, key=lambda x: x[0])
        if lowest_dd[0] != float("inf"):
            metrics["lowest_drawdown"] = {"value": -lowest_dd[0], "name": lowest_dd[1]}

        # Best win rate
        win_rates = [(r.get("win_rate") or 0, r.get("name", "")) for r in results]
        best_wr = max(win_rates, key=lambda x: x[0])
        if best_wr[0] > 0:
            metrics["best_win_rate"] = {"value": best_wr[0], "name": best_wr[1]}

        return metrics

    def _calculate_statistics(
        self,
        results: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Calculate statistical summary for comparison."""
        import statistics

        if len(results) < 2:
            return {}

        def safe_stats(values):
            clean = [v for v in values if v is not None]
            if len(clean) < 2:
                return {"mean": 0, "std": 0, "min": 0, "max": 0, "median": 0}
            return {
                "mean": statistics.mean(clean),
                "std": statistics.stdev(clean),
                "min": min(clean),
                "max": max(clean),
                "median": statistics.median(clean),
            }

        returns = [r.get("total_return") for r in results]
        sharpes = [r.get("sharpe_ratio") for r in results]
        drawdowns = [r.get("max_drawdown") for r in results]
        win_rates = [r.get("win_rate") for r in results]

        ret_stats = safe_stats(returns)
        sharpe_stats = safe_stats(sharpes)
        dd_stats = safe_stats(drawdowns)
        wr_stats = safe_stats(win_rates)

        return {
            "return_mean": ret_stats["mean"],
            "return_std": ret_stats["std"],
            "return_min": ret_stats["min"],
            "return_max": ret_stats["max"],
            "return_median": ret_stats["median"],
            "sharpe_mean": sharpe_stats["mean"],
            "sharpe_std": sharpe_stats["std"],
            "sharpe_min": sharpe_stats["min"],
            "sharpe_max": sharpe_stats["max"],
            "sharpe_median": sharpe_stats["median"],
            "dd_mean": dd_stats["mean"],
            "dd_std": dd_stats["std"],
            "dd_min": dd_stats["min"],
            "dd_max": dd_stats["max"],
            "dd_median": dd_stats["median"],
            "wr_mean": wr_stats["mean"],
            "wr_std": wr_stats["std"],
            "wr_min": wr_stats["min"],
            "wr_max": wr_stats["max"],
            "wr_median": wr_stats["median"],
        }

    def _format_trades(self, trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format trade data for display."""
        formatted = []
        for trade in trades[:50]:  # Limit to 50 trades for performance
            formatted.append({
                "entry_date": trade.get("entry_date", "N/A"),
                "exit_date": trade.get("exit_date", "N/A"),
                "type": trade.get("type", "N/A"),
                "size": trade.get("size", 0),
                "entry_price": trade.get("entry_price", 0),
                "exit_price": trade.get("exit_price", 0),
                "pnl": trade.get("pnl", 0),
                "return_pct": trade.get("return_pct", 0),
            })
        return formatted

    def _embed_image_as_base64(self, plot_url: Optional[str]) -> Optional[str]:
        """
        Convert image file to base64 data URL for embedding in HTML.

        Args:
            plot_url: URL like '/images/xxx.png' or filename

        Returns:
            Base64 data URL or None if image not found
        """
        if not plot_url:
            return None

        # Extract filename from URL
        if plot_url.startswith("/images/"):
            filename = plot_url.replace("/images/", "")
        else:
            filename = plot_url

        # Build full path
        image_path = IMAGES_DIR / filename

        if not image_path.exists():
            logger.warning(f"Image not found for embedding: {image_path}")
            return None

        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Determine MIME type
            suffix = image_path.suffix.lower()
            mime_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".svg": "image/svg+xml",
            }
            mime_type = mime_types.get(suffix, "image/png")

            return f"data:{mime_type};base64,{image_data}"
        except Exception as e:
            logger.error(f"Failed to embed image {image_path}: {e}")
            return None

    def _add_chart_configs(
        self,
        context: Dict[str, Any],
        report_type: str,
        source_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Add ECharts configuration to context."""
        # Equity curve chart
        if report_type == "backtest" and source_data:
            metrics = source_data[0].get("metrics", {})
            equity_curve = metrics.get("equity_curve", {})

            if equity_curve:
                dates = list(equity_curve.keys())
                values = list(equity_curve.values())

                # Calculate label interval to avoid overcrowding
                label_interval = max(0, len(dates) // 15) if len(dates) > 15 else 0

                context["equity_chart"] = {
                    "tooltip": {
                        "trigger": "axis",
                        "backgroundColor": "rgba(24, 24, 27, 0.95)",
                        "borderColor": "rgba(255, 255, 255, 0.1)",
                        "textStyle": {"color": "#fafafa"},
                    },
                    "xAxis": {
                        "type": "category",
                        "data": dates,
                        "axisLabel": {
                            "color": "#a1a1aa",
                            "rotate": 45,
                            "interval": label_interval,
                            "fontSize": 11,
                        },
                        "axisLine": {"lineStyle": {"color": "rgba(255, 255, 255, 0.1)"}},
                        "axisTick": {"lineStyle": {"color": "rgba(255, 255, 255, 0.1)"}},
                    },
                    "yAxis": {
                        "type": "value",
                        "axisLabel": {"color": "#a1a1aa", "fontSize": 11},
                        "axisLine": {"lineStyle": {"color": "rgba(255, 255, 255, 0.1)"}},
                        "splitLine": {"lineStyle": {"color": "rgba(255, 255, 255, 0.05)"}},
                    },
                    "series": [{
                        "data": values,
                        "type": "line",
                        "smooth": True,
                        "lineStyle": {"color": "#22d3ee", "width": 2},
                        "areaStyle": {
                            "color": {
                                "type": "linear",
                                "x": 0, "y": 0, "x2": 0, "y2": 1,
                                "colorStops": [
                                    {"offset": 0, "color": "rgba(34, 211, 238, 0.3)"},
                                    {"offset": 1, "color": "rgba(34, 211, 238, 0.02)"},
                                ],
                            }
                        },
                        "symbol": "none",
                    }],
                    "grid": {
                        "left": "3%",
                        "right": "4%",
                        "top": "10%",
                        "bottom": "18%",
                        "containLabel": True,
                    },
                    "dataZoom": [
                        {"type": "inside", "start": 0, "end": 100},
                        {
                            "type": "slider",
                            "start": 0,
                            "end": 100,
                            "height": 20,
                            "bottom": 5,
                            "borderColor": "transparent",
                            "backgroundColor": "rgba(255, 255, 255, 0.05)",
                            "fillerColor": "rgba(34, 211, 238, 0.2)",
                            "handleStyle": {"color": "#22d3ee"},
                            "textStyle": {"color": "#a1a1aa"},
                        },
                    ],
                }

        # Comparison charts
        if report_type == "comparison" and len(source_data) > 1:
            # Metrics bar chart
            names = [r.get("name", f"Result {i+1}") for i, r in enumerate(context.get("results", []))]
            returns = [r.get("total_return", 0) for r in context.get("results", [])]
            sharpes = [r.get("sharpe_ratio", 0) or 0 for r in context.get("results", [])]

            context["metrics_bar_chart"] = {
                "tooltip": {"trigger": "axis"},
                "legend": {"data": ["Return %", "Sharpe"], "textStyle": {"color": "#a1a1aa"}},
                "xAxis": {
                    "type": "category",
                    "data": names,
                    "axisLabel": {"color": "#a1a1aa", "rotate": 45},
                },
                "yAxis": [
                    {"type": "value", "name": "Return %", "axisLabel": {"color": "#a1a1aa"}},
                    {"type": "value", "name": "Sharpe", "axisLabel": {"color": "#a1a1aa"}},
                ],
                "series": [
                    {
                        "name": "Return %",
                        "type": "bar",
                        "data": returns,
                        "itemStyle": {"color": "#22d3ee"},
                    },
                    {
                        "name": "Sharpe",
                        "type": "bar",
                        "yAxisIndex": 1,
                        "data": sharpes,
                        "itemStyle": {"color": "#22c55e"},
                    },
                ],
                "grid": {"left": "3%", "right": "4%", "bottom": "15%", "containLabel": True},
            }

        return context

    def _extract_metrics_summary(
        self,
        context: Dict[str, Any],
        report_type: str,
    ) -> Dict[str, Any]:
        """Extract summary metrics for list display."""
        if report_type == "comparison":
            return {
                "num_results": len(context.get("results", [])),
                "best_return": context.get("comparison_metrics", {}).get("best_return", {}).get("value"),
            }
        else:
            return {
                "total_return": context.get("total_return"),
                "sharpe_ratio": context.get("sharpe_ratio"),
                "max_drawdown": context.get("max_drawdown"),
                "total_trades": context.get("total_trades"),
            }


# Singleton instance
_report_generator: Optional[ReportGenerator] = None


def get_report_generator() -> ReportGenerator:
    """Get singleton ReportGenerator instance."""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator


__all__ = [
    "ReportGenerator",
    "get_report_generator",
]
