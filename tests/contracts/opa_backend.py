"""OPA server for policy-engine contract tests; skipped unless ``TEST_OPA_URL`` is set.

CI installs OPA and serves ``deploy/opa`` on localhost so both engines run the suite.
"""

import os

import pytest

from sentinelflow.security.opa_engine import OpaPolicyEngine


def opa_engine() -> OpaPolicyEngine:
    """Return an engine pointed at the test OPA server, or skip the test."""
    url = os.environ.get("TEST_OPA_URL")
    if not url:
        pytest.skip("TEST_OPA_URL not set")
    return OpaPolicyEngine(url)
