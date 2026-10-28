"""The HTTP surface the UI client needs, so ``httpx.Client`` and test clients both fit."""

from collections.abc import Mapping
from typing import Protocol


class Response(Protocol):
    """The parts of an HTTP response the client reads."""

    @property
    def status_code(self) -> int:
        """HTTP status."""
        ...

    @property
    def is_error(self) -> bool:
        """Whether the status is 4xx/5xx."""
        ...

    @property
    def content(self) -> bytes:
        """Raw body."""
        ...

    def json(self) -> object:
        """Parsed JSON body."""
        ...


class Http(Protocol):
    """An HTTP client bound to the API base URL (``httpx.Client`` or a test client)."""

    def get(
        self,
        url: str,
        *,
        params: Mapping[str, int] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        """Send a GET request."""
        ...

    def post(
        self, url: str, *, json: object = None, headers: Mapping[str, str] | None = None
    ) -> Response:
        """Send a POST request with a JSON body."""
        ...
