# ADR 0005 — One Python package with enforced layers

**Status:** Accepted

## Context
A multi-package uv workspace maximises reuse but adds many `pyproject.toml` files and
indirection. The project's priority is a codebase that is simple to read and review.

## Decision
One installable package `sentinelflow` with layered sub-packages
(`core → domain → contracts → security → workflows|providers → api|runtime|simulator → bootstrap`).
Layer rules are enforced with **import-linter** in CI.

## Consequences
- ✅ Simple to navigate, install and run; still strictly layered.
- ✅ Splitting a layer into its own package later is mechanical because boundaries are enforced.
- ⚠️ Relies on CI tooling (not the packaging system) to keep boundaries.
