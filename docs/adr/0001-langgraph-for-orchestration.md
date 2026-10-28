# ADR 0001 — LangGraph for workflow orchestration

**Status:** Accepted

## Context
Incident workflows are multi-step, branch on results, call several systems, must pause
for human approval for hours, and must survive worker crashes.

## Decision
Use **LangGraph** `StateGraph`s, one per workflow, composed by an orchestrator graph, with a
PostgreSQL checkpointer (`thread_id = run_id`).

## Consequences
- ✅ Built-in `interrupt()` / `Command(resume=…)` gives human-in-the-loop with durable state.
- ✅ Checkpoints after every super-step → stateless workers, crash recovery.
- ✅ `Send` enables parallel enrichment fan-out; sub-graphs give modularity.
- ⚠️ State must be serialisable by the checkpointer — validate frozen dataclasses in a Phase 1 spike.
- ⚠️ Not a general job scheduler: queueing, retries across processes and DLQ are ours (LLD 07).
- Alternatives considered: Temporal (heavier ops, less LLM-native), plain Celery chains
  (no durable interrupts), CrewAI (less control over flow and state).
