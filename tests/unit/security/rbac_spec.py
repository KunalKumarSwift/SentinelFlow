"""Independent copy of the RBAC matrix from docs/03-lld/03-security.md §3.

Kept separate from ``security/roles.py`` on purpose: if both came from one table,
a wrong grant could never fail a test.
"""

READ = {"incident:read"}
RUN_ALL = {"workflow:run:triage", "workflow:run:investigation", "workflow:run:containment"}

EXPECTED: dict[str, set[str]] = {
    "alert-source": {"alert:ingest"},
    "soc-analyst-l1": READ | {"workflow:run:triage", "workflow:run:containment", "action:propose"},
    "soc-analyst-l2": READ
    | RUN_ALL
    | {
        "incident:read_pii",
        "incident:close",
        "action:propose",
        "action:approve:low",
        "action:approve:medium",
    },
    "incident-commander": READ
    | RUN_ALL
    | {
        "incident:read_all",
        "incident:read_pii",
        "incident:close",
        "action:propose",
        "action:approve:low",
        "action:approve:medium",
        "action:approve:high",
    },
    "security-engineer": READ | {"workflow:publish", "integration:manage"},
    "auditor": {"audit:read", "audit:verify"},
    "executive": READ | {"incident:read_all"},
    "orchestrator": READ
    | RUN_ALL
    | {
        "incident:read_all",
        "incident:read_pii",
        "action:propose",
        "action:execute",
        "intel:lookup",
        "identity:read",
        "events:read",
    },
    "platform-admin": {"audit:read", "audit:verify", "tenant:admin"},
}
