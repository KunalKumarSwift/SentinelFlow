"""Download the identity provider's JSON Web Key Set over HTTPS."""

from typing import cast

import httpx

from sentinelflow.domain.errors import ProviderError


class HttpJwksFetcher:
    """Callable that returns the JWKS document at ``url``; failures are ``ProviderError``."""

    def __init__(self, url: str, transport: httpx.BaseTransport | None = None) -> None:
        """Fetch from ``url``; ``transport`` lets tests replace the network."""
        self._url, self._transport = url, transport

    def __call__(self) -> dict[str, object]:
        """Return the parsed JWKS document.

        Raises:
            ProviderError: If the IdP is unreachable or answers with something else.
        """
        try:
            with httpx.Client(transport=self._transport, timeout=5) as client:
                response = client.get(self._url)
                response.raise_for_status()
                document: object = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(f"JWKS fetch failed: {type(exc).__name__}", retryable=True) from exc
        if not isinstance(document, dict) or "keys" not in document:
            raise ProviderError("JWKS document has no 'keys'", retryable=False)
        return cast(dict[str, object], document)
