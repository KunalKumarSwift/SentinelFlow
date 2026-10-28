# ADR 0007 — Checkpointed lifecycle state holds identifiers only

**Status:** Accepted

## Context
The lifecycle pauses for human approval using LangGraph `interrupt()` and a checkpointer.
A Phase 2 spike showed that putting domain objects in checkpointed state is fragile:
`MappingProxyType` fields are not msgpack-serialisable, tuples come back as lists, and
LangGraph warns that deserialising unregistered classes will be blocked in a future version.

## Decision
The lifecycle graph's state is `run_id`, `tenant_id`, `incident_id`, `alert_id` and
`approval_ids` — nothing else. Each step loads domain objects from repositories and saves
its result back. Triage and investigation sub-graphs compile with `checkpointer=False`
because they are pure, run inside one lifecycle step, and the parent checkpoints after it.

## Consequences
- ✅ Checkpoints are tiny, JSON-safe and portable to the Postgres checkpointer.
- ✅ Repositories stay the single source of truth; a resume re-reads current approvals, so a
  forged or stale resume payload cannot approve anything.
- ✅ No custom serialisers or allow-lists for domain classes.
- ⚠️ Steps do a few extra repository reads (cheap compared with LLM calls).
