"""Choose the notifier from settings. Switch logic only."""

from sentinelflow.contracts.notifier import Notifier
from sentinelflow.core.config import Settings


def make_notifier(settings: Settings) -> Notifier | None:
    """Return a chat-webhook notifier when ``NOTIFY_WEBHOOK_URL`` is set, else ``None``."""
    if settings.notify_webhook_url is None:
        return None
    from sentinelflow.providers.notify.webhook_notifier import WebhookNotifier

    return WebhookNotifier(settings.notify_webhook_url.get_secret_value(), settings.notify_style)
