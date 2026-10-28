# Benchmarks

Measured on 2026-10-28 to show what the **platform** costs (API, policy, audit chain,
queue, checkpoints, Postgres writes), not LLM latency: `LLM_BACKEND=none`, so triage
fails safe to `needs_review` and investigation uses playbook defaults. Each run executes
the full lifecycle up to the approval pause: triage → investigation → two approval
requests → checkpoint → run `waiting`.

## Set-up

| Item | Value |
|---|---|
| Machine | 1 VM, 4 vCPU (Xeon @ 2.8 GHz), 15 GB RAM |
| Processes | 1 × `sentinelflow-api` (`RUN_WORKER_IN_API=false`), N × `sentinelflow-worker` |
| State | PostgreSQL 16 and Redis 7 **on the same VM** (competing for the same 4 vCPUs) |
| Config | `STORAGE_BACKEND=postgres`, `QUEUE_BACKEND=redis`, JSON logs, metrics on |

## 1. API under mixed load (Locust)

`uv run locust -f scripts/load/locustfile.py --headless -u 20 -r 5 -t 60s` with 4 workers
running. 20 users; each posts a never-seen brute-force alert (weight 3) or lists incidents
(weight 1), pausing 0.5–1.5 s between requests.

| Endpoint | Requests | Failures | Median | p95 | p99 |
|---|---|---|---|---|---|
| `POST /v1/alerts` | 865 | 0 | 20 ms | 68 ms | 98 ms |
| `GET /v1/incidents` | 282 | 0 | 32 ms | 69 ms | 97 ms |
| All | 1 187 (19.8 req/s) | 0 | 21 ms | 69 ms | 100 ms |

All 713 runs started during the test reached `waiting` within the test window, with an empty
queue and no dead letters, so the workers kept up with ingest. 865 alerts made 713 runs
because alerts whose user/IP fingerprint matched an open incident were deduplicated into it.

## 2. Worker throughput (backlog drain)

Workers stopped, ~400–440 runs queued, then N workers started; time until the queue is
empty (`scripts/load/run_stats.py` reports runs/s between the first and last finished run;
the wall-clock figure also includes process start-up).

| Workers | Runs | Wall clock | Throughput |
|---|---|---|---|
| 1 | 438 | 26.5 s | **18.1 runs/s** |
| 2 | 392 | 13.8 s | **33.3 runs/s** |
| 4 | 390 | 8.8 s | **54.7 runs/s** |

Scaling is near-linear up to the core count even though Postgres and Redis share the same
four vCPUs. The roadmap target, 1 000 alerts in 60 s with 4 workers (~17 runs/s), is met
with about 3× headroom.

## 3. What the load test found

Starting the API and four workers at the same moment crashed one worker at start-up:
concurrent `CREATE TABLE IF NOT EXISTS` statements race inside PostgreSQL's catalog
(`UniqueViolation` on `pg_type`). Schema set-up now takes an advisory lock. LangGraph's
checkpointer migrations needed a **polling** try-lock instead, because their
`CREATE INDEX CONCURRENTLY` waits for every open transaction, including a waiter blocked
in `pg_advisory_lock`, which deadlocks without Postgres noticing. Both are covered by
`tests/contracts/test_schema_setup.py`.

## Caveats

- With a real model, LLM latency dominates (seconds per call). Workers are I/O-bound then,
  so run more workers per core and budget the provider's rate limit.
- `GET /v1/incidents` returns every incident of the tenant (no pagination yet), so its
  latency grows with the table. Cursor pagination is on the API roadmap.
- One VM, one run per configuration: treat the numbers as indicative, not as a capacity plan.

## Reproduce

```bash
# terminal 1-5: API + workers against local Postgres/Redis (or `docker compose up --scale worker=4`)
RUN_WORKER_IN_API=false STORAGE_BACKEND=postgres QUEUE_BACKEND=redis ... uv run sentinelflow-api
METRICS_PORT=9201 ... uv run sentinelflow-worker      # x4, distinct METRICS_PORT
# load
uv run locust -f scripts/load/locustfile.py --headless -u 20 -r 5 -t 60s --host http://127.0.0.1:8000
uv run python scripts/load/run_stats.py "$DATABASE_URL"
```
