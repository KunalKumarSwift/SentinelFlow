"""RSA keys and Keycloak-shaped tokens for OIDC tests (generated per test run)."""

import json
from collections.abc import Mapping
from functools import cache

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from tests.builders import T0

ISSUER = "http://keycloak:8080/realms/sentinelflow"
AUDIENCE = "sentinelflow-api"


@cache
def private_key(name: str = "k1") -> rsa.RSAPrivateKey:
    """Return a 2048-bit test key, one per name."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def jwks(*kids: str) -> dict[str, object]:
    """Return a JWKS document publishing the public halves of ``kids``."""
    keys: list[object] = []
    for kid in kids:
        jwk = json.loads(RSAAlgorithm.to_jwk(private_key(kid).public_key()))
        keys.append({**jwk, "kid": kid, "use": "sig", "alg": "RS256"})
    return {"keys": keys}


def claims(**changes: object) -> dict[str, object]:
    """Return claims like Keycloak issues for an L2 analyst of tenant ``acme``."""
    base: dict[str, object] = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": "f1e2d3c4",
        "iat": int(T0.timestamp()),
        "exp": int(T0.timestamp()) + 300,
        "tenant_id": "acme",
        "team": "soc-emea",
        "realm_access": {"roles": ["soc-analyst-l2", "offline_access", "default-roles-x"]},
    }
    return {**base, **changes}


def token(payload: Mapping[str, object], kid: str = "k1", alg: str = "RS256") -> str:
    """Sign ``payload`` with key ``kid``."""
    return jwt.encode(dict(payload), private_key(kid), algorithm=alg, headers={"kid": kid})
