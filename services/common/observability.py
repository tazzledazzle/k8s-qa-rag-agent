"""JSON logging, per-request correlation id, and optional OpenTelemetry for FastAPI apps."""

from __future__ import annotations

import contextvars
import logging
import os
import sys
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, cast

try:
    from pythonjsonlogger.json import JsonFormatter
except ImportError:
    from pythonjsonlogger.jsonlogger import JsonFormatter  # type: ignore[no-redef]
from starlette.middleware.base import BaseHTTPMiddleware  # type: ignore[import-not-found]
from starlette.requests import Request  # type: ignore[import-not-found]
from starlette.types import ASGIApp  # type: ignore[import-not-found]

if TYPE_CHECKING:
    from fastapi import FastAPI  # type: ignore[import-not-found]

correlation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)

CORRELATION_HEADER = "X-Correlation-ID"


class _CorrelationIdFilter(logging.Filter):
    """Attach correlation_id from context to every log record (empty string if unset)."""

    def filter(self, record: logging.LogRecord) -> bool:
        cid = correlation_id_var.get()
        record.correlation_id = cid if cid else ""
        return True


def _json_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_CorrelationIdFilter())
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s"
    handler.setFormatter(
        JsonFormatter(
            fmt=fmt,
            datefmt="%Y-%m-%dT%H:%M:%S",
            json_ensure_ascii=False,
        )
    )
    setattr(handler, "_k8s_qa_json_handler", True)
    return handler


def configure_json_logging() -> None:
    """Attach a single JSON stdout handler to the root logger (idempotent)."""
    root = logging.getLogger()
    if any(getattr(h, "_k8s_qa_json_handler", False) for h in root.handlers):
        return
    root.addHandler(_json_handler())
    root.setLevel(logging.INFO)


def shutdown_otel() -> None:
    """Flush OTLP spans on process exit."""
    try:
        from opentelemetry import trace  # type: ignore[import-not-found]

        provider = trace.get_tracer_provider()
        if hasattr(provider, "force_flush"):
            provider.force_flush()
        if hasattr(provider, "shutdown"):
            provider.shutdown()
    except Exception:
        pass


def init_otel_fastapi(app: object, service_name: str) -> None:
    """Instrument FastAPI and export traces when OTEL_EXPORTER_OTLP_ENDPOINT is set."""
    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        return
    app_f = cast(FastAPI, app)
    if getattr(app_f.state, "otel_instrumented", False):
        return
    endpoint = (os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or "").strip()
    if not endpoint:
        return
    try:
        from opentelemetry import trace  # type: ignore[import-not-found]
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore[import-not-found]
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore[import-not-found]
        from opentelemetry.sdk.resources import Resource  # type: ignore[import-not-found]
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore[import-not-found]
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore[import-not-found]
        from opentelemetry.trace import Span  # type: ignore[import-not-found]
    except ImportError:
        logging.getLogger(__name__).warning("OpenTelemetry packages not available; skipping OTEL")
        return

    def server_request_hook(span: Span, _scope: dict[str, Any]) -> None:
        cid = correlation_id_var.get()
        if cid and span.is_recording():
            span.set_attribute("correlation_id", cid)

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app_f, server_request_hook=server_request_hook)
    app_f.state.otel_instrumented = True


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Set correlation_id from X-Correlation-ID or UUID; log request start/finish."""

    def __init__(self, app: ASGIApp, service: str) -> None:
        super().__init__(app)
        self._service = service
        self._log = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        raw = (request.headers.get(CORRELATION_HEADER) or "").strip()
        cid = raw or str(uuid.uuid4())
        token = correlation_id_var.set(cid)
        start = time.perf_counter()
        self._log.info(
            "request_started",
            extra={
                "correlation_id": cid,
                "service": self._service,
                "method": request.method,
                "path": request.url.path,
            },
        )
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = int((time.perf_counter() - start) * 1000)
            self._log.exception(
                "request_failed",
                extra={
                    "correlation_id": cid,
                    "service": self._service,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            raise
        else:
            duration_ms = int((time.perf_counter() - start) * 1000)
            self._log.info(
                "request_finished",
                extra={
                    "correlation_id": cid,
                    "service": self._service,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            return response
        finally:
            correlation_id_var.reset(token)


def create_app_lifespan(service_name: str):
    from fastapi import FastAPI

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_json_logging()
        init_otel_fastapi(app, service_name)
        yield
        shutdown_otel()

    return lifespan
