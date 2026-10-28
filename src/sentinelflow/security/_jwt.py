"""Typed adapter around PyJWT, pinned to HS256.

PyJWT's annotations reference optional ``cryptography`` types that strict pyright
reports as unknown; keeping every PyJWT call here confines the ignores to one file.
"""

from collections.abc import Mapping, Sequence

import jwt
from jwt.types import Options

ALGORITHM = "HS256"
InvalidSignatureError = jwt.InvalidSignatureError
InvalidIssuerError = jwt.InvalidIssuerError
InvalidTokenError = jwt.InvalidTokenError


def encode(claims: Mapping[str, object], secret: str) -> str:
    """Sign ``claims`` with HS256 and return the compact JWT."""
    return jwt.encode(dict(claims), secret, algorithm=ALGORITHM)  # pyright: ignore[reportUnknownMemberType] -- see module docstring


def decode(token: str, secret: str, issuer: str, required: Sequence[str]) -> dict[str, object]:
    """Verify signature and issuer, require ``required`` claims; leave time checks to caller.

    Raises:
        jwt.InvalidTokenError: Or a subclass, for any invalid token.
    """
    options: Options = {"verify_exp": False, "verify_iat": False, "require": list(required)}
    decoded: dict[str, object] = jwt.decode(  # pyright: ignore[reportUnknownMemberType] -- see module docstring
        token, secret, algorithms=[ALGORITHM], issuer=issuer, options=options
    )
    return decoded
