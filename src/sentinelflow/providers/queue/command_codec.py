"""JSON encoding of run commands for out-of-process queues.

Commands carry ids only, so the payload is small and holds nothing sensitive. Decoding
validates every field: a queue entry is input from outside this process.
"""

import json
from dataclasses import asdict
from typing import cast

from sentinelflow.contracts.run_queue import ResumeRun, RunCommand, StartRun

_TYPES: dict[str, type[StartRun] | type[ResumeRun]] = {"start": StartRun, "resume": ResumeRun}


def encode_command(command: RunCommand) -> str:
    """Return ``command`` as a JSON object tagged with its type."""
    kind = "start" if isinstance(command, StartRun) else "resume"
    return json.dumps({"type": kind, **asdict(command)}, sort_keys=True)


def decode_command(payload: str) -> RunCommand:
    """Parse a payload produced by ``encode_command``.

    Raises:
        ValueError: If the payload is not a well-formed command.
    """
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("command payload must be a JSON object")
    fields = cast(dict[str, object], data)
    cls = _TYPES.get(str(fields.pop("type", "")))
    if cls is None or not all(isinstance(v, str) for v in fields.values()):
        raise ValueError(f"malformed command payload: {sorted(fields)}")
    try:
        return cls(**{k: str(v) for k, v in fields.items()})
    except TypeError as exc:
        raise ValueError(f"malformed command payload: {sorted(fields)}") from exc
