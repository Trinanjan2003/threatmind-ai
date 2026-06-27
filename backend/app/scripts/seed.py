"""Seed initial data: the four roles and (in non-prod) one demo user per role.

Run with:  python -m app.scripts.seed
Idempotent — safe to run repeatedly.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.application.auth.rbac import permissions_for_role
from app.core import security
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.domain.enums import RoleName
from app.infrastructure.db.models.user import RoleModel, UserModel
from app.infrastructure.db.session import session_scope

logger = get_logger(__name__)

_ROLE_DESCRIPTIONS = {
    RoleName.SUPER_ADMIN: "Full platform administration",
    RoleName.SOC_MANAGER: "Manages SOC operations, data sources, and audit",
    RoleName.ANALYST: "Investigates alerts and runs hunts",
    RoleName.READ_ONLY: "Read-only access to dashboards and findings",
}

# Demo users created only outside production.
_DEMO_USERS = [
    ("admin@threatmind.local", "Ada Admin", RoleName.SUPER_ADMIN),
    ("manager@threatmind.local", "Marcus Manager", RoleName.SOC_MANAGER),
    ("analyst@threatmind.local", "Priya Analyst", RoleName.ANALYST),
    ("viewer@threatmind.local", "Riley Viewer", RoleName.READ_ONLY),
]
_DEMO_PASSWORD = "ChangeMe123!"  # noqa: S105 - dev-only demo credential


async def seed_roles() -> dict[RoleName, RoleModel]:
    created: dict[RoleName, RoleModel] = {}
    async with session_scope() as session:
        for role_name in RoleName:
            existing = (
                await session.execute(
                    select(RoleModel).where(RoleModel.name == role_name.value)
                )
            ).scalar_one_or_none()
            perms = sorted(p.value for p in permissions_for_role(role_name))
            if existing:
                existing.permissions = perms
                existing.description = _ROLE_DESCRIPTIONS[role_name]
                created[role_name] = existing
            else:
                model = RoleModel(
                    name=role_name.value,
                    description=_ROLE_DESCRIPTIONS[role_name],
                    permissions=perms,
                )
                session.add(model)
                created[role_name] = model
        logger.info("roles_seeded", count=len(created))
    return created


async def seed_demo_users() -> None:
    if settings.is_production:
        logger.info("skip_demo_users_in_production")
        return
    async with session_scope() as session:
        for email, name, role_name in _DEMO_USERS:
            exists = (
                await session.execute(
                    select(UserModel).where(UserModel.email == email)
                )
            ).scalar_one_or_none()
            if exists:
                continue
            role = (
                await session.execute(
                    select(RoleModel).where(RoleModel.name == role_name.value)
                )
            ).scalar_one()
            session.add(
                UserModel(
                    email=email,
                    full_name=name,
                    hashed_password=security.hash_password(_DEMO_PASSWORD),
                    is_active=True,
                    roles=[role],
                )
            )
        logger.info("demo_users_seeded", note="password is ChangeMe123! (dev only)")


async def main() -> None:
    configure_logging(level=settings.log_level, json_logs=settings.log_json)
    await seed_roles()
    await seed_demo_users()
    from app.infrastructure.db.session import dispose_engine

    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
