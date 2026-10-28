"""JWKS download: a document with keys is returned; anything else is a provider error."""

import httpx
import pytest

from sentinelflow.domain.errors import ProviderError
from sentinelflow.providers.identity.jwks_http import HttpJwksFetcher

URL = "http://keycloak:8080/realms/sentinelflow/protocol/openid-connect/certs"


def _fetch(response: httpx.Response) -> dict[str, object]:
    return HttpJwksFetcher(URL, httpx.MockTransport(lambda _: response))()


def test_document_with_keys_is_returned() -> None:
    assert _fetch(httpx.Response(200, json={"keys": []})) == {"keys": []}


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(503),
        httpx.Response(200, text="<html>login</html>"),
        httpx.Response(200, json=["not", "an", "object"]),
        httpx.Response(200, json={"no": "keys"}),
    ],
)
def test_anything_else_is_a_provider_error(response: httpx.Response) -> None:
    with pytest.raises(ProviderError, match="JWKS"):
        _fetch(response)
