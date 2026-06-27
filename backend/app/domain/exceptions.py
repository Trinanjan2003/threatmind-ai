"""Domain-level exceptions.

These are pure (no HTTP knowledge). The API layer maps them onto the
``app.core.errors`` HTTP error model.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain rule violations."""


class EntityNotFoundError(DomainError):
    def __init__(self, entity: str, identifier: object) -> None:
        super().__init__(f"{entity} '{identifier}' was not found")
        self.entity = entity
        self.identifier = identifier


class DuplicateEntityError(DomainError):
    def __init__(self, entity: str, field: str, value: object) -> None:
        super().__init__(f"{entity} with {field}='{value}' already exists")
        self.entity = entity
        self.field = field
        self.value = value


class InvalidCredentialsError(DomainError):
    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class InactiveUserError(DomainError):
    def __init__(self) -> None:
        super().__init__("This account is inactive")


class MFARequiredError(DomainError):
    def __init__(self) -> None:
        super().__init__("Multi-factor authentication is required")


class PermissionDeniedError(DomainError):
    def __init__(self, permission: str) -> None:
        super().__init__(f"Missing required permission: {permission}")
        self.permission = permission


class InvariantViolationError(DomainError):
    """A business invariant was violated (e.g. an out-of-range confidence score)."""
