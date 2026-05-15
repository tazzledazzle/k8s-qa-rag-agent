# OpenTelemetry Demo Platform

A portable, interview-ready sandbox: multi-service app with **Kotlin** API + Temporal worker, **one Python agent** (LangChain + Ollama), full OpenTelemetry instrumentation, W3C trace propagation, [temporalio/auto-setup](https://hub.docker.com/r/temporalio/auto-setup), and [Grafana otel-lgtm](https://grafana.com/docs/opentelemetry/docker-lgtm).

## Architecture

- **API (Kotlin, Ktor)** — Entrypoint `POST /chat`; starts Temporal workflow, returns result. OTel + W3C.
- **Worker (Kotlin)** — Temporal workflow + activity; activity calls Agent via HTTP. OTel + W3C.
- **Agent (Python, FastAPI)** — LangChain pipeline + Ollama; `POST /invoke`. OTel Python SDK.
- **Infrastructure** — Temporal (`temporalio/auto-setup`), Grafana otel-lgtm (Collector + Tempo + Grafana).

```
Client → API → Temporal → Worker → Agent (LangChain)
         ↓         ↓         ↓         ↓
              OTel Collector → Tempo → Grafana
```

## Prerequisites

- **Ollama** (local LLM): [Install](https://ollama.ai) and pull a model, e.g. `ollama pull llama3.2`
- **Docker** and **Docker Compose** (for Temporal + Grafana)
- **JDK 17+** and **Gradle** (for Kotlin services)
- **Python 3.11+** (for Agent service)

**Configuration:** All env vars and defaults are in [CONFIG.md](CONFIG.md).

## Quick Start

1. **Start infrastructure**

   ```bash
   docker compose up -d
   ```

   - Temporal: gRPC on `localhost:7233`
   - Grafana: http://localhost:3000 (admin / admin)
   - OTLP: gRPC `localhost:4317`, HTTP `localhost:4318`

2. **Start services** (in this order, in separate terminals)

   ```bash
   # (1) Agent (Python) — requires Ollama running with a model
   cd agent && pip install -r requirements.txt && python -m agent.main

   # (2) Worker (Kotlin)
   cd worker && ./gradlew run

   # (3) API (Kotlin)
   cd api && ./gradlew run
   ```

3. **Smoke check** — confirm each service is up before sending chat:

   - **API:** `GET http://localhost:8080/health` — returns `{"status":"ok","service":"otel-demo-api"}`.
   - **Agent:** `GET http://localhost:8000/health` — returns `{"status":"ok","service":"otel-demo-agent"}`.

   Quick validation: `curl -s http://localhost:8080/health` should include `"service":"otel-demo-api"`. If it says `"otel-demo-agent"` instead, a stale Agent process is on port 8080 — kill it and restart.

4. **Send a request**

   ```bash
   curl -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'
   ```

   **POST /chat** requires **Temporal**, **Worker**, and **Agent** to be running; until they are up, the API returns **503** with `{"error":"temporal_unavailable",...}`. Use `make run` or start infra then Agent, Worker, and API (see [integration/README.md](integration/README.md)) for the full flow.

   Use port **8080** (API preferred default). If you get `404 Not Found` or `{"detail":"Not Found"}`, you are likely hitting the wrong process—check that `GET /health` returns `"service":"otel-demo-api"`. More examples in `test-data/sample_requests.json` (each has a `body` with `"message"` only).

5. **View traces in Grafana**

   - Open Grafana at http://localhost:3000 (login: admin / admin).
   - Go to **Explore** → select **Tempo**.
   - Find the trace: use the **TraceQL** tab with `resource.service.name="otel-demo-api"` (service names are `otel-demo-api`, `otel-demo-worker`, `otel-demo-agent` — not `"api"`). String values must be quoted. Alternatively use **Search** or time range.
   - You should see one trace with spans for API, worker, and agent.

**Troubleshooting**

- **404 or `{"detail":"Not Found"}` on `/chat`** — You are likely hitting the Agent (or another app), not the API. The API returns `{"status":"ok","service":"otel-demo-api"}` for `GET /health`; the Agent returns `{"status":"ok","service":"otel-demo-agent"}`. Use port 8080 for the API; if 8080 is in use the API fails at startup with a clear message (set `API_PORT` to override). See [CONFIG.md](CONFIG.md).
- **0 traces in Tempo** — (1) Send at least one request to the API `/chat` (correct port). (2) In TraceQL use `resource.service.name="otel-demo-api"`.

## Project Layout

- `api/` — Kotlin Ktor API (Temporal client, OTel)
- `worker/` — Kotlin Temporal worker (workflow, activities, HTTP to Agent)
- `agent/` — Python FastAPI + LangChain + Ollama (OTel)
- `docs/` — ARCHITECTURE.md, USE_CASES.md, INTERVIEW_SCRIPT.md
- `test-data/` — Fixtures and sample requests
- **E2E steps:** See [integration/README.md](integration/README.md) for full run order, health checks, and trace verification.

## Testing

- **Unit tests**
  - **Kotlin**: `./gradlew :api:test :worker:test`
  - **Agent**: `cd agent && .venv/bin/python -m pytest tests/ -v` (create venv and install deps first; see [agent/README.md](agent/README.md)).
- **Integration (E2E)**: Start infra + API + Worker + Agent, then `curl -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'`. See [docs/TESTING.md](docs/TESTING.md) for full steps and test data location.
- **Prerequisite for local/demo**: Ollama installed and a model pulled (e.g. `ollama pull llama3.2`).

## License

MIT
