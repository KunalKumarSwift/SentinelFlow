# One image for every process: the API (`sentinelflow-api`) and workers (`sentinelflow-worker`).
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# Dependencies first, so a code change does not invalidate the dependency layer.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN uv sync --locked --no-dev

# Never run as root inside the container.
RUN useradd --system --uid 10001 sentinel
USER sentinel

ENV API_HOST=0.0.0.0 API_PORT=8000
EXPOSE 8000
CMD ["sentinelflow-api"]
