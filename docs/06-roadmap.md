# 06 — Roadmap

Each phase is a set of **small TDD slices**. A slice is done when its tests pass and it meets
the definition of done in the [engineering guidelines](04-engineering-guidelines.md#7-definition-of-done-per-slice).
"First tests" lists the tests to write before any production code.

## Phase 0 — Bootstrap ✅

| Slice | Deliverable | First tests |
|---|---|---|
| 0.1 | `pyproject.toml` (uv), ruff, pyright strict, pytest, import-linter config | A trivial `test_package_imports` |
| 0.2 | `scripts/check_file_size.py` | Fails on a 121-line temp file, passes on 120 |
| 0.3 | GitHub Actions CI: lint, type-check, import rules, size check, tests | CI green on the trivial test |
| 0.4 | `core/clock.py`, `core/ids.py`, `core/config.py` | `FakeClock` advances; config defaults; required secret missing raises |

## Phase 1 — MVP: ingest and triage (single process) ✅

| Slice | Deliverable | First tests |
|---|---|---|
| 1.1 ✅ | Domain enums + `Alert`, `Entities`, `Incident` | Frozen; equality; invalid severity rejected |
| 1.2 ✅ | `fingerprint_alert`, `is_duplicate` | Same entities → same fingerprint; outside window → not duplicate |
| 1.3 ✅ | `score_severity` + table | Table-driven cases per rule and modifier |
| 1.4 ✅ | Incident state machine `next_status` | Every legal transition; illegal raises |
| 1.5 ✅ | Simulator core + `brute_force` + `benign` | Same seed → identical output; expected fields set |
| 1.6 ✅ | Protocols + fakes + `MockThreatIntel`, `MockIdentity` | Contract tests for intel and identity |
| 1.7 ✅ | Permissions, roles, RBAC check | Generated RBAC matrix tests |
| 1.8 ✅ | `Principal` from HS256 JWT | Valid; expired; bad signature; missing claim |
| 1.9 ✅ | Ingestion service (dedup + incident upsert) | New alert → new incident; duplicate → merged |
| 1.10 ✅ | Triage graph with `FakeLLM` | Brute-force → HIGH/TP; benign → FP closed; invalid LLM output → NEEDS_REVIEW |
| 1.11 ✅ | Workflow registry + orchestrator (triage only) | Unknown workflow rejected; permission required |
| 1.12 ✅ | `MemoryRunQueue` + worker loop | StartRun runs graph; failure not acked |
| 1.13a ✅ | API app: bearer auth, permission dependency, problem+json errors, health, dev-token | 401/403 paths; error mapping; dev-token hidden outside dev |
| 1.13b ✅ | API routes: alerts, incidents, workflows/runs (start) | 401/403/404/409 paths; tenant isolation; happy path |
| 1.14 ✅ | `OllamaLLM` + `AnthropicLLM` providers + facade | Facade selects by config; error translation (no network in unit tests) |
| 1.15 ✅ | Composition root, `sentinelflow-api` (API + worker thread), `sentinelflow-sim` CLI | End-to-end: alert → worker → triaged incident; unsupported backends fail at start-up |

**Demo:** `sentinelflow-sim run brute_force` → incident triaged HIGH in Swagger.

## Phase 2 — Secure containment ✅

| Slice | Deliverable | First tests |
|---|---|---|
| 2.1 ✅ | Action catalogue + `approval_requirement` | Table-driven by kind × severity |
| 2.2 ✅ | ABAC rules (`security/abac_rules.py`, one small function each) | Allow + deny case per rule |
| 2.3 ✅ | Policy engine (deny-overrides) | Order: tenant → RBAC → ABAC; reason strings |
| 2.4a ✅ | Audit chain + `AuditStore` (memory) | Hypothesis tamper tests |
| 2.4b ✅ | Audit API (`/v1/audit`, `/v1/audit/verify`) + recording API events | auditor-only; tamper → `ok=false` |
| 2.5 ✅ | Tool guard | Scope ∩ initiator ∩ orchestrator; every call audited |
| 2.6a ✅ | Injection detector + triage `scan_for_injection` + `prompt_injection` scenario | Injection phrases flagged; verdict forced to review |
| 2.6b ✅ | PII redaction in API responses | PII hidden without `incident:read_pii` |
| 2.7a ✅ | Event store contract + memory store, timeline builder, ATT&CK table + keyword retrieval | Window/entity/tenant filtering; repeat collapsing; ranking |
| 2.7b ✅ | Investigation graph (LLM picks techniques/actions only from candidates) | Techniques only from candidates; actions only from catalogue |
| 2.8a ✅ | Approvals (quorum, rejection, expiry), run records, their repositories; `IdentityProvider.apply` (idempotent) | Two-person rule; duplicate decision → conflict; idempotent apply |
| 2.8b ✅ | Lifecycle: investigation + containment with `interrupt` and a checkpointer | Pauses; resumes; executes only with quorum |
| 2.9 ✅ | Approvals API + resume command; run records + `GET /v1/runs/{id}` | SoD, self-action, distinct approvers, 409 on decided |
| 2.10 ✅ | Report step + ticketing (facts from the audit trail) | Report contains facts; ticket created |
| 2.11a ✅ | PostgreSQL repositories (incidents, alerts, approvals, runs, audit) | Contract tests run against memory and Postgres (CI service container) |
| 2.11b ✅ | Postgres checkpointer + `STORAGE_BACKEND=postgres` wiring | A paused run resumes in a fresh runtime (simulated restart) |
| 2.12 ✅ | Remaining simulator scenarios | Each scenario's `expected` met end-to-end (graph level) |

**Demo:** leaked-key scenario → commander + second approver → key revoked → report; audit verifies.

## Phase 3 — Scale and observe ✅

| Slice | Deliverable | First tests |
|---|---|---|
| 3.1 ✅ | `RedisRunQueue` (visibility-deadline sorted set, Lua claim, DLQ; ADR 0008) | Contract tests shared with memory queue |
| 3.2 ✅ | Docker Compose: api, worker ×N, postgres, redis, ollama; `sentinelflow-worker`; Postgres tickets | Smoke test script (run against API + 2 worker processes) |
| 3.3 ✅ | Rate limiting + LLM budget decorator | 429 after limit; `BudgetExceededError` → NEEDS_REVIEW |
| 3.4 ✅ | structlog + correlation IDs | Log line contains run_id/tenant_id |
| 3.5 ✅ | OpenTelemetry + Jaeger (Langfuse callback deferred) | Span created per node (in-memory exporter) |
| 3.6 ✅ | Prometheus metrics + Grafana dashboard JSON | Metric increments on run completion |
| 3.7 ✅ | Locust load test + [`docs/benchmarks.md`](benchmarks.md) | — (measurement; found and fixed a start-up schema race) |
| 3.8 ✅ | Crash-recovery demo (kill worker mid-run) | Integration test: un-acked run resumed by another worker |

## Phase 4 — Production-grade identity and deployment ✅ (open: 4.6 extra providers, demo video)

| Slice | Deliverable |
|---|---|
| 4.1 ✅ | Keycloak realm export + RS256/JWKS verifier |
| 4.2 ✅ | `OpaPolicyEngine` + Rego policies, same test-suite as in-code engine |
| 4.3 ✅ | PostgreSQL row-level security per tenant |
| 4.4 ✅ | Access-review scheduled workflow |
| 4.5 ✅ | Helm chart, HPA for API, KEDA for workers |
| 4.6 (part) ✅ | Optional real providers: **AbuseIPDB done**; VirusTotal, GitHub Issues, Slack/Discord webhook open |
| 4.7 ✅ | Minimal UI (Streamlit): incidents, approvals inbox, audit view |
| 4.8 (part) ✅ | Architecture diagram + highlights in the README ✅; demo video open |

## Résumé checkpoints

- After Phase 1: "LangGraph triage pipeline with RBAC-protected FastAPI, TDD, 90 %+ coverage".
- After Phase 2: add "policy engine (RBAC+ABAC), human-in-the-loop approvals, hash-chained audit log, prompt-injection defences".
- After Phase 3: add measured throughput/latency numbers and crash-recovery guarantees
  (measured: p95 69 ms at ~20 req/s, 18 → 55 runs/s from 1 → 4 workers; see benchmarks).
- After Phase 4: add "OIDC (Keycloak), OPA, multi-tenant RLS, Kubernetes autoscaling".
