import pytest

from pydantic_settings_example import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    get_settings.cache_clear()


def test_defaults() -> None:
    s = Settings(_env_file=None)
    assert s.db_url == "sqlite:///./app.db"
    assert s.debug is False


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXAMPLE_DB_URL", "postgresql://x")
    monkeypatch.setenv("EXAMPLE_DEBUG", "true")
    s = Settings(_env_file=None)
    assert s.db_url == "postgresql://x"
    assert s.debug is True
