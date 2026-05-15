# Trace-driven debugging walkthrough

Use **TraceQL** (primary) or the Grafana UI (fallback) to follow a chat request across API → worker → agent and reason about failures and latency.

## Prerequisites

- Infra and all three apps running (e.g. `make run` or follow [integration/README.md](../integration/README.md)).
- At least one `POST /chat` sent so a trace exists (e.g. `curl -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'`).

## 1. Follow one request (TraceQL)

1. Open Grafana → **Explore** → select **Tempo**.
2. Open the **TraceQL** tab.
3. Run a query to list traces for the API service:
   ```text
   { resource.service.name="otel-demo-api" }
   ```
4. Pick the latest trace from the results. The trace should show spans from **otel-demo-api**, **otel-demo-worker**, and **otel-demo-agent** in one request.

**Alternative: use the UI** — In Explore → Tempo, open the **Search** tab, choose “Service name” and select `otel-demo-api` (or use the query builder), then run Search and open a trace from the list.

## 2. TraceQL examples

- **By service name (API):** `{ resource.service.name="otel-demo-api" }`
- **By service name (worker):** `{ resource.service.name="otel-demo-worker" }`
- **By service name (agent):** `{ resource.service.name="otel-demo-agent" }`
- **By span name:** `{ name="POST /chat" }` or `{ name=~".*invoke.*" }`
- Use the time range picker (e.g. “Last 1 hour”) to narrow results.

**Alternative: use the UI** — Use the Search tab filters (Service name, Span name, etc.) and run Search; then open a trace to see the span list and timeline.

## 3. Identify which service failed

- In the trace view, check **span status** (e.g. Error) and **span events** (e.g. `agent.invocation.start` / `agent.invocation.end`).
- A span with status Error or an exception event indicates where the failure occurred (API, worker, or agent).
- **TraceQL** can filter by status, e.g. `{ resource.service.name="otel-demo-api" && status=error }` (syntax may vary by Tempo version).

**Alternative: use the UI** — Open the trace and scan the span list and timeline for red/error indicators and exception details.

## 4. Reason about latency

- In the trace view, compare **span durations** (parent vs child). The slowest span(s) show where time is spent (e.g. agent LLM call vs worker activity).
- Parent-child relationship: API → (Temporal) → worker activity → agent `/invoke`. The longest leaf span usually dominates total latency.

**Alternative: use the UI** — Use the trace timeline and span list to see duration per span and the parent-child hierarchy.

## 5. Domain attributes and events

Spans in this demo include:

- **Attributes:** `message.type` (chat / invoke), `workflow.id`, `task.queue` (worker/activity).
- **Events:** `agent.invocation.start`, `agent.invocation.end` (worker and agent).

Use these in TraceQL or in the UI to filter or inspect specific steps.

## 6. Small metrics story (latency + throughput)

This demo uses **traces and logs** as the primary observability signals. A **small metrics story** (e.g. chat request count, latency histogram per service) can be added by:

- Exposing OTLP **metrics** from the API, worker, and agent (counter for request count, histogram for duration) and sending them to the same OTLP endpoint (`http://localhost:4317`).
- Configuring **Grafana otel-lgtm** (or your collector) to accept OTLP metrics and expose them in Grafana (e.g. Explore → Prometheus/Mimir or a dashboard).

Once metrics are exported, you can correlate them with traces (e.g. high latency in a metric and then open a trace for that time range in Tempo).

## See also

- [CONFIG.md](../CONFIG.md) — Env vars and ports.
- [BROKEN_OBSERVABILITY.md](BROKEN_OBSERVABILITY.md) — What to do when traces stop showing up (e.g. config flag).
