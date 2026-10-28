"""Contract every RunQueue implementation must satisfy (memory and Redis)."""

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest

from sentinelflow.contracts.run_queue import Delivery, RunQueue, StartRun
from sentinelflow.providers.queue.memory_queue import MemoryRunQueue
from sentinelflow.providers.queue.redis_queue import RedisRunQueue
from tests.builders import T0
from tests.contracts.redis_backend import fresh_redis
from tests.fakes.fake_clock import FakeClock

TIMEOUT = timedelta(seconds=60)
Factory = Callable[[FakeClock], RunQueue]
IMPLEMENTATIONS: list[Factory] = [
    lambda clock: MemoryRunQueue(clock, TIMEOUT),
    lambda clock: RedisRunQueue(fresh_redis(), clock, TIMEOUT),
]


def _cmd(n: int = 1) -> StartRun:
    return StartRun(f"run-{n}", "acme", "triage", "inc-1", "alt-1", "svc-orchestrator")


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(T0)


@pytest.fixture(params=IMPLEMENTATIONS)
def queue(request: pytest.FixtureRequest, clock: FakeClock) -> RunQueue:
    factory: Factory = request.param
    return factory(clock)


def test_published_command_is_claimed_once(queue: RunQueue) -> None:
    queue.publish(_cmd())
    [delivery] = queue.claim("w1", max_items=10)
    assert (delivery.command, delivery.attempt) == (_cmd(), 1)
    assert queue.claim("w2", max_items=10) == []


def test_claim_respects_max_items(queue: RunQueue) -> None:
    for n in range(3):
        queue.publish(_cmd(n))
    assert len(queue.claim("w1", max_items=2)) == 2


def test_unacked_delivery_is_redelivered_after_timeout(queue: RunQueue, clock: FakeClock) -> None:
    queue.publish(_cmd())
    queue.claim("w1", max_items=1)
    clock.advance(TIMEOUT - timedelta(seconds=1))
    assert queue.claim("w2", max_items=1) == []
    clock.advance(timedelta(seconds=1))
    [again] = queue.claim("w2", max_items=1)
    assert (again.command, again.attempt) == (_cmd(), 2)


def test_acked_delivery_is_never_redelivered(queue: RunQueue, clock: FakeClock) -> None:
    queue.publish(_cmd())
    [delivery] = queue.claim("w1", max_items=1)
    queue.ack(delivery)
    clock.advance(TIMEOUT * 2)
    assert queue.claim("w1", max_items=1) == []


def test_dead_lettered_delivery_is_kept_aside(queue: RunQueue, clock: FakeClock) -> None:
    queue.publish(_cmd())
    [delivery] = queue.claim("w1", max_items=1)
    queue.dead_letter(delivery, "poison")
    clock.advance(TIMEOUT * 2)
    assert queue.claim("w1", max_items=1) == []
    assert [(d.command, reason) for d, reason in queue.dead_letters()] == [(_cmd(), "poison")]


def test_claims_are_oldest_first(queue: RunQueue) -> None:
    for n in range(12):
        queue.publish(_cmd(n))
    claimed = [d.command for d in queue.claim("w1", max_items=12)]
    assert claimed == [_cmd(n) for n in range(12)]


def test_concurrent_consumers_never_share_a_delivery(queue: RunQueue) -> None:
    for n in range(30):
        queue.publish(_cmd(n))

    def claim(worker: int) -> Sequence[Delivery]:
        return queue.claim(f"w{worker}", max_items=3)

    with ThreadPoolExecutor(max_workers=6) as pool:
        batches = list(pool.map(claim, range(12)))
    ids = [d.id for batch in batches for d in batch]
    assert len(ids) == len(set(ids)) == 30


def test_depth_counts_messages_not_yet_acked(queue: RunQueue) -> None:
    for n in range(3):
        queue.publish(_cmd(n))
    [first] = queue.claim("w1", max_items=1)
    assert queue.depth() == 3
    queue.ack(first)
    assert queue.depth() == 2
