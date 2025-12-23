"""
Unit tests for strategy loader service.
"""
from unittest.mock import MagicMock, patch

import backtrader as bt
import pytest

from src.service.strategy_loader import StrategyLoaderError, load_user_strategy


class TestStrategyLoader:
    """Tests for load_user_strategy function."""

    @pytest.fixture
    def mock_strategy_source(self):
        """Mock strategy source code."""
        return (
            "/path/to/strategy.py",
            """
import backtrader as bt

class UserStrategy(bt.Strategy):
    params = (('period', 20),)

    def __init__(self):
        self.sma = bt.indicators.SMA(self.data.close, period=self.params.period)

    def next(self):
        if not self.position and self.data.close > self.sma:
            self.buy()
"""
        )

    @pytest.fixture
    def mock_sandbox_config_soft(self):
        """Mock sandbox config in soft mode."""
        with patch("src.service.strategy_loader.get_sandbox_config") as mock:
            config = MagicMock()
            config.mode = "soft"
            mock.return_value = config
            yield mock

    @pytest.fixture
    def mock_sandbox_config_subprocess(self):
        """Mock sandbox config in subprocess mode."""
        with patch("src.service.strategy_loader.get_sandbox_config") as mock:
            config = MagicMock()
            config.mode = "subprocess"
            config.timeout_seconds = 10
            config.max_memory_mb = 256
            config.allow_network = False
            config.allow_file_write = False
            mock.return_value = config
            yield mock

    @patch("src.service.strategy_loader.execute_strategy_code")
    @patch("src.service.strategy_loader.read_user_strategy_source")
    def test_load_user_strategy_soft_mode(
        self, mock_read_source, mock_execute, mock_sandbox_config_soft, mock_strategy_source
    ):
        """Test loading strategy in soft sandbox mode."""
        mock_read_source.return_value = mock_strategy_source

        # Create a real UserStrategy class for testing
        class UserStrategy(bt.Strategy):
            pass

        mock_execute.return_value = {"UserStrategy": UserStrategy}

        result = load_user_strategy("test_strategy")

        assert result is UserStrategy
        assert issubclass(result, bt.Strategy)
        mock_read_source.assert_called_once_with("test_strategy")
        mock_execute.assert_called_once()

    @patch("src.service.strategy_loader.IsolatedSandbox")
    @patch("src.service.strategy_loader.execute_strategy_code")
    @patch("src.service.strategy_loader.read_user_strategy_source")
    def test_load_user_strategy_subprocess_mode(
        self,
        mock_read_source,
        mock_execute,
        mock_sandbox_class,
        mock_sandbox_config_subprocess,
        mock_strategy_source
    ):
        """Test loading strategy in subprocess sandbox mode."""
        mock_read_source.return_value = mock_strategy_source

        # Mock isolated sandbox
        mock_sandbox_instance = MagicMock()
        mock_sandbox_instance.execute_strategy.return_value = {
            "strategy_class": "UserStrategy",
            "status": "success"
        }
        mock_sandbox_class.return_value = mock_sandbox_instance

        # Create a real UserStrategy class
        class UserStrategy(bt.Strategy):
            pass

        mock_execute.return_value = {"UserStrategy": UserStrategy}

        result = load_user_strategy("test_strategy")

        assert result is UserStrategy
        assert issubclass(result, bt.Strategy)

        # Verify subprocess was used for validation
        mock_sandbox_class.assert_called_once()
        mock_sandbox_instance.execute_strategy.assert_called_once()

        # Verify code was executed again in main process
        mock_execute.assert_called_once()

    @patch("src.service.strategy_loader.read_user_strategy_source")
    def test_load_user_strategy_file_not_found(self, mock_read_source):
        """Test error handling when strategy file not found."""
        mock_read_source.side_effect = FileNotFoundError("Strategy not found")

        with pytest.raises(StrategyLoaderError) as exc_info:
            load_user_strategy("nonexistent_strategy")

        assert "Strategy 'nonexistent_strategy' not found" in str(exc_info.value)

    @patch("src.service.strategy_loader.execute_strategy_code")
    @patch("src.service.strategy_loader.read_user_strategy_source")
    def test_load_user_strategy_no_userstrategy_class(
        self, mock_read_source, mock_execute, mock_sandbox_config_soft, mock_strategy_source
    ):
        """Test error when UserStrategy class not found in code."""
        mock_read_source.return_value = mock_strategy_source
        mock_execute.return_value = {}  # No UserStrategy class

        with pytest.raises(StrategyLoaderError) as exc_info:
            load_user_strategy("test_strategy")

        assert "UserStrategy class not found" in str(exc_info.value)

    @patch("src.service.strategy_loader.execute_strategy_code")
    @patch("src.service.strategy_loader.read_user_strategy_source")
    def test_load_user_strategy_not_bt_strategy(
        self, mock_read_source, mock_execute, mock_sandbox_config_soft, mock_strategy_source
    ):
        """Test error when UserStrategy doesn't inherit from bt.Strategy."""
        mock_read_source.return_value = mock_strategy_source

        # Create a class that's not a bt.Strategy subclass
        class UserStrategy:
            pass

        mock_execute.return_value = {"UserStrategy": UserStrategy}

        with pytest.raises(StrategyLoaderError) as exc_info:
            load_user_strategy("test_strategy")

        assert "UserStrategy must inherit from backtrader.Strategy" in str(exc_info.value)

    @patch("src.service.strategy_loader.IsolatedSandbox")
    @patch("src.service.strategy_loader.read_user_strategy_source")
    def test_load_user_strategy_timeout(
        self, mock_read_source, mock_sandbox_class, mock_sandbox_config_subprocess, mock_strategy_source
    ):
        """Test handling of sandbox timeout."""
        from src.service.isolated_sandbox import SandboxTimeoutError

        mock_read_source.return_value = mock_strategy_source

        mock_sandbox_instance = MagicMock()
        mock_sandbox_instance.execute_strategy.side_effect = SandboxTimeoutError(
            "Strategy execution timed out"
        )
        mock_sandbox_class.return_value = mock_sandbox_instance

        with pytest.raises(StrategyLoaderError) as exc_info:
            load_user_strategy("test_strategy")

        assert "timed out during validation" in str(exc_info.value)

    @patch("src.service.strategy_loader.IsolatedSandbox")
    @patch("src.service.strategy_loader.read_user_strategy_source")
    def test_load_user_strategy_sandbox_error(
        self, mock_read_source, mock_sandbox_class, mock_sandbox_config_subprocess, mock_strategy_source
    ):
        """Test handling of general sandbox errors."""
        from src.service.isolated_sandbox import SandboxExecutionError

        mock_read_source.return_value = mock_strategy_source

        mock_sandbox_instance = MagicMock()
        mock_sandbox_instance.execute_strategy.side_effect = SandboxExecutionError(
            "Dangerous operation detected"
        )
        mock_sandbox_class.return_value = mock_sandbox_instance

        with pytest.raises(StrategyLoaderError) as exc_info:
            load_user_strategy("test_strategy")

        assert "Failed to load strategy" in str(exc_info.value)

    @patch("src.service.strategy_loader.execute_strategy_code")
    @patch("src.service.strategy_loader.read_user_strategy_source")
    def test_load_user_strategy_compilation_error(
        self, mock_read_source, mock_execute, mock_sandbox_config_soft, mock_strategy_source
    ):
        """Test handling of Python syntax/compilation errors."""
        from src.service.strategy_sandbox import StrategySandboxError

        mock_read_source.return_value = mock_strategy_source
        mock_execute.side_effect = StrategySandboxError("SyntaxError: invalid syntax")

        with pytest.raises(StrategyLoaderError) as exc_info:
            load_user_strategy("test_strategy")

        assert "Failed to load strategy" in str(exc_info.value)

    @patch("src.service.strategy_loader.IsolatedSandbox")
    @patch("src.service.strategy_loader.execute_strategy_code")
    @patch("src.service.strategy_loader.read_user_strategy_source")
    def test_load_user_strategy_subprocess_no_strategy_class_in_result(
        self,
        mock_read_source,
        mock_execute,
        mock_sandbox_class,
        mock_sandbox_config_subprocess,
        mock_strategy_source
    ):
        """Test error when subprocess validation returns no strategy class."""
        mock_read_source.return_value = mock_strategy_source

        mock_sandbox_instance = MagicMock()
        mock_sandbox_instance.execute_strategy.return_value = {
            "status": "success"
            # Missing 'strategy_class' key
        }
        mock_sandbox_class.return_value = mock_sandbox_instance

        with pytest.raises(StrategyLoaderError) as exc_info:
            load_user_strategy("test_strategy")

        assert "UserStrategy class not found" in str(exc_info.value)
