# 01 — Requirements

## 1. Problem statement

Security Operations Centres (SOCs) drown in alerts. Analysts spend most of their time
enriching and de-duplicating alerts rather than responding to real attacks. LLM agents
can help, but an agent that can disable users or revoke keys is itself a high-value
attack target. We need automation that is **fast, explainable, and provably governed**.

## 2. Goals

| ID | Goal |
|---|---|
| G1 | Automate alert ingestion, triage, investigation and reporting with LangGraph workflows |
| G2 | Gate every privileged action behind RBAC/ABAC policy and, where required, human approval |
| G3 | Keep a tamper-evident audit trail of every decision, tool call and approval |
| G4 | Scale horizontally: stateless workers, durable state, queue-based execution |
| G5 | Run end-to-end locally for free (synthetic data, mock providers, local LLM) |
| G6 | Be a readable, well-tested reference codebase (TDD, small files, documented) |

## 3. Non-goals

- Building a real SIEM, EDR, or detection-rule engine. Alerts arrive already "detected".
- Real enforcement against production systems. Containment acts on mock providers.
- A polished front-end in early phases. API + Swagger + CLI first.

## 4. Personas and roles

| Persona | Role key | Typical goal |
|---|---|---|
| Alert source (service) | `alert-source` | Push alerts into the platform |
| Tier-1 analyst | `soc-analyst-l1` | Review triaged incidents, propose containment |
| Tier-2 analyst | `soc-analyst-l2` | Run investigations, approve low/medium-impact actions |
| Incident commander | `incident-commander` | Approve high-impact actions, own critical incidents |
| Security engineer | `security-engineer` | Publish workflows, manage integrations |
| Auditor | `auditor` | Read and verify the audit log (no PII) |
| Executive | `executive` | Read reports and dashboards |
| Orchestrator (service) | `orchestrator` | Worker identity; executes *approved* actions only |
| Platform admin | `platform-admin` | Manage tenants, users and role assignments |

## 5. Use cases

| ID | Use case | Primary actor |
|---|---|---|
| UC1 | Ingest an alert and attach it to a new or existing incident | alert-source |
| UC2 | Triage an incident: enrich, score severity, decide true/false positive | system (on behalf of the incident's team) |
| UC3 | Investigate an incident: build a timeline, map to MITRE ATT&CK | soc-analyst-l2 |
| UC4 | Propose containment actions from an allow-listed action catalogue | soc-analyst-l1+ / system |
| UC5 | Approve or reject a proposed action | soc-analyst-l2 / incident-commander |
| UC6 | Execute approved actions and record the outcome | orchestrator |
| UC7 | Generate a post-incident report | system / soc-analyst-l2 |
| UC8 | Run a scheduled access review and raise findings | system (cron) |
| UC9 | Query and verify the audit log | auditor |
| UC10 | Generate synthetic attack scenarios for demos and tests | developer |

## 6. Demo scenarios (synthetic)

| Scenario | Signals | Expected outcome |
|---|---|---|
| Brute force → success | N failed logins then a success from one IP | High severity; propose `disable_user` + `block_ip` |
| Impossible travel | Two logins, distant geos, minutes apart | Medium; propose `force_mfa_reset` |
| Leaked access key | Unusual API calls from unknown IP using a key | Critical; propose `revoke_access_key` (two approvals) |
| Phishing click | Malicious URL in email + proxy hit | Medium; propose `purge_email` + `reset_password` |
| Suspicious PowerShell | Encoded command + outbound connection | High; propose `isolate_host` |
| Data exfiltration | Large off-hours download | High; escalate only, no automatic action |
| Prompt injection | Alert text tries to instruct the agent | Flagged; verdict unaffected; audit entry |
| Benign noise | Normal activity resembling an attack | Closed as false positive |

## 7. Functional requirements

| ID | Requirement |
|---|---|
| FR1 | Accept alerts via REST and from a pluggable alert source |
| FR2 | Deduplicate alerts by fingerprint within a time window; group into incidents |
| FR3 | Enrich incidents with threat intel, user and asset context via providers |
| FR4 | Score severity with deterministic rules; use the LLM only for classification and narrative |
| FR5 | LLM output must be schema-validated; actions must come from the allow-listed catalogue |
| FR6 | Containment pauses for approval according to the action's impact level |
| FR7 | Approvals enforce separation of duties and no self-approval |
| FR8 | Every workflow step, policy decision, approval and action is audited |
| FR9 | Audit log is append-only and hash-chained; a verify endpoint detects tampering |
| FR10 | Users only see incidents of their tenant (and team, unless elevated) |
| FR11 | PII fields are redacted for roles without `incident:read_pii` |
| FR12 | Workflows are registered in a registry with version and required permissions |
| FR13 | A simulator produces deterministic (seeded) scenarios |

## 8. Non-functional requirements

| ID | Category | Requirement |
|---|---|---|
| NFR1 | Security | Default deny; least privilege; tokens are short-lived |
| NFR2 | Security | LLM never holds credentials and never executes actions directly |
| NFR3 | Reliability | A worker crash mid-run must not lose or duplicate an action (checkpoint + idempotency) |
| NFR4 | Scalability | Throughput scales linearly with worker count; API is stateless |
| NFR5 | Performance | Triage p95 < 10 s with a hosted LLM; ingestion p95 < 200 ms |
| NFR6 | Cost | Per-tenant LLM token budget; deterministic logic preferred over LLM calls |
| NFR7 | Observability | Structured logs with correlation IDs; traces per run (Phase 3) |
| NFR8 | Maintainability | Files 50–100 lines; functions ≤ 20 lines; ≥ 90 % coverage on domain + features |
| NFR9 | Portability | Runs fully offline with Ollama and mock providers |
| NFR10 | Testability | All external dependencies injectable; unit tests never touch the network |
