"""
Unit tests for worker configuration module.
"""
import json
import pytest
from pathlib import Path

from src.config.worker_config import (
    WorkerPoolConfig,
    get_worker_pool_config,
    get_config,
    reset_config,
    _parse_bool,
)


class TestParseBool:
    """Tests for _parse_bool helper function."""

    def test_parse_bool_true_values(self):
        """Test that various true representations are parsed correctly."""
        assert _parse_bool(True) is True
        assert _parse_bool("true") is True
        assert _parse_bool("1") is True
        assert _parse_bool("yes") is True
        assert _parse_bool("on") is True

    def test_parse_bool_false_values(self):
        """Test that various false representations are parsed correctly."""
        assert _parse_bool(False) is False
        assert _parse_bool("false") is False
        assert _parse_bool("0") is False


class TestWorkerPoolConfig:
    """Tests for WorkerPoolConfig dataclass."""

    def test_default_values(self):
        """Test default worker pool configuration values."""
        config = WorkerPoolConfig()
        assert config.enabled is True
        assert config.pool_size == 4
        assert config.task_timeout_seconds == 300.0
        assert config.max_memory_mb == 1024
        assert config.heartbeat_interval_seconds == 10.0
        assert config.shutdown_timeout_seconds == 30.0
        assert config.max_queue_size == 100
        assert config.allow_network is True
        assert config.allow_file_write is True

    def test_custom_values(self):
        """Test custom worker pool configuration values."""
        config = WorkerPoolConfig(
            enabled=False,
            pool_size=8,
            task_timeout_seconds=600.0,
            max_memory_mb=2048,
        )
        assert config.enabled is False
        assert config.pool_size == 8
        assert config.task_timeout_seconds == 600.0
        assert config.max_memory_mb == 2048


class TestGetWorkerPoolConfig:
    """Tests for get_worker_pool_config function."""

    def test_get_worker_pool_config_no_file(self, tmp_path, monkeypatch):
        """Test getting worker pool config when config file doesn't exist."""
        monkeypatch.setattr("src.config.worker_config.CONFIG_DIR", tmp_path)
        config = get_worker_pool_config()
        # Should return defaults
        assert config.enabled is True
        assert config.pool_size == 4

    def test_get_worker_pool_config_with_file(self, tmp_path, monkeypatch):
        """Test getting worker pool config from config file."""
        config_data = {
            "workerPool": {
                "enabled": False,
                "poolSize": 8,
                "taskTimeoutSeconds": 600,
                "maxMemoryMB": 2048,
            }
        }
        config_file = tmp_path / "strategy_config.json"
        config_file.write_text(json.dumps(config_data))
        monkeypatch.setattr("src.config.worker_config.CONFIG_DIR", tmp_path)

        config = get_worker_pool_config()
        assert config.enabled is False
        assert config.pool_size == 8
        assert config.task_timeout_seconds == 600.0
        assert config.max_memory_mb == 2048

    def test_get_worker_pool_config_partial(self, tmp_path, monkeypatch):
        """Test getting worker pool config with partial configuration."""
        config_data = {"workerPool": {"poolSize": 2}}
        config_file = tmp_path / "strategy_config.json"
        config_file.write_text(json.dumps(config_data))
        monkeypatch.setattr("src.config.worker_config.CONFIG_DIR", tmp_path)

        config = get_worker_pool_config()
        assert config.pool_size == 2
        # Other values should be defaults
        assert config.enabled is True
        assert config.task_timeout_seconds == 300.0


class TestSingletons:
    """Tests for singleton configuration functions."""

    def test_get_config_singleton(self, tmp_path, monkeypatch):
        """Test that get_config returns singleton instance."""
        reset_config()
        monkeypatch.setattr("src.config.worker_config.CONFIG_DIR", tmp_path)
        
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config(self, tmp_path, monkeypatch):
        """Test that reset_config clears singleton instance."""
        monkeypatch.setattr("src.config.worker_config.CONFIG_DIR", tmp_path)
        
        config1 = get_config()
        reset_config()
        config2 = get_config()
        # After reset, should be a new instance
        assert config1 is not config2
