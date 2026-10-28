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


class NotFoundError(SentinelFlowError):
    """A requested resource does not exist or is not visible to the caller (HTTP 404)."""


class UnknownWorkflowError(NotFoundError):
    """No workflow is registered under the requested name."""


class AuthorizationError(SentinelFlowError):
    """The caller is authenticated but not allowed to do this (HTTP 403)."""


class PolicyDeniedError(AuthorizationError):
    """The policy engine denied a request; the message is the human-readable reason."""


class UnknownActionError(DomainError):
    """A requested action is not in the action catalogue (the allow-list)."""


class ConflictError(SentinelFlowError):
    """The request conflicts with current state, e.g. an approval already decided (HTTP 409)."""
