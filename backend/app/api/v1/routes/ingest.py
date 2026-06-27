"""Ingestion routes — file upload and supported-source discovery."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import get_alert_repo, require_permissions
from app.application.detection.engine import DetectionEngine
from app.application.ingestion.ingest_file import IngestFileUseCase, IngestSummary
from app.container import container
from app.core.errors import ValidationError
from app.domain.enums import DataSourceType, Permission
from app.infrastructure.db.repositories import SqlAlchemyAlertRepository
from app.infrastructure.parsers.registry import list_supported

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.get("/supported", summary="List supported data sources")
async def supported() -> dict[str, object]:
    sources = list_supported()
    return {
        "sources": sources,
        "implemented": [k for k, v in sources.items() if v],
        "total": len(sources),
    }


@router.post(
    "/upload",
    response_model=IngestSummary,
    summary="Upload and ingest a log file",
    dependencies=[Depends(require_permissions(Permission.DATASOURCES_READ))],
)
async def upload(
    alerts: Annotated[SqlAlchemyAlertRepository, Depends(get_alert_repo)],
    source_type: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
) -> IngestSummary:
    try:
        st = DataSourceType(source_type)
    except ValueError as exc:
        raise ValidationError(
            f"Unknown source_type '{source_type}'",
            details={"allowed": [s.value for s in DataSourceType]},
        ) from exc

    content = await file.read()
    uc = IngestFileUseCase(search=container.search, alerts=alerts, engine=DetectionEngine())
    return await uc.execute(source_type=st, content=content, job_id=file.filename)
