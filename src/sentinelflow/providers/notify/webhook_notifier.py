"""Post notifications to a Slack or Discord incoming webhook.

The webhook URL is a credential (anyone holding it can post), so it never appears in
error messages.
"""

from typing import Literal

import httpx

from sentinelflow.domain.errors import ProviderError

Style = Literal["slack", "discord"]
_FIELD: dict[Style, str] = {"slack": "text", "discord": "content"}
_RETRYABLE = {429, 500, 502, 503, 504}


class WebhookNotifier:
    """``Notifier`` for chat incoming webhooks."""

    def __init__(
        self, url: str, style: Style, transport: httpx.BaseTransport | None = None
    ) -> None:
        """Post to ``url`` in ``style``'s payload format."""
        self._url, self._field = url, _FIELD[style]
        self._client = httpx.Client(transport=transport, timeout=5)

    def notify(self, channel: str, message: str) -> None:
        """Post ``[channel] message``.

        Raises:
            ProviderError: If the webhook fails (429/5xx and network errors are retryable).
        """
        try:
            response = self._client.post(self._url, json={self._field: f"[{channel}] {message}"})
        except httpx.HTTPError as exc:
            raise ProviderError(
                f"webhook unreachable: {type(exc).__name__}", retryable=True
            ) from exc
        if response.is_error:
            status = response.status_code
            raise ProviderError(f"webhook returned {status}", retryable=status in _RETRYABLE)
