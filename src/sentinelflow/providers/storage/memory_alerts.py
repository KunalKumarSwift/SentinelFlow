"""In-memory alert store for tests and single-process mode."""

from collections import defaultdict

from sentinelflow.contracts.repositories import StoredAlert


class MemoryAlertRepository:
    """Keeps alerts in lists keyed by ``(tenant_id, fingerprint)``."""

    def __init__(self) -> None:
        """Start empty."""
        self._by_fp: defaultdict[tuple[str, str], list[StoredAlert]] = defaultdict(list)

    def add(self, stored: StoredAlert) -> None:
        """Store an ingested alert."""
        self._by_fp[(stored.alert.tenant_id, stored.fingerprint)].append(stored)

    def latest_with_fingerprint(self, tenant_id: str, fingerprint: str) -> StoredAlert | None:
        """Return the matching alert with the latest ``observed_at``, if any."""
        matches = self._by_fp.get((tenant_id, fingerprint), [])
        return max(matches, key=lambda s: s.alert.observed_at, default=None)
