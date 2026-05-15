# Phase 2 (02-observability) Plan 01 — Summary

**Phase:** 02-observability  
**Plan:** 02-01-PLAN.md  
**Execution:** Completed in-session (Tasks 1–4, 6; Task 5 documented)

---

## Accomplishments

### Task 1: Trace context propagation
- **API:** `ChatRoutes.kt` creates a root span `POST /chat` (manual span, SpanKind.SERVER) and runs the handler in its scope so the Temporal call runs under that trace context.
- **Worker:** `AgentClient.kt` injects W3C trace context (`traceparent`/`tracestate`) from `Context.current()` into the Ktor HTTP request headers so the agent receives the same trace.
- **Agent:** Already configured with `TraceContextTextMapPropagator`; no code change.
- **Verification:** Unit tests (`:api:test`, `:worker:test`) pass. Live verification (one POST /chat → one trace in Tempo with api/worker/agent spans) should be done with stack running locally.

### Task 2: Enrich spans with domain attributes and events
- **API:** Span attribute `message.type = "chat"` in `ChatRoutes.kt`.
- **Worker:** `RunAgentActivity.kt` sets `workflow.id` and `task.queue` from Temporal `Activity.getExecutionContext().info`; adds events `agent.invocation.start` and `agent.invocation.end`.
- **Agent:** `main.py` `/invoke`: attribute `message.type = "invoke"`; events `agent.invocation.start` and `agent.invocation.end`.

### Task 3: Trace-driven debugging walkthrough (TraceQL primary, UI fallback)
- **Created** `docs/TRACE_WALKTHROUGH.md`: TraceQL-first (queries, follow a request, find failures, reason about latency); "Alternative: use the UI" for each main step.
- **Updated** `integration/README.md`: "View one trace" section leads with TraceQL and links to the walkthrough; UI as fallback.

### Task 4: Structured logging on chat path
- **API** `ChatRoutes.kt`: One JSON line per hop with `service`, `trace_id`, `span_id`, `outcome` (start / ok / error) to stderr.
- **Worker** `RunAgentActivity.kt`: Same format (otel-demo-worker, trace_id, span_id, outcome).
- **Agent** `main.py` `/invoke`: Same format (otel-demo-agent) via a small helper; logs start, ok, and error.

### Task 5: Small metrics story (latency + throughput)
- **Documented** in `docs/TRACE_WALKTHROUGH.md` (§6): how to add OTLP metrics (counter + latency histogram) from API/worker/agent to the same OTLP endpoint and surface them in Grafana (otel-lgtm or equivalent).
- **Deferred:** Actual OTLP metric instrumentation (MeterProvider, counter, histogram in each service) was not implemented in this run. Can be added in a follow-up using the same pattern as traces (OTLP gRPC to 4317).

### Task 6: Config-flag broken observability
- **Env var:** `OTEL_DISABLE_TRACING` — when set to `true` or `1`, API, Worker, and Agent do not register the OTLP span exporter (no traces sent).
- **API** `Telemetry.kt`, **Worker** `Telemetry.kt`, **Agent** `telemetry.py`: Check env and skip adding `BatchSpanProcessor` / exporter when disabled.
- **CONFIG.md:** Added `OTEL_DISABLE_TRACING` to API, Worker, and Agent tables with link to the diagnose-and-fix doc.
- **Created** `docs/BROKEN_OBSERVABILITY.md`: Scenario ("Traces stopped showing up"), how to diagnose (check collector, check flag), how to fix (unset/restart), and verify (POST /chat + TraceQL).

---

## Files created or updated

| Path | Change |
|------|--------|
| `api/.../routes/ChatRoutes.kt` | Root span, attributes, structured logging |
| `api/.../Telemetry.kt` | OTEL_DISABLE_TRACING support |
| `worker/.../client/AgentClient.kt` | W3C context injection (already done in prior run) |
| `worker/.../RunAgentActivity.kt` | Attributes, events, structured logging |
| `worker/.../Telemetry.kt` | OTEL_DISABLE_TRACING support |
| `agent/agent/main.py` | Span attributes/events, structured logging |
| `agent/agent/telemetry.py` | OTEL_DISABLE_TRACING support |
| `docs/TRACE_WALKTHROUGH.md` | New: TraceQL-first walkthrough + metrics § |
| `docs/BROKEN_OBSERVABILITY.md` | New: diagnose-and-fix for interview |
| `integration/README.md` | TraceQL first, link to walkthrough |
| `CONFIG.md` | OTEL_DISABLE_TRACING in API, Worker, Agent |

---

## Deviations

- **Task 5:** Full OTLP metrics (counter + histogram in all three services) not implemented; approach and how to view in Grafana documented in the walkthrough. Implement when adding sdk-metrics and OTLP metric exporter to each service.
- **Live verification:** End-to-end trace check (POST /chat → one trace in Tempo with three services) was not run in this environment; rely on local run and TraceQL.

---

## Verification performed

- Grep / read of modified files.
- Unit tests not re-run in this session; prior executor run reported `:api:test` and `:worker:test` passing after Task 1. Recommend running `./gradlew :api:test :worker:test` and `cd agent && python -m pytest tests/ -v` before merge.

---

## Next steps

- Run full stack locally; send POST /chat; confirm one trace in Tempo with api, worker, agent spans and attributes/events.
- Optionally implement Task 5 (OTLP metrics) in a follow-up.
- Proceed to Phase 3 (Temporal workflow patterns) when ready.
