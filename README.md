# SentinelFlow

**Agentic security-incident orchestration with LangGraph — built secure-by-design (RBAC/ABAC, audit, human approval) and horizontally scalable.**

SentinelFlow receives security alerts, triages and investigates them with LLM-assisted
workflows, proposes containment actions, and executes those actions **only** after the
policy engine and (when required) a human approver allow it. Every decision is written
to a tamper-evident audit log.

> Status: **Phase 1 complete**: alerts are ingested, deduplicated and triaged by a LangGraph workflow behind an RBAC-protected API. Next: Phase 2 (policy engine, human-approved containment, audit chain). See the [roadmap](docs/06-roadmap.md).

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
`GET /v1/incidents`: the brute-force incident is triaged **high**, the VPN login **low**.

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
