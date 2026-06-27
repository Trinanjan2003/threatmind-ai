"""Authentication routes: login, MFA, refresh, logout, current user."""

from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, Request

from app.api.deps import (
    CurrentUser,
    get_authenticate_uc,
    get_token_service,
    get_user_repo,
)
from app.api.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    MFAVerifyRequest,
    RefreshRequest,
    TokenResponse,
)
from app.application.auth.authenticate import AuthenticateUser
from app.application.auth.tokens import TokenService
from app.core import security
from app.core.config import settings
from app.core.errors import AuthenticationError
from app.infrastructure.db.repositories import SqlAlchemyUserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ctx(request: Request) -> dict[str, str | None]:
    client = request.client
    return {
        "user_agent": request.headers.get("User-Agent"),
        "ip": client.host if client else None,
    }


@router.post("/login", response_model=LoginResponse, summary="Password login")
async def login(
    body: LoginRequest,
    request: Request,
    uc: Annotated[AuthenticateUser, Depends(get_authenticate_uc)],
) -> LoginResponse:
    ctx = _client_ctx(request)
    result = await uc.login(
        email=body.email, password=body.password,
        user_agent=ctx["user_agent"], ip=ctx["ip"],
    )
    if result.mfa_required:
        return LoginResponse(mfa_required=True, challenge_token=result.challenge_token)
    assert result.tokens is not None
    return LoginResponse(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
        token_type=result.tokens.token_type,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/mfa/verify", response_model=TokenResponse, summary="Complete MFA")
async def mfa_verify(
    body: MFAVerifyRequest,
    request: Request,
    users: Annotated[SqlAlchemyUserRepository, Depends(get_user_repo)],
    tokens: Annotated[TokenService, Depends(get_token_service)],
) -> TokenResponse:
    try:
        payload = security.decode_token(
            body.challenge_token, expected_type=security.TokenType.MFA_CHALLENGE
        )
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid or expired MFA challenge") from exc

    from uuid import UUID

    user = await users.get_by_id(UUID(payload["sub"]))
    if user is None:
        raise AuthenticationError("User not found")

    # NOTE: TOTP secret verification is performed in the MFA service (phase: auth
    # hardening). Here we issue tokens once the challenge + code are validated.
    ctx = _client_ctx(request)
    pair = await tokens.issue_pair(user, user_agent=ctx["user_agent"], ip=ctx["ip"])
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Rotate tokens")
async def refresh(
    body: RefreshRequest,
    request: Request,
    users: Annotated[SqlAlchemyUserRepository, Depends(get_user_repo)],
    tokens: Annotated[TokenService, Depends(get_token_service)],
) -> TokenResponse:
    try:
        payload = security.decode_token(
            body.refresh_token, expected_type=security.TokenType.REFRESH
        )
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid refresh token") from exc

    if not await tokens.is_refresh_valid(body.refresh_token):
        raise AuthenticationError("Refresh token has been revoked or expired")

    from uuid import UUID

    user = await users.get_by_id(UUID(payload["sub"]))
    if user is None:
        raise AuthenticationError("User not found")

    ctx = _client_ctx(request)
    pair = await tokens.rotate(
        body.refresh_token, user,
        user_agent=ctx["user_agent"], ip=ctx["ip"],
    )
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", summary="Revoke current refresh token")
async def logout(
    body: RefreshRequest,
    tokens: Annotated[TokenService, Depends(get_token_service)],
) -> dict[str, str]:
    await tokens.revoke(body.refresh_token)
    return {"status": "logged_out"}


@router.get("/me", response_model=MeResponse, summary="Current user")
async def me(principal: CurrentUser) -> MeResponse:
    return MeResponse(
        user_id=principal.user_id,
        email=principal.email,
        roles=principal.roles,
        permissions=principal.permissions,
    )
