"""Tracing is off unless an OTLP endpoint is configured."""

from opentelemetry.sdk.trace import Tracer as SdkTracer
from opentelemetry.trace import NoOpTracer
from pydantic import SecretStr

from sentinelflow.core.config import Settings
from sentinelflow.facades.tracing_facade import make_tracer

SECRET = SecretStr("s" * 32)


def test_no_endpoint_means_no_tracing() -> None:
    assert isinstance(make_tracer(Settings(jwt_secret=SECRET)), NoOpTracer)  # type: ignore[call-arg]
    empty = Settings(jwt_secret=SECRET, otlp_endpoint="")  # type: ignore[call-arg]
    assert isinstance(make_tracer(empty), NoOpTracer)


def test_endpoint_enables_an_exporting_tracer() -> None:
    # The exporter connects only when spans are flushed, so no collector is needed here.
    settings = Settings(jwt_secret=SECRET, otlp_endpoint="http://jaeger:4318")  # type: ignore[call-arg]
    assert isinstance(make_tracer(settings), SdkTracer)
