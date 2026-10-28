"""Post-incident reports as GitHub issues, one per (tenant, incident).

Issues are found by a ``[tenant/incident]`` title marker through the search API, so the
provider keeps no state of its own. The token never appears in error messages.
"""

from typing import cast

import httpx

from sentinelflow.contracts.ticketing import Ticket
from sentinelflow.domain.errors import ProviderError

API = "https://api.github.com"
_RETRYABLE = {429, 500, 502, 503, 504}
Json = dict[str, object]


class GitHubTicketing:
    """``TicketingProvider`` on the issues of one repository (``owner/name``)."""

    def __init__(self, repo: str, token: str, transport: httpx.BaseTransport | None = None) -> None:
        """Use ``repo`` with a fine-grained token allowed to read and write its issues."""
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        self._repo = repo
        self._http = httpx.Client(base_url=API, headers=headers, transport=transport, timeout=10)

    def upsert(self, tenant_id: str, incident_id: str, title: str, body: str) -> str:
        """Create the incident's issue, or replace its title and body; return ``GH-<n>``."""
        fields: Json = {"title": f"{_marker(tenant_id, incident_id)} {title}", "body": body}
        existing = self._find(tenant_id, incident_id)
        if existing is None:
            issue = self._call("POST", f"/repos/{self._repo}/issues", fields)
        else:
            issue = self._call("PATCH", f"/repos/{self._repo}/issues/{existing['number']}", fields)
        return f"GH-{issue['number']}"

    def get(self, tenant_id: str, incident_id: str) -> Ticket | None:
        """Return the incident's issue as a ticket, if one exists."""
        issue = self._find(tenant_id, incident_id)
        if issue is None:
            return None
        return Ticket(
            f"GH-{issue['number']}", incident_id, str(issue["title"]), str(issue.get("body") or "")
        )

    def _find(self, tenant_id: str, incident_id: str) -> Json | None:
        query = f'repo:{self._repo} is:issue in:title "{_marker(tenant_id, incident_id)}"'
        items = self._call("GET", "/search/issues", params={"q": query}).get("items")
        if not isinstance(items, list):
            raise ProviderError("GitHub search returned no item list", retryable=False)
        found = [cast(Json, i) for i in cast(list[object], items) if isinstance(i, dict)]
        return found[0] if found else None

    def _call(
        self, method: str, path: str, json: Json | None = None, params: dict[str, str] | None = None
    ) -> Json:
        try:
            response = self._http.request(method, path, json=json, params=params)
        except httpx.HTTPError as exc:
            raise ProviderError(
                f"GitHub unreachable: {type(exc).__name__}", retryable=True
            ) from exc
        if response.is_error:
            status = response.status_code
            raise ProviderError(f"GitHub returned {status}", retryable=status in _RETRYABLE)
        return cast(Json, response.json())


def _marker(tenant_id: str, incident_id: str) -> str:
    return f"[{tenant_id}/{incident_id}]"
