"""Settings tests start from an environment without any SentinelFlow variables."""

import pytest

SECRET = "s" * 32
MANAGED_VARS = (
    "JWT_SECRET",
    "LLM_BACKEND",
    "ANTHROPIC_API_KEY",
    "STORAGE_BACKEND",
    "DATABASE_URL",
    "QUEUE_BACKEND",
    "RUN_WORKER_IN_API",
    "LOG_FORMAT",
    "AUTH_MODE",
    "OIDC_ISSUER",
    "INTEL_BACKEND",
    "ABUSEIPDB_API_KEY",
    "TICKETING_BACKEND",
    "GITHUB_REPO",
    "GITHUB_TOKEN",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in MANAGED_VARS:
        monkeypatch.delenv(name, raising=False)
