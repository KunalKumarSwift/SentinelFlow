"""Name → scenario function lookup used by the CLI and by tests."""

from collections.abc import Callable, Mapping
from types import MappingProxyType

from sentinelflow.simulator.context import ScenarioContext
from sentinelflow.simulator.output import ScenarioOutput
from sentinelflow.simulator.scenarios import benign_travel, brute_force

Scenario = Callable[[ScenarioContext], ScenarioOutput]

SCENARIOS: Mapping[str, Scenario] = MappingProxyType(
    {
        "brute_force": brute_force.generate,
        "benign_travel": benign_travel.generate,
    }
)
