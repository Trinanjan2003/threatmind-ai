"""Detection engineering routes — generate detection content from techniques."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import require_permissions
from app.core.errors import ValidationError
from app.domain.enums import DetectionFormat, Permission
from app.infrastructure.detections.generators import generate_detection

router = APIRouter(prefix="/detections", tags=["detections"])


class GenerateDetectionRequest(BaseModel):
    technique_id: str = Field(examples=["T1059.001"])
    format: str = Field(default="sigma", examples=["sigma", "yara", "suricata", "splunk_spl", "kql"])
    context: str = ""


@router.get(
    "/formats",
    summary="List supported detection formats",
    dependencies=[Depends(require_permissions(Permission.DETECTIONS_READ))],
)
async def formats() -> dict[str, list[str]]:
    return {"formats": [f.value for f in DetectionFormat]}


@router.post(
    ":generate",
    summary="Generate detection content for a MITRE technique",
    status_code=201,
    dependencies=[Depends(require_permissions(Permission.DETECTIONS_WRITE))],
)
async def generate(body: GenerateDetectionRequest) -> dict[str, str]:
    try:
        content = generate_detection(
            fmt=body.format, technique_id=body.technique_id, context=body.context
        )
    except ValueError as exc:
        raise ValidationError(
            f"Invalid format '{body.format}'",
            details={"allowed": [f.value for f in DetectionFormat]},
        ) from exc
    return {"format": body.format, "technique_id": body.technique_id, "content": content}
