"""Run commands survive a JSON round trip; anything else is rejected."""

import json

import pytest

from sentinelflow.contracts.run_queue import ResumeRun, RunCommand, StartRun
from sentinelflow.providers.queue.command_codec import decode_command, encode_command

COMMANDS: list[RunCommand] = [
    StartRun("run-1", "acme", "triage", "inc-1", "alt-1", "svc-orchestrator"),
    ResumeRun("run-1", "acme", "apr-1"),
]


@pytest.mark.parametrize("command", COMMANDS)
def test_round_trip(command: RunCommand) -> None:
    assert decode_command(encode_command(command)) == command


@pytest.mark.parametrize(
    "payload",
    [
        json.dumps({"type": "delete_everything", "run_id": "r"}),
        json.dumps({"type": "resume", "run_id": "r"}),
        json.dumps({"type": "resume", "run_id": 1, "tenant_id": "a", "approval_id": "b"}),
        json.dumps(["not", "an", "object"]),
    ],
)
def test_malformed_payload_is_rejected(payload: str) -> None:
    with pytest.raises(ValueError, match="command"):
        decode_command(payload)
