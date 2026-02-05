"""OpenTelemetry instrumentation setup."""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from nexlayer.config.settings import get_settings


def setup_telemetry() -> None:
    """Initialise OpenTelemetry tracing.

    In production the OTLP exporter sends spans to a collector.
    In development / tests we fall back to a no-op or console exporter.
    """
    settings = get_settings()

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": "0.1.0",
            "deployment.environment": settings.app_env,
        }
    )

    provider = TracerProvider(resource=resource)

    # Only attach the OTLP exporter when an endpoint is configured and
    # we are not in a test/dev-only mode.
    if settings.otel_exporter_otlp_endpoint and settings.app_env != "test":
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        except Exception:
            # Gracefully degrade if the collector is unreachable
            pass

    trace.set_tracer_provider(provider)


def get_tracer(name: str = "nexlayer") -> trace.Tracer:
    return trace.get_tracer(name)
