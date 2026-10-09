"""Automatic maintenance block optimization endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_model_bundle
from backend.app.core.model_registry import ModelBundle
from backend.app.database.database import get_db
from backend.app.database.schemas import ApiResponse, OptimizationRequest, OptimizationResult
from backend.app.services.optimization_service import optimize_maintenance

router = APIRouter(prefix="/optimization", tags=["Optimization"])


@router.post("", response_model=ApiResponse[OptimizationResult])
def optimize_schedule(
    payload: OptimizationRequest,
    db: Session = Depends(get_db),
    bundle: ModelBundle = Depends(require_model_bundle),
) -> ApiResponse[OptimizationResult]:
    result = optimize_maintenance(db, payload, bundle)
    return ApiResponse(message="Maintenance schedule optimized.", data=result)
