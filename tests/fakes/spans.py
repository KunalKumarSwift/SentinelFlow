"""An OpenTelemetry tracer that keeps finished spans in memory (no global provider)."""

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Tracer


def span_recorder() -> tuple[Tracer, InMemorySpanExporter]:
    """Return a tracer and the exporter that collects its spans."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider.get_tracer("tests"), exporter
