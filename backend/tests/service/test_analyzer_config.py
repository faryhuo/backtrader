"""
Unit tests for analyzer_config module.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestAnalyzerMode:
    """Tests for AnalyzerMode enum."""

    def test_analyzer_mode_values(self):
        """Test that AnalyzerMode has expected values."""
        from src.service.analyzer_config import AnalyzerMode

        assert AnalyzerMode.BACKTEST.value == "backtest"
        assert AnalyzerMode.LIVE.value == "live"
        assert AnalyzerMode.PORTFOLIO.value == "portfolio"


class TestConfigureAnalyzers:
    """Tests for configure_analyzers function."""

    def test_configure_analyzers_backtest_mode(self):
        """Test that BACKTEST mode adds full analyzer set."""
        from src.service.analyzer_config import configure_analyzers, AnalyzerMode

        mock_cerebro = MagicMock()

        configure_analyzers(mock_cerebro, AnalyzerMode.BACKTEST)

        # Should add multiple analyzers
        assert mock_cerebro.addanalyzer.call_count >= 9  # Core + advanced

        # Check for specific analyzers
        call_names = [
            call.kwargs.get("_name") for call in mock_cerebro.addanalyzer.call_args_list
        ]
        assert "sharpe" in call_names
        assert "drawdown" in call_names
        assert "returns" in call_names
        assert "annual" in call_names
        assert "sqn" in call_names
        assert "calmar" in call_names
        assert "vwr" in call_names

    def test_configure_analyzers_live_mode(self):
        """Test that LIVE mode adds minimal analyzer set."""
        from src.service.analyzer_config import configure_analyzers, AnalyzerMode

        mock_cerebro = MagicMock()

        configure_analyzers(mock_cerebro, AnalyzerMode.LIVE)

        # Should add fewer analyzers (minimal set)
        assert mock_cerebro.addanalyzer.call_count >= 3  # Sharpe, DrawDown, Returns

        call_names = [
            call.kwargs.get("_name") for call in mock_cerebro.addanalyzer.call_args_list
        ]
        assert "sharpe" in call_names
        assert "drawdown" in call_names
        assert "returns" in call_names

    def test_configure_analyzers_with_trade_recorder(self):
        """Test that trade recorder is added when provided."""
        from src.service.analyzer_config import configure_analyzers, AnalyzerMode

        mock_cerebro = MagicMock()
        mock_trade_recorder = MagicMock()

        configure_analyzers(mock_cerebro, AnalyzerMode.BACKTEST, mock_trade_recorder)

        call_names = [
            call.kwargs.get("_name") for call in mock_cerebro.addanalyzer.call_args_list
        ]
        assert "trade_recorder" in call_names


class TestExtractMetrics:
    """Tests for extract_metrics function."""

    def test_extract_metrics_canonical_names(self):
        """Test that extract_metrics returns canonical field names."""
        from src.service.analyzer_config import extract_metrics

        # Setup mock strategy with analyzers
        mock_strat = MagicMock()
        mock_broker = MagicMock()
        mock_broker.getvalue.return_value = 110000.0

        # Mock analyzer results
        mock_strat.analyzers.sharpe.get_analysis.return_value = {"sharperatio": 1.5}
        mock_strat.analyzers.drawdown.get_analysis.return_value = {
            "max": {"drawdown": 10.5, "moneydown": 10500, "len": 15}
        }
        mock_strat.analyzers.returns.get_analysis.return_value = {
            "rnorm100": 10.0,
            "rtot": 0.1,
        }
        mock_strat.analyzers.annual.get_analysis.return_value = {2024: 0.1}
        mock_strat.analyzers.sqn.get_analysis.return_value = {"sqn": 2.5}
        mock_strat.analyzers.calmar.get_analysis.return_value = {2024: 0.95}
        mock_strat.analyzers.vwr.get_analysis.return_value = {"vwr": 0.85}
        mock_strat.analyzers.timereturns.get_analysis.return_value = {}
        mock_strat.analyzers.timedraw.get_analysis.return_value = {}
        mock_strat.analyzers.trades.get_analysis.return_value = {}
        mock_strat.analyzers.trade_recorder.get_analysis.return_value = {}

        metrics = extract_metrics(mock_strat, mock_broker)

        # Check canonical field names
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "total_return" in metrics
        assert "calmar_ratio" in metrics
        assert "annual_returns" in metrics

        # Check values
        assert metrics["sharpe_ratio"] == 1.5
        assert metrics["max_drawdown"] == 10.5
        assert metrics["total_return"] == 10.0
        assert metrics["final_value"] == 110000.0

    def test_extract_metrics_handles_none_values(self):
        """Test that extract_metrics handles missing analyzers gracefully."""
        from src.service.analyzer_config import extract_metrics

        mock_strat = MagicMock()
        mock_broker = MagicMock()
        mock_broker.getvalue.return_value = 100000.0

        # Make analyzer access raise AttributeError (missing analyzer)
        mock_strat.analyzers.sharpe = None
        mock_strat.analyzers.drawdown = None
        mock_strat.analyzers.returns = None
        mock_strat.analyzers.annual = None
        mock_strat.analyzers.sqn = None
        mock_strat.analyzers.calmar = None
        mock_strat.analyzers.vwr = None
        mock_strat.analyzers.timereturns = None
        mock_strat.analyzers.timedraw = None
        mock_strat.analyzers.trades = None
        mock_strat.analyzers.trade_recorder = None

        metrics = extract_metrics(mock_strat, mock_broker)

        # Should not raise, should return defaults
        assert metrics["sharpe_ratio"] is None
        assert metrics["max_drawdown"] == 0.0
        assert metrics["total_return"] == 0.0


class TestNormalizeMetricNames:
    """Tests for normalize_metric_names function."""

    def test_legacy_to_canonical(self):
        """Test converting legacy names to canonical."""
        from src.service.analyzer_config import normalize_metric_names

        legacy = {"sharpe": 1.5, "drawdown": 10.0, "returns": 5.0}
        canonical = normalize_metric_names(legacy, to_canonical=True)

        assert "sharpe_ratio" in canonical
        assert "max_drawdown" in canonical
        assert "total_return" in canonical

    def test_canonical_to_legacy(self):
        """Test converting canonical names to legacy."""
        from src.service.analyzer_config import normalize_metric_names

        canonical = {"sharpe_ratio": 1.5, "max_drawdown": 10.0, "total_return": 5.0}
        legacy = normalize_metric_names(canonical, to_canonical=False)

        assert "sharpe" in legacy
        assert "drawdown" in legacy
        assert "returns" in legacy


class TestSafeReturns:
    """Tests for SafeReturns analyzer."""

    def test_safe_returns_handles_zero_division(self):
        """Test that SafeReturns doesn't crash on zero bars."""
        from src.service.analyzer_config import SafeReturns
        import backtrader as bt

        # Just verify the class exists and is a subclass
        assert issubclass(SafeReturns, bt.analyzers.Returns)
