"""One way to open a Redis client, so every Redis-backed provider decodes the same way."""

from redis import Redis


def open_redis(url: str) -> Redis:
    """Return a lazily-connecting client whose replies are ``str``, not ``bytes``."""
    return Redis.from_url(url, decode_responses=True)  # pyright: ignore[reportUnknownMemberType] -- untyped **kwargs
