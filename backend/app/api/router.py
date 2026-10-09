"""Aggregate backend route modules."""

from fastapi import APIRouter

from backend.app.api.routes import assets, dashboard, health, optimization, prediction

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(assets.router)
api_router.include_router(prediction.router)
api_router.include_router(optimization.router)
api_router.include_router(dashboard.router)
