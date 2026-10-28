# LLD 03 — Security

Principles: **default deny**, **least privilege**, **defence in depth**, **LLM proposes,
code disposes**, **everything audited**.

## 1. Authentication

| Phase | Mechanism |
|---|---|
| 1–3 | HS256 JWT signed with a dev secret. `POST /v1/auth/dev-token` exists **only** when `APP_ENV=dev` |
| 4 | RS256 JWT from Keycloak (OIDC). Public keys fetched from JWKS and cached; `iss` and `aud` validated |

Required claims: `sub`, `tenant_id`, `team`, `roles` (list of strings), `kind` (`user` /
`service`), `iss` (= `sentinelflow`), `iat`, `exp`. `security/tokens.py` exposes:

```python
class Hs256TokenService:
    def __init__(self, secret: str, clock: Clock, ttl: timedelta = MAX_LIFETIME) -> None: ...
    def issue(self, principal: Principal) -> str: ...
    def verify(self, token: str) -> Principal:  # raises AuthenticationError
        ...
```

Verification rules:

- Only `HS256` is accepted, so `alg: none` and algorithm-confusion tokens fail.
- Signature and issuer are checked by PyJWT; every PyJWT call lives in `security/_jwt.py`.
- `exp - iat` must be ≤ 15 minutes, so long-lived tokens are rejected even if correctly signed.
- Expiry is compared with the injected `Clock`, not the wall clock, so tests are deterministic.
- Secrets shorter than 32 characters are refused at construction.
- Claims are type-checked (`roles` must be a list of strings; unknown `kind` is rejected).

## 2. Permissions

Permissions are strings `resource:verb[:qualifier]`, defined once as the `Permission` StrEnum in
`security/permissions.py` (a typo is a type error, not a silent deny).

| Permission | Meaning |
|---|---|
| `alert:ingest` | Submit alerts |
| `incident:read` | Read incidents of own team |
| `incident:read_all` | Read incidents of every team in the tenant |
| `incident:read_pii` | See unredacted user identifiers |
| `incident:close` | Close or escalate an incident |
| `workflow:run:<name>` | Start a given workflow |
| `action:propose` | Propose containment actions |
| `action:approve:low` / `:medium` / `:high` | Approve by impact level |
| `action:execute` | Execute an approved action (orchestrator only) |
| `intel:lookup`, `identity:read`, `events:read` | Read-only provider access |
| `audit:read`, `audit:verify` | Audit log access |
| `workflow:publish`, `integration:manage` | Platform configuration |
| `tenant:admin` | Manage users and role bindings |

## 3. RBAC matrix (`security/roles.py`)

| Permission ↓ / Role → | alert-source | l1 | l2 | commander | sec-eng | auditor | exec | orchestrator | admin |
|---|---|---|---|---|---|---|---|---|---|
| alert:ingest | ✅ | | | | | | | | |
| incident:read | | ✅ | ✅ | ✅ | ✅ | | ✅ | ✅ | |
| incident:read_all | | | | ✅ | | | ✅ | ✅ | |
| incident:read_pii | | | ✅ | ✅ | | | | ✅ | |
| incident:close | | | ✅ | ✅ | | | | | |
| workflow:run:triage | | ✅ | ✅ | ✅ | | | | ✅ | |
| workflow:run:investigation | | | ✅ | ✅ | | | | ✅ | |
| workflow:run:containment | | ✅ | ✅ | ✅ | | | | ✅ | |
| action:propose | | ✅ | ✅ | ✅ | | | | ✅ | |
| action:approve:low/medium | | | ✅ | ✅ | | | | | |
| action:approve:high | | | | ✅ | | | | | |
| action:execute | | | | | | | | ✅ | |
| intel:lookup, identity:read, events:read | | | | | | | | ✅ | |
| audit:read / verify | | | | | | ✅ | | | ✅ |
| workflow:publish, integration:manage | | | | | ✅ | | | | |
| tenant:admin | | | | | | | | | ✅ |

The table is data (`ROLE_PERMISSIONS: Mapping[str, frozenset[Permission]]` in
`security/roles.py`). The tests keep an **independent** copy of this matrix
(`tests/unit/security/rbac_spec.py`) and check every role × permission pair against the code.
If both came from one table, a wrong grant could never fail a test.

Note: no human role holds `action:execute`. Humans approve; only the orchestrator
executes — and only approved actions.

## 4. ABAC rules (`security/abac_rules.py`)

Each rule is a small pure function `(Request) -> Decision | None` (`None` = not applicable).

| Rule | Denies when |
|---|---|
| `same_tenant` | `principal.tenant_id != resource.tenant_id` (always evaluated first) |
| `team_scope` | Incident team ≠ principal team and principal lacks `incident:read_all` |
| `no_self_action` | Approver is the target user of the action |
| `separation_of_duties` | Approver proposed the action, or initiated the run |
| `distinct_approvers` | Approver already recorded a decision on this approval |
| `approval_still_open` | Approval is not `PENDING` or has expired (default TTL 4 h) |
| `executed_only_if_approved` | `action:execute` requested and the approval quorum is not met |

## 5. Policy engine

```python
@dataclass(frozen=True, slots=True)
class AccessRequest:
    principal: Principal
    permission: str
    resource: Resource          # kind, id, tenant_id, team, attributes
    context: Mapping[str, str]  # e.g. run_id, initiator, proposer

@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    reason: str                 # always populated — shown to users and audited

class PolicyEngine(Protocol):
    def evaluate(self, request: AccessRequest) -> Decision: ...
```

Algorithm of `InCodePolicyEngine` (deny overrides):

1. Run `same_tenant` → deny immediately if it fails.
2. RBAC: does any of the principal's roles grant `permission`? If not → deny `"missing permission X"`.
3. Run every applicable ABAC rule; the **first** deny wins.
4. Otherwise allow `"granted by role R"`.

Every decision (allow **and** deny) is audited by the caller. Phase 4 adds
`OpaPolicyEngine` implementing the same protocol by calling an OPA sidecar with the
same `AccessRequest` JSON; the same test-suite runs against both.

## 6. Tool guard (`security/tool_guard.py`)

The single choke point for side-effecting provider calls inside workflows.

```python
class ToolGuard:
    def run(self, call: ToolCall, ctx: RunContext) -> ToolOutcome:
        """Authorise, execute and audit one tool call on behalf of the run's initiator."""
```

Steps:

1. **Scope check** — `call.permission ∈ workflow.max_scope`, else deny.
2. **Initiator check** — policy engine with the *initiator* principal (except `action:execute`,
   which is checked against the orchestrator + approval quorum).
3. **Orchestrator check** — policy engine with the *orchestrator* service principal.
4. **Execute** — call the provider with idempotency key `run_id:call.id`.
5. **Audit** — write `tool.allowed` / `tool.denied` / `tool.failed` with the reason.

Effective permission = initiator ∩ workflow scope ∩ orchestrator. This blocks the
*confused deputy*: a workflow can never do more than the person who started it.

## 7. Audit chain (`security/audit_chain.py`)

```
hash_n = SHA256( hash_{n-1} || canonical_json(event_n without hash) )
hash_0 = SHA256("sentinelflow-genesis:" + tenant_id)
```

- One chain per tenant; `seq` is a gap-free counter per tenant.
- Canonical JSON = sorted keys, UTF-8, no whitespace, ISO-8601 UTC timestamps.
- `verify_chain(events) -> VerifyResult(ok, first_bad_seq)` is pure and property-tested.
- Storage is append-only: the DB role used by the app has `INSERT, SELECT` only on `audit_events`.
- Audited verbs: `alert.ingested`, `run.started|interrupted|resumed|completed|failed`,
  `policy.allowed|denied`, `tool.*`, `approval.requested|decided`, `injection.suspected`,
  `auth.failed`.

## 8. Data protection

- `security/redaction.py`: `redact_incident(incident, principal) -> Incident` replaces user
  identifiers with a stable pseudonym (`user-7f3a…`, HMAC of the value) unless the principal
  has `incident:read_pii`.
- LLM prompts always use the redacted view; the mapping back to real IDs stays in code.
- Secrets live in environment variables loaded by `core/config.py`; never logged (pydantic `SecretStr`).

## 9. Prompt-injection defence (`security/injection.py`)

Untrusted data = any alert/event field. Controls:

1. **Delimit and label** untrusted data in prompts: `<untrusted_alert_data>…</untrusted_alert_data>`
   plus a system instruction that it is data, not instructions.
2. **Detect** with simple, testable heuristics (phrases like "ignore previous", "you are now",
   role tags, base64 blobs with instructions) → `injection_suspected = True`, audited.
3. **Constrain output** — structured output only; enums for verdict/action kinds.
4. **Fail safe** — suspicion or invalid output → `NEEDS_REVIEW`, never auto-close, never auto-act.
5. **No authority** — even a perfect injection can only change a *suggestion*; execution
   still requires policy + human approval.

## 10. Threat model (STRIDE summary)

| Threat | Example | Mitigation |
|---|---|---|
| Spoofing | Forged JWT | Signature + `exp` + `iss`/`aud` checks; short TTL |
| Tampering | Edit audit rows to hide an approval | Hash chain + INSERT-only DB grant + verify endpoint |
| Repudiation | "I never approved that" | Approver identity, time and reason in audit chain |
| Information disclosure | Analyst reads another team's incident | Tenant + team ABAC; RLS in Phase 4; PII redaction |
| Denial of service | Alert flood | Rate limits, dedup, queue back-pressure, LLM budget |
| Elevation of privilege | Prompt injection asks agent to disable the CEO | Allow-listed actions, tool guard, human approval, SoD |
| Elevation of privilege | L1 uses workflow to act as orchestrator | Effective-permission intersection in tool guard |
