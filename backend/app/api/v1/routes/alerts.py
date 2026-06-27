"""Alert routes — list, detail, update, assign, close."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, get_alert_repo, require_permissions
from app.api.schemas.alert import AlertResponse, AlertUpdateRequest
from app.api.schemas.common import Page
from app.core.errors import NotFoundError
from app.domain.enums import AlertCategory, AlertStatus, Permission, Severity
from app.domain.repositories.alert_repository import AlertFilter
from app.infrastructure.db.repositories import SqlAlchemyAlertRepository

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get(
    "",
    response_model=Page[AlertResponse],
    summary="List/filter alerts",
    dependencies=[Depends(require_permissions(Permission.ALERTS_READ))],
)
async def list_alerts(
    repo: Annotated[SqlAlchemyAlertRepository, Depends(get_alert_repo)],
    status: AlertStatus | None = None,
    severity: Severity | None = None,
    category: AlertCategory | None = None,
    host: str | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    sort: str = "-created_at",
) -> Page[AlertResponse]:
    flt = AlertFilter(
        status=status,
        severity=severity,
        category=category,
        host=host,
        query=q,
        offset=(page - 1) * page_size,
        limit=page_size,
        sort=sort,
    )
    alerts, total = await repo.search(flt)
    return Page.build(
        [AlertResponse.from_entity(a) for a in alerts],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Alert detail",
    dependencies=[Depends(require_permissions(Permission.ALERTS_READ))],
)
async def get_alert(
    alert_id: UUID,
    repo: Annotated[SqlAlchemyAlertRepository, Depends(get_alert_repo)],
) -> AlertResponse:
    alert = await repo.get_by_id(alert_id)
    if alert is None:
        raise NotFoundError(f"Alert {alert_id} not found")
    return AlertResponse.from_entity(alert)


@router.patch(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Update alert status/assignee",
    dependencies=[Depends(require_permissions(Permission.ALERTS_WRITE))],
)
async def update_alert(
    alert_id: UUID,
    body: AlertUpdateRequest,
    repo: Annotated[SqlAlchemyAlertRepository, Depends(get_alert_repo)],
    _: CurrentUser,
) -> AlertResponse:
    alert = await repo.get_by_id(alert_id)
    if alert is None:
        raise NotFoundError(f"Alert {alert_id} not found")
    if body.assigned_to is not None:
        alert.assign(body.assigned_to)
    if body.status is not None:
        if body.status in {
            AlertStatus.RESOLVED,
            AlertStatus.FALSE_POSITIVE,
            AlertStatus.SUPPRESSED,
        }:
            alert.close(status=body.status)
        else:
            alert.status = body.status
    updated = await repo.update(alert)
    return AlertResponse.from_entity(updated)
