# 04 — Engineering Guidelines

These rules apply to every line of code in this repository. Reviews (human or AI) check them.

## 1. Test-Driven Development

We follow **red → green → refactor** in small steps.

1. **Red** — write the smallest test that describes the next behaviour. Run it. It must fail
   for the *expected* reason (not an import error).
2. **Green** — write the minimum code that makes it pass. Hard-coding is fine at this point.
3. **Refactor** — remove duplication, improve names, split long functions. Tests stay green.
4. **Commit** — one behaviour per commit when practical (`test:` + `feat:` can be one commit).

Rules:

- No production code without a failing test that demands it.
- One logical assertion per test; use `pytest.mark.parametrize` for tables of cases.
- Tests describe behaviour, not implementation: `test_dedup_merges_alert_into_open_incident`,
  not `test_dedup_calls_repository_get`.
- A bug fix starts with a test that reproduces the bug.
- Tests never touch the network, real time, or global randomness — inject `Clock`, `Random`, `IdFactory`.

## 2. Size limits

| Unit | Limit | Why |
|---|---|---|
| File | 50–100 lines (CI fails > 120 physical lines) | Fits on one screen; one reason to change |
| Function | ≤ 20 lines | Readable without scrolling; easy to name |
| Parameters | ≤ 4 (else a frozen dataclass) | Call sites stay readable |
| Indentation | ≤ 2 levels inside a function | Use early returns and small helpers |
| Line length | 100 characters | Ruff-enforced |

If a file grows past 100 lines, split by responsibility (e.g. `scoring.py` → `scoring.py` +
`scoring_table.py`). Constant tables and prompt templates go in their own `*_table.py` /
`prompts.py` files.

## 3. Coding principles

| Principle | In this codebase |
|---|---|
| **Single responsibility** | One class or one cohesive group of functions per file |
| **Open/closed** | New provider = new file + one facade branch; no edits to workflows |
| **Liskov / Protocols** | Every implementation passes the shared contract test for its protocol |
| **Interface segregation** | Small protocols (`ThreatIntelProvider` ≠ `IdentityProvider`) |
| **Dependency inversion** | Workflows depend on `contracts/`, never on `providers/` |
| **Pure core, effectful edges** | Business rules are pure functions on frozen dataclasses; I/O in providers |
| **Composition over inheritance** | Decorator providers (`BudgetedLLM`) instead of subclass trees |
| **Explicit over implicit** | No globals, no service locator, no monkey-patching in tests |
| **Fail safe** | When unsure (invalid LLM output, policy error), choose the more restrictive outcome |
| **YAGNI** | Build what the current roadmap slice needs; extract helpers at the third repetition |

## 4. Python style

- Python **3.12+**, managed with **uv**.
- **Type hints everywhere**; `pyright --strict` must pass. No `Any` (use `object`, generics or
  `TypedDict`). `# type: ignore[code]` only with a one-line reason.
- **Ruff** for lint and format (rules: `E, F, I, B, UP, SIM, RUF, S, N, D`).
- **Frozen dataclasses** (`@dataclass(frozen=True, slots=True)`) for domain values; Pydantic only
  at boundaries (API, queue, LLM output, config).
- **Privacy:** `_leading_underscore` for module-private names; each package's `__init__.py`
  re-exports its public API with `__all__`.
- **Errors:** raise typed exceptions from `domain/errors.py`; never bare `except:`; never
  catch-log-and-continue.
- **Config:** only `core/config.py` reads environment variables.
- **Imports:** stdlib → third-party → local (Ruff `I`). Heavy libraries imported lazily inside providers.

## 5. Documentation

Every module, public class and public function has a **Google-style docstring**.

```python
"""Scores incident severity from the detection rule and enrichment data.

Design: a pure function over a lookup table so the rules are easy to test and audit.
"""


def score_severity(rule_id: str, enrichment: Enrichment) -> Severity:
    """Return the incident severity for a rule, adjusted by enrichment signals.

    Args:
        rule_id: Detection rule that raised the alert, e.g. ``"brute_force_success"``.
        enrichment: Threat-intel and user context gathered during triage.

    Returns:
        The adjusted severity, clamped to the INFO..CRITICAL range.

    Raises:
        UnknownRule: If ``rule_id`` is not in the base-severity table.
    """
```

- Inline comments explain **why**, never **what**. One line.
- Docs in `docs/` are updated in the **same PR** as the behaviour they describe.
- Significant decisions get an ADR in `docs/adr/`.

## 6. Git workflow

- Branch per roadmap slice: `feat/triage-scoring`, `fix/dedup-window`.
- Conventional commits: `feat:`, `fix:`, `test:`, `refactor:`, `docs:`, `chore:`.
- PRs stay small (≈ < 300 changed lines) and link the roadmap slice.

## 7. Definition of done (per slice)

- [ ] Tests written first and passing; coverage of new code ≥ 90 %.
- [ ] `ruff check`, `ruff format --check`, `pyright`, `lint-imports`, file-size check all pass.
- [ ] Every new file within the size limits; every public symbol documented.
- [ ] Security-relevant behaviour has a test for the **deny** path, not only the allow path.
- [ ] Docs/ADR updated if behaviour or design changed.

## 8. Tooling commands (once the project is bootstrapped)

```bash
uv sync                          # install
uv run pytest                    # all tests
uv run pytest -m "not e2e"       # fast suite
uv run ruff check . && uv run ruff format --check .
uv run pyright
uv run lint-imports              # layer rules
uv run python scripts/check_file_size.py --max 120
```
