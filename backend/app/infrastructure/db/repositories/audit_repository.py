"""SQLAlchemy implementation of the append-only audit log repository."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.audit_repository import AuditEntry, AuditLogRepository
from app.infrastructure.db.models.audit import AuditLogModel


class SqlAlchemyAuditLogRepository(AuditLogRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, entry: AuditEntry) -> None:
        self._session.add(
            AuditLogModel(
                actor_id=entry.actor_id,
                actor_label=entry.actor_label,
                action=entry.action,
                resource_type=entry.resource_type,
                resource_id=entry.resource_id,
                status=entry.status,
                ip=entry.ip,
                user_agent=entry.user_agent,
                audit_metadata=entry.metadata,
            )
        )
        await self._session.flush()

    async def query(
        self, *, actor_id: UUID | None = None, action: str | None = None,
        offset: int = 0, limit: int = 50,
    ) -> tuple[list[dict[str, Any]], int]:
        stmt = select(AuditLogModel)
        if actor_id:
            stmt = stmt.where(AuditLogModel.actor_id == actor_id)
        if action:
            stmt = stmt.where(AuditLogModel.action == action)

        total = (
            await self._session.execute(
                select(func.count()).select_from(stmt.subquery())
            )
        ).scalar_one()

        rows = (
            await self._session.execute(
                stmt.order_by(AuditLogModel.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        ).scalars().all()

        items = [
            {
                "id": str(r.id),
                "actor_id": str(r.actor_id) if r.actor_id else None,
                "actor_label": r.actor_label,
                "action": r.action,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "status": r.status,
                "ip": r.ip,
                "metadata": r.audit_metadata,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
        return items, int(total)
