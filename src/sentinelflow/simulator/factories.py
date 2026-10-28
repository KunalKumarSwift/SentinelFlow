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
