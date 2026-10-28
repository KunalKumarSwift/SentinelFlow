"""``PolicyEngine`` backed by Open Policy Agent (Rego in ``deploy/opa``).

The request is sent as OPA ``input``; the policy returns ``{"allowed", "reason"}``. The
engine **fails closed**: an unreachable server, an error status, a missing policy or a
malformed answer all deny, so an OPA outage can never open access.
"""

from typing import cast

import httpx

from sentinelflow.security.opa_input import to_input
from sentinelflow.security.policy import AccessRequest, Decision

DECISION_PATH = "sentinelflow/authz/decision"
UNAVAILABLE = Decision(False, "policy engine unavailable")


class OpaPolicyEngine:
    """Asks an OPA server for each decision."""

    def __init__(self, url: str, transport: httpx.BaseTransport | None = None) -> None:
        """Query OPA at ``url``; ``transport`` lets tests replace the network."""
        self._client = httpx.Client(base_url=url, transport=transport, timeout=2)

    def evaluate(self, request: AccessRequest) -> Decision:
        """Return OPA's decision, or deny if none can be obtained."""
        try:
            response = self._client.post(
                f"/v1/data/{DECISION_PATH}", json={"input": to_input(request)}
            )
            response.raise_for_status()
            body: object = response.json()
        except (httpx.HTTPError, ValueError):
            return UNAVAILABLE
        return _decision(body)


def _decision(body: object) -> Decision:
    result = cast(dict[str, object], body).get("result") if isinstance(body, dict) else None
    if not isinstance(result, dict):
        return UNAVAILABLE
    fields = cast(dict[str, object], result)
    allowed, reason = fields.get("allowed"), fields.get("reason")
    if not isinstance(allowed, bool) or not isinstance(reason, str):
        return UNAVAILABLE
    return Decision(allowed, reason)
