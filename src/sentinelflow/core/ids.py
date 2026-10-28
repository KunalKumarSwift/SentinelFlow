"""Identifier generation.

Ids are ``<prefix>-<random hex>`` so a log line or URL shows what kind of object
it refers to (``inc-…`` incident, ``run-…`` workflow run). Generation is injected
through ``IdFactory`` so tests can use predictable, sequential ids.
"""

import re
import uuid
from typing import Protocol

_PREFIX_PATTERN = re.compile(r"^[a-z]{1,12}$")


class IdFactory(Protocol):
    """Creates unique identifiers."""

    def new_id(self, prefix: str) -> str:
        """Return a new identifier starting with ``prefix``."""
        ...


class UuidIdFactory:
    """Creates random, globally unique identifiers based on UUID4."""

    def new_id(self, prefix: str) -> str:
        """Return ``<prefix>-<32 hex chars>``.

        Args:
            prefix: 1-12 lowercase letters naming the object kind, e.g. ``"inc"``.

        Returns:
            A new unique identifier.

        Raises:
            ValueError: If the prefix is not 1-12 lowercase letters.
        """
        validate_prefix(prefix)
        return f"{prefix}-{uuid.uuid4().hex}"


def validate_prefix(prefix: str) -> None:
    """Raise ``ValueError`` unless ``prefix`` is 1-12 lowercase letters.

    Args:
        prefix: Candidate id prefix.

    Raises:
        ValueError: If the prefix has the wrong length or characters.
    """
    if not _PREFIX_PATTERN.fullmatch(prefix):
        raise ValueError(f"id prefix must be 1-12 lowercase letters, got {prefix!r}")
