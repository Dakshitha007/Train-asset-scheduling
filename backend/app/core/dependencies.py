"""FastAPI dependencies shared by route modules."""

from fastapi import HTTPException, Request, status

from backend.app.core.model_registry import ModelBundle


def require_model_bundle(request: Request) -> ModelBundle:
    """Retrieve the single startup-loaded model or report service unavailability."""
    bundle = getattr(request.app.state, "model_bundle", None)
    if bundle is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The trained model is unavailable. Check model artifact paths and startup logs.",
        )
    return bundle
