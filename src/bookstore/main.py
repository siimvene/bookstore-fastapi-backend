from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from bookstore.api.books import router as books_router
from bookstore.api.dependencies import DbSession
from bookstore.config.database import get_engine
from bookstore.config.settings import get_settings
from bookstore.core.exceptions import (
    ProblemDetail,
    problem_detail_handler,
    request_validation_handler,
    unhandled_exception_handler,
)
from bookstore.config.telemetry import instrument_app, setup_telemetry, shutdown_telemetry
from bookstore.core.logging import configure_logging
from bookstore.core.middleware import RequestContextMiddleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    configure_logging()
    if settings.otel_enabled:
        setup_telemetry(settings)
    logger.info("application_starting", app=settings.app_name)
    yield
    if settings.otel_enabled:
        shutdown_telemetry()
    await get_engine().dispose()
    logger.info("application_stopped", app=settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()

    docs_url = f"{settings.api_prefix}/docs" if settings.enable_swagger_ui else None
    redoc_url = f"{settings.api_prefix}/redoc" if settings.enable_api_docs else None
    openapi_url = (
        f"{settings.api_prefix}/openapi.json" if settings.enable_api_docs else None
    )

    application = FastAPI(
        title=settings.app_title,
        description=settings.app_description,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    application.add_middleware(RequestContextMiddleware)

    if settings.cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=settings.cors_allow_methods,
            allow_headers=settings.cors_allow_headers,
            allow_credentials=True,
        )

    application.add_exception_handler(ProblemDetail, problem_detail_handler)  # type: ignore[arg-type]
    application.add_exception_handler(
        RequestValidationError, request_validation_handler
    )  # type: ignore[arg-type]
    application.add_exception_handler(Exception, unhandled_exception_handler)

    application.include_router(books_router, prefix=settings.api_prefix)

    @application.get(f"{settings.api_prefix}/health", response_model=None)
    async def health(db: DbSession) -> JSONResponse:
        try:
            await db.execute(text("SELECT 1"))
            return JSONResponse(content={"status": "UP"})
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"status": "DOWN", "detail": str(e)},
            )

    # Instrument with OpenTelemetry if enabled
    settings = get_settings()
    if settings.otel_enabled:
        instrument_app(application)

    return application


app = create_app()
