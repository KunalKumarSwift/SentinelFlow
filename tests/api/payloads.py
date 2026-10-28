"""Request bodies shared by API tests."""

ALERT = {
    "source": "simulator",
    "rule_id": "brute_force_success",
    "title": "Successful login after repeated failures",
    "observed_at": "2026-01-01T09:00:00Z",
    "entities": {"user": "alice", "ip": "203.0.113.9"},
    "raw": {"failed_attempts": "42"},
}
