"""Tests for turning scenarios into API calls."""

import json
import sys

import httpx
import pytest

from sentinelflow.simulator.cli import main, run
from sentinelflow.simulator.payload import alert_payload
from tests.builders import an_alert

ISSUED = "tok-123"


def test_payload_matches_api_schema_and_omits_tenant() -> None:
    payload = alert_payload(an_alert())
    assert payload == {
        "source": "simulator",
        "rule_id": "brute_force_success",
        "title": "Successful login after repeated failures",
        "observed_at": "2026-01-01T09:00:00+00:00",
        "entities": {"user": "alice", "ip": "203.0.113.9"},
        "raw": {"failed_attempts": "42"},
    }


def _transport(seen: list[httpx.Request]) -> httpx.MockTransport:
    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path == "/v1/auth/dev-token":
            return httpx.Response(200, json={"access_token": ISSUED})
        return httpx.Response(202, json={"incident_id": "inc-1", "deduplicated": False})

    return httpx.MockTransport(handle)


def test_run_gets_dev_token_then_posts_alerts(capsys: pytest.CaptureFixture[str]) -> None:
    seen: list[httpx.Request] = []
    code = main(["run", "brute_force", "--seed", "42", "--api", "http://api"], _transport(seen))
    assert code == 0
    assert [r.url.path for r in seen] == ["/v1/auth/dev-token", "/v1/alerts"]
    assert seen[1].headers["Authorization"] == f"Bearer {ISSUED}"
    assert json.loads(seen[1].content)["rule_id"] == "brute_force_success"
    assert "inc-1" in capsys.readouterr().out


def test_unknown_scenario_exits_with_error() -> None:
    with pytest.raises(SystemExit):
        main(["run", "nope"], _transport([]))


def test_console_entry_point_parses_process_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["sentinelflow-sim", "run", "nope"])
    with pytest.raises(SystemExit):
        run()
