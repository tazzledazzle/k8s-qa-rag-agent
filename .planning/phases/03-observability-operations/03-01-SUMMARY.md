# Plan 03-01 summary — OBS-01 (correlation + structured logs)

**Executed:** 2026-05-15  
**Requirements:** OBS-01

## Decisions

- **Structured logs:** Single JSON **stdout** handler on the root logger (`JsonFormatter` from `pythonjsonlogger.json` with fallback import path).
- **Correlation:** `contextvars` + `X-Correlation-ID` middleware; filter attaches `correlation_id` to every `LogRecord` for assertions and log processors.
- **Lifespan:** `create_app_lifespan(service_name)` configures logging, optional OTEL, and `shutdown_otel()` on exit.

## Delivered

- `services/common/observability.py` — middleware, JSON logging, OTEL FastAPI hook (gated on `OTEL_EXPORTER_OTLP_ENDPOINT`).
- `services/qa_agent/main.py`, `services/retriever/main.py` — lifespan + middleware.
- `services/qa_agent/tools.py` — outbound retriever calls send `X-Correlation-ID` when set.
- `tests/test_correlation_id.py` — correlation propagation and log attachment (mocks for external deps).

## Verification

- `pytest tests/test_correlation_id.py` and full `pytest tests/` (see execute session / CI).
