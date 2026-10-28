"""Render a ``Prompt`` into chat messages with untrusted data fenced off.

Untrusted values are wrapped in named ``<untrusted_data>`` blocks after any closing
tag inside them is neutralised, so attacker text cannot end its block early and
pose as instructions.
"""

from sentinelflow.contracts.llm import Prompt

_CLOSE = "</untrusted_data>"
_ESCAPED_CLOSE = "&lt;/untrusted_data&gt;"


def render(prompt: Prompt) -> list[tuple[str, str]]:
    """Return ``[("system", ...), ("human", ...)]`` messages for ``prompt``."""
    blocks = [_block(name, value) for name, value in prompt.untrusted.items()]
    human = "\n\n".join([*blocks, prompt.instructions])
    return [("system", prompt.system), ("human", human)]


def _block(name: str, value: str) -> str:
    safe = value.replace(_CLOSE, _ESCAPED_CLOSE)
    return f'<untrusted_data name="{name}">\n{safe}\n{_CLOSE}'
