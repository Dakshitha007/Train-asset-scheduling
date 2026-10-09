"""Single and batch priority prediction endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.dependencies import require_model_bundle
from backend.app.core.model_registry import ModelBundle
from backend.app.core.config import settings
from backend.app.database.database import get_db
from backend.app.database.schemas import (
    ApiResponse,
    AssetCreate,
    PredictionBatchRequest,
    PredictionResult,
)
from backend.app.services.prediction_service import predict_and_record

router = APIRouter(prefix="/prediction", tags=["Prediction"])


def _check_batch_size(assets: list[AssetCreate]) -> None:
    configured_limit = min(settings.max_batch_size, 500)
    if len(assets) > configured_limit:
        raise HTTPException(
            status_code=413,
            detail=f"Batch size exceeds the configured limit of {configured_limit}.",
        )


@router.post("", response_model=ApiResponse[PredictionResult])
def predict_one(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    bundle: ModelBundle = Depends(require_model_bundle),
) -> ApiResponse[PredictionResult]:
    _check_batch_size([payload])
    result = predict_and_record(db, [payload], bundle)[0]
    return ApiResponse(message="Maintenance priority predicted.", data=result)


@router.post("/batch", response_model=ApiResponse[list[PredictionResult]])
def predict_batch(
    payload: PredictionBatchRequest,
    db: Session = Depends(get_db),
    bundle: ModelBundle = Depends(require_model_bundle),
) -> ApiResponse[list[PredictionResult]]:
    _check_batch_size(payload.assets)
    results = predict_and_record(db, payload.assets, bundle)
    return ApiResponse(message="Batch priorities predicted.", data=results)
