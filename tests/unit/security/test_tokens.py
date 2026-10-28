"""Tests for issuing and verifying HS256 access tokens."""

import json
from datetime import timedelta

import jwt
import pytest

from sentinelflow.domain.errors import AuthenticationError
from sentinelflow.domain.principals import Principal, PrincipalKind
from sentinelflow.security.tokens import Hs256TokenService
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock

SECRET = "k" * 32
SHORT_SECRET = "s" * 5
OTHER_SECRET = "x" * 32
ALICE = Principal("u-alice", "acme", "soc-emea", frozenset({"soc-analyst-l1"}))
BOT = Principal("svc-sim", "acme", "ops", frozenset({"alert-source"}), PrincipalKind.SERVICE)


def _service(clock: FakeClock | None = None, secret: str = SECRET) -> Hs256TokenService:
    return Hs256TokenService(secret=secret, clock=clock or FakeClock(T0))


def _forge(claims: dict[str, object], secret: str = SECRET) -> str:
    """Sign raw claims with HS256, bypassing PyJWT's encode-side claim checks."""
    base: dict[str, object] = {
        "sub": "u-alice",
        "tenant_id": "acme",
        "team": "soc-emea",
        "roles": ["soc-analyst-l1"],
        "kind": "user",
        "iss": "sentinelflow",
        "iat": int(T0.timestamp()),
        "exp": int((T0 + timedelta(minutes=5)).timestamp()),
    }
    payload = json.dumps(base | claims).encode()
    return jwt.PyJWS().encode(payload, secret, algorithm="HS256")  # pyright: ignore[reportUnknownMemberType]


@pytest.mark.parametrize("principal", [ALICE, BOT])
def test_issued_token_round_trips_to_same_principal(principal: Principal) -> None:
    service = _service()
    assert service.verify(service.issue(principal)) == principal


def test_token_is_rejected_after_expiry() -> None:
    clock = FakeClock(T0)
    service = _service(clock)
    token = service.issue(ALICE)
    clock.advance(timedelta(minutes=15, seconds=1))
    with pytest.raises(AuthenticationError, match="expired"):
        service.verify(token)


def test_token_signed_with_other_secret_is_rejected() -> None:
    token = _service(secret=OTHER_SECRET).issue(ALICE)
    with pytest.raises(AuthenticationError, match="signature"):
        _service().verify(token)


def test_unsigned_alg_none_token_is_rejected() -> None:
    token = jwt.PyJWS().encode(b'{"sub": "u-alice"}', key=None, algorithm="none")  # pyright: ignore[reportUnknownMemberType]
    with pytest.raises(AuthenticationError):
        _service().verify(token)


@pytest.mark.parametrize("claim", ["sub", "tenant_id", "team", "roles", "kind", "exp", "iss"])
def test_missing_claim_is_rejected(claim: str) -> None:
    token = _forge({claim: None})
    with pytest.raises(AuthenticationError):
        _service().verify(token)


def test_wrong_issuer_is_rejected() -> None:
    with pytest.raises(AuthenticationError, match="issuer"):
        _service().verify(_forge({"iss": "evil"}))


def test_long_lived_token_is_rejected() -> None:
    token = _forge({"exp": int((T0 + timedelta(hours=8)).timestamp())})
    with pytest.raises(AuthenticationError, match="lifetime"):
        _service().verify(token)


def test_roles_must_be_a_list_of_strings() -> None:
    with pytest.raises(AuthenticationError, match="roles"):
        _service().verify(_forge({"roles": "platform-admin"}))


def test_garbage_is_rejected() -> None:
    with pytest.raises(AuthenticationError):
        _service().verify("not-a-jwt")


def test_short_secret_is_refused() -> None:
    with pytest.raises(ValueError, match="32"):
        _service(secret=SHORT_SECRET)


def test_ttl_longer_than_maximum_is_refused() -> None:
    with pytest.raises(ValueError, match="ttl"):
        Hs256TokenService(secret=SECRET, clock=FakeClock(T0), ttl=timedelta(hours=1))


def test_non_integer_timestamps_are_rejected() -> None:
    with pytest.raises(AuthenticationError, match="integers"):
        _service().verify(_forge({"iat": "yesterday"}))


def test_unknown_principal_kind_is_rejected() -> None:
    with pytest.raises(AuthenticationError, match="kind"):
        _service().verify(_forge({"kind": "superuser"}))
