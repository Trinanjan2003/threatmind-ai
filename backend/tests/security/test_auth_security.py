"""Security-focused tests: token handling, RBAC enforcement, encryption."""

from __future__ import annotations

import time

import jwt
import pytest

from app.application.auth.rbac import RBACPolicy
from app.core import security
from app.domain.enums import Permission
from app.domain.exceptions import PermissionDeniedError


@pytest.mark.security
class TestTokenSecurity:
    def test_access_token_cannot_be_used_as_refresh(self) -> None:
        token = security.create_access_token("u1", roles=[], permissions=[])
        with pytest.raises(jwt.InvalidTokenError):
            security.decode_token(token, expected_type=security.TokenType.REFRESH)

    def test_tampered_token_rejected(self) -> None:
        token = security.create_access_token("u1", roles=["analyst"], permissions=[])
        tampered = token[:-3] + ("aaa" if not token.endswith("aaa") else "bbb")
        with pytest.raises(jwt.PyJWTError):
            security.decode_token(tampered)

    def test_token_signed_with_other_key_rejected(self) -> None:
        forged = jwt.encode({"sub": "attacker", "type": "access"}, "wrong-key", algorithm="HS256")
        with pytest.raises(jwt.PyJWTError):
            security.decode_token(forged)

    def test_refresh_token_hash_is_not_reversible(self) -> None:
        token = security.create_refresh_token("u1")
        h = security.hash_opaque_token(token)
        assert token not in h
        assert len(h) == 64  # sha256 hex


@pytest.mark.security
class TestRBACEnforcement:
    def test_missing_permission_denied(self) -> None:
        granted = {Permission.ALERTS_READ.value}
        with pytest.raises(PermissionDeniedError):
            RBACPolicy.require(granted, Permission.USERS_MANAGE)

    def test_privilege_escalation_blocked(self) -> None:
        # A read-only user's granted set must never satisfy a write permission.
        from app.application.auth.rbac import permissions_for_role
        from app.domain.enums import RoleName

        readonly = {p.value for p in permissions_for_role(RoleName.READ_ONLY)}
        for sensitive in (Permission.USERS_MANAGE, Permission.SETTINGS_MANAGE, Permission.ALERTS_WRITE):
            assert not RBACPolicy.has(readonly, sensitive)


@pytest.mark.security
class TestEncryption:
    def test_password_hash_is_salted(self) -> None:
        h1 = security.hash_password("same-password")
        h2 = security.hash_password("same-password")
        assert h1 != h2  # unique salt per hash
        assert security.verify_password("same-password", h1)
        assert security.verify_password("same-password", h2)
