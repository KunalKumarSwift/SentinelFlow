# LLD 08 — Attack Simulator

The simulator produces **deterministic, seeded** synthetic data so demos and tests are
reproducible and free. It replaces a real SIEM in Phases 1–3.

## 1. Output of a scenario

```python
@dataclass(frozen=True, slots=True)
class ScenarioOutput:
    name: str
    alerts: tuple[Alert, ...]             # what a SIEM would raise
    events: tuple[SecurityEvent, ...]     # raw log lines for the event store
    seed_data: SeedData                   # users, assets, intel indicators
    expected: Expectation                 # severity, verdict, action kinds — used by tests
```

`expected` makes every scenario an **end-to-end test case**: run the lifecycle and assert
the outcome matches.

## 2. Scenarios

One module per scenario in `simulator/scenarios/`, each exposing
`generate(rng: Random, clock: Clock, tenant: str) -> ScenarioOutput`.

| Module | Alerts | Events | Expected |
|---|---|---|---|
| `brute_force.py` | `brute_force_success` | 30–60 failed logins + 1 success, one external IP | HIGH, TP, `DISABLE_USER`, `BLOCK_IP` |
| `impossible_travel.py` | `impossible_travel` | Two logins, countries ≥ 5 000 km apart, < 30 min | MEDIUM, TP, `FORCE_MFA_RESET` |
| `leaked_key.py` | `access_key_anomaly` | Burst of `ListBuckets`/`GetObject` from unknown IP | CRITICAL, TP, `REVOKE_ACCESS_KEY` (2 approvals) |
| `phishing.py` | `phishing_click` | Email received + proxy hit on malicious URL | MEDIUM, TP, `PURGE_EMAIL`, `RESET_PASSWORD` |
| `powershell.py` | `suspicious_process` | Encoded PowerShell + outbound connection | HIGH, TP, `ISOLATE_HOST` |
| `exfiltration.py` | `large_download` | 10 GB download at 03:00 local | HIGH, TP, no action → ESCALATED |
| `prompt_injection.py` | `brute_force_success` | Same as brute force, `raw.user_agent` contains injection text | `injection_suspected`, NEEDS_REVIEW |
| `benign.py` | `impossible_travel` | Login via corporate VPN egress | LOW, FALSE_POSITIVE, closed |

## 3. Building blocks (small, shared)

| Module | Provides |
|---|---|
| `simulator/factories.py` | `make_user`, `make_ip(kind="external"|"internal"|"malicious")`, `make_host` |
| `simulator/geo.py` | Small static table of cities with coordinates; `distance_km(a, b)` |
| `simulator/timeline.py` | `spread(start, count, every)` → timestamps |
| `simulator/registry.py` | `SCENARIOS: Mapping[str, ScenarioFn]` |
| `simulator/sinks.py` | `HttpSink` (POST to API), `JsonlSink` (write files), `MemorySink` (tests) |
| `simulator/cli.py` | Command-line entry |

## 4. CLI

```bash
# one scenario against a running API
sentinelflow-sim run brute_force --seed 42 --api http://localhost:8000

# a mixed stream for load tests: 1000 alerts, 20% benign, 50 alerts/s
sentinelflow-sim stream --count 1000 --benign-ratio 0.2 --rate 50 --seed 7

# write to files instead of HTTP
sentinelflow-sim run leaked_key --out ./samples/
```

The simulator authenticates with an `alert-source` service token, exactly like a real integration.

## 5. Determinism rules

- All randomness from an injected `random.Random(seed)`; never the global `random`.
- All time from an injected `Clock`; tests use `FakeClock(start=2026-01-01T00:00Z)`.
- IDs from an injected `IdFactory` (sequential in tests).
- Same seed + same version → byte-identical output (asserted by a snapshot test).
