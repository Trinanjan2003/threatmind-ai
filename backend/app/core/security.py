"""Security primitives: password hashing, JWT, field encryption, MFA, API keys.

This module is intentionally framework-agnostic so it can be unit-tested without
FastAPI. HTTP concerns (extracting tokens, raising 401/403) live in ``app.api.deps``.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pyotp
from cryptography.fernet import Fernet, InvalidToken
from passlib.context import CryptContext

from app.core.config import settings

# Argon2id preferred, bcrypt retained for verification compatibility.
_pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


# ─────────────────────────── Passwords ───────────────────────────
def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def needs_rehash(hashed: str) -> bool:
    return _pwd_context.needs_update(hashed)


# ─────────────────────────── JWT ───────────────────────────
class TokenType:
    ACCESS = "access"  # noqa: S105 - label, not a secret
    REFRESH = "refresh"  # noqa: S105
    MFA_CHALLENGE = "mfa_challenge"  # noqa: S105


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": secrets.token_urlsafe(16),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(
    subject: str, *, roles: list[str], permissions: list[str]
) -> str:
    return _create_token(
        subject,
        TokenType.ACCESS,
        timedelta(minutes=settings.access_token_expire_minutes),
        {"roles": roles, "permissions": permissions},
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject, TokenType.REFRESH, timedelta(days=settings.refresh_token_expire_days)
    )


def create_mfa_challenge_token(subject: str) -> str:
    return _create_token(
        subject, TokenType.MFA_CHALLENGE, timedelta(minutes=5)
    )


def decode_token(token: str, *, expected_type: str | None = None) -> dict[str, Any]:
    """Decode and validate a JWT. Raises ``jwt.PyJWTError`` subclasses on failure."""
    payload: dict[str, Any] = jwt.decode(
        token, settings.secret_key, algorithms=[settings.jwt_algorithm]
    )
    if expected_type is not None and payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(
            f"Expected token type {expected_type!r}, got {payload.get('type')!r}"
        )
    return payload


# ─────────────────────────── Opaque token / API-key hashing ───────────────────────────
def hash_opaque_token(token: str) -> str:
    """SHA-256 hash for refresh tokens / API keys stored at rest."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    """Return (full_key, prefix, hash). Only the hash is persisted."""
    raw = secrets.token_urlsafe(32)
    prefix = raw[:8]
    full = f"tmai_{raw}"
    return full, prefix, hash_opaque_token(full)


# ─────────────────────────── Field encryption (at rest) ───────────────────────────
def _fernet() -> Fernet:
    key = settings.encryption_key.encode()
    return Fernet(key)


def encrypt_value(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:  # pragma: no cover - defensive
        raise ValueError("Failed to decrypt value (invalid key or data)") from exc


# ─────────────────────────── MFA (TOTP) ───────────────────────────
def generate_totp_secret() -> str:
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, account_name: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(
        name=account_name, issuer_name=settings.mfa_issuer
    )


def verify_totp(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def generate_recovery_codes(count: int = 10) -> list[str]:
    return [secrets.token_hex(5) for _ in range(count)]
