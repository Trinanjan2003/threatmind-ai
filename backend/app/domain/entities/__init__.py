"""Domain entities — the core business objects."""

from app.domain.entities.alert import Alert
from app.domain.entities.user import Role, User

__all__ = ["Alert", "Role", "User"]
