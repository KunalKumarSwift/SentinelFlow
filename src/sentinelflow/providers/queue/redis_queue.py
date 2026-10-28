# redis-py leaves some **kwargs / shard_hint parameters untyped.
# pyright: reportUnknownMemberType=false
"""Run queue on Redis: at-least-once delivery with a visibility timeout.

Layout under ``prefix`` (default ``sf:runs``):

* ``:visible`` sorted set: message id → epoch-ms from which it may be claimed
* ``:payload`` / ``:attempts`` hashes: message id → encoded command / claim count
* ``:dlq`` list of dead-lettered entries; ``:seq`` counter for ordered ids

Claiming is one Lua script, so concurrent workers never receive the same delivery.
Visibility uses the injected clock rather than Redis time, which keeps the contract
tests deterministic (see ADR 0008).
"""

import json
from collections.abc import Sequence
from datetime import timedelta
from typing import cast

from redis import Redis

from sentinelflow.contracts.run_queue import Delivery, RunCommand
from sentinelflow.core.clock import Clock
from sentinelflow.providers.queue.command_codec import decode_command, encode_command
from sentinelflow.providers.queue.redis_claim import CLAIM_SCRIPT, parse_claimed


class RedisRunQueue:
    """``RunQueue`` shared by every API process and worker that points at one Redis."""

    def __init__(
        self, client: Redis, clock: Clock, timeout: timedelta, prefix: str = "sf:runs"
    ) -> None:
        """Use ``client`` (``decode_responses=True``); redeliver after ``timeout``."""
        self._r, self._clock, self._timeout_ms = client, clock, _ms(timeout)
        self._k = {n: f"{prefix}:{n}" for n in ("visible", "payload", "attempts", "dlq", "seq")}
        self._claim = client.register_script(CLAIM_SCRIPT)

    def publish(self, command: RunCommand) -> None:
        """Make ``command`` claimable now."""
        msg_id = f"msg-{self._r.incr(self._k['seq']):012d}"
        with self._r.pipeline() as tx:
            tx.hset(self._k["payload"], msg_id, encode_command(command))
            tx.zadd(self._k["visible"], {msg_id: self._now_ms()})
            tx.execute()

    def claim(self, consumer: str, max_items: int) -> Sequence[Delivery]:
        """Atomically claim up to ``max_items`` visible messages, oldest first."""
        now = self._now_ms()
        keys = [self._k["visible"], self._k["attempts"], self._k["payload"]]
        raw = self._claim(keys=keys, args=[now, now + self._timeout_ms, max_items, consumer])
        return [Delivery(i, decode_command(p), n) for i, n, p in parse_claimed(raw)]

    def ack(self, delivery: Delivery) -> None:
        """Forget the message for good."""
        self._forget(delivery.id)

    def dead_letter(self, delivery: Delivery, reason: str) -> None:
        """Move the message to the dead-letter list with ``reason``."""
        entry = {
            "id": delivery.id,
            "attempt": delivery.attempt,
            "reason": reason,
            "command": encode_command(delivery.command),
        }
        self._r.rpush(self._k["dlq"], json.dumps(entry))
        self._forget(delivery.id)

    def dead_letters(self) -> Sequence[tuple[Delivery, str]]:
        """Return dead-lettered messages with reasons, oldest first."""
        entries = cast(list[str], self._r.lrange(self._k["dlq"], 0, -1))
        return [_dead(json.loads(e)) for e in entries]

    def _forget(self, msg_id: str) -> None:
        with self._r.pipeline() as tx:
            tx.zrem(self._k["visible"], msg_id)
            tx.hdel(self._k["payload"], msg_id)
            tx.hdel(self._k["attempts"], msg_id)
            tx.execute()

    def _now_ms(self) -> int:
        return int(self._clock.now().timestamp() * 1000)


def _ms(delta: timedelta) -> int:
    return int(delta.total_seconds() * 1000)


def _dead(entry: dict[str, object]) -> tuple[Delivery, str]:
    command = decode_command(str(entry["command"]))
    delivery = Delivery(str(entry["id"]), command, int(str(entry["attempt"])))
    return delivery, str(entry["reason"])
