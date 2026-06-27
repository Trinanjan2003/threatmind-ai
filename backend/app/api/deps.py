"""FastAPI dependencies: DB session, repositories, current user, RBAC guards."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Annotated, Any

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.authenticate import AuthenticateUser
from app.application.auth.tokens import TokenService
from app.application.dto import AuthenticatedPrincipal
from app.core import security
from app.core.errors import AuthenticationError, AuthorizationError
from app.domain.enums import Permission
from app.infrastructure.db.repositories import (
    SqlAlchemyAlertRepository,
    SqlAlchemyAuditLogRepository,
    SqlAlchemyRefreshTokenRepository,
    SqlAlchemyUserRepository,
)
from app.infrastructure.db.session import get_session_factory

_bearer = HTTPBearer(auto_error=False)


# ─────────────────────────── DB session ───────────────────────────
async def get_db() -> AsyncIterator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_db)]


# ─────────────────────────── Repositories ───────────────────────────
def get_user_repo(db: DbSession) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(db)


def get_refresh_repo(db: DbSession) -> SqlAlchemyRefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(db)


def get_alert_repo(db: DbSession) -> SqlAlchemyAlertRepository:
    return SqlAlchemyAlertRepository(db)


def get_audit_repo(db: DbSession) -> SqlAlchemyAuditLogRepository:
    return SqlAlchemyAuditLogRepository(db)


# ─────────────────────────── Use cases ───────────────────────────
def get_token_service(
    refresh: Annotated[SqlAlchemyRefreshTokenRepository, Depends(get_refresh_repo)],
) -> TokenService:
    return TokenService(refresh)


def get_authenticate_uc(
    users: Annotated[SqlAlchemyUserRepository, Depends(get_user_repo)],
    tokens: Annotated[TokenService, Depends(get_token_service)],
) -> AuthenticateUser:
    return AuthenticateUser(users, tokens)


# ─────────────────────────── Current principal ───────────────────────────
async def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthenticatedPrincipal:
    if credentials is None:
        raise AuthenticationError("Missing bearer token")
    try:
        payload = security.decode_token(
            credentials.credentials, expected_type=security.TokenType.ACCESS
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired") from exc
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid token") from exc

    return AuthenticatedPrincipal(
        user_id=payload["sub"],
        email=payload.get("email", ""),
        roles=payload.get("roles", []),
        permissions=payload.get("permissions", []),
    )


CurrentUser = Annotated[AuthenticatedPrincipal, Depends(get_current_principal)]


# ─────────────────────────── RBAC guard ───────────────────────────
def require_permissions(
    *required: Permission,
) -> Callable[[AuthenticatedPrincipal], Coroutine[Any, Any, AuthenticatedPrincipal]]:
    """Dependency factory enforcing that the caller holds all given permissions."""

    async def _guard(principal: CurrentUser) -> AuthenticatedPrincipal:
        granted = set(principal.permissions)
        missing = [p.value for p in required if p.value not in granted]
        if missing:
            raise AuthorizationError(
                "Insufficient permissions",
                details={"missing": missing},
            )
        return principal

    return _guard


def client_identifier(request: Request, principal: AuthenticatedPrincipal | None = None) -> str:
    """Stable key for rate limiting: user id if known, else client IP."""
    if principal is not None:
        return f"user:{principal.user_id}"
    client = request.client
    return f"ip:{client.host}" if client else "ip:unknown"
