"""Settings: each backend refuses to start without what it needs."""

import pytest
from pydantic import ValidationError

from sentinelflow.core.config import load_settings
from tests.unit.core.conftest import SECRET


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


def test_api_without_worker_requires_shared_storage_and_queue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("RUN_WORKER_IN_API", "false")
    with pytest.raises(ValidationError, match="QUEUE_BACKEND=redis"):
        load_settings()


def test_api_without_worker_is_allowed_with_postgres_and_redis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name, value in {
        "JWT_SECRET": SECRET,
        "RUN_WORKER_IN_API": "false",
        "STORAGE_BACKEND": "postgres",
        "DATABASE_URL": "postgresql://db/sf",
        "QUEUE_BACKEND": "redis",
    }.items():
        monkeypatch.setenv(name, value)
    assert load_settings().run_worker_in_api is False


def test_logs_are_json_unless_console_is_chosen(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", SECRET)
    assert load_settings().log_format == "json"
    monkeypatch.setenv("LOG_FORMAT", "console")
    assert load_settings().log_format == "console"


def test_oidc_mode_requires_an_issuer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("AUTH_MODE", "oidc")
    with pytest.raises(ValidationError, match="OIDC_ISSUER"):
        load_settings()
    monkeypatch.setenv("OIDC_ISSUER", "http://keycloak:8080/realms/sentinelflow")
    assert load_settings().auth_mode == "oidc"


def test_abuseipdb_intel_requires_an_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("INTEL_BACKEND", "abuseipdb")
    with pytest.raises(ValidationError, match="ABUSEIPDB_API_KEY"):
        load_settings()
    monkeypatch.setenv("ABUSEIPDB_API_KEY", "k" * 80)
    assert load_settings().intel_backend == "abuseipdb"


def test_github_ticketing_requires_repo_and_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("TICKETING_BACKEND", "github")
    monkeypatch.setenv("GITHUB_REPO", "acme-sec/incidents")
    with pytest.raises(ValidationError, match="GITHUB_TOKEN"):
        load_settings()
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_x")
    assert load_settings().ticketing_backend == "github"
