# ADR 0008 — Redis run queue as a sorted set of visibility deadlines

**Status:** Accepted (supersedes the "Redis Streams + consumer group" plan in LLD 07)

## Context
The plan was Redis Streams with a consumer group and `XAUTOCLAIM` to re-claim the work of
crashed workers. `XAUTOCLAIM` decides that a message is stale using the **Redis server's**
clock, so the shared `RunQueue` contract tests (which advance an injected `FakeClock`)
cannot run against it without sleeping in real time. Our needs are modest: at-least-once
delivery, a visibility timeout, a dead-letter list and no double claims.

## Decision
`RedisRunQueue` keeps a sorted set of message id → "claimable from" timestamp, plus hashes
for payloads and attempt counts and a list for dead letters. A claim is one Lua script:
pick visible ids oldest-first, push their deadline `timeout` into the future and increment
their attempt count, so concurrent workers never share a delivery. Time comes from the
injected `Clock`. Commands are JSON with a `type` tag and are validated on decode.

## Consequences
- ✅ The memory and Redis queues pass the **same** contract tests, including redelivery
  after the timeout, ordering, dead-lettering and concurrent claims.
- ✅ Crash recovery needs no separate re-claim loop: an unacked message simply becomes
  visible again.
- ⚠️ Worker clocks must be roughly in sync (NTP); skew shortens or lengthens the timeout.
- ⚠️ No consumer-group introspection (`XPENDING`); the `:visible` set and `:attempts` hash
  answer the same questions.
