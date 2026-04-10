"""OpenTelemetry setup for distributed tracing.

Configures OTLP exporter, auto-instruments FastAPI, SQLAlchemy, and httpx.
Disabled by default — enable with OTEL_ENABLED=true.
"""

import structlog
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from bookstore.config.settings import Settings

logger = structlog.get_logger()


def setup_telemetry(settings: Settings) -> None:
    """Initialize OpenTelemetry tracing with OTLP exporter."""
    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": settings.app_version,
            "deployment.environment": settings.environment,
        }
    )

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Auto-instrument httpx (must be done before FastAPI)
    HTTPXClientInstrumentor().instrument()

    logger.info(
        "opentelemetry_configured",
        service=settings.otel_service_name,
        endpoint=settings.otel_exporter_endpoint,
    )


def instrument_app(app: object) -> None:
    """Instrument a FastAPI application with OpenTelemetry."""
    FastAPIInstrumentor.instrument_app(app)  # type: ignore[arg-type]


def instrument_db_engine(engine: object) -> None:
    """Instrument a SQLAlchemy engine with OpenTelemetry."""
    SQLAlchemyInstrumentor().instrument(engine=engine)


def shutdown_telemetry() -> None:
    """Flush and shut down the tracer provider."""
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        provider.shutdown()
