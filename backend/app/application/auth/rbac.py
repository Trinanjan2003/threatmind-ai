"""RBAC policy — the canonical role→permission mapping and permission checks.

This is pure domain/application logic (no I/O), so it is trivially unit-testable
and is the single source of truth used both to seed the database and to enforce
access at runtime.
"""

from __future__ import annotations

from app.domain.enums import Permission, RoleName
from app.domain.exceptions import PermissionDeniedError

# The authoritative role → permission matrix (mirrors docs/06-security-model.md).
ROLE_PERMISSIONS: dict[RoleName, set[Permission]] = {
    RoleName.SUPER_ADMIN: set(Permission),  # every permission
    RoleName.SOC_MANAGER: {
        Permission.DASHBOARD_READ,
        Permission.ALERTS_READ,
        Permission.ALERTS_WRITE,
        Permission.INCIDENTS_READ,
        Permission.INCIDENTS_WRITE,
        Permission.HUNTS_RUN,
        Permission.INVESTIGATIONS_RUN,
        Permission.DETECTIONS_READ,
        Permission.DETECTIONS_WRITE,
        Permission.DATASOURCES_READ,
        Permission.DATASOURCES_WRITE,
        Permission.AUDIT_READ,
    },
    RoleName.ANALYST: {
        Permission.DASHBOARD_READ,
        Permission.ALERTS_READ,
        Permission.ALERTS_WRITE,
        Permission.INCIDENTS_READ,
        Permission.INCIDENTS_WRITE,
        Permission.HUNTS_RUN,
        Permission.INVESTIGATIONS_RUN,
        Permission.DETECTIONS_READ,
        Permission.DETECTIONS_WRITE,
        Permission.DATASOURCES_READ,
    },
    RoleName.READ_ONLY: {
        Permission.DASHBOARD_READ,
        Permission.ALERTS_READ,
        Permission.INCIDENTS_READ,
        Permission.DETECTIONS_READ,
    },
}


def permissions_for_role(role: RoleName) -> set[Permission]:
    return set(ROLE_PERMISSIONS.get(role, set()))


class RBACPolicy:
    """Stateless permission checker operating on a set of permission keys."""

    @staticmethod
    def has(granted: set[str], required: Permission) -> bool:
        return required.value in granted

    @staticmethod
    def require(granted: set[str], *required: Permission) -> None:
        """Raise ``PermissionDeniedError`` unless all required perms are granted."""
        for perm in required:
            if perm.value not in granted:
                raise PermissionDeniedError(perm.value)
