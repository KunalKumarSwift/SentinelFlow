"""Exception hierarchy shared by the whole application.

Every error raised on purpose derives from ``SentinelFlowError`` so callers (for
example the API error mapper) can tell expected failures from bugs.
"""


class SentinelFlowError(Exception):
    """Base class for all expected SentinelFlow errors."""


class DomainError(SentinelFlowError):
    """A business rule or invariant was violated."""


class InvalidValueError(DomainError):
    """A value object was built with a value that breaks its invariants."""


class UnknownRuleError(DomainError):
    """An alert names a detection rule the system has no severity mapping for."""


class InvalidTransitionError(DomainError):
    """An incident was asked to move to a status its lifecycle does not allow."""


class AuthenticationError(SentinelFlowError):
    """A credential is missing, malformed, expired or not trusted (HTTP 401)."""


class ProviderError(SentinelFlowError):
    """An external system (LLM, threat intel, directory, ...) failed or misbehaved."""

    def __init__(self, message: str, *, retryable: bool) -> None:
        """Create the error; ``retryable`` tells callers whether a retry may succeed."""
        super().__init__(message)
        self.retryable = retryable
