# SentinelFlow

**Agentic security-incident orchestration with LangGraph — built secure-by-design (RBAC/ABAC, audit, human approval) and horizontally scalable.**

SentinelFlow receives security alerts, triages and investigates them with LLM-assisted
workflows, proposes containment actions, and executes those actions **only** after the
policy engine and (when required) a human approver allow it. Every decision is written
to a tamper-evident audit log.

> **Status: all four roadmap phases are built** (MVP → secure containment → scale & observe →
> production identity & deployment): 980+ tests at 100 % coverage, with contract suites that
> run against in-memory **and** real PostgreSQL / Redis / OPA backends. Open items: VirusTotal,
> GitHub Issues and Slack providers, a Langfuse callback, a demo video. See the
> [roadmap](docs/06-roadmap.md).

## Highlights

- **LangGraph orchestration with human-in-the-loop.** A lifecycle graph (triage →
  investigation → approvals → containment → report) pauses with `interrupt()` and resumes
  from a **PostgreSQL checkpointer** on any worker, crash-safe and proven by tests.
- **The LLM proposes, code decides.** The model can only *narrow* an allow-listed playbook,
  never set severity, never dismiss a HIGH incident. Untrusted text goes in escaped
  `<untrusted_data>` blocks, prompt injection is detected and forces human review, and every
  side effect goes through a **tool guard**.
- **Authorisation in depth.** RBAC + ABAC (separation of duties, no self-approval, distinct
  approvers, two-person rule for critical incidents), an in-code engine **and** an equivalent
  **OPA/Rego** policy passing one shared test suite, **Keycloak OIDC** (RS256/JWKS with key
  rotation), and **PostgreSQL row-level security** per tenant.
- **Tamper-evident audit.** A per-tenant SHA-256 hash chain, verifiable through the API.
  Reports are written from verified audit facts, and PII is pseudonymised for anyone without
  `incident:read_pii`.
- **Scales out.** Stateless API and worker processes over Redis (an at-least-once queue with a
  Lua claim and visibility timeout) and Postgres; per-tenant rate limits and LLM token
  budgets. **Measured:** p95 69 ms under load and 18 → 55 runs/s from 1 → 4 workers
  ([benchmarks](docs/benchmarks.md)).
- **Observable and deployable.** structlog JSON with correlation ids, OpenTelemetry spans per
  step, Prometheus metrics with a Grafana dashboard, Docker Compose, and a hardened Helm
  chart (HPA, KEDA on queue depth, CronJob).
- **Engineering discipline.** TDD, files ≤ 120 lines, functions ≤ 20 lines, `pyright --strict`,
  enforced import layers, 8 ADRs, and full HLD/LLD docs updated with every change.

## Architecture

```mermaid
flowchart LR
    SIEM[Detection sources<br/>simulator · SIEM] -->|POST /v1/alerts| API
    Analyst[Analysts<br/>Streamlit UI · Swagger] -->|OIDC bearer token| API
    subgraph API[FastAPI · stateless]
      Auth[auth · rate limit] --> Policy[policy engine<br/>in-code or OPA]
    end
    API -->|StartRun / ResumeRun| Q[(Redis queue)]
    Q --> W1[worker] & W2[worker ×N]
    subgraph Worker[LangGraph lifecycle]
      T[triage] --> I[investigation] --> A{{approval<br/>interrupt}} --> C[containment] --> R[report]
    end
    W1 --- Worker
    Worker -->|tool guard| Providers[LLM · threat intel · identity · ticketing]
    API & Worker --> PG[(PostgreSQL<br/>RLS · audit chain · checkpoints)]
    Worker -. spans/metrics .-> Obs[OTel · Prometheus · Grafana]
```

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
| 2 | Triage | Enrich (threat intel, user), score severity, filter false positives |
| 3 | Investigation | Timeline, MITRE ATT&CK mapping, related events |
| 4 | Containment | Propose actions → policy check → human approval → execute |
| 5 | Report | Post-incident report built from verified audit facts |
| 6 | Access review | Scheduled scan for dormant / over-privileged accounts |

All external systems (SIEM, threat intel, identity provider, ticketing, LLM) are
**pluggable providers** chosen by configuration. Mock providers fed by a synthetic attack
simulator (8 scenarios) let the whole system run locally for free.

## Getting started

```bash
uv sync                                   # install (Python 3.12+)
uv run pytest -m "not e2e"                # run the tests (in-memory backends)
uv run ruff check . && uv run pyright     # lint + strict type check
uv run lint-imports                       # enforce the layer rules
# optional: also run the contract tests against real backends
TEST_DATABASE_URL=postgresql://... TEST_REDIS_URL=redis://localhost/15 uv run pytest -m "not e2e"
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
3. The worker resumes the paused LangGraph run, executes both actions and **closes** the
   incident; `GET /v1/incidents/{id}/report` shows the report and `GET /v1/audit/verify`
   (as `auditor`) proves the whole trail is untampered.

To keep incidents, approvals, the audit chain and paused runs across restarts, use
PostgreSQL (tables are created at start-up):

```bash
STORAGE_BACKEND=postgres DATABASE_URL=postgresql://user:pass@localhost:5432/sentinelflow \
APP_ENV=dev JWT_SECRET=change-me-to-32-or-more-characters uv run sentinelflow-api
```

### Analyst UI (Streamlit)

```bash
uv run streamlit run src/sentinelflow/ui/app.py     # http://localhost:8501
```

Pick a user and role in the sidebar (dev tokens), then browse incidents, approve or reject
from the approvals inbox, and verify the audit chain. The UI is a pure REST client
(enforced by an import-linter contract), so every API rule applies to it.

### Run scaled out (Docker Compose)

```bash
docker compose up --build --scale worker=3       # API + 3 workers + Postgres + Redis
uv run python scripts/smoke_test.py               # alert in → run paused for approval
```

The API process only serves HTTP (`RUN_WORKER_IN_API=false`); `sentinelflow-worker`
processes share the work through Redis and resume each other's paused runs from
PostgreSQL checkpoints.

### Deploy to Kubernetes (Helm)

```bash
kubectl create secret generic sentinelflow-secrets \
  --from-literal=JWT_SECRET=... --from-literal=DATABASE_URL=postgresql://...
helm install sf deploy/helm/sentinelflow --set worker.keda.enabled=true
```

API behind an HPA, workers scaled by KEDA on queue depth, and the access review as a
daily CronJob. Pods are non-root with read-only filesystems.

### Sign in with Keycloak (OIDC) instead of dev tokens

```bash
AUTH_MODE=oidc docker compose --profile oidc up --build
TOKEN=$(curl -s -d grant_type=password -d client_id=sentinelflow-cli \
  -d username=bob -d password=demo-password \
  http://localhost:8080/realms/sentinelflow/protocol/openid-connect/token | jq -r .access_token)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/incidents
```

Demo users (password `demo-password`): `alice` (L1), `bob` (L2), `carol` and `dave`
(incident commanders), `erin` (auditor).

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
| [Benchmarks](docs/benchmarks.md) | Measured API latency and worker throughput (1 → 4 workers) |
| [ADRs](docs/adr/README.md) | Architecture decision records |

## Tech stack

Python 3.12 · uv · LangGraph · LangChain · FastAPI · Pydantic · PostgreSQL (psycopg 3, RLS,
LangGraph checkpointer) · Redis · PyJWT (HS256 dev / RS256 OIDC) · Keycloak · OPA/Rego ·
Ollama / Claude Haiku · structlog · OpenTelemetry · Prometheus · Grafana · Streamlit ·
Docker Compose · Helm/Kubernetes (HPA, KEDA) · pytest · hypothesis · Locust · ruff · pyright ·
import-linter

## Engineering principles (short version)

- **Test-driven:** no production code without a failing test first.
- **Small files:** 50–100 lines per file, ≤ 20 lines per function.
- **Readable:** typed, documented (Google-style docstrings), one responsibility per module.
- **Injectable:** every external dependency is a `Protocol`; tests use fakes, never network.
