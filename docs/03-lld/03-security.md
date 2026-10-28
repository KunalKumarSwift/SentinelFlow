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

**OIDC / Keycloak (built, slice 4.1).** `AUTH_MODE=oidc` swaps the API's verifier for
`security/oidc/verifier.OidcTokenVerifier` (both satisfy `security/verifier.TokenVerifier`):

- **RS256 only.** The key is chosen by the token's `kid` from the realm JWKS
  (`security/oidc/jwks.CachedJwks`, downloaded by `providers/identity/jwks_http.py`). HS256
  dev tokens, `alg: none` and tokens signed by unpublished keys are all rejected with 401.
- **Key rotation:** an unknown `kid` triggers a JWKS refresh, but at most once per 30 s, so
  forged key ids cannot flood the IdP. Keys also refresh hourly. An unreachable IdP is a
  `ProviderError` (503), never an accepted token.
- `iss` must equal `OIDC_ISSUER`, `aud` must contain `OIDC_AUDIENCE` (`sentinelflow-api`),
  `exp - iat` ≤ 1 h, and expiry is checked with the injected clock.
- **Claim mapping** (`security/oidc/claims.py`): `sub`; `tenant_id` and `team` from
  user-attribute mappers; roles from `realm_access.roles`, **kept only if they are SentinelFlow
  roles and never `orchestrator`** (the system principal's role cannot be granted by an IdP
  administrator; deny test included). A `client_id` claim (client-credentials token) makes
  the principal a `service`.
- `deploy/keycloak/realm-sentinelflow.json` provides the realm: roles, the bearer-only
  `sentinelflow-api` client, a public `sentinelflow-cli` client (password grant, demo only)
  with audience and attribute mappers, a `siem-connector` service account (`alert-source`)
  and demo users. `docker compose --profile oidc up` imports it. *The realm file is checked
  for valid JSON only; it has not been imported into a live Keycloak in this environment.*

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
class AccessRequest:                     # security/policy.py
    principal: Principal
    permission: Permission
    resource: Resource                   # kind, id, tenant_id, team
    action: ActionContext | None = None  # target_user, proposer, initiator,
                                         # prior_approvers, approval_open, quorum_met

@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    reason: str                          # always populated — shown to users and audited

class PolicyEngine(Protocol):
    def evaluate(self, request: AccessRequest) -> Decision: ...
```

`ActionContext` is a typed dataclass rather than a string map, so a missing or misspelt
fact is a type error. Approval rules **fail closed**: an `action:approve:*` request without
an `ActionContext` is denied.

Algorithm of `InCodePolicyEngine` (deny overrides):

1. Run `same_tenant` → deny immediately if it fails.
2. RBAC: does any of the principal's roles grant `permission`? If not → deny `"missing permission X"`.
3. Run every applicable ABAC rule; the **first** deny wins.
4. Otherwise allow `"granted by role R"`.

Every decision (allow **and** deny) is audited by the caller.

**OPA engine (built, slice 4.2).** `POLICY_ENGINE=opa` swaps in `security/opa_engine.OpaPolicyEngine`,
which posts the request (`security/opa_input.to_input`: sets become sorted lists, no action →
`null`) to `/v1/data/sentinelflow/authz/decision` and reads `{allowed, reason}`. It **fails
closed**: an unreachable server, an error status, no loaded policy or a malformed answer all
deny with `policy engine unavailable`. The policy, `deploy/opa/sentinelflow/authz.rego`,
reproduces the order and the exact reason strings above. Its role data, `deploy/opa/data.json`,
is generated from `security/roles.py` by `scripts/gen_opa_data.py`, and a drift test keeps the
two in step. `tests/contracts/test_policy_engine_contract.py` runs **both engines** through
every rule and the full role × permission matrix. In CI, OPA is installed with `setup-opa`,
`opa test deploy/opa` runs the Rego unit tests, and an OPA server provides `TEST_OPA_URL`.

## 6. Tool guard (`security/tool_guard.py`)

The single choke point for **side-effecting** provider calls inside workflows (proposing
and executing actions). Read-only enrichment lookups are not routed through it.

```python
class ToolGuard:
    def run[T](self, call: ToolCall, ctx: RunContext, effect: Callable[[str], T]) -> T:
        """Authorise, then run effect(idempotency_key = f"{run_id}:{call.id}"), auditing all."""
    def authorize(self, call: ToolCall, ctx: RunContext) -> Decision: ...

ToolCall(id, permission, resource, action: ActionContext | None)
RunContext(run_id, initiator: Principal, max_scope: frozenset[Permission])
```

Steps:

1. **Scope check** — `call.permission ∈ ctx.max_scope`, else deny `"… is outside workflow scope"`.
2. **Initiator check** — policy engine with the *initiator*; skipped for `action:execute`
   (no human role holds it — humans approve).
3. **Orchestrator check** — policy engine with `orchestrator_for(tenant)`; for
   `action:execute` this applies the `executed_only_if_approved` quorum rule.
4. **Execute** — `effect(idempotency_key)`; providers use the key to ignore repeats.
5. **Audit** — `tool.allowed` / `tool.denied` (with the reason, prefixed `initiator:` or
   `orchestrator:`) / `tool.failed` (on `ProviderError`, which is re-raised).

Effective permission = workflow scope ∩ initiator ∩ orchestrator. This blocks the
*confused deputy*: a workflow can never do more than the person who started it.

## 7. Audit chain (`security/audit_chain.py`)

```
hash_n = SHA256( hash_{n-1} || canonical_json(event_n without hash) )
hash_0 = SHA256("sentinelflow-genesis:" + tenant_id)
```

- One chain per tenant; `seq` is a gap-free counter per tenant.
- Canonical JSON = sorted keys, UTF-8, no whitespace, ISO-8601 UTC timestamps.
- `chain_next(previous, draft) -> AuditEvent` and `verify_chain(tenant_id, events) ->
  VerifyResult(ok, first_bad_seq)` are pure and property-tested (Hypothesis): any edit is
  reported at its own `seq`, a deleted event at the first `seq` after the gap.
- `MemoryAuditStore` serialises appends with a lock so `seq` stays gap-free when API and
  worker threads write concurrently.
- Storage is append-only: the DB role used by the app has `INSERT, SELECT` only on `audit_events`.
- Writes go through `security/audit_recorder.py::AuditRecorder.record(actor, verb, resource,
  details)`; the outcome follows the verb suffix (`*.denied`, `*.failed`, else `ok`).
- Recorded today: `alert.ingested`, `run.queued`, `policy.denied` (every API permission
  denial), `incident.triaged` (by `svc-orchestrator`). Planned verbs: `alert.ingested`, `run.started|interrupted|resumed|completed|failed`,
  `policy.allowed|denied`, `tool.*`, `approval.requested|decided`, `injection.suspected`,
  `auth.failed`.

## 8. Data protection

- `security/redaction.py`: `Redactor.entities_for(principal, entities)` replaces `user` and
  `email_id` with stable pseudonyms (`user-7f3a…`, HMAC-SHA256 of field + value) unless the
  principal has `incident:read_pii`. The key is derived from the deployment secret with
  domain separation (`sentinelflow:pii:`), never the token-signing secret itself.
- LLM prompts always use the redacted view; the mapping back to real IDs stays in code.
- Secrets live in environment variables loaded by `core/config.py`; never logged (pydantic `SecretStr`).

## 9. Prompt-injection defence (`security/injection.py`)

Untrusted data = any alert/event field. Controls:

1. **Delimit and label** untrusted data in prompts: `<untrusted_alert_data>…</untrusted_alert_data>`
   plus a system instruction that it is data, not instructions.
2. **Detect** with named, testable regex heuristics (`override_instructions`,
   `role_reassignment`, `chat_markup`, `delimiter_escape`, `verdict_steering`,
   `prompt_exfiltration`) → `TriageResult.injection_indicators`, recorded on the incident's
   audit trail. Escaped `</untrusted_data>` closers in prompts (LLD 04) back this up.
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
