# LLD 05 — REST API

FastAPI app built by `api/app.py::create_app(container)`. Routers live one per resource in
`api/routes/`. Request/response schemas (Pydantic) live in `api/schemas/` and are mapped
to domain objects at the edge.

## 1. Conventions

- Base path `/v1`. JSON only. UTF-8.
- Auth: `Authorization: Bearer <JWT>` on every route except health and dev-token
  (`api/auth.py::Auth`; Swagger's *Authorize* button works via the HTTP bearer scheme).
- Each route declares its permission with a dependency:
  `principal: Annotated[Principal, Depends(auth.require(Permission.INCIDENT_READ))]`.
- Resource-level checks (tenant, team, SoD) happen in the service layer via the policy engine.
- Errors use **RFC 9457 problem details**:
  `{"type": "...", "title": "Forbidden", "status": 403, "detail": "missing permission action:approve:high", "correlation_id": "..."}`
- Lists use cursor pagination: `?limit=50&cursor=<opaque>` → `{"items": [...], "next_cursor": "..."}`.
- Every response carries `X-Correlation-ID` (a valid incoming one, `[A-Za-z0-9_-]{1,64}`, is reused; otherwise generated) for log/trace correlation ✅.

## 2. Endpoints

| Method | Path | Permission | Description |
|---|---|---|---|
| POST | `/v1/auth/dev-token` | none (mounted only when `APP_ENV=dev`; otherwise 404) | Issue a JWT for any identity — local demos only |
| POST | `/v1/alerts` | `alert:ingest` | 202. Ingest one alert (tenant from token; extra body fields → 422); a new incident gets a triage run queued (`run_id`) ✅ |
| GET | `/v1/incidents` | `incident:read` | Tenant's incidents, oldest first ✅ (filters, cursor pagination and team scope: Phase 2) |
| GET | `/v1/incidents/{id}` | `incident:read` | Incident detail; other tenants' incidents are 404; `user`/`email_id` pseudonymised without `incident:read_pii` ✅ |
| GET | `/v1/incidents/{id}/report` | `incident:read` | Post-incident report (ticket); user identifiers pseudonymised ✅ |
| POST | `/v1/incidents/{id}/close` | `incident:close` | Close / escalate with a reason |
| GET | `/v1/workflows` | `incident:read` | Registry listing: name, version, required permission ✅ |
| POST | `/v1/workflows/{name}/runs` | `workflow:run:<name>` | 202. Queue a run; unknown workflow/incident → 404, incident not `NEW` → 409 ✅ |
| GET | `/v1/runs/{run_id}` | `incident:read` | Run status `queued/running/waiting/completed/failed` and initiator ✅ |
| GET | `/v1/approvals` | `action:approve:*` (any) | Pending approvals the policy engine says the caller may decide (role by impact, team, no self-action, SoD) ✅ |
| POST | `/v1/approvals/{id}/decision` | `action:approve:<impact>` | Approve / reject with reason; denials audited; a closed approval queues `ResumeRun` ✅ |
| GET | `/v1/audit` | `audit:read` | Tenant's audit events, paged by `after_seq` + `limit` (≤ 500) ✅ |
| GET | `/v1/audit/verify` | `audit:verify` | Re-hash the tenant's whole chain → `{ok, first_bad_seq, checked}` ✅ |
| GET | `/healthz` | none | Liveness |
| GET | `/readyz` | none | Readiness (DB, queue reachable) |
| GET | `/metrics` | none (restrict at the network edge) | Prometheus metrics of this API process ✅ |

## 3. Key schemas

```python
class AlertIn(BaseModel):
    source: str = Field(max_length=64)
    rule_id: str = Field(pattern=r"^[a-z0-9_]{3,64}$")
    title: str = Field(max_length=200)
    observed_at: datetime
    entities: EntitiesIn
    raw: dict[str, str] = Field(default_factory=dict, max_length=50)   # untrusted

class AlertAccepted(BaseModel):
    alert_id: str
    incident_id: str
    deduplicated: bool
    run_id: str | None            # set when a new lifecycle run was queued

class StartRunIn(BaseModel):
    incident_id: str

class DecisionIn(BaseModel):
    approved: bool
    reason: str = Field(min_length=5, max_length=500)

class IncidentOut(BaseModel):
    id: str
    status: IncidentStatus
    severity: Severity
    verdict: Verdict | None
    team: str
    entities: EntitiesOut         # redacted unless incident:read_pii
    pending_approvals: int
```

`tenant_id` is **never** accepted from the request body — it always comes from the token.

## 4. Status codes

`api/problems.py` is the only place that maps errors to HTTP; business code raises typed
`SentinelFlowError` subclasses. The first matching class wins:

| Code | Raised as | When |
|---|---|---|
| 200 / 201 / 202 | — | OK / created / accepted (async run queued) |
| 401 (+ `WWW-Authenticate: Bearer`) | `AuthenticationError` | Missing, expired or invalid token |
| 403 | `AuthorizationError` / `PolicyDeniedError` | Policy denied (reason in `detail`) |
| 404 | `NotFoundError` | Not found **or** not visible to caller (avoid leaking existence across tenants) |
| 409 | `InvalidTransitionError` (later `ConflictError`) | Illegal state transition, approval already decided |
| 422 | Pydantic validation, `DomainError` | Malformed body; invalid value; unknown rule |
| 429 (+ `Retry-After`) | `RateLimitedError` | Tenant exceeded its per-second limit for the route group ✅ |
| 503 | `ProviderError` | An external provider failed |
| 500 | anything else | Generic `detail: "unexpected error"`; internal messages are never leaked |

## 5. Approval decision flow (`api/approval_service.py`)

1. Load the approval for the caller's tenant (404 otherwise) and expire it if overdue.
2. `api/approval_policy.decision_for` builds an `AccessRequest` with permission
   `action:approve:<impact>`, the incident as resource (team scope) and an `ActionContext`
   (target user, proposer, run initiator, prior approvers, still open) and asks the policy
   engine. Deny → `policy.denied` audit + 403 with the reason.
3. `record_decision` (any rejection rejects; quorum approves) → save → `approval.decided` audit.
4. If the approval left `PENDING`, publish `ResumeRun(run_id)`; the worker re-reads every
   approval of the run, so the resume message carries no authority of its own.

Deciding twice or deciding a closed approval is denied by the ABAC rules (403 with reason).
