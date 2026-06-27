"""SQLAlchemy implementations of the user/role/refresh-token repositories."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import Role, User
from app.domain.enums import Permission, RoleName
from app.domain.repositories.user_repository import (
    RefreshTokenRepository,
    RoleRepository,
    UserRepository,
)
from app.infrastructure.db.models.user import (
    RefreshTokenModel,
    RoleModel,
    UserModel,
)


def _to_role(model: RoleModel) -> Role:
    return Role(
        id=model.id,
        name=RoleName(model.name),
        description=model.description,
        permissions={Permission(p) for p in model.permissions},
    )


def _to_user(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        full_name=model.full_name,
        is_active=model.is_active,
        is_sso=model.is_sso,
        hashed_password=model.hashed_password,
        mfa_enabled=bool(model.mfa and model.mfa.enabled),
        roles=[_to_role(r) for r in model.roles],
        last_login_at=model.last_login_at,
    )


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        if model is None or model.deleted_at is not None:
            return None
        return _to_user(model)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(
            func.lower(UserModel.email) == email.lower(),
            UserModel.deleted_at.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_user(model) if model else None

    async def get_by_sso_subject(self, subject: str) -> User | None:
        stmt = select(UserModel).where(
            UserModel.sso_subject == subject, UserModel.deleted_at.is_(None)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_user(model) if model else None

    async def list(self, *, offset: int = 0, limit: int = 25) -> tuple[list[User], int]:
        base = select(UserModel).where(UserModel.deleted_at.is_(None))
        total = (
            await self._session.execute(
                select(func.count()).select_from(base.subquery())
            )
        ).scalar_one()
        rows = (
            await self._session.execute(
                base.order_by(UserModel.created_at.desc()).offset(offset).limit(limit)
            )
        ).scalars().unique().all()
        return [_to_user(r) for r in rows], int(total)

    async def add(self, user: User, *, hashed_password: str | None) -> User:
        model = UserModel(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            is_active=user.is_active,
            is_sso=user.is_sso,
        )
        # Attach roles by name.
        if user.roles:
            names = [r.name.value for r in user.roles]
            roles = (
                await self._session.execute(
                    select(RoleModel).where(RoleModel.name.in_(names))
                )
            ).scalars().all()
            model.roles = list(roles)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_user(model)

    async def update(self, user: User) -> User:
        model = await self._session.get(UserModel, user.id)
        if model is None:
            raise ValueError(f"User {user.id} not found")
        model.full_name = user.full_name
        model.is_active = user.is_active
        if user.roles:
            names = [r.name.value for r in user.roles]
            roles = (
                await self._session.execute(
                    select(RoleModel).where(RoleModel.name.in_(names))
                )
            ).scalars().all()
            model.roles = list(roles)
        await self._session.flush()
        return _to_user(model)

    async def set_password(self, user_id: UUID, hashed_password: str) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(hashed_password=hashed_password)
        )

    async def soft_delete(self, user_id: UUID) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(deleted_at=datetime.now(UTC), is_active=False)
        )


class SqlAlchemyRoleRepository(RoleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_name(self, name: RoleName) -> Role | None:
        stmt = select(RoleModel).where(RoleModel.name == name.value)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_role(model) if model else None

    async def list(self) -> list[Role]:
        rows = (await self._session.execute(select(RoleModel))).scalars().all()
        return [_to_role(r) for r in rows]


class SqlAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def store(
        self, *, user_id: UUID, token_hash: str, expires_at_epoch: int,
        user_agent: str | None, ip: str | None,
    ) -> None:
        self._session.add(
            RefreshTokenModel(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=datetime.fromtimestamp(expires_at_epoch, tz=UTC),
                user_agent=user_agent,
                ip=ip,
                created_at=datetime.now(UTC),
            )
        )
        await self._session.flush()

    async def is_valid(self, token_hash: str) -> bool:
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash == token_hash,
            RefreshTokenModel.revoked_at.is_(None),
            RefreshTokenModel.expires_at > datetime.now(UTC),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None

    async def revoke(self, token_hash: str) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.token_hash == token_hash)
            .values(revoked_at=datetime.now(UTC))
        )

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
