"""Unit tests for the RBAC policy."""

from __future__ import annotations

import pytest

from app.application.auth.rbac import RBACPolicy, permissions_for_role
from app.domain.enums import Permission, RoleName
from app.domain.exceptions import PermissionDeniedError


def test_super_admin_has_all_permissions() -> None:
    perms = permissions_for_role(RoleName.SUPER_ADMIN)
    assert perms == set(Permission)


def test_read_only_cannot_write_alerts() -> None:
    perms = {p.value for p in permissions_for_role(RoleName.READ_ONLY)}
    assert Permission.ALERTS_READ.value in perms
    assert Permission.ALERTS_WRITE.value not in perms


def test_analyst_cannot_manage_users() -> None:
    perms = {p.value for p in permissions_for_role(RoleName.ANALYST)}
    assert Permission.USERS_MANAGE.value not in perms
    assert Permission.HUNTS_RUN.value in perms


def test_require_raises_when_missing() -> None:
    granted = {Permission.ALERTS_READ.value}
    RBACPolicy.require(granted, Permission.ALERTS_READ)  # no raise
    with pytest.raises(PermissionDeniedError):
        RBACPolicy.require(granted, Permission.ALERTS_WRITE)


def test_soc_manager_can_read_audit_but_not_manage_settings() -> None:
    perms = {p.value for p in permissions_for_role(RoleName.SOC_MANAGER)}
    assert Permission.AUDIT_READ.value in perms
    assert Permission.SETTINGS_MANAGE.value not in perms
