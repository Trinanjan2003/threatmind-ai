"""Unit tests for the AuthenticateUser use case + TokenService (fakes only)."""

from __future__ import annotations

import uuid

import pytest

from app.application.auth.authenticate import AuthenticateUser
from app.application.auth.tokens import TokenService
from app.core import security
from app.domain.entities.user import Role, User
from app.domain.enums import Permission, RoleName
from app.domain.exceptions import InactiveUserError, InvalidCredentialsError


class _FakeUserRepo:
    def __init__(self, user: User | None) -> None:
        self._user = user

    async def get_by_email(self, email: str) -> User | None:
        return self._user

    # Unused abstract methods.
    async def get_by_id(self, *_): ...  # pragma: no cover
    async def get_by_sso_subject(self, *_): ...  # pragma: no cover
    async def list(self, **_): ...  # pragma: no cover
    async def add(self, *a, **k): ...  # pragma: no cover
    async def update(self, *a): ...  # pragma: no cover
    async def set_password(self, *a): ...  # pragma: no cover
    async def soft_delete(self, *a): ...  # pragma: no cover


class _FakeRefreshRepo:
    def __init__(self) -> None:
        self.stored: list[str] = []

    async def store(self, *, user_id, token_hash, expires_at_epoch, user_agent, ip) -> None:
        self.stored.append(token_hash)

    async def is_valid(self, token_hash: str) -> bool:
        return token_hash in self.stored

    async def revoke(self, token_hash: str) -> None: ...  # pragma: no cover
    async def revoke_all_for_user(self, user_id) -> None: ...  # pragma: no cover


def _user(*, active: bool = True, mfa: bool = False, password: str = "Secret123!") -> User:
    role = Role(id=uuid.uuid4(), name=RoleName.ANALYST, description="", permissions={Permission.ALERTS_READ})
    return User(
        id=uuid.uuid4(), email="a@corp.com", full_name="A", is_active=active,
        hashed_password=security.hash_password(password), mfa_enabled=mfa, roles=[role],
    )


def _uc(user: User | None) -> AuthenticateUser:
    return AuthenticateUser(_FakeUserRepo(user), TokenService(_FakeRefreshRepo()))


@pytest.mark.unit
class TestLogin:
    async def test_successful_login_issues_tokens(self) -> None:
        result = await _uc(_user()).login(email="a@corp.com", password="Secret123!")
        assert result.tokens is not None and not result.mfa_required
        payload = security.decode_token(result.tokens.access_token, expected_type=security.TokenType.ACCESS)
        assert payload["roles"] == ["analyst"]

    async def test_unknown_user_raises_invalid_credentials(self) -> None:
        with pytest.raises(InvalidCredentialsError):
            await _uc(None).login(email="ghost@corp.com", password="x")

    async def test_wrong_password_raises(self) -> None:
        with pytest.raises(InvalidCredentialsError):
            await _uc(_user()).login(email="a@corp.com", password="wrong")

    async def test_inactive_user_raises(self) -> None:
        with pytest.raises(InactiveUserError):
            await _uc(_user(active=False)).login(email="a@corp.com", password="Secret123!")

    async def test_mfa_user_gets_challenge(self) -> None:
        result = await _uc(_user(mfa=True)).login(email="a@corp.com", password="Secret123!")
        assert result.mfa_required and result.challenge_token
        assert result.tokens is None

    async def test_complete_mfa_issues_tokens(self) -> None:
        user = _user(mfa=True)
        result = await _uc(user).complete_mfa(user=user)
        assert result.tokens is not None


@pytest.mark.unit
class TestTokenService:
    async def test_issue_and_validate_refresh(self) -> None:
        repo = _FakeRefreshRepo()
        svc = TokenService(repo)
        pair = await svc.issue_pair(_user())
        assert await svc.is_refresh_valid(pair.refresh_token)
