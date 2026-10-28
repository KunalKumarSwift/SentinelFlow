# LLD 05 — REST API

FastAPI app built by `api/app.py::create_app(container)`. Routers live one per resource in
`api/routes/`. Request/response schemas (Pydantic) live in `api/schemas/` and are mapped
to domain objects at the edge.

## 1. Conventions

- Base path `/v1`. JSON only. UTF-8.
- Auth: `Authorization: Bearer <JWT>` on every route except health and dev-token.
- Each route declares its permission with a dependency:
  `principal: Principal = Depends(require("incident:read"))`.
- Resource-level checks (tenant, team, SoD) happen in the service layer via the policy engine.
- Errors use **RFC 9457 problem details**:
  `{"type": "...", "title": "Forbidden", "status": 403, "detail": "missing permission action:approve:high", "correlation_id": "..."}`
- Lists use cursor pagination: `?limit=50&cursor=<opaque>` → `{"items": [...], "next_cursor": "..."}`.
- Every response carries `X-Correlation-ID` (generated if absent) for log/trace correlation.

## 2. Endpoints

| Method | Path | Permission | Description |
|---|---|---|---|
| POST | `/v1/auth/dev-token` | none (dev only) | Issue a JWT for a seeded user |
| POST | `/v1/alerts` | `alert:ingest` | Ingest one alert; returns incident id and whether deduplicated |
| GET | `/v1/incidents` | `incident:read` | List incidents visible to the caller (filters: status, severity) |
| GET | `/v1/incidents/{id}` | `incident:read` | Incident detail, redacted per role |
| POST | `/v1/incidents/{id}/close` | `incident:close` | Close / escalate with a reason |
| GET | `/v1/workflows` | `incident:read` | Registry listing: name, version, required permission |
| POST | `/v1/workflows/{name}/runs` | `workflow:run:<name>` | Start a workflow for an incident |
| GET | `/v1/runs/{run_id}` | `incident:read` | Run status: `queued/running/waiting/completed/failed` |
| GET | `/v1/approvals` | `action:approve:*` (any) | Pending approvals the caller is eligible for |
| POST | `/v1/approvals/{id}/decision` | `action:approve:<impact>` | Approve / reject with reason |
| GET | `/v1/audit` | `audit:read` | Audit events (filters: incident_id, verb, since) |
| GET | `/v1/audit/verify` | `audit:verify` | Verify the tenant's hash chain |
| GET | `/healthz` | none | Liveness |
| GET | `/readyz` | none | Readiness (DB, queue reachable) |
| GET | `/metrics` | none (internal network) | Prometheus metrics (Phase 3) |

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

| Code | When |
|---|---|
| 200 / 201 / 202 | OK / created / accepted (async run queued) |
| 400 | Schema validation failure |
| 401 | Missing, expired or invalid token |
| 403 | Policy denied (reason in `detail`) |
| 404 | Not found **or** not visible to caller (avoid leaking existence across tenants) |
| 409 | Approval already decided, illegal state transition |
| 429 | Rate limit or LLM budget exceeded |

## 5. Approval decision flow (service layer)

```python
def decide(approval_id: str, body: DecisionIn, principal: Principal) -> Approval:
    approval = approvals.get(approval_id, tenant_id=principal.tenant_id)   # 404 if absent
    action = actions.get(approval.action_id)
    request = AccessRequest(principal, f"action:approve:{action.impact}", resource_of(action), context_of(approval))
    decision = policy.evaluate(request)
    audit.record_policy(decision, request)
    if not decision.allowed:
        raise PolicyDenied(decision.reason)
    updated = record_decision(approval, ApprovalDecision(principal.subject, body.approved, body.reason, clock.now()))
    approvals.update(updated)
    queue.publish(ResumeRun(run_id=approval.run_id, approval_id=approval.id))
    return updated
```

(Shown as one block for readability; the real code splits it into three ≤ 20-line functions.)
