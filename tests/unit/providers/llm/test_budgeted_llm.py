"""The budget decorator charges each call to the prompt's tenant and fails safe when spent."""

import pytest
from pydantic import BaseModel

from sentinelflow.contracts.llm import Prompt
from sentinelflow.domain.errors import BudgetExceededError, ProviderError
from sentinelflow.providers.budget.memory_token_budget import MemoryTokenBudget
from sentinelflow.providers.llm.budgeted_llm import OUTPUT_ALLOWANCE, BudgetedLLM, estimate_tokens
from tests.builders import T0
from tests.fakes.fake_clock import FakeClock
from tests.fakes.fake_llm import FakeLLM
from tests.fakes.fake_metrics import RecordingMetrics


class Answer(BaseModel):
    value: int


PROMPT = Prompt("p", "S" * 40, "I" * 40, {"x": "U" * 20}, tenant_id="acme")


def test_estimate_counts_prompt_characters_and_an_output_allowance() -> None:
    assert estimate_tokens(PROMPT) == 100 // 4 + OUTPUT_ALLOWANCE


def test_call_within_budget_is_passed_through() -> None:
    llm = BudgetedLLM(FakeLLM({"p": {"value": 1}}), MemoryTokenBudget(FakeClock(T0)), 10_000)
    assert llm.structured(PROMPT, Answer) == Answer(value=1)


def test_call_over_budget_is_refused_without_reaching_the_model() -> None:
    inner = FakeLLM({"p": {"value": 1}})
    llm = BudgetedLLM(inner, MemoryTokenBudget(FakeClock(T0)), estimate_tokens(PROMPT) - 1)
    with pytest.raises(BudgetExceededError, match="acme") as caught:
        llm.structured(PROMPT, Answer)
    assert inner.prompts == [] and isinstance(caught.value, ProviderError)
    assert caught.value.retryable is False


def test_prompt_without_tenant_is_charged_to_an_unattributed_bucket() -> None:
    budget = MemoryTokenBudget(FakeClock(T0))
    llm = BudgetedLLM(FakeLLM({"p": {"value": 1}}), budget, estimate_tokens(PROMPT))
    llm.structured(Prompt("p", "S" * 40, "I" * 40, {"x": "U" * 20}), Answer)
    assert not budget.try_spend("unattributed", 1, estimate_tokens(PROMPT))


def test_reserved_tokens_are_reported() -> None:
    metrics = RecordingMetrics()
    budget = MemoryTokenBudget(FakeClock(T0))
    llm = BudgetedLLM(FakeLLM({"p": {"value": 1}}), budget, 10_000, metrics)
    llm.structured(PROMPT, Answer)
    assert metrics.calls == [("llm_tokens", "acme", estimate_tokens(PROMPT))]
