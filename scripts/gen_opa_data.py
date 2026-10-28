"""Write ``deploy/opa/data.json`` (role → permissions) from ``security/roles.py``.

    uv run python scripts/gen_opa_data.py

The role matrix has one source of truth; ``tests/unit/security/test_opa_data.py`` fails
if the committed file drifts from it.
"""

import json
from pathlib import Path

from sentinelflow.security.roles import ROLE_PERMISSIONS

TARGET = Path(__file__).resolve().parents[1] / "deploy" / "opa" / "data.json"


def render() -> str:
    """Return the data document OPA loads under ``data.sentinelflow.roles``."""
    roles = {
        role: sorted(p.value for p in perms) for role, perms in sorted(ROLE_PERMISSIONS.items())
    }
    return json.dumps({"sentinelflow": {"roles": roles}}, indent=2) + "\n"


if __name__ == "__main__":
    TARGET.write_text(render(), encoding="utf-8")
