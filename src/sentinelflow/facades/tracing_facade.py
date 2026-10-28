"""Choose the tracer from settings: OTLP export when an endpoint is set, else a no-op."""

from opentelemetry.trace import NoOpTracer, Tracer

from sentinelflow.core.config import Settings

SERVICE_NAME = "sentinelflow"


def make_tracer(settings: Settings) -> Tracer:
    """Return a tracer exporting spans over OTLP/HTTP, or a no-op one.

    The provider is created here rather than installed globally, so tests and several
    runtimes in one process never share tracing state.
    """
    if not settings.otlp_endpoint:  # unset or empty (Compose passes "" when not chosen)
        return NoOpTracer()
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(resource=Resource.create({"service.name": SERVICE_NAME}))
    exporter = OTLPSpanExporter(endpoint=f"{settings.otlp_endpoint.rstrip('/')}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter))
    return provider.get_tracer(SERVICE_NAME)
