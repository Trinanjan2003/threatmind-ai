"""Event search routes (Elasticsearch-backed)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_permissions
from app.api.schemas.common import Page
from app.container import container
from app.core.errors import NotFoundError
from app.domain.enums import Permission

router = APIRouter(prefix="/events", tags=["events"])


@router.get(
    "",
    summary="Search normalized events",
    dependencies=[Depends(require_permissions(Permission.ALERTS_READ))],
)
async def search_events(
    q: str | None = None,
    host: str | None = None,
    user: str | None = None,
    source_type: str | None = None,
    time_from: datetime | None = None,
    time_to: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> Page[dict[str, object]]:
    items, total = await container.search.search_events(
        query=q,
        host=host,
        user=user,
        source_type=source_type,
        time_from=time_from,
        time_to=time_to,
        offset=(page - 1) * page_size,
        limit=page_size,
    )
    return Page.build(items, page=page, page_size=page_size, total=total)


@router.get(
    "/{event_id}",
    summary="Get a single normalized event",
    dependencies=[Depends(require_permissions(Permission.ALERTS_READ))],
)
async def get_event(event_id: str) -> dict[str, object]:
    event = await container.search.get_event(event_id)
    if event is None:
        raise NotFoundError(f"Event {event_id} not found")
    return event
