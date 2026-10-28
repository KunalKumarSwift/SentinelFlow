"""Property tests for the tamper-evident audit hash chain."""

from dataclasses import replace
from datetime import timedelta

from hypothesis import given
from hypothesis import strategies as st

from sentinelflow.domain.audit import AuditEvent, AuditEventDraft
from sentinelflow.security.audit_chain import chain_next, genesis_hash, verify_chain
from tests.builders import T0

texts = st.text(min_size=1, max_size=20)


def _draft(actor: str, verb: str, outcome: str, note: str, minutes: int) -> AuditEventDraft:
    at = T0 + timedelta(minutes=minutes)
    return AuditEventDraft("acme", at, actor, verb, "inc-1", outcome, {"note": note})


drafts = st.builds(_draft, texts, texts, texts, st.text(max_size=20), st.integers(0, 10_000))


def _chain(items: list[AuditEventDraft]) -> list[AuditEvent]:
    events: list[AuditEvent] = []
    for draft in items:
        events.append(chain_next(events[-1] if events else None, draft))
    return events


@given(st.lists(drafts, min_size=1, max_size=15))
def test_untampered_chain_verifies(items: list[AuditEventDraft]) -> None:
    events = _chain(items)
    assert [e.seq for e in events] == list(range(1, len(items) + 1))
    assert verify_chain("acme", events).ok


@given(st.lists(drafts, min_size=1, max_size=15), st.data())
def test_any_edit_is_detected_at_its_seq(items: list[AuditEventDraft], data: st.DataObject) -> None:
    events = _chain(items)
    index = data.draw(st.integers(0, len(events) - 1))
    edited = replace(events[index], outcome=events[index].outcome + "!")
    result = verify_chain("acme", [*events[:index], edited, *events[index + 1 :]])
    assert (result.ok, result.first_bad_seq) == (False, index + 1)


@given(st.lists(drafts, min_size=2, max_size=15))
def test_deleting_an_event_is_detected(items: list[AuditEventDraft]) -> None:
    events = _chain(items)
    result = verify_chain("acme", events[1:])
    assert not result.ok and result.first_bad_seq == 2


def test_chains_start_from_a_tenant_specific_genesis() -> None:
    assert genesis_hash("acme") != genesis_hash("globex")
    first = _chain([AuditEventDraft("acme", T0, "u", "v", "r", "ok", {})])[0]
    assert first.prev_hash == genesis_hash("acme")
    assert not verify_chain("globex", [replace(first, tenant_id="globex")]).ok


def test_empty_chain_verifies() -> None:
    assert verify_chain("acme", []).ok
