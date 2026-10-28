# 03 — Low-Level Design

The LLD is split into small documents, one concern each (the same rule we apply to code).

| Doc | Covers |
|---|---|
| [00 Code structure](00-code-structure.md) | Package layout, layering rules, dependency injection, naming |
| [01 Domain model](01-domain-model.md) | Value objects, enums, pure business rules |
| [02 Workflows](02-workflows.md) | LangGraph state, nodes, edges, interrupts for every graph |
| [03 Security](03-security.md) | AuthN, permissions, RBAC matrix, ABAC rules, policy engine, tool guard, audit chain, threat model |
| [04 Integrations](04-integrations.md) | Provider protocols, mock and real providers, facades, configuration |
| [05 API](05-api.md) | REST endpoints, schemas, errors, pagination |
| [06 Data model](06-data-model.md) | PostgreSQL tables, indexes, row-level security, Redis keys |
| [07 Execution runtime](07-execution-runtime.md) | Queue commands, worker loop, idempotency, retries, budgets |
| [08 Simulator](08-simulator.md) | Synthetic scenario generator |

Code snippets in these docs are **illustrative signatures**, not final code. Final code is
written test-first and may differ in details; when it does, update the doc in the same PR.
