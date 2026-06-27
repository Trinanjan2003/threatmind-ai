"""Auth request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class MFAVerifyRequest(BaseModel):
    challenge_token: str
    code: str = Field(min_length=6, max_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginResponse(BaseModel):
    mfa_required: bool = False
    challenge_token: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None


class MeResponse(BaseModel):
    user_id: str
    email: str
    roles: list[str]
    permissions: list[str]
