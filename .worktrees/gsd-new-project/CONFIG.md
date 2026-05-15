# Configuration reference

Single reference for environment variables and defaults used by otel-demo-platform. Linked from [README.md](README.md), [integration/README.md](integration/README.md), and [agent/README.md](agent/README.md).

**Preferred defaults (Phase 1):** API on **8080**, Agent on **8000**. Set `API_PORT` / `AGENT_PORT` only when you need to avoid conflicts. Infra (Temporal, Grafana) use fixed ports below.

---

## API (Kotlin, Ktor)

| Variable                      | Default                                       | Description                                                                                                            |
|-------------------------------|-----------------------------------------------|------------------------------------------------------------------------------------------------------------------------|
| `API_PORT`                    | `8080` when unset                             | HTTP port. When unset, API uses 8080 and fails with a clear message if 8080 is in use. Set `API_PORT` to force a specific port (process will fail if that port is in use). |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317`                       | OTLP gRPC endpoint for traces.                                                                                         |
| `OTEL_DISABLE_TRACING`       | unset                                         | When set to `true` or `1`, disables trace export (for interview: broken observability scenario). See [docs/BROKEN_OBSERVABILITY.md](docs/BROKEN_OBSERVABILITY.md). |
| `API_AUTH_ENABLED`           | unset                                         | When `true` or `1`, enables simple auth for `POST /chat` (401 on missing/invalid token).                              |
| `API_AUTH_TOKEN`             | unset                                         | Shared API token expected in the `Authorization` header (plain or `Bearer <token>`) when auth is enabled.             |
| `CHAT_RATE_LIMIT_ENABLED`    | unset                                         | When `true` or `1`, enables in-process rate limiting for `POST /chat`.                                                |
| `CHAT_RATE_LIMIT_PER_MINUTE` | unset                                         | Maximum number of `POST /chat` requests per minute per API instance when rate limiting is enabled.                    |

---

## Worker (Kotlin, Temporal)

| Variable                      | Default                 | Description                                                     |
|-------------------------------|-------------------------|-----------------------------------------------------------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP gRPC endpoint for traces.                                  |
| `OTEL_DISABLE_TRACING`       | unset                   | When `true` or `1`, disables trace export (broken observability scenario). See [docs/BROKEN_OBSERVABILITY.md](docs/BROKEN_OBSERVABILITY.md). |
| `TEMPORAL_ADDRESS`            | `localhost:7233`        | Temporal gRPC address.                                          |
| `TEMPORAL_TASK_QUEUE`         | `agent-task-queue`      | Task queue for workflows.                                       |
| `AGENT_BASE_URL`              | `http://localhost:8000` | Base URL of the Agent service (`POST {AGENT_BASE_URL}/invoke`). |

---

## Agent (Python, FastAPI)

| Variable                      | Default                                              | Description                                                                                        |
|-------------------------------|------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| `AGENT_PORT`                  | `8000` when unset                                   | HTTP port. When unset, Agent uses 8000 only; if 8000 is in use the process exits with a clear message. Set `AGENT_PORT` to override. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317`                              | OTLP gRPC endpoint for traces.                                                                     |
| `OTEL_DISABLE_TRACING`       | unset                                                | When `true` or `1`, disables trace export (broken observability scenario). See [docs/BROKEN_OBSERVABILITY.md](docs/BROKEN_OBSERVABILITY.md). |
| `OLLAMA_BASE_URL`             | `http://localhost:11434`                             | Ollama API URL.                                                                                    |
| `OLLAMA_MODEL`                | `llama3.2`                                           | Model name (e.g. after `ollama pull llama3.2`).                                                    |
| `AGENT_LLM_OFF`               | unset                                                | When set to `1` or `true`, the agent uses a stub executor (no Ollama). Use for CI or environments without GPU/Ollama. See [agent/README.md](agent/README.md) and docs. |
| `AGENT_FAIL_ALL_REQUESTS`    | unset                                                | When set to `1` or `true`, `/invoke` immediately returns 5xx and marks spans/logs as agent failures (for the \"Agent/LLM error spike\" incident demo). |
| `AGENT_AUTH_ENABLED`         | unset                                                | When `true` or `1`, enables simple auth for `/invoke` (401 on missing/invalid token).                                 |
| `AGENT_AUTH_TOKEN`           | unset                                                | Shared token expected in the `Authorization` header (plain or `Bearer <token>`) when Agent auth is enabled.          |

---

## Infrastructure (Docker Compose)

| Service             | Port(s)                                             | Notes                                                                                          |
|---------------------|-----------------------------------------------------|------------------------------------------------------------------------------------------------|
| Temporal            | `7233` (gRPC)                                       | `temporalio/auto-setup`.                                                                      |
| Grafana (otel-lgtm) | `3000` (UI), `4317` (OTLP gRPC), `4318` (OTLP HTTP) | Grafana + Tempo + collector. Admin defaults are demo-only (`admin` / `admin`) unless overridden. |
| Postgres            | `5432`                                              | Used by Temporal. In hardened mode, not exposed directly to the host.                         |

### Infrastructure environment variables (via Docker Compose)

These variables are consumed by `docker-compose.yml` and `docker-compose.hardened.yml`:

| Variable                      | Default (demo mode)                 | Description                                                                                         |
|-------------------------------|-------------------------------------|-----------------------------------------------------------------------------------------------------|
| `TEMPORAL_DB_USER`           | `temporal_demo`                     | Postgres user for Temporal metadata DB. Override for non-demo deployments.                         |
| `TEMPORAL_DB_PASSWORD`       | `temporal_demo`                     | Postgres password for Temporal DB. Override for non-demo deployments.                              |
| `TEMPORAL_DB_NAME`           | `temporal`                          | Postgres database name for Temporal.                                                               |
| `OTEL_LGTM_ADMIN_USER`      | `admin`                             | Grafana admin username. In hardened mode you MUST set this to a non-default value.                 |
| `OTEL_LGTM_ADMIN_PASSWORD`  | `admin`                             | Grafana admin password. In hardened mode you MUST set this to a strong, non-default value.        |

**Modes:**

- **Demo mode (default):** `docker compose up -d` uses the defaults above for fast local setup.
- **Hardened mode (illustrative):** `docker compose -f docker-compose.yml -f docker-compose.hardened.yml up -d` requires non-default values for credentials and removes direct Postgres host exposure.

---

## Run order (recommended)

1. Start infra: `docker compose up -d`
2. Start **Agent** (needs Ollama + model): `cd agent && python -m agent.main`
3. Start **Worker**: `cd worker && ./gradlew run`
4. Start **API**: `cd api && ./gradlew run`

Or use the one-command target (Makefile / scripts) that starts infra + all three apps with preferred defaults (Phase 1).
