"""FastAPI application factory and process lifecycle."""

from contextlib import asynccontextmanager
import logging
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.logging import configure_logging
from backend.app.core.model_registry import load_model_bundle
from backend.app.database.database import engine, initialize_database

logger = logging.getLogger(__name__)


def _error_response(
    *, message: str, data: Any = None, status_code: int
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            {"success": False, "message": message, "data": data}
        ),
    )


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.log_level)
    initialize_database()
    application.state.model_bundle = None
    try:
        application.state.model_bundle = load_model_bundle()
        logger.info(
            "model_loaded",
            extra={"model_version": application.state.model_bundle.model_version},
        )
    except Exception:
        logger.exception("model_unavailable_at_startup")
    try:
        yield
    finally:
        application.state.model_bundle = None
        engine.dispose()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Railway asset management, maintenance-priority inference, and "
            "constraint-based block scheduling."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "http_request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    @application.exception_handler(HTTPException)
    async def handle_http_exception(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        del request
        if isinstance(exc.detail, dict) and "message" in exc.detail:
            message = str(exc.detail["message"])
            data = exc.detail.get("data")
        else:
            message = str(exc.detail)
            data = None
        return _error_response(
            message=message,
            data=data,
            status_code=exc.status_code,
        )

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        del request
        return _error_response(
            message="Request validation failed.",
            data={"errors": jsonable_encoder(exc.errors())},
            status_code=422,
        )

    @application.exception_handler(IntegrityError)
    async def handle_integrity_error(
        request: Request, exc: IntegrityError
    ) -> JSONResponse:
        logger.info(
            "database_integrity_conflict",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        del exc
        return _error_response(
            message="The request conflicts with existing database state.",
            status_code=status.HTTP_409_CONFLICT,
        )

    @application.exception_handler(SQLAlchemyError)
    async def handle_database_error(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        logger.exception(
            "database_operation_failed",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        del request, exc
        return _error_response(
            message="A database operation could not be completed.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @application.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "unhandled_request_error",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        del exc
        return _error_response(
            message="An unexpected server error occurred.",
            data={"request_id": getattr(request.state, "request_id", None)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    application.include_router(api_router)
    return application


app = create_app()
