"""User, Role, and refresh-token repository interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.user import Role, User
from app.domain.enums import RoleName


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_by_sso_subject(self, subject: str) -> User | None: ...

    @abstractmethod
    async def list(self, *, offset: int = 0, limit: int = 25) -> tuple[list[User], int]:
        """Return (users, total_count)."""

    @abstractmethod
    async def add(self, user: User, *, hashed_password: str | None) -> User: ...

    @abstractmethod
    async def update(self, user: User) -> User: ...

    @abstractmethod
    async def set_password(self, user_id: UUID, hashed_password: str) -> None: ...

    @abstractmethod
    async def soft_delete(self, user_id: UUID) -> None: ...


class RoleRepository(ABC):
    @abstractmethod
    async def get_by_name(self, name: RoleName) -> Role | None: ...

    @abstractmethod
    async def list(self) -> list[Role]: ...


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def store(
        self, *, user_id: UUID, token_hash: str, expires_at_epoch: int,
        user_agent: str | None, ip: str | None,
    ) -> None: ...

    @abstractmethod
    async def is_valid(self, token_hash: str) -> bool: ...

    @abstractmethod
    async def revoke(self, token_hash: str) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: UUID) -> None: ...
