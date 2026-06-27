"""Uniform error model.

Domain code raises ``AppError`` subclasses (or plain ``DomainError`` from the
domain layer); the API layer maps them to the standard error envelope:

    {"error": {"code": "...", "message": "...", "details": {...}, "request_id": "..."}}
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base application error carrying an HTTP status, machine code, and details."""

    status_code: int = 500
    code: str = "INTERNAL"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}


class ValidationError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"


class AuthenticationError(AppError):
    status_code = 401
    code = "UNAUTHENTICATED"


class AuthorizationError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"


class RateLimitError(AppError):
    status_code = 429
    code = "RATE_LIMITED"


class AIUnavailableError(AppError):
    status_code = 503
    code = "AI_UNAVAILABLE"


def error_envelope(
    *, code: str, message: str, details: dict[str, Any], request_id: str | None
) -> dict[str, Any]:
    """Build the standard error response body."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": request_id,
        }
    }
