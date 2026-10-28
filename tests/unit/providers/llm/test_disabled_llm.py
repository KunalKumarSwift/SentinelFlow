"""LLM_BACKEND=none: every call fails permanently, so triage routes to humans."""

import pytest

from sentinelflow.contracts.llm import Prompt
from sentinelflow.domain.errors import ProviderError
from sentinelflow.providers.llm.disabled_llm import DisabledLLM
from tests.unit.providers.llm.test_invoke import Answer


def test_disabled_llm_raises_permanent_error() -> None:
    with pytest.raises(ProviderError, match="no LLM configured") as info:
        DisabledLLM().structured(Prompt("p", "S", "I"), Answer)
    assert info.value.retryable is False
