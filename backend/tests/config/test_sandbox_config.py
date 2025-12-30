"""
Unit tests for sandbox configuration module.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from src.config.sandbox_config import (
    SandboxConfig,
    StrategyConfig,
    get_sandbox_config,
    get_strategy_config,
    get_config,
    get_strategy_config_singleton,
    reset_config,
    _parse_bool,
)


class TestParseBool:
    """Tests for _parse_bool helper function."""

    def test_parse_bool_true_values(self):
        """Test that various true representations are parsed correctly."""
        assert _parse_bool(True) is True
        assert _parse_bool("true") is True
        assert _parse_bool("True") is True
        assert _parse_bool("TRUE") is True
        assert _parse_bool("1") is True
        assert _parse_bool("yes") is True
        assert _parse_bool("on") is True

    def test_parse_bool_false_values(self):
        """Test that various false representations are parsed correctly."""
        assert _parse_bool(False) is False
        assert _parse_bool("false") is False
        assert _parse_bool("False") is False
        assert _parse_bool("0") is False
        assert _parse_bool("no") is False
        assert _parse_bool("off") is False

    def test_parse_bool_other_values(self):
        """Test that other values are converted to bool."""
        assert _parse_bool(1) is True
        assert _parse_bool(0) is False
        assert _parse_bool("") is False


class TestStrategyConfig:
    """Tests for StrategyConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = StrategyConfig()
        assert config.file_path == "data/strategies/"

    def test_custom_values(self):
        """Test custom configuration values."""
        config = StrategyConfig(file_path="custom/path/")
        assert config.file_path == "custom/path/"

    def test_get_absolute_path_relative(self):
        """Test get_absolute_path with relative path."""
        config = StrategyConfig(file_path="data/strategies/")
        path = config.get_absolute_path()
        assert path.is_absolute()
        assert path.name == "strategies" or "strategies" in str(path)

    def test_get_absolute_path_absolute(self, tmp_path):
        """Test get_absolute_path with absolute path."""
        abs_path = str(tmp_path / "strategies")
        config = StrategyConfig(file_path=abs_path)
        path = config.get_absolute_path()
        assert str(path) == abs_path


class TestSandboxConfig:
    """Tests for SandboxConfig dataclass."""

    def test_default_values(self):
        """Test default sandbox configuration values."""
        config = SandboxConfig()
        assert config.mode == "subprocess"
        assert config.timeout_seconds == 30.0
        assert config.max_memory_mb == 512
        assert config.max_cpu_percent == 100
        assert config.allow_network is False
        assert config.allow_file_write is False
        assert config.docker_image == "python:3.11-slim"
        assert config.docker_network == "none"
        assert config.process_pool_size == 2
        assert config.enable_caching is True

    def test_custom_values(self):
        """Test custom sandbox configuration values."""
        config = SandboxConfig(
            mode="docker",
            timeout_seconds=60.0,
            max_memory_mb=1024,
            allow_network=True,
        )
        assert config.mode == "docker"
        assert config.timeout_seconds == 60.0
        assert config.max_memory_mb == 1024
        assert config.allow_network is True


class TestGetSandboxConfig:
    """Tests for get_sandbox_config function."""

    def test_get_sandbox_config_no_file(self, tmp_path, monkeypatch):
        """Test getting sandbox config when config file doesn't exist."""
        monkeypatch.setattr("src.config.sandbox_config.CONFIG_DIR", tmp_path)
        config = get_sandbox_config()
        # Should return defaults
        assert config.mode == "subprocess"
        assert config.timeout_seconds == 30.0

    def test_get_sandbox_config_with_file(self, tmp_path, monkeypatch):
        """Test getting sandbox config from config file."""
        config_data = {
            "sandbox": {
                "mode": "docker",
                "timeoutSeconds": 60,
                "maxMemoryMB": 1024,
                "allowNetwork": True,
            }
        }
        config_file = tmp_path / "strategy_config.json"
        config_file.write_text(json.dumps(config_data))
        monkeypatch.setattr("src.config.sandbox_config.CONFIG_DIR", tmp_path)

        config = get_sandbox_config()
        assert config.mode == "docker"
        assert config.timeout_seconds == 60.0
        assert config.max_memory_mb == 1024
        assert config.allow_network is True

    def test_get_sandbox_config_invalid_mode(self, tmp_path, monkeypatch):
        """Test that invalid mode is converted to subprocess."""
        config_data = {"sandbox": {"mode": "invalid_mode"}}
        config_file = tmp_path / "strategy_config.json"
        config_file.write_text(json.dumps(config_data))
        monkeypatch.setattr("src.config.sandbox_config.CONFIG_DIR", tmp_path)

        config = get_sandbox_config()
        assert config.mode == "subprocess"


class TestGetStrategyConfig:
    """Tests for get_strategy_config function."""

    def test_get_strategy_config_no_file(self, tmp_path, monkeypatch):
        """Test getting strategy config when config file doesn't exist."""
        monkeypatch.setattr("src.config.sandbox_config.CONFIG_DIR", tmp_path)
        config = get_strategy_config()
        assert config.file_path == "data/strategies/"

    def test_get_strategy_config_with_file(self, tmp_path, monkeypatch):
        """Test getting strategy config from config file."""
        config_data = {"strategy": {"filePath": "custom/strategies/"}}
        config_file = tmp_path / "strategy_config.json"
        config_file.write_text(json.dumps(config_data))
        monkeypatch.setattr("src.config.sandbox_config.CONFIG_DIR", tmp_path)

        config = get_strategy_config()
        assert config.file_path == "custom/strategies/"


class TestSingletons:
    """Tests for singleton configuration functions."""

    def test_get_config_singleton(self, tmp_path, monkeypatch):
        """Test that get_config returns singleton instance."""
        reset_config()
        monkeypatch.setattr("src.config.sandbox_config.CONFIG_DIR", tmp_path)
        
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_get_strategy_config_singleton(self, tmp_path, monkeypatch):
        """Test that get_strategy_config_singleton returns singleton instance."""
        reset_config()
        monkeypatch.setattr("src.config.sandbox_config.CONFIG_DIR", tmp_path)
        
        config1 = get_strategy_config_singleton()
        config2 = get_strategy_config_singleton()
        assert config1 is config2

    def test_reset_config(self, tmp_path, monkeypatch):
        """Test that reset_config clears singleton instances."""
        monkeypatch.setattr("src.config.sandbox_config.CONFIG_DIR", tmp_path)
        
        config1 = get_config()
        reset_config()
        config2 = get_config()
        # After reset, should be a new instance
        # Note: They have same values but should be different objects
        assert config1 is not config2
