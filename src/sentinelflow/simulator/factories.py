"""Small random building blocks shared by scenarios.

External addresses come from the documentation ranges (RFC 5737) so generated data
can never point at a real host.
"""

from datetime import datetime, timedelta
from random import Random

USERS = ("alice", "bob", "chen", "dana", "emeka", "farah", "goran", "hana")
COUNTRIES = ("IN", "DE", "US", "BR", "JP", "GB", "AU", "ZA")
DEPARTMENTS = ("finance", "engineering", "sales", "hr")


def pick_user(rng: Random) -> str:
    """Return a random user id from the fixed directory."""
    return rng.choice(USERS)


def external_ip(rng: Random) -> str:
    """Return a random address from 203.0.113.0/24 (TEST-NET-3)."""
    return f"203.0.113.{rng.randint(1, 254)}"


def vpn_egress_ip(rng: Random) -> str:
    """Return a random corporate VPN egress address in 10.8.0.0/24."""
    return f"10.8.0.{rng.randint(1, 254)}"


def spread(start: datetime, count: int, every: timedelta) -> tuple[datetime, ...]:
    """Return ``count`` timestamps beginning at ``start``, ``every`` apart."""
    return tuple(start + every * i for i in range(count))


def host_name(rng: Random) -> str:
    """Return a random workstation name such as ``wks-0042``."""
    return f"wks-{rng.randint(1, 9999):04d}"


def access_key_id(rng: Random) -> str:
    """Return a random, obviously fake cloud access key id."""
    return "AKIAFAKE" + "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567") for _ in range(12))


def lure_url(rng: Random) -> str:
    """Return a phishing URL under the reserved ``.example`` domain."""
    return f"https://login-verify-{rng.randint(100, 999)}.example/session"


def message_id(rng: Random) -> str:
    """Return a random e-mail message id."""
    return f"msg-{rng.randint(10**7, 10**8 - 1)}"
