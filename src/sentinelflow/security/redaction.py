"""Replace personal identifiers with stable pseudonyms for roles without ``incident:read_pii``.

Pseudonyms are an HMAC of field and value, so the same user always maps to the same
pseudonym (analysts can still correlate incidents) but cannot be reversed without the key.
"""

import hashlib
import hmac

from sentinelflow.domain.alerts import Entities
from sentinelflow.domain.principals import Principal
from sentinelflow.security.permissions import Permission
from sentinelflow.security.rbac import has_permission

PII_FIELDS = frozenset({"user", "email_id"})


class Redactor:
    """Produces role-appropriate views of entities."""

    def __init__(self, key: bytes) -> None:
        """Use ``key`` (at least 32 bytes) for pseudonyms.

        Raises:
            ValueError: If the key is too short.
        """
        if len(key) < 32:
            raise ValueError("redaction key must be at least 32 bytes")
        self._key = key

    def pseudonym(self, field: str, value: str) -> str:
        """Return ``<field>-<12 hex chars>`` for ``value``."""
        digest = hmac.new(self._key, f"{field}:{value}".encode(), hashlib.sha256).hexdigest()
        return f"{field}-{digest[:12]}"

    def entities_for(self, principal: Principal, entities: Entities) -> dict[str, str]:
        """Return the entities ``principal`` may see, pseudonymising PII if needed."""
        present = entities.present()
        if has_permission(principal, Permission.INCIDENT_READ_PII):
            return present
        return {k: self.pseudonym(k, v) if k in PII_FIELDS else v for k, v in present.items()}
