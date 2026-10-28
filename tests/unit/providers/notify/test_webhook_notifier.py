"""Chat webhooks: Slack and Discord payloads; failures become provider errors."""

import json
from typing import cast

import httpx
import pytest

from sentinelflow.domain.errors import ProviderError
from sentinelflow.providers.notify.webhook_notifier import Style, WebhookNotifier

URL = "https://hooks.example/services/T000/B000/secret"


def _notifier(style: str, response: httpx.Response, seen: list[httpx.Request]) -> WebhookNotifier:
    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return response

    return WebhookNotifier(URL, cast(Style, style), transport=httpx.MockTransport(handle))


@pytest.mark.parametrize(("style", "key"), [("slack", "text"), ("discord", "content")])
def test_payload_matches_the_chat_service(style: str, key: str) -> None:
    seen: list[httpx.Request] = []
    _notifier(style, httpx.Response(204), seen).notify("approvals", "hello")
    assert json.loads(seen[0].content) == {key: "[approvals] hello"}


@pytest.mark.parametrize(("status", "retryable"), [(429, True), (503, True), (404, False)])
def test_errors_are_provider_errors_without_the_secret_url(status: int, retryable: bool) -> None:
    with pytest.raises(ProviderError) as caught:
        _notifier("slack", httpx.Response(status), []).notify("approvals", "hi")
    assert caught.value.retryable is retryable and "secret" not in str(caught.value)


def test_unreachable_webhook_is_retryable() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    notifier = WebhookNotifier(URL, "slack", transport=httpx.MockTransport(refuse))
    with pytest.raises(ProviderError) as caught:
        notifier.notify("approvals", "hi")
    assert caught.value.retryable
