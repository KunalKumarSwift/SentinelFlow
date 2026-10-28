"""No notifications by default; a webhook notifier when a URL is configured."""

from pydantic import SecretStr

from sentinelflow.core.config import Settings
from sentinelflow.facades.notify_facade import make_notifier
from sentinelflow.providers.notify.webhook_notifier import WebhookNotifier

SECRET = SecretStr("s" * 32)


def test_default_sends_nothing() -> None:
    assert make_notifier(Settings(jwt_secret=SECRET)) is None  # type: ignore[call-arg]


def test_webhook_url_enables_chat_notifications() -> None:
    url = SecretStr("https://discord.example/api/webhooks/1/x")
    settings = Settings(jwt_secret=SECRET, notify_webhook_url=url, notify_style="discord")  # type: ignore[call-arg]
    assert isinstance(make_notifier(settings), WebhookNotifier)
