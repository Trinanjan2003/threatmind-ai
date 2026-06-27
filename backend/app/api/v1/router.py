"""Aggregate all v1 routers under a single APIRouter."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import alerts, auth, dashboard, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(alerts.router)
api_router.include_router(dashboard.router)
