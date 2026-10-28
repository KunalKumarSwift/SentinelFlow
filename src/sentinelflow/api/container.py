"""Everything the API needs, built once by the composition root (or by tests)."""

from dataclasses import dataclass

from sentinelflow.security.tokens import Hs256TokenService


@dataclass(frozen=True, slots=True)
class ApiContainer:
    """Injected services for the HTTP layer.

    Attributes:
        app_env: ``"dev"`` enables the dev-token endpoint; any other value hides it.
    """

    app_env: str
    tokens: Hs256TokenService
