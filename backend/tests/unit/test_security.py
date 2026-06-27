"""Unit tests for core security primitives (no I/O)."""

from __future__ import annotations

import jwt
import pytest

from app.core import security


def test_password_hash_roundtrip() -> None:
    hashed = security.hash_password("S3cretP@ss")
    assert hashed != "S3cretP@ss"
    assert security.verify_password("S3cretP@ss", hashed)
    assert not security.verify_password("wrong", hashed)


def test_access_token_contains_claims() -> None:
    token = security.create_access_token(
        "user-1", roles=["analyst"], permissions=["alerts:read"]
    )
    payload = security.decode_token(token, expected_type=security.TokenType.ACCESS)
    assert payload["sub"] == "user-1"
    assert payload["roles"] == ["analyst"]
    assert "alerts:read" in payload["permissions"]


def test_wrong_token_type_rejected() -> None:
    refresh = security.create_refresh_token("user-1")
    with pytest.raises(jwt.InvalidTokenError):
        security.decode_token(refresh, expected_type=security.TokenType.ACCESS)


def test_field_encryption_roundtrip() -> None:
    # Use a valid Fernet key for this test.
    from cryptography.fernet import Fernet

    from app.core.config import settings

    original = settings.encryption_key
    settings.encryption_key = Fernet.generate_key().decode()
    try:
        ct = security.encrypt_value("totp-secret")
        assert ct != "totp-secret"
        assert security.decrypt_value(ct) == "totp-secret"
    finally:
        settings.encryption_key = original


def test_totp_verification() -> None:
    import pyotp

    secret = security.generate_totp_secret()
    code = pyotp.TOTP(secret).now()
    assert security.verify_totp(secret, code)
    assert not security.verify_totp(secret, "000000")


def test_api_key_generation() -> None:
    full, prefix, hashed = security.generate_api_key()
    assert full.startswith("tmai_")
    assert full.startswith(f"tmai_{prefix}")
    assert security.hash_opaque_token(full) == hashed
