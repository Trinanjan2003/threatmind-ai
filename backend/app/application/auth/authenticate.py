"""Authentication use cases: password login + MFA challenge completion."""

from __future__ import annotations

from app.application.auth.tokens import TokenService
from app.application.dto import LoginResult
from app.core import security
from app.domain.entities.user import User
from app.domain.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
)
from app.domain.repositories.user_repository import UserRepository


class AuthenticateUser:
    """Validates credentials and either issues tokens or an MFA challenge."""

    def __init__(self, users: UserRepository, tokens: TokenService) -> None:
        self._users = users
        self._tokens = tokens

    async def login(
        self,
        *,
        email: str,
        password: str,
        user_agent: str | None = None,
        ip: str | None = None,
    ) -> LoginResult:
        user = await self._users.get_by_email(email.lower().strip())

        # Constant-ish behavior: always verify against *something* to reduce
        # username-enumeration timing signals.
        if user is None or user.hashed_password is None:
            security.verify_password(password, _DUMMY_HASH)
            raise InvalidCredentialsError()

        if not security.verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InactiveUserError()

        if user.mfa_enabled:
            challenge = security.create_mfa_challenge_token(str(user.id))
            return LoginResult(mfa_required=True, challenge_token=challenge)

        tokens = await self._tokens.issue_pair(user, user_agent=user_agent, ip=ip)
        return LoginResult(tokens=tokens)

    async def complete_mfa(
        self,
        *,
        user: User,
        tokens_ctx_user_agent: str | None = None,
        tokens_ctx_ip: str | None = None,
    ) -> LoginResult:
        """Issue tokens after a verified MFA challenge (TOTP checked by caller)."""
        tokens = await self._tokens.issue_pair(
            user, user_agent=tokens_ctx_user_agent, ip=tokens_ctx_ip
        )
        return LoginResult(tokens=tokens)


# A precomputed argon2 hash of a random string, used to keep timing uniform when
# the user does not exist. (Value is not a real credential.)
_DUMMY_HASH = security.hash_password("tm-ai-dummy-password-for-timing")
