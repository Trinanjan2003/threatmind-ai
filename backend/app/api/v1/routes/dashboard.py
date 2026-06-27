"""Dashboard KPI/overview routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_alert_repo, require_permissions
from app.domain.enums import AlertCategory, Permission
from app.domain.repositories.alert_repository import AlertFilter
from app.infrastructure.db.repositories import SqlAlchemyAlertRepository

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_OPEN_STATUSES = {"new", "triaging", "investigating"}


@router.get(
    "/overview",
    summary="KPI overview cards",
    dependencies=[Depends(require_permissions(Permission.DASHBOARD_READ))],
)
async def overview(
    repo: Annotated[SqlAlchemyAlertRepository, Depends(get_alert_repo)],
) -> dict[str, object]:
    by_status = await repo.count_by_status()
    by_severity = await repo.count_by_severity()
    return {
        "alerts_by_status": {s.value: c for s, c in by_status.items()},
        "alerts_by_severity": {s.value: c for s, c in by_severity.items()},
        "open_alerts": sum(c for s, c in by_status.items() if s.value in _OPEN_STATUSES),
    }


@router.get(
    "/threat-heatmap",
    summary="Threat heatmap data (host x category)",
    dependencies=[Depends(require_permissions(Permission.DASHBOARD_READ))],
)
async def threat_heatmap(
    repo: Annotated[SqlAlchemyAlertRepository, Depends(get_alert_repo)],
) -> dict[str, object]:
    # Build a host x category intensity grid from current alerts.
    alerts, _ = await repo.search(AlertFilter(limit=1000))
    grid: dict[str, dict[str, int]] = {}
    for a in alerts:
        host = a.host or "unknown"
        grid.setdefault(host, {})
        grid[host][a.category.value] = grid[host].get(a.category.value, 0) + 1
    cells = [
        {"host": host, "category": cat, "value": val}
        for host, cats in grid.items()
        for cat, val in cats.items()
    ]
    return {"cells": cells, "categories": [c.value for c in AlertCategory]}
