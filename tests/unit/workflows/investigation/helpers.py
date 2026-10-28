"""Shared builders for investigation tests."""

from collections.abc import Iterable, Mapping

from sentinelflow.domain.events import SecurityEvent
from sentinelflow.providers.events.memory_event_store import MemoryEventStore
from sentinelflow.workflows.investigation import InvestigationDeps
from tests.fakes.fake_llm import FakeLLM

NAME = "investigation.analyse"


def answer(
    techniques: Iterable[str] = ("T1110",),
    actions: Iterable[str] = ("disable_user", "block_ip"),
) -> dict[str, object]:
    """Return a raw LLM answer for the analysis schema."""
    return {
        "narrative": "Password spraying followed by a successful login.",
        "technique_ids": list(techniques),
        "suggested_actions": list(actions),
    }


def deps(
    events: Iterable[SecurityEvent] = (), script: Mapping[str, object] | Exception | None = None
) -> tuple[InvestigationDeps, FakeLLM]:
    """Return deps with an event store and a scripted LLM."""
    llm = FakeLLM({NAME: answer() if script is None else script})  # type: ignore[dict-item]
    return InvestigationDeps(events=MemoryEventStore(events), llm=llm), llm
