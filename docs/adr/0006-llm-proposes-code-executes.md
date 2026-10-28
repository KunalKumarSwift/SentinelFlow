# ADR 0006 — LLM proposes, deterministic code executes

**Status:** Accepted

## Context
Alert content is attacker-controlled. If the LLM can call privileged tools, prompt injection
becomes privilege escalation.

## Decision
The LLM never receives credentials and never calls side-effecting tools. It returns
schema-validated *suggestions* (verdict, techniques, action kinds from an allow-list).
Deterministic code turns suggestions into `ProposedAction`s, the tool guard authorises them,
humans approve them by policy, and only the orchestrator executes them.

## Consequences
- ✅ Worst case of a successful injection is a wrong *suggestion*, caught by policy and approval.
- ✅ Every privileged effect is explainable and audited.
- ⚠️ Less "autonomous" than free-form agent tool use — an intentional trade-off for safety.
