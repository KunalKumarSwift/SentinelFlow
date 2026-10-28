# 05 — Testing Strategy

## 1. Test pyramid

| Level | Share | Scope | Speed | Location |
|---|---|---|---|---|
| Unit | ~70 % | Pure domain rules, single nodes, security rules, providers with fakes | ms | `tests/unit/` |
| Contract | ~5 % | Every implementation of a protocol passes the same suite | ms–s | `tests/contracts/` |
| Graph / integration | ~15 % | Compiled graphs with fakes + `InMemorySaver`; worker with `MemoryRunQueue` | < 1 s each | `tests/integration/` |
| API | ~8 % | FastAPI `TestClient` with fake container; auth and error mapping | < 1 s each | `tests/api/` |
| End-to-end | ~2 % | Docker Compose stack + simulator scenarios | minutes | `tests/e2e/` (marked `e2e`) |

CI runs everything except `e2e` on every push; `e2e` runs nightly and before releases.

## 2. Fakes, not mocks

`tests/fakes/` contains one hand-written fake per protocol (`FakeLLM`, `FakeThreatIntel`,
`FakeIdentityProvider`, `FakeClock`, `FakeAuditStore`, …). Fakes:

- are simple in-memory implementations that **pass the contract test** for their protocol;
- record calls for assertions (`fake_identity.applied_actions`);
- are configured with plain data (`FakeThreatIntel({"203.0.113.9": IpReputation(...)})`).

`unittest.mock.patch` of internal modules is **not allowed**: if something needs patching,
it should have been injected.

## 3. Testing LLM behaviour

| Layer | How |
|---|---|
| Unit / graph tests | `FakeLLM` returns scripted structured outputs keyed by `Prompt.name`; tests assert the prompt contents (e.g. PII redacted, untrusted data delimited) |
| Failure handling | `FakeLLM` scripted to return invalid output / raise `ProviderError` → assert fail-safe path (`NEEDS_REVIEW`) |
| Quality evaluation (optional) | `evals/` directory: each simulator scenario + expected verdict/techniques; run against Ollama or Haiku on demand, report accuracy. Not part of CI (costs money / time) |

## 4. Security test matrix

Security tests are **generated from an independent spec** of the matrix, so a wrong grant in
the code fails a test:

```python
@pytest.mark.parametrize(("role", "permission", "expected"), rbac_matrix_cases())
def test_rbac_matrix(role: str, permission: str, expected: bool) -> None:
    decision = engine.evaluate(request_for(role, permission))
    assert decision.allowed is expected
```

Plus explicit scenario tests for every ABAC rule, each with an allow **and** a deny case:

| Test | Expectation |
|---|---|
| Analyst from tenant A reads tenant B incident | 404 (not 403 — do not leak existence) |
| L2 approves HIGH-impact action | 403 `missing permission action:approve:high` |
| Commander approves action targeting themself | 403 `no_self_action` |
| Proposer approves own proposal | 403 `separation_of_duties` |
| Same commander approves twice on CRITICAL | 409 / denied `distinct_approvers` |
| L1 starts containment that would execute | Tool guard denies `action:execute` |
| Forged `ResumeRun` without stored approval | Run stays waiting; nothing executed |
| Tampered audit row | `/v1/audit/verify` returns `ok=false, first_bad_seq=n` |
| Prompt-injection scenario | `injection_suspected=true`, verdict `NEEDS_REVIEW`, no actions executed |
| Expired / bad-signature token | 401 |

## 5. Property-based tests (Hypothesis)

- Audit chain: for any list of events, `verify(chain(events))` is ok; changing any byte of any
  event makes verify fail at that `seq`.
- Severity: result always within `INFO..CRITICAL`; adding a malicious-IP signal never lowers severity.
- Fingerprint: order of entity fields does not change the fingerprint.

## 6. Graph test pattern (containment example)

```python
def test_containment_executes_only_after_approval(container: TestContainer) -> None:
    graph = build_containment_graph(container.containment_deps)
    config = run_config(run_id="run-1", initiator=container.l1_analyst)

    graph.invoke(initial_state(proposed=[disable_user("alice")]), config)
    assert container.identity.applied_actions == []                  # paused at interrupt

    container.approve(action_id="act-1", approver=container.commander)
    graph.invoke(Command(resume={"approval_id": "apr-1"}), config)
    assert container.identity.applied_actions == [disable_user("alice")]
```

## 7. End-to-end scenarios

For every simulator scenario: start the stack, run the scenario, approve where expected
with the right role, then assert the final incident matches `ScenarioOutput.expected`
and `/v1/audit/verify` is ok.

## 8. Load tests (Phase 3)

Locust file in `loadtests/`: ingest stream of mixed scenarios; report p50/p95 ingest latency,
end-to-end run duration, queue depth over time and worker scaling. Results recorded in
`docs/benchmarks.md` — these numbers go on the résumé.

## 9. Coverage and quality gates

- Line + branch coverage ≥ 90 % for `domain/`, `security/`, `workflows/`; ≥ 80 % overall.
- Mutation testing (`mutmut`) on `security/` before Phase 2 completes — security code must
  have tests that actually fail when logic is altered.
