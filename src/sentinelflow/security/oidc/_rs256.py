"""Typed adapter around PyJWT for RS256 tokens (all PyJWT calls for OIDC live here).

PyJWT's annotations reference optional ``cryptography`` types that strict pyright
reports as unknown; keeping the calls here confines the ignores to one file.
"""

from collections.abc import Mapping, Sequence

import jwt
from jwt.types import Options

ALGORITHM = "RS256"
InvalidTokenError = jwt.InvalidTokenError
InvalidAudienceError = jwt.InvalidAudienceError
InvalidIssuerError = jwt.InvalidIssuerError


def key_id(token: str) -> str | None:
    """Return the unverified ``kid`` header, used only to pick the verification key."""
    header: dict[str, object] = jwt.get_unverified_header(token)
    kid = header.get("kid")
    return kid if isinstance(kid, str) else None


def parse_jwks(document: Mapping[str, object]) -> dict[str, jwt.PyJWK]:
    """Return the RSA signing keys of a JWKS document by ``kid``; others are ignored."""
    keys = jwt.PyJWKSet.from_dict(dict(document)).keys  # pyright: ignore[reportUnknownMemberType] -- see module docstring
    return {k.key_id: k for k in keys if k.key_id and k.key_type == "RSA"}


def decode(
    token: str, key: jwt.PyJWK, issuer: str, audience: str, required: Sequence[str]
) -> dict[str, object]:
    """Verify an RS256 signature, issuer and audience; time checks are the caller's.

    Raises:
        jwt.InvalidTokenError: Or a subclass, for any invalid token.
    """
    options: Options = {"verify_exp": False, "verify_iat": False, "require": list(required)}
    decoded: dict[str, object] = jwt.decode(  # pyright: ignore[reportUnknownMemberType] -- see module docstring
        token, key, algorithms=[ALGORITHM], issuer=issuer, audience=audience, options=options
    )
    return decoded
