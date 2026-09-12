"""Application-level exceptions.

Services raise these; the transport layers (API / web) translate them into HTTP
responses. Messages are safe to show to users — no internal details.
"""


class LoopError(Exception):
    """Base class for expected, user-facing application errors."""

    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationError(LoopError):
    status_code = 422


class NotFoundError(LoopError):
    status_code = 404


class PermissionDeniedError(LoopError):
    status_code = 403


class AuthenticationError(LoopError):
    status_code = 401
