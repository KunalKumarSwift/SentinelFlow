"""Typed client for the endpoints the UI uses.

It holds no authority of its own: every call carries the signed-in user's bearer token
and the API enforces every rule.
"""

from collections.abc import Mapping
from typing import cast

from pydantic import TypeAdapter

from sentinelflow.ui.http import Http, Response
from sentinelflow.ui.models import ApprovalView, AuditView, IncidentView, VerifyView

_INCIDENTS = TypeAdapter(list[IncidentView])
_APPROVALS = TypeAdapter(list[ApprovalView])
_AUDIT = TypeAdapter(list[AuditView])


class ApiError(Exception):
    """The API refused a request; ``str(error)`` shows the status and problem detail."""

    def __init__(self, status: int, detail: str) -> None:
        """Keep the HTTP status for callers that branch on it."""
        super().__init__(f"{status}: {detail}")
        self.status = status


class SentinelFlowClient:
    """One signed-in user's view of the API."""

    def __init__(self, http: Http, token: str) -> None:
        """Send requests through ``http`` with ``token``."""
        self._http, self._headers = http, {"Authorization": f"Bearer {token}"}

    def incidents(self) -> list[IncidentView]:
        """Return the incidents the user may see."""
        return _INCIDENTS.validate_python(self._get("/v1/incidents")["items"])

    def approvals(self) -> list[ApprovalView]:
        """Return the approvals the user may decide."""
        return _APPROVALS.validate_python(self._get("/v1/approvals")["items"])

    def decide(self, approval_id: str, *, approved: bool, reason: str) -> None:
        """Approve or reject one approval."""
        body = {"approved": approved, "reason": reason}
        _check(
            self._http.post(
                f"/v1/approvals/{approval_id}/decision", json=body, headers=self._headers
            )
        )

    def audit(self, after_seq: int, limit: int) -> list[AuditView]:
        """Return a page of the tenant's audit events."""
        params = {"after_seq": after_seq, "limit": limit}
        return _AUDIT.validate_python(self._get("/v1/audit", params)["items"])

    def verify(self) -> VerifyView:
        """Re-verify the tenant's audit chain."""
        return VerifyView.model_validate(self._get("/v1/audit/verify"))

    def _get(self, path: str, params: Mapping[str, int] | None = None) -> dict[str, object]:
        body = _check(self._http.get(path, params=params, headers=self._headers)).json()
        if not isinstance(body, dict):
            raise ApiError(502, "unexpected response shape")
        return cast(dict[str, object], body)


def dev_token(http: Http, identity: Mapping[str, object]) -> str:
    """Get a token from the dev-token endpoint (``APP_ENV=dev`` only)."""
    body = _check(http.post("/v1/auth/dev-token", json=dict(identity))).json()
    token = cast(dict[str, object], body).get("access_token") if isinstance(body, dict) else None
    if not isinstance(token, str):
        raise ApiError(502, "no access token in response")
    return token


def _check(response: Response) -> Response:
    if response.is_error:
        body: object = response.json() if response.content else None
        detail = cast(dict[str, object], body).get("detail", "") if isinstance(body, dict) else ""
        raise ApiError(response.status_code, str(detail))
    return response
