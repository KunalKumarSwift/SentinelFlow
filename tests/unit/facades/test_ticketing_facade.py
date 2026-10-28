"""Reports stay in our store by default; GitHub Issues when configured."""

from pydantic import SecretStr

from sentinelflow.core.config import Settings
from sentinelflow.facades.ticketing_facade import make_ticketing
from sentinelflow.providers.ticketing.github_ticketing import GitHubTicketing
from sentinelflow.providers.ticketing.memory_ticketing import MemoryTicketing

SECRET = SecretStr("s" * 32)


def test_default_keeps_the_store() -> None:
    store = MemoryTicketing()
    assert make_ticketing(Settings(jwt_secret=SECRET), store) is store  # type: ignore[call-arg]


def test_github_backend_files_issues() -> None:
    settings = Settings(  # type: ignore[call-arg]
        jwt_secret=SECRET,
        ticketing_backend="github",
        github_repo="acme-sec/incidents",
        github_token=SecretStr("ghp_x"),
    )
    assert isinstance(make_ticketing(settings, MemoryTicketing()), GitHubTicketing)
