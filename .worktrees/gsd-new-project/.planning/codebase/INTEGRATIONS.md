# External Integrations

**Analysis Date:** 2025-03-03

## APIs & External Services

**Workflow engine:**
- Temporal — gRPC `localhost:7233` (default). API starts workflows; worker runs workflows and activities. SDK: `io.temporal:temporal-sdk`, `temporal-kotlin` 1.24.0. Config: `TEMPORAL_ADDRESS`, `TEMPORAL_TASK_QUEUE`. No auth in code.

**LLM (Agent only):**
- Ollama — HTTP (default `OLLAMA_BASE_URL=http://localhost:11434`). Used via `langchain-ollama` in `agent/agent/chain.py`. Config: `OLLAMA_BASE_URL`, `OLLAMA_MODEL` (default `llama3.2`).

## Data Storage

**Databases:**
- PostgreSQL 15 — Used only by Temporal (docker-compose: `postgres` service, user `temporal`). No app-level DB connection in API, worker, or agent.

**File Storage:**
- Local filesystem only (e.g. debug log path in `api/.../Main.kt`; not used for business data).

**Caching:**
- None.

## Authentication & Identity

**Auth Provider:**
- None. No auth on API `/chat` or `/health`, Agent `/invoke` or `/health`, or Temporal in the demo. Worker calls Agent over HTTP with no auth headers.

## Monitoring & Observability

**Tracing:**
- OpenTelemetry OTLP (gRPC). All three services export to `OTEL_EXPORTER_OTLP_ENDPOINT` (default `http://localhost:4317`). W3C trace context propagation in API and worker (`api/.../Telemetry.kt`, `worker/.../Telemetry.kt`); Agent uses TraceContextTextMapPropagator (`agent/agent/telemetry.py`). Collector: Grafana otel-lgtm in docker-compose (ports 4317 gRPC, 4318 HTTP).

**Error Tracking:**
- None (no Sentry or similar).

**Logs:**
- stdout/stderr (e.g. API/worker startup, chat route logs). No structured log aggregation in code.

## CI/CD & Deployment

**Hosting:**
- Not specified; demo runs locally. Docker Compose for Temporal + otel-lgtm only; API, worker, and agent run as separate processes.

**CI Pipeline:**
- GitHub Actions under `.github/workflows/` (CI: unit tests + e2e smoke).

## Environment Configuration

**Required env vars (for full flow):**
- `OTEL_EXPORTER_OTLP_ENDPOINT` — Optional; default `http://localhost:4317` (all three services).
- `API_PORT` — Optional; default or first free in 8080..8089 (API).
- `AGENT_PORT` — Optional; default 8000 or next available (Agent).
- `AGENT_BASE_URL` — Optional; default `http://localhost:8000` (Worker).
- `TEMPORAL_ADDRESS` — Optional; default `localhost:7233` (API, Worker).
- `TEMPORAL_TASK_QUEUE` — Optional; default `agent-task-queue` (API, Worker).
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL` — Optional for Agent; defaults `http://localhost:11434`, `llama3.2`.

**Secrets location:**
- No secrets in repo. Docker-compose Postgres uses plain env (temporal/temporal); not for production use.

## Webhooks & Callbacks

**Incoming:**
- API: `POST /chat`, `GET /health`. Agent: `POST /invoke`, `GET /health`. No webhook endpoints.

**Outgoing:**
- Worker → Agent: HTTP `POST {AGENT_BASE_URL}/invoke` with JSON `{"message":"..."}`. API → Temporal: gRPC workflow start. No other callbacks.

---

*Integration audit: 2025-03-03*
