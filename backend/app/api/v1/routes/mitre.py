"""MITRE ATT&CK routes — technique reference and matrix."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_permissions
from app.core.errors import NotFoundError
from app.domain.enums import Permission
from app.domain.enums import MitreTactic
from app.infrastructure.mitre.knowledge_base import MITRE_TECHNIQUES, get_technique

router = APIRouter(prefix="/mitre", tags=["mitre"])


@router.get(
    "/matrix",
    summary="ATT&CK matrix grouped by tactic",
    dependencies=[Depends(require_permissions(Permission.ALERTS_READ))],
)
async def matrix() -> dict[str, object]:
    columns: dict[str, list[dict[str, str]]] = {t.value: [] for t in MitreTactic}
    for rec in MITRE_TECHNIQUES.values():
        columns[rec.tactic.value].append(
            {"technique_id": rec.technique_id, "name": rec.name}
        )
    return {
        "tactics": [
            {"tactic": tactic, "techniques": techs}
            for tactic, techs in columns.items()
            if techs
        ]
    }


@router.get(
    "/techniques",
    summary="List known MITRE techniques",
    dependencies=[Depends(require_permissions(Permission.ALERTS_READ))],
)
async def list_techniques() -> dict[str, object]:
    return {
        "techniques": [
            {
                "technique_id": r.technique_id,
                "name": r.name,
                "tactic": r.tactic.value,
                "description": r.description,
            }
            for r in MITRE_TECHNIQUES.values()
        ],
        "total": len(MITRE_TECHNIQUES),
    }


@router.get(
    "/techniques/{technique_id}",
    summary="Technique detail",
    dependencies=[Depends(require_permissions(Permission.ALERTS_READ))],
)
async def technique_detail(technique_id: str) -> dict[str, object]:
    rec = get_technique(technique_id)
    if rec is None:
        raise NotFoundError(f"Technique {technique_id} not found")
    return {
        "technique_id": rec.technique_id,
        "name": rec.name,
        "tactic": rec.tactic.value,
        "description": rec.description,
        "url": f"https://attack.mitre.org/techniques/{rec.technique_id.replace('.', '/')}/",
    }
