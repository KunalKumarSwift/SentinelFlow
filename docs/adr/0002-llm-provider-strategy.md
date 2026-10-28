# ADR 0002 — Pluggable LLM: FakeLLM → Ollama → Claude Haiku

**Status:** Accepted

## Context
The project must be free or very cheap to run, fully testable offline, and still able to
show results from a capable hosted model.

## Decision
All LLM access goes through an `LLMProvider` protocol with three implementations:

| Backend | Cost | Use |
|---|---|---|
| `FakeLLM` | Free | All automated tests; deterministic |
| Ollama (`qwen2.5:7b` / `llama3.1:8b`) | Free (local CPU/GPU) | Default local development |
| Claude Haiku 5.5 (`claude-haiku-5-5`) | $0.10 / $0.50 per 1M input/output tokens | Hosted demos, quality evals |

The LLM is used only where judgement or language is needed (classification, narrative,
report). Deterministic logic (scoring, dedup, policy) never calls the LLM.

## Consequences
- ✅ CI costs nothing; tests are fast and deterministic.
- ✅ Switching models is a config change (`LLM_BACKEND`, `LLM_MODEL`).
- ✅ A full demo run (a few thousand tokens per incident) costs fractions of a cent on Haiku.
- ⚠️ Small local models are weaker at structured output → strict validation + fail-safe
  `NEEDS_REVIEW` path is mandatory, not optional.
- ⚠️ Provider pricing changes; re-check before publishing numbers.
