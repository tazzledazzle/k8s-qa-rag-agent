"""OpenTelemetry setup: W3C propagation, OTLP gRPC exporter."""
import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


def setup_telemetry(service_name: str, otlp_endpoint: str) -> None:
    if not otlp_endpoint:
        return
    disable = os.environ.get("OTEL_DISABLE_TRACING", "").lower() in ("true", "1")
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    if not disable:
        endpoint = otlp_endpoint.replace("http://", "").replace("https://", "")
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    set_global_textmap(TraceContextTextMapPropagator())


def instrument_app(app):  # noqa: ANN001
    FastAPIInstrumentor.instrument_app(app)
