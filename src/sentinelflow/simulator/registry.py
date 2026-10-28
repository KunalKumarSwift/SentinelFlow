"""Name → scenario function lookup used by the CLI and by tests."""

from collections.abc import Callable, Mapping
from types import MappingProxyType

from sentinelflow.simulator.context import ScenarioContext
from sentinelflow.simulator.output import ScenarioOutput
from sentinelflow.simulator.scenarios import (
    benign_travel,
    brute_force,
    exfiltration,
    impossible_travel,
    leaked_key,
    phishing,
    powershell,
    prompt_injection,
)

Scenario = Callable[[ScenarioContext], ScenarioOutput]

SCENARIOS: Mapping[str, Scenario] = MappingProxyType(
    {
        "brute_force": brute_force.generate,
        "benign_travel": benign_travel.generate,
        "prompt_injection": prompt_injection.generate,
        "impossible_travel": impossible_travel.generate,
        "leaked_key": leaked_key.generate,
        "phishing": phishing.generate,
        "powershell": powershell.generate,
        "exfiltration": exfiltration.generate,
    }
)
