"""The atomic claim step of ``RedisRunQueue`` and the parser for its reply."""

from typing import cast

# KEYS: visible zset, attempts hash, payload hash. ARGV: now, new deadline, max, consumer.
# Moves each visible message's deadline forward and bumps its attempt count in one step,
# so two workers can never claim the same message.
CLAIM_SCRIPT = """
local ids = redis.call('ZRANGEBYSCORE', KEYS[1], '-inf', ARGV[1], 'LIMIT', 0, ARGV[3])
local out = {}
for _, id in ipairs(ids) do
  redis.call('ZADD', KEYS[1], ARGV[2], id)
  local n = redis.call('HINCRBY', KEYS[2], id, 1)
  table.insert(out, id)
  table.insert(out, n)
  table.insert(out, redis.call('HGET', KEYS[3], id))
end
return out
"""


def parse_claimed(reply: object) -> list[tuple[str, int, str]]:
    """Turn the script's flat ``[id, attempts, payload, ...]`` reply into triples.

    Raises:
        ValueError: If the reply does not have the expected shape.
    """
    if not isinstance(reply, list):
        raise ValueError("claim reply must be a list")
    items = cast(list[object], reply)
    if len(items) % 3:
        raise ValueError("claim reply must hold id, attempts, payload triples")
    triples = zip(items[0::3], items[1::3], items[2::3], strict=True)
    return [(_text(i), _count(n), _text(p)) for i, n, p in triples]


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"claim reply: expected text, got {type(value).__name__}")
    return value


def _count(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"claim reply: expected integer, got {type(value).__name__}")
    return value
