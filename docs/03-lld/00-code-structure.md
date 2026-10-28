# LLD 00 — Code Structure

## 1. Repository layout

```
WorkflowOrchestration/
├── pyproject.toml            # one installable package: sentinelflow
├── .importlinter             # enforces the layer rules below
├── docker-compose.yml        # Phase 2+
├── docs/
├── src/sentinelflow/
│   ├── core/                 # generic utilities, zero domain knowledge
│   │   ├── config.py         # the ONLY module that reads environment variables
│   │   ├── logging.py
│   │   ├── clock.py          # Clock protocol + SystemClock (time is injected)
│   │   └── ids.py            # id generation (injectable)
│   ├── domain/               # frozen dataclasses + pure rules, no I/O
│   │   ├── alerts.py  incidents.py  severity.py  actions.py
│   │   ├── approvals.py  principals.py  audit.py  errors.py
│   ├── contracts/            # typing.Protocol interfaces only
│   │   ├── llm.py  threat_intel.py  identity.py  event_store.py
│   │   ├── ticketing.py  notifier.py  repositories.py  run_queue.py
│   │   └── audit_store.py  policy.py
│   ├── security/             # authN/authZ building blocks
│   │   ├── tokens.py  permissions.py  roles.py  rbac.py  abac_rules.py
│   │   ├── policy_engine.py  tool_guard.py  redaction.py
│   │   └── injection.py  audit_chain.py
│   ├── providers/            # one concrete implementation per file
│   │   ├── llm/        fake_llm.py  ollama_llm.py  anthropic_llm.py
│   │   ├── intel/      mock_intel.py
│   │   ├── identity/   mock_identity.py
│   │   ├── events/     memory_event_store.py
│   │   ├── storage/    memory_*.py  postgres_*.py
│   │   └── queue/      memory_queue.py  redis_queue.py
│   ├── facades/              # config value → provider instance (switch only)
│   ├── workflows/
│   │   ├── registry.py
│   │   ├── ingestion/  triage/  investigation/  containment/  report/  access_review/
│   │   └── orchestrator/
│   ├── runtime/              # worker loop, command handling
│   ├── api/                  # FastAPI routes, schemas, dependencies
│   ├── simulator/            # synthetic scenario generators, demo seed, CLI (sentinelflow-sim)
│   └── bootstrap/            # composition root: wiring.py builds everything; serve.py runs it
└── tests/                    # mirrors src/ one-to-one
    ├── fakes/                # one Fake per protocol, shared by all tests
    ├── unit/  integration/  api/  e2e/
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
