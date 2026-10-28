"""Interface for telling people that something needs them (chat, e-mail, pager)."""

from typing import Protocol


class Notifier(Protocol):
    """Sends a short message to a named channel."""

    def notify(self, channel: str, message: str) -> None:
        """Deliver ``message`` to ``channel``.

        Raises:
            ProviderError: If the message could not be delivered.
        """
        ...
