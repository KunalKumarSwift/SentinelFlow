# SentinelFlow

**Agentic security-incident orchestration with LangGraph — built secure-by-design (RBAC/ABAC, audit, human approval) and horizontally scalable.**

SentinelFlow receives security alerts, triages and investigates them with LLM-assisted
workflows, proposes containment actions, and executes those actions **only** after the
policy engine and (when required) a human approver allow it. Every decision is written
to a tamper-evident audit log.

> Status: **Phase 2 complete**: alerts are triaged and investigated by LangGraph workflows; containment runs only after policy-checked human approval (two-person rule for critical incidents); every step is in a hash-chained audit log; reports are built from verified facts; state can live in PostgreSQL. Next: Phase 3 (Redis queue, observability, load tests). See the [roadmap](docs/06-roadmap.md).

## Why this project exists

Most "AI agent" demos let the LLM call any tool with god-mode credentials. SentinelFlow
shows the opposite:

- The LLM **proposes**; deterministic code **decides and executes**.
- Every tool call is checked against **who** asked, **what** they asked for, and **on which resource**.
- Sensitive actions pause the graph (`interrupt`) until an authorised human approves.
- Workers are stateless; graph state lives in a checkpointer, so any worker can resume any run.

## Workflows

| # | Workflow | Purpose |
|---|---|---|
| 1 | Ingestion & dedup | Normalise alerts, group duplicates into incidents |
| 2 | Triage | Enrich (threat intel, user, asset), score severity, filter false positives |
| 3 | Investigation | Timeline, MITRE ATT&CK mapping, related events (RAG) |
| 4 | Containment | Propose actions → policy check → human approval → execute |
| 5 | Report | Post-incident report with root cause and lessons learned |
| 6 | Access review | Scheduled scan for dormant / over-privileged accounts |

All external systems (SIEM, threat intel, identity provider, ticketing, LLM) are
**pluggable providers**. Phase 1 ships with mock providers fed by a synthetic
attack simulator, so the whole system runs locally for free.

## Getting started

```bash
uv sync                                   # install (Python 3.12+)
uv run pytest                             # run the tests
uv run ruff check . && uv run pyright     # lint + strict type check
uv run lint-imports                       # enforce the layer rules
```

### Run the demo (offline, free)

```bash
# terminal 1: API + background worker (in-memory, mock intel, no LLM)
APP_ENV=dev JWT_SECRET=change-me-to-32-or-more-characters uv run sentinelflow-api

# terminal 2: fire synthetic attacks at it
uv run sentinelflow-sim run brute_force --seed 42
uv run sentinelflow-sim run benign_travel --seed 42
```

Open <http://127.0.0.1:8000/docs>, get a token from `POST /v1/auth/dev-token`
(e.g. roles `["soc-analyst-l1"]`, tenant `acme`), click **Authorize**, then
`GET /v1/incidents`: the brute-force incident is **awaiting approval** (high), the VPN login
is closed or triaged **low**. Then, as approvers:

1. Token for `incident-commander` → `GET /v1/approvals` → approve `disable_user`.
2. Token for `soc-analyst-l2` → approve `block_ip` (an L2 cannot approve the high-impact one).
3. The worker resumes the paused LangGraph run and the incident becomes **contained**;
   `GET /v1/audit/verify` (as `auditor`) proves the whole trail is untampered.

To keep incidents, approvals, the audit chain and paused runs across restarts, use
PostgreSQL (tables are created at start-up):

```bash
STORAGE_BACKEND=postgres DATABASE_URL=postgresql://user:pass@localhost:5432/sentinelflow \
APP_ENV=dev JWT_SECRET=change-me-to-32-or-more-characters uv run sentinelflow-api
```

### Run scaled out (Docker Compose)

```bash
docker compose up --build --scale worker=3       # API + 3 workers + Postgres + Redis
uv run python scripts/smoke_test.py               # alert in → run paused for approval
```

The API process only serves HTTP (`RUN_WORKER_IN_API=false`); `sentinelflow-worker`
processes share the work through Redis and resume each other's paused runs from
PostgreSQL checkpoints.

Choose an LLM for real verdicts:

| `LLM_BACKEND` | Cost | Extra settings |
|---|---|---|
| `none` (default) | free | — every incident goes to human review (`needs_review`) |
| `ollama` | free, local | `OLLAMA_URL`, `LLM_MODEL` (default `qwen2.5:7b`) |
| `anthropic` | ~$0.10 / $0.50 per 1M tokens | `ANTHROPIC_API_KEY`, `LLM_MODEL` (default `claude-haiku-5-5`) |

## Documentation

| Doc | What it covers |
|---|---|
| [01 Requirements](docs/01-requirements.md) | Goals, personas, use cases, functional & non-functional requirements |
| [02 High-Level Design](docs/02-hld.md) | Architecture, components, data flow, security & scaling strategy |
| [03 Low-Level Design](docs/03-lld/README.md) | Code layout, domain model, graphs, security internals, API, data, runtime, simulator |
| [04 Engineering Guidelines](docs/04-engineering-guidelines.md) | TDD workflow, coding principles, file-size and style rules |
| [05 Testing Strategy](docs/05-testing-strategy.md) | Test pyramid, fakes, security test matrix, LLM evaluation |
| [06 Roadmap](docs/06-roadmap.md) | Phased delivery plan as small TDD slices |
| [ADRs](docs/adr/README.md) | Architecture decision records |

## Tech stack (planned)

Python 3.12 · uv · LangGraph · LangChain · FastAPI · Pydantic · PostgreSQL · Redis Streams ·
PyJWT → Keycloak · in-code policy engine → OPA · Ollama / Claude Haiku · pytest · ruff · pyright ·
import-linter · Docker Compose → Kubernetes · OpenTelemetry · Langfuse · Prometheus · Grafana

## Engineering principles (short version)

- **Test-driven:** no production code without a failing test first.
- **Small files:** 50–100 lines per file, ≤ 20 lines per function.
- **Readable:** typed, documented (Google-style docstrings), one responsibility per module.
- **Injectable:** every external dependency is a `Protocol`; tests use fakes, never network.
