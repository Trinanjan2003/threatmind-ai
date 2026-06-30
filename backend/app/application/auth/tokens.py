"""Token service — issuing and rotating access/refresh tokens.

Wraps the low-level primitives in ``app.core.security`` and persists refresh
tokens (hashed) so they can be rotated and revoked.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.application.dto import TokenPair
from app.core import security
from app.core.config import settings
from app.domain.entities.user import User
from app.domain.repositories.user_repository import RefreshTokenRepository


class TokenService:
    def __init__(self, refresh_tokens: RefreshTokenRepository) -> None:
        self._refresh_tokens = refresh_tokens

    async def issue_pair(
        self, user: User, *, user_agent: str | None = None, ip: str | None = None
    ) -> TokenPair:
        access = security.create_access_token(
            str(user.id),
            roles=user.role_names,
            permissions=user.permission_keys(),
        )
        refresh = security.create_refresh_token(str(user.id))
        expires_at = datetime.now(UTC) + timedelta(
            days=settings.refresh_token_expire_days
        )
        await self._refresh_tokens.store(
            user_id=user.id,
            token_hash=security.hash_opaque_token(refresh),
            expires_at_epoch=int(expires_at.timestamp()),
            user_agent=user_agent,
            ip=ip,
        )
        return TokenPair(access_token=access, refresh_token=refresh)

    async def rotate(
        self, refresh_token: str, user: User, **ctx: str | None
    ) -> TokenPair:
        """Validate + revoke the old refresh token, then issue a fresh pair."""
        old_hash = security.hash_opaque_token(refresh_token)
        await self._refresh_tokens.revoke(old_hash)
        return await self.issue_pair(user, **ctx)

    async def revoke(self, refresh_token: str) -> None:
        await self._refresh_tokens.revoke(security.hash_opaque_token(refresh_token))

    async def revoke_all(self, user_id: UUID) -> None:
        await self._refresh_tokens.revoke_all_for_user(user_id)

    async def is_refresh_valid(self, refresh_token: str) -> bool:
        return await self._refresh_tokens.is_valid(
            security.hash_opaque_token(refresh_token)
        )
