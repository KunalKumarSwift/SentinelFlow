# Architecture Decision Records

Short records of significant decisions: context, decision, consequences.
New ADRs copy the format below and take the next number. ADRs are never edited after
acceptance; a new ADR supersedes an old one.

| # | Decision | Status |
|---|---|---|
| [0001](0001-langgraph-for-orchestration.md) | LangGraph for workflow orchestration | Accepted |
| [0002](0002-llm-provider-strategy.md) | Pluggable LLM: FakeLLM → Ollama → Claude Haiku | Accepted |
| [0003](0003-policy-engine.md) | In-code policy engine first, OPA later, same protocol | Accepted |
| [0004](0004-synthetic-data-first.md) | Synthetic simulator instead of real security tools | Accepted |
| [0005](0005-single-package-layered.md) | One Python package with enforced layers | Accepted |
| [0006](0006-llm-proposes-code-executes.md) | LLM proposes, deterministic code executes | Accepted |
| [0007](0007-id-only-checkpoint-state.md) | Checkpointed lifecycle state holds identifiers only | Accepted |
