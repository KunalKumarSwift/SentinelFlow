"""Tests for id generation and its sequential test fake."""

import pytest

from sentinelflow.core.ids import IdFactory, UuidIdFactory
from tests.fakes.fake_ids import SequentialIdFactory


def test_uuid_ids_start_with_prefix() -> None:
    assert UuidIdFactory().new_id("inc").startswith("inc-")


def test_uuid_ids_are_unique() -> None:
    factory = UuidIdFactory()
    assert len({factory.new_id("inc") for _ in range(100)}) == 100


@pytest.mark.parametrize("prefix", ["", "INC", "in-c", "x" * 13])
def test_uuid_ids_reject_invalid_prefix(prefix: str) -> None:
    with pytest.raises(ValueError, match="prefix"):
        UuidIdFactory().new_id(prefix)


def test_sequential_ids_count_per_prefix() -> None:
    factory: IdFactory = SequentialIdFactory()
    ids = [factory.new_id("inc"), factory.new_id("alt"), factory.new_id("inc")]
    assert ids == ["inc-0001", "alt-0001", "inc-0002"]
