# LLD 04 — Integrations (Providers)

Every external system sits behind a `typing.Protocol` in `contracts/`. Implementations
live in `providers/`, one class per file. A **facade** picks the implementation from
config. Tests use **fakes** from `tests/fakes/`.

```
contracts/threat_intel.py   → ThreatIntelProvider (Protocol)
providers/intel/mock_intel.py   → MockThreatIntel        (Phase 1, reads seeded data)
providers/intel/abuseipdb_intel.py → AbuseIpdbThreatIntel  (Phase 4, free tier)
facades/intel_facade.py     → make_threat_intel(config) -> ThreatIntelProvider
tests/fakes/fake_intel.py   → FakeThreatIntel (in-memory dict, records calls)
```

## 1. Protocols

Methods are added when the first slice needs them (Phase 1 has `ip_reputation` and
`lookup_user`); each addition extends the shared contract tests in `tests/contracts/`.

```python
class LLMProvider(Protocol):
    def structured(self, prompt: Prompt, schema: type[T]) -> T: ...
    def text(self, prompt: Prompt) -> str: ...

class ThreatIntelProvider(Protocol):
    def ip_reputation(self, ip: str) -> IpReputation | None: ...
    def url_reputation(self, url: str) -> UrlReputation | None: ...

class IdentityProvider(Protocol):
    def lookup_user(self, user_id: str) -> UserContext | None: ...
    def list_accounts(self, tenant_id: str) -> Sequence[Account]: ...
    def apply(self, action: ProposedAction, idempotency_key: str) -> ActionResult: ...

class EventStore(Protocol):
    def related_events(self, query: EventQuery) -> Sequence[SecurityEvent]: ...

class TicketingProvider(Protocol):
    def upsert_ticket(self, incident_id: str, body: str) -> str: ...

class Notifier(Protocol):
    def notify(self, channel: str, message: str) -> None: ...

class RunQueue(Protocol):
    def publish(self, command: RunCommand) -> None: ...
    def claim(self, consumer: str, max_items: int) -> Sequence[Delivery]: ...
    def ack(self, delivery: Delivery) -> None: ...
    def dead_letter(self, delivery: Delivery, reason: str) -> None: ...

class AuditStore(Protocol):
    def append(self, event: AuditEventDraft) -> AuditEvent: ...
    def read(self, tenant_id: str, after_seq: int, limit: int) -> Sequence[AuditEvent]: ...

class Clock(Protocol):
    def now(self) -> datetime: ...
```

Repositories (`IncidentRepository`, `AlertRepository`, `ApprovalRepository`,
`RunRepository`) follow the same pattern with `get`, `add`, `update`, `list_for(principal_scope)`.

All provider methods are synchronous in Phase 1 for simplicity; Phase 3 introduces
`async` variants where I/O dominates (HTTP intel lookups, Redis, Postgres).

## 2. LLM providers

| Provider | Package | When |
|---|---|---|
| `FakeLLM` | none | All unit/graph tests. Returns scripted responses keyed by prompt name; records prompts for assertions |
| `OllamaLLM` | `langchain-ollama` (`ChatOllama`) | Default for local dev. Free, offline |
| `AnthropicLLM` | `langchain-anthropic` (`ChatAnthropic`) | Low-cost hosted: `claude-haiku-5-5` |

Both real providers wrap LangChain's `with_structured_output(schema)` and translate
library errors into `ProviderError`. Every call reports token usage to the budget
tracker (LLD 07 §6).

```python
@dataclass(frozen=True, slots=True)
class Prompt:
    name: str                       # "triage.classify" — used for tracing and FakeLLM lookup
    system: str
    untrusted: Mapping[str, str]    # rendered inside <untrusted_*> delimiters
    instructions: str
```

## 3. Mock providers (Phase 1)

Mock providers are **realistic but deterministic**. They read from a `SeedData` object
produced by the simulator, so a scenario's intel, users and events are consistent.

| Mock | Behaviour |
|---|---|
| `MockThreatIntel` | Serves the scenario's `IpReputation`s (known-bad IPs score 85–100); unknown IPs return `None` ("no intel", never a made-up score) |
| `MockIdentity` | In-memory directory served from seed data; unknown users return `None`. `apply()` (Phase 2) flips flags (`disabled`, `mfa_reset`) and is idempotent per key |
| `MemoryEventStore` | Holds the scenario's raw events; filters by entity and time window |
| `MemoryTicketing` | Dict of tickets; returns `TCK-0001` style IDs |
| `ConsoleNotifier` | Logs the message |

## 4. Facades and configuration

Facades contain switch logic only:

```python
def make_llm(settings: Settings) -> LLMProvider:
    """Return the configured LLM provider."""
    match settings.llm_backend:
        case "anthropic":
            return AnthropicLLM(model=settings.llm_model, api_key=settings.anthropic_api_key)
        case "ollama":
            return OllamaLLM(model=settings.llm_model, base_url=settings.ollama_url)
        case _:
            return FakeLLM.from_fixtures(settings.fake_llm_fixtures)
```

`core/config.py` (pydantic-settings, read once at start-up):

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `dev` | `dev` enables the dev-token endpoint |
| `JWT_SECRET` | — (required) | HS256 signing secret (Phases 1–3) |
| `LLM_BACKEND` | `fake` | `fake` / `ollama` / `anthropic` |
| `LLM_MODEL` | `qwen2.5:7b` | Model name for the selected backend |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama endpoint |
| `ANTHROPIC_API_KEY` | — | Only for `anthropic` backend |
| `STORAGE_BACKEND` | `memory` | `memory` / `postgres` |
| `DATABASE_URL` | — | PostgreSQL DSN |
| `QUEUE_BACKEND` | `memory` | `memory` / `redis` |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis DSN |
| `INTEL_BACKEND` | `mock` | `mock` / `abuseipdb` |
| `TENANT_TOKEN_BUDGET_DAILY` | `200000` | LLM tokens per tenant per day |

## 5. Adding a new provider (checklist)

1. Write a contract test for the protocol (if not present) in `tests/contracts/`.
2. Create `providers/<area>/<backend>_<concern>.py` — one class.
3. Make the contract test pass for the new class (parametrised over implementations).
4. Add one `case` to the facade.
5. Add config fields with defaults; document them in this table.
