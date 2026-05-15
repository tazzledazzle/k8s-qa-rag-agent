# Technology Stack

**Analysis Date:** 2025-03-03

## Languages

**Primary:**
- Kotlin 1.9.24 (JVM 17) — API, worker, and shared contracts; see `api/build.gradle.kts`, `worker/build.gradle.kts`, `contracts/build.gradle.kts`.
- Python ≥3.11 — Agent service (FastAPI + LangChain); see `agent/pyproject.toml`.

**Secondary:**
- Not applicable (no other languages in service code).

## Runtime

**Environment:**
- JVM 17 (Kotlin modules); Gradle `jvmToolchain(17)` in each Kotlin subproject.
- Python 3.11+ (agent); `.python-version` at repo root and in `agent/`.

**Package Manager:**
- Gradle (Kotlin) — root `build.gradle.kts`, `settings.gradle.kts`; no wrapper version file inspected.
- uv / pip (Python) — `agent/pyproject.toml`, `agent/uv.lock`; agent README uses `pip install -e ".[dev]"`.

## Frameworks

**Core:**
- Ktor 2.3.9 — API server (Netty, ContentNegotiation, Jackson), and worker HTTP client (CIO, ContentNegotiation). See `api/build.gradle.kts`, `worker/build.gradle.kts`.
- FastAPI — Agent HTTP API; see `agent/agent/main.py` and `agent/pyproject.toml` (fastapi≥0.115.0).
- Temporal SDK 1.24.0 (Kotlin) — Workflow client in API, workflow + activity implementation in worker; see `api/build.gradle.kts`, `worker/build.gradle.kts`, `contracts/build.gradle.kts`.

**Testing:**
- JUnit 5 (Kotlin) — `kotlin-test-junit5`, `junit-platform-launcher`; Ktor `server-test-host` for API tests; `temporal-testing` for worker. See `api/build.gradle.kts`, `worker/build.gradle.kts`.
- pytest 8+ with pytest-asyncio (Agent); see `agent/pyproject.toml` and `agent/tests/`.

**Build/Dev:**
- Gradle (Kotlin) — multi-project: `api`, `worker`, `contracts`.
- Hatchling (Python wheel); pytest config in `[tool.pytest.ini_options]` in `agent/pyproject.toml`.

## Key Dependencies

**Critical:**
- `io.temporal:temporal-sdk` / `temporal-kotlin` 1.24.0 — Workflow orchestration; used in API (client), worker (client + worker), contracts (interfaces).
- `io.opentelemetry:opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp` 1.35.0 — Tracing and OTLP export in API and worker.
- `opentelemetry-instrumentation-annotations` 2.3.0 — Present in API/worker; manual OTel setup in `api/.../Telemetry.kt` and `worker/.../Telemetry.kt`.
- FastAPI, uvicorn, LangChain, langchain-ollama — Agent service and LLM pipeline; see `agent/agent/main.py`, `agent/agent/chain.py`.
- OpenTelemetry Python (api, sdk, exporter-otlp-proto-grpc, instrumentation-fastapi) — Agent tracing; see `agent/agent/telemetry.py`.

**Infrastructure:**
- Jackson (ktor-serialization-jackson, jackson-module-kotlin) — JSON in API and worker.
- Docker: `temporalio/auto-setup:1.24.2`, `grafana/otel-lgtm:latest`, Postgres 15 for Temporal; see `docker-compose.yml`.

## Configuration

**Environment:**
- Env vars only; no `.env` read by app code. API: `API_PORT`, `OTEL_EXPORTER_OTLP_ENDPOINT`; Worker: `OTEL_EXPORTER_OTLP_ENDPOINT`, `TEMPORAL_ADDRESS`, `TEMPORAL_TASK_QUEUE`, `AGENT_BASE_URL`; Agent: `OTEL_EXPORTER_OTLP_ENDPOINT`, `AGENT_PORT`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`. See `api/.../Main.kt`, `worker/.../Main.kt`, `api/.../TemporalClientFactory.kt`, `agent/agent/main.py`, `agent/agent/chain.py`.

**Build:**
- Root and subproject `build.gradle.kts`; `settings.gradle.kts` includes `api`, `worker`, `contracts`. Agent: `pyproject.toml` (no separate build config).

## Platform Requirements

**Development:**
- JDK 17+, Gradle, Python 3.11+, Ollama (for agent LLM). Docker + Docker Compose for Temporal and otel-lgtm. See root `README.md`.

**Production:**
- Same runtimes; deployment target not specified (portable demo). Temporal and OTLP collector (e.g. otel-lgtm) required for full flow.

---

*Stack analysis: 2025-03-03*
