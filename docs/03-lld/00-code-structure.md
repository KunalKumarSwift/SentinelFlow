# LLD 00 — Code Structure

## 1. Repository layout (as built)

```
WorkflowOrchestration/
├── pyproject.toml  uv.lock   # one installable package: sentinelflow (+ dev / ui groups)
├── .importlinter             # layer contract + "UI is a pure HTTP client" contract
├── Dockerfile  docker-compose.yml
├── deploy/                   # helm chart, keycloak realm, opa policy, prometheus, grafana, postgres init
├── scripts/                  # check_file_size, gen_opa_data, smoke_test, load/ (locust, run_stats)
├── docs/                     # requirements, HLD, LLD 00-08, guidelines, testing, roadmap, benchmarks, ADRs
├── src/sentinelflow/
│   ├── core/          clock, ids, config (the ONLY env reader), logging
│   ├── domain/        frozen dataclasses + pure rules: alerts, incidents, severity, scoring(+table),
│   │                  dedup, enrichment, triage, investigation, timeline, attack(+table), playbooks,
│   │                  actions(+table), approvals, runs, audit, report, access_review, principals, errors
│   ├── contracts/     Protocols: llm, threat_intel, identity, accounts, event_store, repositories,
│   │                  approvals, runs, run_queue, audit_store, ticketing, metrics, rate_limit, token_budget
│   ├── security/      permissions, roles, rbac, abac_rules, policy(+engine), opa_engine(+input),
│   │                  tokens (HS256), oidc/ (RS256/JWKS), verifier, tool_guard, audit_chain/recorder/reader,
│   │                  injection, redaction, throttle, system_principals
│   ├── providers/     llm/ (ollama, anthropic, disabled, budgeted), intel/ (mock, abuseipdb),
│   │                  identity/ (mock, accounts, jwks_http), storage/ (memory + postgres/),
│   │                  queue/ (memory, redis), ratelimit/, budget/, metrics/, events/, ticketing/
│   ├── facades/       config → provider switches: llm, intel, policy, auth, tracing, shared_state
│   ├── workflows/     ingestion, triage, investigation, report, orchestrator (lifecycle graph),
│   │                  access_review, registry, run_start
│   ├── runtime/       worker, dispatch, start/resume handlers, access_review_job
│   ├── api/           FastAPI app, auth, correlation, problems, routes/, schemas/
│   ├── simulator/     scenarios/ (8), demo seed + accounts, CLI (sentinelflow-sim)
│   ├── ui/            Streamlit app over the REST API (client, http, models, views)
│   └── bootstrap/     composition root: wiring, stores, container, lifecycle; serve / worker /
│                      access-review entry points
└── tests/             unit/ integration/ api/ contracts/ (memory + Postgres/Redis/OPA) fakes/
```

Each workflow folder follows the same shape:

```
workflows/triage/
├── __init__.py      # exports build_triage_graph only
├── state.py         # TypedDict state for this graph
├── deps.py          # frozen dataclass of injected protocols
├── prompts.py       # prompt templates (data, not logic)
├── nodes/           # one node factory per file, ≤ 60 lines each
│   ├── enrich.py  score.py  classify.py  route.py
└── graph.py         # wires nodes and edges, nothing else
```

## 2. Layer rules (enforced by import-linter in CI)

```
bootstrap                      ← may import anything (composition root)
api  |  runtime  |  simulator  ← entry points
facades                        ← config value → provider (imports providers)
workflows  |  providers        ← independent of each other
security
contracts
domain
core
```

- A layer may import only layers **below** it.
- `workflows` never imports `providers`: it receives them through `deps.py` as protocols.
- Sibling workflows never import each other; the orchestrator composes them via the registry.
- Modules starting with `_` are private to their package.

## 3. Dependency injection pattern

No global singletons and no service locators. Dependencies enter through one frozen
dataclass per feature, built in `bootstrap.py`.

```python
@dataclass(frozen=True, slots=True)
class TriageDeps:
    """Everything the triage graph needs from the outside world."""

    intel: ThreatIntelProvider
    identity: IdentityProvider
    llm: LLMProvider
    clock: Clock
```

Nodes are built by **factory functions** that close over their dependencies, so each
node is a plain callable that tests can invoke directly with fakes:

```python
def make_enrich_node(deps: TriageDeps) -> Callable[[TriageState], TriageUpdate]:
    """Build the node that adds threat-intel and user context to an incident."""

    def enrich(state: TriageState) -> TriageUpdate:
        ip_rep = deps.intel.ip_reputation(state["incident"].entities.ip)
        user = deps.identity.lookup_user(state["incident"].entities.user)
        return {"enrichment": Enrichment(ip_reputation=ip_rep, user=user)}

    return enrich
```

## 4. Naming conventions

| Thing | Convention | Example |
|---|---|---|
| Protocol | `<Concern>Provider` / `<Thing>Repository` | `ThreatIntelProvider`, `IncidentRepository` |
| Implementation | `<Backend><Concern>` | `MockThreatIntel`, `PostgresIncidentRepository` |
| Fake for tests | `Fake<Concern>` | `FakeLLM`, `FakeClock` |
| Node factory | `make_<verb>_node` | `make_enrich_node` |
| Graph builder | `build_<workflow>_graph` | `build_triage_graph` |
| Pure rule | verb phrase | `score_severity`, `fingerprint_alert` |
| Test | `test_<unit>_<behaviour>_<condition>` | `test_score_severity_is_critical_when_key_leaked` |

## 5. Size budget

| Unit | Limit |
|---|---|
| File | 50–100 lines (hard cap 120 physical lines, checked in CI) |
| Function | ≤ 20 lines, ≤ 4 parameters (group more into a dataclass) |
| Class | One public responsibility; split if it needs a second docstring paragraph to explain |
| Nesting | ≤ 2 levels of indentation inside a function body; use early returns |
