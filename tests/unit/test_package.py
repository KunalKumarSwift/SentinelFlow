"""Smoke test: the package is installed and exposes its version."""

import sentinelflow


def test_package_exposes_version() -> None:
    assert sentinelflow.__version__ == "0.1.0"
