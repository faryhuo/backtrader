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


def test_get_sqlite_db_path_from_url_resolves_relative_path(monkeypatch):
    monkeypatch.setattr(settings, "PROJECT_ROOT", Path("/app"))

    path = settings.get_sqlite_db_path_from_url("sqlite:///trading_sessions.db")

    assert path == Path("/app/trading_sessions.db")


def test_ensure_database_dir_uses_effective_database_url(tmp_path, monkeypatch):
    db_path = tmp_path / "runtime" / "trading_sessions.db"
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{db_path}")

    settings.ensure_database_dir()

    assert db_path.parent.is_dir()
