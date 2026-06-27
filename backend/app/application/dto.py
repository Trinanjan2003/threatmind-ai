"""Internal DTOs passed between use cases and the API layer.

These are plain dataclasses (transport-agnostic). API Pydantic schemas in
``app.api.schemas`` adapt these to/from HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 - protocol label, not a secret


@dataclass(slots=True)
class LoginResult:
    """Either a full token pair, or an MFA challenge that must be completed."""

    tokens: TokenPair | None = None
    mfa_required: bool = False
    challenge_token: str | None = None


@dataclass(slots=True)
class AuthenticatedPrincipal:
    """The identity resolved from a validated access token."""

    user_id: str
    email: str
    roles: list[str]
    permissions: list[str]
