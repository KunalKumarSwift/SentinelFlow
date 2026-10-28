"""Heuristic prompt-injection detector for untrusted alert and log text.

Deliberately simple and explainable: each named pattern is one regular expression.
It is one layer of several (delimiting, schema-validated output, fail-safe decisions,
no LLM authority over actions); a miss here still cannot make the LLM act.
"""

import re
from collections.abc import Iterable

_PATTERNS: dict[str, re.Pattern[str]] = {
    name: re.compile(pattern, re.IGNORECASE)
    for name, pattern in {
        "override_instructions": (
            r"\b(ignore|disregard|forget|override)\b[^.\n]{0,40}"
            r"\b(previous|prior|above|earlier|all|any)\b[^.\n]{0,20}\binstructions?\b"
        ),
        "role_reassignment": r"\byou are now\b|\bact as (an? )?(admin|root|system|unrestricted)\b",
        "chat_markup": r"<\|im_(start|end)\|>|<\|(system|assistant|user)\|>|\[/?INST\]|<</?SYS>>",
        "delimiter_escape": r"<\s*/?\s*(untrusted_data|system)\b",
        "verdict_steering": (
            r"\b(mark|classify|label|treat|report)\b[^.\n]{0,40}"
            r"\b(benign|false[ _-]?positive|harmless|safe)\b"
        ),
        "prompt_exfiltration": (
            r"\b(reveal|print|show|repeat)\b[^.\n]{0,30}"
            r"\b(system prompt|your instructions|hidden instructions)\b"
        ),
    }.items()
}


def detect_injection(texts: Iterable[str]) -> tuple[str, ...]:
    """Return the sorted names of every injection pattern found in ``texts``."""
    found = {name for text in texts for name, rx in _PATTERNS.items() if rx.search(text)}
    return tuple(sorted(found))
