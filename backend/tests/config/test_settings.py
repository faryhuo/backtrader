from pathlib import Path

from src.config import settings


def test_ensure_resource_dirs_creates_directories(tmp_path, monkeypatch):
    resources_dir = tmp_path / "resources"
    frontend_dir = resources_dir / "frontend"
    images_dir = resources_dir / "images"
    strategy_dir = resources_dir / "strategy"
    config_dir = resources_dir / "config"

    monkeypatch.setattr(settings, "RESOURCES_DIR", resources_dir)
    monkeypatch.setattr(settings, "FRONTEND_DIR", frontend_dir)
    monkeypatch.setattr(settings, "IMAGES_DIR", images_dir)
    monkeypatch.setattr(settings, "STRATEGY_DIR", strategy_dir)
    monkeypatch.setattr(settings, "CONFIG_DIR", config_dir)

    settings.ensure_resource_dirs()

    assert resources_dir.is_dir()
    assert frontend_dir.is_dir()
    assert images_dir.is_dir()
    assert strategy_dir.is_dir()
    assert config_dir.is_dir()

