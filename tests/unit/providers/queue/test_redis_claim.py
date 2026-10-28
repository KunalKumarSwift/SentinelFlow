"""The claim reply parser accepts well-formed replies and rejects anything else."""

import pytest

from sentinelflow.providers.queue.redis_claim import parse_claimed


def test_flat_reply_becomes_triples() -> None:
    assert parse_claimed(["m1", 1, "{}", "m2", 3, "[]"]) == [("m1", 1, "{}"), ("m2", 3, "[]")]


@pytest.mark.parametrize(
    "reply", ["m1", ["m1", 1], [1, 1, "{}"], ["m1", "1", "{}"], ["m1", True, "{}"]]
)
def test_malformed_reply_is_rejected(reply: object) -> None:
    with pytest.raises(ValueError, match="claim reply"):
        parse_claimed(reply)
