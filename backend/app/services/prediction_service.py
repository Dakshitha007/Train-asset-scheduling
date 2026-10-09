"""Priority inference and prediction audit persistence."""

from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.model_registry import ModelBundle
from backend.app.database.models import AuditLog, PredictionRecord
from backend.app.database.schemas import AssetCreate, PredictionResult
from backend.app.services.asset_service import upsert_asset
from backend.app.utils.preprocessing import prepare_model_features
from backend.app.utils.validators import ModelContractError, validate_prediction_values


def _recommendation(priority_score: float) -> str:
    if priority_score >= 90:
        return "Urgent engineering review"
    if priority_score >= 75:
        return "Plan maintenance in the next available block"
    return "Continue routine monitoring"


def predict_priority_values(
    assets: Sequence[AssetCreate], bundle: ModelBundle
) -> list[float]:
    """Run inference against the startup-loaded model and saved transforms."""
    try:
        features = prepare_model_features(assets, bundle)
        raw_predictions = bundle.model.predict(features)
        return validate_prediction_values(raw_predictions, len(assets))
    except ModelContractError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Loaded model preprocessing artifacts are inconsistent.",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Loaded model preprocessing artifacts are unavailable.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Priority inference failed for the supplied feature data.",
        ) from exc


def predict_and_record(
    db: Session,
    assets: Sequence[AssetCreate],
    bundle: ModelBundle,
) -> list[PredictionResult]:
    """Predict a batch and persist current asset state plus immutable scores."""
    predictions = predict_priority_values(assets, bundle)
    results = [
        PredictionResult(
            asset_id=asset.asset_id,
            predicted_priority_score=score,
            recommended_action=_recommendation(score),
            model_version=bundle.model_version,
        )
        for asset, score in zip(assets, predictions, strict=True)
    ]
    try:
        for asset, result in zip(assets, results, strict=True):
            upsert_asset(db, asset)
            db.add(
                PredictionRecord(
                    asset_id=asset.asset_id,
                    predicted_priority_score=result.predicted_priority_score,
                    predicted_failure_probability=asset.predicted_failure_probability,
                    model_version=bundle.model_version,
                )
            )
            db.add(
                AuditLog(
                    action="prediction.created",
                    entity="prediction",
                    entity_id=asset.asset_id,
                    details=f"priority={result.predicted_priority_score:.4f}",
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return results
