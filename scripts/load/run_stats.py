"""Summarise workflow runs after a load test: status counts and worker throughput.

uv run python scripts/load/run_stats.py postgresql://user:pass@localhost:5432/db
"""

import sys

import psycopg

_SQL = (
    "select status, count(*), min(updated_at), max(updated_at)"
    " from workflow_runs group by status order by status"
)


def main(url: str) -> None:
    """Print per-status counts and, for finished runs, runs per second."""
    with psycopg.connect(url) as conn:
        rows = conn.execute(_SQL).fetchall()
    for status, count, first, last in rows:
        span = (last - first).total_seconds()
        rate = f"{count / span:.1f} runs/s over {span:.0f} s" if span > 0 else "-"
        print(f"{status:<10} {count:>6}  {rate}")


if __name__ == "__main__":
    main(sys.argv[1])
