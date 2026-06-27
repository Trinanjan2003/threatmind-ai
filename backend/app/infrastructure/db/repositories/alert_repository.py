"""SQLAlchemy implementation of the alert repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.alert import Alert
from app.domain.enums import (
    AlertCategory,
    AlertSource,
    AlertStatus,
    MitreTactic,
    Severity,
)
from app.domain.repositories.alert_repository import AlertFilter, AlertRepository
from app.domain.value_objects.confidence import ConfidenceScore
from app.domain.value_objects.evidence import Evidence
from app.domain.value_objects.mitre import MitreTechnique
from app.infrastructure.db.models.alert import AlertModel

_SORTABLE = {"created_at": AlertModel.created_at, "severity": AlertModel.severity}


def _to_entity(m: AlertModel) -> Alert:
    return Alert(
        id=m.id,
        title=m.title,
        description=m.description,
        category=AlertCategory(m.category),
        severity=Severity(m.severity),
        confidence=ConfidenceScore(m.confidence),
        source=AlertSource(m.source),
        status=AlertStatus(m.status),
        host=m.host,
        user_principal=m.user_principal,
        explanation=m.explanation,
        evidence=[Evidence(**e) for e in (m.evidence or [])],
        techniques=[
            MitreTechnique(
                technique_id=t["technique_id"],
                name=t["name"],
                tactic=MitreTactic(t["tactic"]),
            )
            for t in (m.techniques or [])
        ],
        assigned_to=m.assigned_to,
        first_seen=m.first_seen,
        last_seen=m.last_seen,
    )


def _apply_to_model(m: AlertModel, a: Alert) -> None:
    m.title = a.title
    m.description = a.description
    m.category = a.category.value
    m.severity = a.severity.value
    m.confidence = int(a.confidence)
    m.source = a.source.value
    m.status = a.status.value
    m.host = a.host
    m.user_principal = a.user_principal
    m.explanation = a.explanation
    m.evidence = [e.to_dict() for e in a.evidence]
    m.techniques = [
        {"technique_id": t.technique_id, "name": t.name, "tactic": t.tactic.value}
        for t in a.techniques
    ]
    m.assigned_to = a.assigned_to
    m.first_seen = a.first_seen
    m.last_seen = a.last_seen


class SqlAlchemyAlertRepository(AlertRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, alert_id: UUID) -> Alert | None:
        model = await self._session.get(AlertModel, alert_id)
        return _to_entity(model) if model else None

    async def search(self, flt: AlertFilter) -> tuple[list[Alert], int]:
        stmt = select(AlertModel)
        if flt.status:
            stmt = stmt.where(AlertModel.status == flt.status.value)
        if flt.severity:
            stmt = stmt.where(AlertModel.severity == flt.severity.value)
        if flt.category:
            stmt = stmt.where(AlertModel.category == flt.category.value)
        if flt.host:
            stmt = stmt.where(AlertModel.host == flt.host)
        if flt.assigned_to:
            stmt = stmt.where(AlertModel.assigned_to == flt.assigned_to)
        if flt.query:
            like = f"%{flt.query}%"
            stmt = stmt.where(
                or_(AlertModel.title.ilike(like), AlertModel.description.ilike(like))
            )

        total = (
            await self._session.execute(
                select(func.count()).select_from(stmt.subquery())
            )
        ).scalar_one()

        # Sorting (whitelist to avoid injection via sort param).
        desc = flt.sort.startswith("-")
        key = flt.sort.lstrip("-")
        column = _SORTABLE.get(key, AlertModel.created_at)
        stmt = stmt.order_by(column.desc() if desc else column.asc())
        stmt = stmt.offset(flt.offset).limit(flt.limit)

        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows], int(total)

    async def add(self, alert: Alert) -> Alert:
        model = AlertModel(id=alert.id)
        _apply_to_model(model, alert)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(self, alert: Alert) -> Alert:
        model = await self._session.get(AlertModel, alert.id)
        if model is None:
            raise ValueError(f"Alert {alert.id} not found")
        _apply_to_model(model, alert)
        await self._session.flush()
        return _to_entity(model)

    async def count_by_status(self) -> dict[AlertStatus, int]:
        rows = await self._session.execute(
            select(AlertModel.status, func.count()).group_by(AlertModel.status)
        )
        return {AlertStatus(s): int(c) for s, c in rows.all()}

    async def count_by_severity(self) -> dict[Severity, int]:
        rows = await self._session.execute(
            select(AlertModel.severity, func.count()).group_by(AlertModel.severity)
        )
        return {Severity(s): int(c) for s, c in rows.all()}
