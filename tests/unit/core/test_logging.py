"""Logging helpers: bound context reaches every line; correlation ids are validated."""

import json

import pytest
import structlog

from sentinelflow.core.logging import (
    bound,
    configure_logging,
    get_logger,
    valid_correlation_id,
)
from tests.fakes.log_capture import capture_logs


def test_bound_context_is_added_to_lines_and_removed_after() -> None:
    with capture_logs() as logs:
        with bound(run_id="run-1", tenant_id="acme"):
            get_logger("t").info("inside")
        get_logger("t").info("outside")
    inside, outside = logs.named("inside")[0], logs.named("outside")[0]
    assert (inside["run_id"], inside["tenant_id"]) == ("run-1", "acme")
    assert "run_id" not in outside


@pytest.mark.parametrize(
    ("value", "ok"),
    [("abc-123_X", True), ("", False), ("x" * 65, False), ("a b", False), ("a\nb", False)],
)
def test_correlation_ids_are_validated(value: str, ok: bool) -> None:
    assert valid_correlation_id(value) is ok


def test_json_output_is_one_object_per_line(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(json_lines=True)
    try:
        with bound(tenant_id="acme"):
            get_logger("t").info("hello", n=1)
    finally:
        structlog.reset_defaults()
    line = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert (line["event"], line["tenant_id"], line["n"], line["level"]) == (
        "hello",
        "acme",
        1,
        "info",
    )
    assert "timestamp" in line
