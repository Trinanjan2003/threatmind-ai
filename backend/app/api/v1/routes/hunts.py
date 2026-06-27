"""Threat hunting routes — launch autonomous multi-agent hunts."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import require_permissions
from app.application.investigation.run_hunt import RunHuntUseCase
from app.container import container
from app.core.errors import NotFoundError
from app.domain.enums import Permission
from app.infrastructure.agents.engine import HuntEngine

router = APIRouter(prefix="/hunts", tags=["hunting"])


class HuntScope(BaseModel):
    hosts: list[str] = Field(default_factory=list)


class LaunchHuntRequest(BaseModel):
    focus: str = Field(examples=["ransomware"])
    query: str | None = None
    scope: HuntScope = Field(default_factory=HuntScope)


@router.post(
    "",
    summary="Launch an autonomous hunt",
    status_code=202,
    dependencies=[Depends(require_permissions(Permission.HUNTS_RUN))],
)
async def launch_hunt(body: LaunchHuntRequest) -> dict[str, object]:
    hunt_id = f"hunt_{uuid.uuid4().hex[:12]}"
    engine = HuntEngine(llm=container.llm, search=container.search)
    uc = RunHuntUseCase(engine=engine, cache=container.cache)
    # Run synchronously here; in production this dispatches to a worker.
    state = await uc.execute(
        hunt_id=hunt_id,
        query=body.query or f"Hunt for {body.focus}",
        focus=body.focus,
        scope_hosts=body.scope.hosts,
    )
    return {
        "id": hunt_id,
        "status": "completed",
        "engine": "langgraph" if engine.uses_langgraph else "sequential",
        "result": state.to_dict(),
    }


@router.get(
    "/{hunt_id}",
    summary="Get hunt status and findings",
    dependencies=[Depends(require_permissions(Permission.HUNTS_RUN))],
)
async def get_hunt(hunt_id: str) -> dict[str, object]:
    cached = await container.cache.get(f"hunt:{hunt_id}")
    if cached is None:
        raise NotFoundError(f"Hunt {hunt_id} not found or expired")
    return {"id": hunt_id, "status": "completed", "result": json.loads(cached)}
