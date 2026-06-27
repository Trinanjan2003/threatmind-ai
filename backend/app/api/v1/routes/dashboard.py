"""Dashboard KPI/overview routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_alert_repo, require_permissions
from app.domain.enums import Permission
from app.infrastructure.db.repositories import SqlAlchemyAlertRepository

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


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
        "open_alerts": sum(
            c for s, c in by_status.items() if s.value in {"new", "triaging", "investigating"}
        ),
    }
