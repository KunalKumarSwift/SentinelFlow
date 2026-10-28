# ADR 0004 — Synthetic simulator instead of real security tools

**Status:** Accepted

## Context
No SIEM, EDR or monitoring stack is available, and real tools are costly to run.

## Decision
Build a seeded attack **simulator** that emits alerts, raw events, seed data (users, intel)
and the **expected outcome** for each scenario. Mock providers read the seed data.
Real integrations (Wazuh, AbuseIPDB, …) are optional Phase 4 providers.

## Consequences
- ✅ Free, offline, reproducible demos; every scenario doubles as an end-to-end test.
- ✅ Forces clean provider protocols — real tools plug in later without workflow changes.
- ⚠️ Synthetic data is simpler than reality; public datasets (OTRF Security-Datasets,
  Splunk BOTS) can be added as an extra provider for realism.
