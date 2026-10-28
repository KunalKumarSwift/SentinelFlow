"""Role → permission matrix (LLD 03 §3). Data only; checked by ``rbac.py``.

No human role holds ``action:execute``: people approve, only the orchestrator
service account executes, and only actions whose approval quorum is met.
"""

from collections.abc import Mapping
from types import MappingProxyType

from sentinelflow.security.permissions import Permission as Perm

_READ = frozenset({Perm.INCIDENT_READ})
_RUN_ALL = frozenset({Perm.RUN_TRIAGE, Perm.RUN_INVESTIGATION, Perm.RUN_CONTAINMENT})
_APPROVE_LOW_MEDIUM = frozenset({Perm.ACTION_APPROVE_LOW, Perm.ACTION_APPROVE_MEDIUM})

ROLE_PERMISSIONS: Mapping[str, frozenset[Perm]] = MappingProxyType(
    {
        "alert-source": frozenset({Perm.ALERT_INGEST}),
        "soc-analyst-l1": _READ | {Perm.RUN_TRIAGE, Perm.RUN_CONTAINMENT, Perm.ACTION_PROPOSE},
        "soc-analyst-l2": _READ
        | _RUN_ALL
        | _APPROVE_LOW_MEDIUM
        | {Perm.INCIDENT_READ_PII, Perm.INCIDENT_CLOSE, Perm.ACTION_PROPOSE},
        "incident-commander": _READ
        | _RUN_ALL
        | _APPROVE_LOW_MEDIUM
        | {
            Perm.INCIDENT_READ_ALL,
            Perm.INCIDENT_READ_PII,
            Perm.INCIDENT_CLOSE,
            Perm.ACTION_PROPOSE,
            Perm.ACTION_APPROVE_HIGH,
        },
        "security-engineer": _READ | {Perm.WORKFLOW_PUBLISH, Perm.INTEGRATION_MANAGE},
        "auditor": frozenset({Perm.AUDIT_READ, Perm.AUDIT_VERIFY}),
        "executive": _READ | {Perm.INCIDENT_READ_ALL},
        "orchestrator": _READ
        | _RUN_ALL
        | {
            Perm.INCIDENT_READ_ALL,
            Perm.INCIDENT_READ_PII,
            Perm.ACTION_PROPOSE,
            Perm.ACTION_EXECUTE,
            Perm.INTEL_LOOKUP,
            Perm.IDENTITY_READ,
            Perm.EVENTS_READ,
        },
        "platform-admin": frozenset({Perm.AUDIT_READ, Perm.AUDIT_VERIFY, Perm.TENANT_ADMIN}),
    }
)
