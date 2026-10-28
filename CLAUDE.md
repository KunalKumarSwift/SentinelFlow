# CLAUDE.md

SentinelFlow: agentic security-incident orchestration with LangGraph. Design docs live in
`docs/` — read `docs/02-hld.md` and the relevant `docs/03-lld/*` file before changing code.

## Non-negotiable rules

- **TDD:** write a failing test first, then the minimum code, then refactor. No code without a test.
- **Small files:** 50–100 lines per file (CI fails > 120). Functions ≤ 20 lines, ≤ 4 parameters.
- **Layers:** `core → domain → contracts → security → workflows|providers → facades → api|runtime|simulator → bootstrap`.
  Import only downward; `workflows` never imports `providers` (inject protocols via `deps.py`).
- **Types:** Python 3.12, full hints, `pyright --strict` clean, no `Any`.
- **Docs:** Google-style docstrings on every module, public class and function. Comments explain why.
- **Values:** frozen dataclasses in the domain; Pydantic only at boundaries.
- **Tests:** use fakes from `tests/fakes/`; never patch internals; no network, real time or global random.
- **Security:** the LLM never executes actions. Side effects go through `security/tool_guard.py`.
  Every security rule needs an allow test **and** a deny test.
- **Config:** only `core/config.py` reads environment variables.
- Update the matching doc in `docs/` in the same change when behaviour or design changes.

## Commands

```bash
uv sync
uv run pytest -m "not e2e"   # TEST_DATABASE_URL / TEST_REDIS_URL add Postgres/Redis tests
uv run ruff check . && uv run ruff format --check .
uv run pyright
uv run lint-imports
uv run python scripts/check_file_size.py --max 120
```
