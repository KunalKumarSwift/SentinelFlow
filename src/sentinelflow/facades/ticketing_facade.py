"""Choose where post-incident reports go. Switch logic only."""

from sentinelflow.contracts.ticketing import TicketingProvider
from sentinelflow.core.config import Settings


def make_ticketing(settings: Settings, store: TicketingProvider) -> TicketingProvider:
    """Return GitHub Issues for ``TICKETING_BACKEND=github``, else the storage-backed ``store``."""
    if (
        settings.ticketing_backend != "github"
        or not settings.github_repo
        or not settings.github_token
    ):
        return store
    from sentinelflow.providers.ticketing.github_ticketing import GitHubTicketing

    return GitHubTicketing(settings.github_repo, settings.github_token.get_secret_value())
