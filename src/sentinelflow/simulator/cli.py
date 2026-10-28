"""``sentinelflow-sim``: generate a scenario and post its alerts to a running API.

    sentinelflow-sim run brute_force --seed 42 --api http://127.0.0.1:8000

The CLI obtains an ``alert-source`` token from the dev-token endpoint, so it only
works against an API started with ``APP_ENV=dev``.
"""

import argparse
import sys
from collections.abc import Sequence
from random import Random

import httpx

from sentinelflow.core.clock import SystemClock
from sentinelflow.core.ids import UuidIdFactory
from sentinelflow.simulator.context import ScenarioContext
from sentinelflow.simulator.payload import alert_payload
from sentinelflow.simulator.registry import SCENARIOS

_SIM_IDENTITY = {"subject": "svc-simulator", "team": "ops", "roles": ["alert-source"]}


def main(argv: Sequence[str], transport: httpx.BaseTransport | None = None) -> int:
    """Run the CLI; ``transport`` lets tests replace the network."""
    args = _parse(argv)
    ctx = ScenarioContext(Random(args.seed), SystemClock(), UuidIdFactory(), args.tenant)
    output = SCENARIOS[args.scenario](ctx)
    with httpx.Client(base_url=args.api, transport=transport, timeout=10) as client:
        headers = _auth_headers(client, args.tenant)
        for alert in output.alerts:
            response = client.post("/v1/alerts", json=alert_payload(alert), headers=headers)
            response.raise_for_status()
            print(f"{args.scenario}: {alert.rule_id} -> {response.json()}")
    return 0


def run() -> None:
    """Console-script entry point."""
    sys.exit(main(sys.argv[1:]))


def _auth_headers(client: httpx.Client, tenant: str) -> dict[str, str]:
    identity = {**_SIM_IDENTITY, "tenant_id": tenant, "kind": "service"}
    response = client.post("/v1/auth/dev-token", json=identity)
    response.raise_for_status()
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _parse(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="sentinelflow-sim", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run_cmd = commands.add_parser("run", help="post one scenario's alerts")
    run_cmd.add_argument("scenario", choices=sorted(SCENARIOS))
    run_cmd.add_argument("--seed", type=int, default=42)
    run_cmd.add_argument("--api", default="http://127.0.0.1:8000")
    run_cmd.add_argument("--tenant", default="acme")
    return parser.parse_args(argv)
