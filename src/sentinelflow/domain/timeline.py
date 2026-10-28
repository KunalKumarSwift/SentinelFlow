"""Turn raw events into a readable timeline, collapsing consecutive repeats."""

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime

from sentinelflow.domain.events import SecurityEvent


@dataclass(frozen=True, slots=True)
class TimelineEntry:
    """One step of an incident, possibly standing for several identical events."""

    start: datetime
    end: datetime
    summary: str
    first_event_id: str
    count: int = 1


def build_timeline(events: Iterable[SecurityEvent]) -> tuple[TimelineEntry, ...]:
    """Return entries in time order; runs of the same kind and entities become one entry."""
    entries: list[TimelineEntry] = []
    keys: list[tuple[str, str]] = []
    for event in sorted(events, key=lambda e: (e.at, e.id)):
        key = (event.kind, _entities(event))
        if keys and keys[-1] == key:
            last = entries[-1]
            entries[-1] = replace(last, end=event.at, count=last.count + 1)
        else:
            keys.append(key)
            entries.append(TimelineEntry(event.at, event.at, "", event.id))
    return tuple(
        replace(e, summary=_summary(k, e.count)) for e, k in zip(entries, keys, strict=True)
    )


def _entities(event: SecurityEvent) -> str:
    return ", ".join(f"{k}={v}" for k, v in event.entities.present().items())


def _summary(key: tuple[str, str], count: int) -> str:
    kind, entities = key
    times = f" x{count}" if count > 1 else ""
    return f"{kind}{times} ({entities})"
