# ADR 0003 — In-code policy engine first, OPA later

**Status:** Accepted

## Context
Authorisation is the core of the project's story. OPA/Rego is the industry standard but adds
a new language and a sidecar, which slows early TDD.

## Decision
Define a `PolicyEngine` protocol. Implement `InCodePolicyEngine` (RBAC table + small ABAC rule
functions, deny-overrides) in Phase 1–2. Add `OpaPolicyEngine` in Phase 4 behind the same
protocol and run the **same** policy test-suite against both.

## Consequences
- ✅ Fast, readable, unit-testable policy from day one.
- ✅ Shows policy-as-code migration path (good interview talking point).
- ⚠️ Two implementations must stay equivalent — enforced by the shared test-suite.
