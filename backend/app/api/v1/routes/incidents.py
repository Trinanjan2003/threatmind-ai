"""Incident routes — timeline reconstruction and report generation.

Demonstrates the reconstruction/reporting logic over the current alert set. In a
full deployment incidents are first-class persisted entities grouping alerts;
here we reconstruct a timeline from the highest-severity alerts on demand.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_alert_repo, require_permissions
from app.application.reporting.timeline import reconstruct_timeline
from app.domain.enums import Permission, Severity
from app.domain.repositories.alert_repository import AlertFilter
from app.infrastructure.db.repositories import SqlAlchemyAlertRepository

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get(
    "/timeline",
    summary="Reconstruct an attack timeline from current alerts",
    dependencies=[Depends(require_permissions(Permission.INCIDENTS_READ))],
)
async def timeline(
    repo: Annotated[SqlAlchemyAlertRepository, Depends(get_alert_repo)],
    host: str | None = None,
) -> dict[str, object]:
    flt = AlertFilter(host=host, limit=200, sort="-created_at")
    alerts, _ = await repo.search(flt)
    steps = reconstruct_timeline(alerts)
    return {"steps": [s.to_dict() for s in steps], "count": len(steps)}


@router.get(
    "/report",
    summary="Generate a markdown incident report from current alerts",
    dependencies=[Depends(require_permissions(Permission.INCIDENTS_READ))],
)
async def report(
    repo: Annotated[SqlAlchemyAlertRepository, Depends(get_alert_repo)],
    host: str | None = None,
) -> dict[str, str]:
    flt = AlertFilter(host=host, limit=200, sort="-created_at")
    alerts, total = await repo.search(flt)
    steps = reconstruct_timeline(alerts)
    crit = sum(1 for a in alerts if a.severity in (Severity.CRITICAL, Severity.HIGH))

    lines = [
        f"# Incident Report{f' — {host}' if host else ''}",
        "",
        f"**Alerts analyzed:** {total}  ",
        f"**High/Critical:** {crit}  ",
        f"**Kill-chain phases observed:** {len({s.phase for s in steps})}",
        "",
        "## Attack Timeline",
        "",
    ]
    for s in steps:
        when = s.occurred_at.isoformat() if s.occurred_at else "unknown time"
        tid = f" `{s.technique_id}`" if s.technique_id else ""
        lines.append(f"{s.order_index + 1}. **[{s.phase}]**{tid} {s.title} — _{when}_")
        lines.append(f"   - {s.description}")
    return {"report_markdown": "\n".join(lines)}
