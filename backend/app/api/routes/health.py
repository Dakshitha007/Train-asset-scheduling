"""Root and readiness endpoints."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.database.database import get_db
from backend.app.database.schemas import ApiResponse, HealthStatus

router = APIRouter(tags=["Health"])


@router.get("/", response_model=ApiResponse[dict[str, str]])
def root() -> ApiResponse[dict[str, str]]:
    return ApiResponse(
        message="RailOpt AI backend is online.",
        data={"service": "RailOpt AI", "api_version": "1.0.0"},
    )


@router.get("/health", response_model=ApiResponse[HealthStatus])
def health(request: Request, db: Session = Depends(get_db)) -> ApiResponse[HealthStatus]:
    model_bundle = getattr(request.app.state, "model_bundle", None)
    database_connected = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_connected = False
    model_loaded = model_bundle is not None
    ready = model_loaded and database_connected
    if not ready:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": "One or more required dependencies are unavailable.",
                "data": {
                    "status": "degraded",
                    "model_loaded": model_loaded,
                    "database_connected": database_connected,
                    "model_version": getattr(model_bundle, "model_version", None),
                },
            },
        )
    return ApiResponse(
        message="Application is healthy.",
        data=HealthStatus(
            status="healthy",
            model_loaded=True,
            database_connected=True,
            model_version=model_bundle.model_version,
        ),
    )
