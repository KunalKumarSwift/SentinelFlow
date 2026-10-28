"""Tests for environment-driven settings."""

import pytest
from pydantic import ValidationError

from sentinelflow.core.config import load_settings

SECRET = "s" * 32
MANAGED_VARS = ("JWT_SECRET", "LLM_BACKEND", "ANTHROPIC_API_KEY", "STORAGE_BACKEND", "DATABASE_URL")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in MANAGED_VARS:
        monkeypatch.delenv(name, raising=False)


def test_defaults_run_fully_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", SECRET)
    settings = load_settings()
    assert (settings.app_env, settings.llm_backend, settings.storage_backend) == (
        "dev",
        "none",
        "memory",
    )


def test_env_vars_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("LLM_BACKEND", "ollama")
    assert load_settings().llm_backend == "ollama"


def test_secret_is_hidden_when_printed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", SECRET)
    assert SECRET not in repr(load_settings())


def test_missing_jwt_secret_is_rejected() -> None:
    with pytest.raises(ValidationError, match="jwt_secret"):
        load_settings()


def test_short_jwt_secret_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", "too-short")
    with pytest.raises(ValidationError, match="at least 32"):
        load_settings()


def test_unknown_backend_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("LLM_BACKEND", "gpt-magic")
    with pytest.raises(ValidationError, match="llm_backend"):
        load_settings()


def test_anthropic_backend_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("LLM_BACKEND", "anthropic")
    with pytest.raises(ValidationError, match="ANTHROPIC_API_KEY"):
        load_settings()


def test_postgres_storage_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("STORAGE_BACKEND", "postgres")
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        load_settings()
