"""Centralized exception handling → uniform error envelope."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.errors import AppError, error_envelope
from app.core.logging import get_logger
from app.domain.exceptions import (
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    InactiveUserError,
    InvalidCredentialsError,
    MFARequiredError,
    PermissionDeniedError,
)

logger = get_logger(__name__)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _domain_to_app_error(exc: DomainError) -> AppError:
    """Translate domain exceptions into HTTP-aware application errors."""
    if isinstance(exc, EntityNotFoundError):
        return AppError(str(exc), code="NOT_FOUND", status_code=404)
    if isinstance(exc, DuplicateEntityError):
        return AppError(str(exc), code="CONFLICT", status_code=409)
    if isinstance(exc, (InvalidCredentialsError, InactiveUserError)):
        return AppError(str(exc), code="UNAUTHENTICATED", status_code=401)
    if isinstance(exc, MFARequiredError):
        return AppError(str(exc), code="MFA_REQUIRED", status_code=401)
    if isinstance(exc, PermissionDeniedError):
        return AppError(str(exc), code="FORBIDDEN", status_code=403)
    return AppError(str(exc), code="VALIDATION_ERROR", status_code=422)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(DomainError)
    async def _domain_error(request: Request, exc: DomainError) -> JSONResponse:
        app_err = _domain_to_app_error(exc)
        return JSONResponse(
            status_code=app_err.status_code,
            content=error_envelope(
                code=app_err.code,
                message=app_err.message,
                details=app_err.details,
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_envelope(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                details={"errors": exc.errors()},
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(
                code="HTTP_ERROR",
                message=str(exc.detail),
                details={},
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", error=str(exc), exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=error_envelope(
                code="INTERNAL",
                message="An internal error occurred",
                details={},
                request_id=_request_id(request),
            ),
        )
