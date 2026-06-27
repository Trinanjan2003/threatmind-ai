"""Aggregate all v1 routers under a single APIRouter."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import (
    alerts,
    auth,
    chat,
    dashboard,
    detections,
    events,
    health,
    hunts,
    ingest,
    mitre,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(alerts.router)
api_router.include_router(dashboard.router)
api_router.include_router(ingest.router)
api_router.include_router(events.router)
api_router.include_router(mitre.router)
api_router.include_router(hunts.router)
api_router.include_router(detections.router)
api_router.include_router(chat.router)
