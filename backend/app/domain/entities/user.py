"""User and Role domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.domain.enums import Permission, RoleName


@dataclass(slots=True)
class Role:
    """A role bundling a set of permissions."""

    id: UUID
    name: RoleName
    description: str
    permissions: set[Permission] = field(default_factory=set)

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions


@dataclass(slots=True)
class User:
    """An authenticated principal of the platform."""

    id: UUID
    email: str
    full_name: str
    is_active: bool = True
    is_sso: bool = False
    hashed_password: str | None = None
    mfa_enabled: bool = False
    roles: list[Role] = field(default_factory=list)
    last_login_at: datetime | None = None

    @property
    def role_names(self) -> list[str]:
        return [r.name.value for r in self.roles]

    @property
    def permissions(self) -> set[Permission]:
        """Union of permissions across all assigned roles."""
        perms: set[Permission] = set()
        for role in self.roles:
            perms |= role.permissions
        return perms

    def permission_keys(self) -> list[str]:
        return sorted(p.value for p in self.permissions)

    def has_permission(self, permission: Permission) -> bool:
        return any(r.has_permission(permission) for r in self.roles)

    def require_active(self) -> None:
        from app.domain.exceptions import InactiveUserError

        if not self.is_active:
            raise InactiveUserError()
