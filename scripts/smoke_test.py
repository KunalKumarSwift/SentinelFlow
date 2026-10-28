"""Smoke test for a running deployment: alert in → a worker pauses the run for approval.

    uv run python scripts/smoke_test.py --api http://127.0.0.1:8000

Exits 0 when the brute-force run reaches ``waiting`` (triaged, investigated, approvals
requested) within the timeout, 1 otherwise. Needs an API started with ``APP_ENV=dev``.
"""

import argparse
import sys
import time

import httpx

from sentinelflow.simulator.cli import main as simulate

ANALYST = {
    "subject": "u-smoke",
    "tenant_id": "acme",
    "team": "soc-emea",
    "roles": ["soc-analyst-l1"],
}


def wait_for_waiting_run(api: str, timeout: float) -> bool:
    """Post a brute-force alert and poll its run until it is ``waiting``."""
    with httpx.Client(base_url=api, timeout=10) as client:
        token = client.post("/v1/auth/dev-token", json=ANALYST).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        before = {i["id"] for i in client.get("/v1/incidents", headers=headers).json()["items"]}
        simulate(["run", "brute_force", "--api", api, "--seed", str(int(time.time()))])
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            items = client.get("/v1/incidents", headers=headers).json()["items"]
            fresh = [i for i in items if i["id"] not in before]
            if fresh and fresh[0]["status"] == "awaiting_approval":
                print(f"ok: {fresh[0]['id']} is awaiting approval")
                return True
            time.sleep(1)
    print("timed out waiting for the worker")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()
    sys.exit(0 if wait_for_waiting_run(args.api, args.timeout) else 1)
