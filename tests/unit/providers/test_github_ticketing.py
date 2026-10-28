"""GitHub Issues as the ticketing system: one issue per (tenant, incident), upserted."""

import json

import httpx
import pytest

from sentinelflow.domain.errors import ProviderError
from sentinelflow.providers.ticketing.github_ticketing import GitHubTicketing


class FakeGitHub:
    """Minimal in-memory GitHub issues API (search, create, update, get)."""

    def __init__(self) -> None:
        self.issues: dict[int, dict[str, object]] = {}
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        if path == "/search/issues":
            needle = request.url.params["q"].split('"')[1]
            items = [i for i in self.issues.values() if needle in str(i["title"])]
            return httpx.Response(200, json={"items": items})
        body: dict[str, object] = json.loads(request.content) if request.content else {}
        if request.method == "POST" and path == "/repos/acme-sec/incidents/issues":
            number = len(self.issues) + 1
            self.issues[number] = {"number": number, **body}
            return httpx.Response(201, json=self.issues[number])
        number = int(path.rsplit("/", 1)[1])
        self.issues[number].update(body)
        return httpx.Response(200, json=self.issues[number])


def _tickets(github: FakeGitHub) -> GitHubTicketing:
    return GitHubTicketing("acme-sec/incidents", "ghp_" + "x" * 36, httpx.MockTransport(github))


def test_first_upsert_creates_an_issue_and_the_second_updates_it() -> None:
    github = FakeGitHub()
    tickets = _tickets(github)
    first = tickets.upsert("acme", "inc-1", "Brute force", "v1")
    second = tickets.upsert("acme", "inc-1", "Brute force", "v2")
    ticket = tickets.get("acme", "inc-1")
    assert first == second == "GH-1" and len(github.issues) == 1
    assert ticket is not None and (ticket.id, ticket.body) == ("GH-1", "v2")
    assert github.requests[0].headers["Authorization"] == "Bearer ghp_" + "x" * 36


def test_issues_are_tenant_scoped_by_their_title_marker() -> None:
    github = FakeGitHub()
    tickets = _tickets(github)
    tickets.upsert("acme", "inc-1", "t", "b")
    assert tickets.get("globex", "inc-1") is None
    assert github.issues[1]["title"] == "[acme/inc-1] t"


@pytest.mark.parametrize(("status", "retryable"), [(403, False), (502, True), (429, True)])
def test_api_errors_are_provider_errors_without_the_token(status: int, retryable: bool) -> None:
    tickets = GitHubTicketing(
        "acme-sec/incidents", "secret-token", httpx.MockTransport(lambda _: httpx.Response(status))
    )
    with pytest.raises(ProviderError) as caught:
        tickets.get("acme", "inc-1")
    assert caught.value.retryable is retryable and "secret-token" not in str(caught.value)


def test_malformed_search_results_are_rejected() -> None:
    body = httpx.Response(200, json={"items": "nope"})
    tickets = GitHubTicketing("acme-sec/incidents", "t", httpx.MockTransport(lambda _: body))
    with pytest.raises(ProviderError, match="search"):
        tickets.get("acme", "inc-1")


def test_unreachable_github_is_retryable() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(ProviderError) as caught:
        GitHubTicketing("acme-sec/incidents", "t", httpx.MockTransport(refuse)).get("acme", "inc-1")
    assert caught.value.retryable
