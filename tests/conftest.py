"""Configuration d'une base SQLite isolée pour chaque test."""
import pytest
from gesco import database

@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    app_dir = tmp_path / "gesco-test"
    monkeypatch.setattr(database, "APP_DIR", app_dir)
    monkeypatch.setattr(database, "DB_PATH", app_dir / "test.db")
    database.initialize_database()
