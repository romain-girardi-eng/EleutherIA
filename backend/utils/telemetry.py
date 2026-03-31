#!/usr/bin/env python3
"""
OpenTelemetry Tracing for EleutherIA

Provides distributed tracing and observability:
- Automatic request tracing
- Custom span creation for RAG pipelines
- Integration with Jaeger/Tempo/OTLP backends

Usage:
    from utils.telemetry import tracer, trace_span

    with trace_span("graphrag_query", attributes={"query": query}):
        result = await process_query(query)
"""

import logging
import os
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry, gracefully degrade if not available
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import Status, StatusCode

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None  # type: ignore[assignment]
    TracerProvider = None  # type: ignore[assignment, misc]
    logger.info("OpenTelemetry not installed, tracing disabled")


# Global tracer instance
_tracer: Any = None


def init_telemetry(
    service_name: str = "eleutheria-api",
    otlp_endpoint: str | None = None,
    enabled: bool = True,
) -> bool:
    """
    Initialize OpenTelemetry tracing.

    Args:
        service_name: Name of the service for traces
        otlp_endpoint: OTLP collector endpoint (e.g., "http://jaeger:4317")
        enabled: Whether to enable tracing

    Returns:
        True if tracing was initialized, False otherwise
    """
    global _tracer

    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available, tracing disabled")
        return False

    if not enabled:
        logger.info("Tracing disabled by configuration")
        return False

    # Get endpoint from env if not provided
    endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        logger.info("No OTLP endpoint configured, tracing disabled")
        return False

    try:
        # Create resource with service info
        resource = Resource.create({
            "service.name": service_name,
            "service.version": os.getenv("APP_VERSION", "3.0.0"),
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        })

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Add OTLP exporter
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer
        _tracer = trace.get_tracer(__name__)

        logger.info(
            "otel_initialized",
            service=service_name,
            endpoint=endpoint,
        )
        return True

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        return False


def instrument_app(app: Any) -> None:
    """
    Instrument FastAPI app and common libraries.

    Args:
        app: FastAPI application instance
    """
    if not OTEL_AVAILABLE:
        return

    try:
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented for tracing")

        # Instrument HTTPX (used for external API calls)
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumented for tracing")

        # Instrument Redis
        RedisInstrumentor().instrument()
        logger.info("Redis instrumented for tracing")

    except Exception as e:
        logger.warning(f"Failed to instrument some libraries: {e}")


def get_tracer() -> Any:
    """Get the global tracer instance."""
    global _tracer
    if _tracer is None and OTEL_AVAILABLE:
        _tracer = trace.get_tracer(__name__)
    return _tracer


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    record_exception: bool = True,
):
    """
    Context manager for creating traced spans.

    Args:
        name: Span name
        attributes: Optional attributes to add to span
        record_exception: Whether to record exceptions

    Example:
        with trace_span("process_query", {"query": query}):
            result = process(query)
    """
    tracer = get_tracer()

    if tracer is None:
        # No-op if tracing not available
        yield None
        return

    with tracer.start_as_current_span(name) as span:
        try:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
            yield span
        except Exception as e:
            if record_exception:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def add_span_attribute(key: str, value: Any) -> None:
    """Add an attribute to the current span."""
    if not OTEL_AVAILABLE:
        return

    span = trace.get_current_span()
    if span:
        span.set_attribute(key, str(value))


def add_span_event(name: str, attributes: dict[str, Any] | None = None) -> None:
    """Add an event to the current span."""
    if not OTEL_AVAILABLE:
        return

    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes=attributes or {})


def set_span_status(success: bool, message: str = "") -> None:
    """Set the status of the current span."""
    if not OTEL_AVAILABLE:
        return

    span = trace.get_current_span()
    if span:
        if success:
            span.set_status(Status(StatusCode.OK, message))
        else:
            span.set_status(Status(StatusCode.ERROR, message))


# Pre-defined span names for consistency
class SpanNames:
    """Standard span names for EleutherIA operations."""

    # GraphRAG
    GRAPHRAG_QUERY = "graphrag.query"
    GRAPHRAG_RETRIEVE = "graphrag.retrieve"
    GRAPHRAG_GENERATE = "graphrag.generate"

    # Agentic GraphRAG
    GRAPHRAG_QUERY_AGENTIC = "graphrag.query.agentic"
    GRAPHRAG_PLANNING = "graphrag.planning"
    GRAPHRAG_RETRIEVAL = "graphrag.retrieval"
    GRAPHRAG_REASONING = "graphrag.reasoning"
    GRAPHRAG_VERIFICATION = "graphrag.verification"

    # Search
    SEARCH_HYBRID = "search.hybrid"
    SEARCH_SEMANTIC = "search.semantic"
    SEARCH_FULLTEXT = "search.fulltext"

    # KG
    KG_LOOKUP = "kg.lookup"
    KG_TRAVERSE = "kg.traverse"
    KG_SEARCH = "kg.search"

    # LLM
    LLM_GENERATE = "llm.generate"
    LLM_EMBED = "llm.embed"

    # Database
    DB_QUERY = "db.query"
    DB_INSERT = "db.insert"

    # Cache
    CACHE_GET = "cache.get"
    CACHE_SET = "cache.set"
