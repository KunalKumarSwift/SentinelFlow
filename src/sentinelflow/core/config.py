"""Application settings, read from environment variables once at start-up.

This is the only module allowed to read the environment. The composition root calls
``load_settings()`` and passes the result down; nothing else imports ``os.environ``.
Defaults run the whole system offline (no LLM, in-memory storage and queue).
Use ``uv run --env-file .env ...`` to load a local env file.

Environment:
    APP_ENV (default: "dev"), JWT_SECRET (required, >= 32 chars),
    LLM_BACKEND (default: "none"), LLM_MODEL (default per backend: qwen2.5:7b / claude-haiku-5-5),
    OLLAMA_URL (default: "http://localhost:11434"), ANTHROPIC_API_KEY,
    STORAGE_BACKEND (default: "memory"), DATABASE_URL,
    QUEUE_BACKEND (default: "memory"), REDIS_URL (default: "redis://localhost:6379/0"),
    INTEL_BACKEND (default: "mock"; "abuseipdb" needs ABUSEIPDB_API_KEY),
    TENANT_TOKEN_BUDGET_DAILY (default: 200000),
    API_HOST (default: "127.0.0.1"), API_PORT (default: 8000),
    RUN_WORKER_IN_API (default: true; false needs Postgres storage and a Redis queue),
    LOG_FORMAT (default: "json"; "console" for human-readable local logs),
    METRICS_PORT (default: 9100; where ``sentinelflow-worker`` serves /metrics),
    OTLP_ENDPOINT (e.g. "http://jaeger:4318"; unset = tracing off),
    AUTH_MODE (default: "hs256"; "oidc" = Keycloak), OIDC_ISSUER, OIDC_AUDIENCE
    (default: "sentinelflow-api"), OIDC_JWKS_URL (default: Keycloak's certs endpoint),
    POLICY_ENGINE (default: "incode"; "opa" = Rego in deploy/opa), OPA_URL,
    ACCESS_REVIEW_TENANTS (default: "acme"; comma-separated),
    NOTIFY_WEBHOOK_URL (unset = no chat notifications), NOTIFY_STYLE ("slack" / "discord"),
    TICKETING_BACKEND ("store" = memory/Postgres; "github" needs GITHUB_REPO, GITHUB_TOKEN).
"""

from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated, immutable application configuration."""

    model_config = SettingsConfigDict(frozen=True)

    app_env: Literal["dev", "test", "prod"] = "dev"
    jwt_secret: SecretStr = Field(min_length=32)
    llm_backend: Literal["none", "ollama", "anthropic"] = "none"
    llm_model: str | None = None
    ollama_url: str = "http://localhost:11434"
    anthropic_api_key: SecretStr | None = None
    storage_backend: Literal["memory", "postgres"] = "memory"
    database_url: SecretStr | None = None
    queue_backend: Literal["memory", "redis"] = "memory"
    redis_url: str = "redis://localhost:6379/0"
    intel_backend: Literal["mock", "abuseipdb"] = "mock"
    abuseipdb_api_key: SecretStr | None = None
    tenant_token_budget_daily: int = Field(default=200_000, gt=0)
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, gt=0, lt=65536)
    run_worker_in_api: bool = True
    log_format: Literal["json", "console"] = "json"
    metrics_port: int = Field(default=9100, gt=0, lt=65536)
    otlp_endpoint: str | None = None
    auth_mode: Literal["hs256", "oidc"] = "hs256"
    oidc_issuer: str | None = None
    oidc_audience: str = "sentinelflow-api"
    oidc_jwks_url: str | None = None
    policy_engine: Literal["incode", "opa"] = "incode"
    opa_url: str = "http://localhost:8181"
    access_review_tenants: str = "acme"
    notify_webhook_url: SecretStr | None = None
    notify_style: Literal["slack", "discord"] = "slack"
    ticketing_backend: Literal["store", "github"] = "store"
    github_repo: str | None = None
    github_token: SecretStr | None = None

    @model_validator(mode="after")
    def _require_backend_credentials(self) -> Self:
        if self.llm_backend == "anthropic" and self.anthropic_api_key is None:
            raise ValueError("LLM_BACKEND=anthropic requires ANTHROPIC_API_KEY")
        if self.storage_backend == "postgres" and self.database_url is None:
            raise ValueError("STORAGE_BACKEND=postgres requires DATABASE_URL")
        if self.intel_backend == "abuseipdb" and self.abuseipdb_api_key is None:
            raise ValueError("INTEL_BACKEND=abuseipdb requires ABUSEIPDB_API_KEY")
        if self.ticketing_backend == "github" and not (self.github_repo and self.github_token):
            raise ValueError("TICKETING_BACKEND=github requires GITHUB_REPO and GITHUB_TOKEN")
        if self.auth_mode == "oidc" and not self.oidc_issuer:
            raise ValueError("AUTH_MODE=oidc requires OIDC_ISSUER")
        shared = self.storage_backend == "postgres" and self.queue_backend == "redis"
        if not self.run_worker_in_api and not shared:
            # Separate workers only see work through a shared database and queue.
            raise ValueError(
                "RUN_WORKER_IN_API=false requires STORAGE_BACKEND=postgres and QUEUE_BACKEND=redis"
            )
        return self


def load_settings() -> Settings:
    """Read and validate settings from the environment.

    Returns:
        The validated settings.

    Raises:
        pydantic.ValidationError: If a value is missing, malformed, or inconsistent.
    """
    return Settings()  # pyright: ignore[reportCallIssue] -- fields are filled from env vars
