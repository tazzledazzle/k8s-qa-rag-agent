# Architecture

**Analysis Date:** 2025-03-03

## Pattern Overview

**Overall:** Multi-service request-response with Temporal workflow orchestration and shared OpenTelemetry tracing.

**Key Characteristics:**
- Single entrypoint (Kotlin API); workflow runs in Temporal; worker executes workflow and activity; activity calls Python agent over HTTP.
- W3C trace context propagated so one request yields one trace across API, worker, and agent.
- No shared database for business data; Temporal uses Postgres for workflow state.

## Layers

**API (Kotlin):**
- Purpose: HTTP entrypoint; start Temporal workflow and return result.
- Location: `api/src/main/kotlin/dev/otel/demo/api/`
- Contains: `Main.kt` (server bootstrap, OTel init, port resolution), `Telemetry.kt`, `TemporalClientFactory.kt`, `plugins/` (routing, serialization), `routes/` (health, chat), `models/`.
- Depends on: `contracts`, Ktor, Temporal client, OpenTelemetry.
- Used by: External clients (e.g. curl, frontends).

**Worker (Kotlin):**
- Purpose: Temporal worker; runs AgentWorkflow and RunAgent activity; activity calls Agent via HTTP.
- Location: `worker/src/main/kotlin/dev/otel/demo/worker/`
- Contains: `Main.kt` (worker registration, env config), `Telemetry.kt`, `AgentWorkflowImpl.kt`, `RunAgentActivity.kt`, `RunAgentActivityInterface.kt`, `client/AgentClient.kt`.
- Depends on: `contracts`, Temporal SDK, Ktor client, OpenTelemetry.
- Used by: Temporal (task queue); no direct external HTTP.

**Agent (Python):**
- Purpose: LangChain + Ollama; exposes `POST /invoke` for the worker.
- Location: `agent/agent/`
- Contains: `main.py` (FastAPI app, `/health`, `/invoke`), `chain.py` (LLM, tools, executor), `telemetry.py` (OTel setup, FastAPI instrumentation).
- Depends on: FastAPI, LangChain, Ollama, OpenTelemetry Python.
- Used by: Worker (HTTP client in `worker/.../client/AgentClient.kt`).

**Contracts (Kotlin):**
- Purpose: Shared Temporal workflow/activity interfaces so API and worker agree on types and task queue.
- Location: `contracts/src/main/kotlin/dev/otel/demo/contracts/`
- Contains: `AgentWorkflow.kt` (WorkflowInterface, `run(message: String): String`).
- Depends on: Temporal SDK only.
- Used by: API (workflow stub), worker (workflow impl, activity interface in worker module).

## Data Flow

**Chat request flow:**

1. Client sends `POST /chat` with `{"message":"..."}` to API (Ktor).
2. API (`api/.../routes/ChatRoutes.kt`) receives body, creates Temporal client via `TemporalClientFactory`, starts workflow with message (`api/.../TemporalClientFactory.kt`).
3. Temporal schedules workflow on task queue `agent-task-queue`; worker (`worker/.../AgentWorkflowImpl.kt`) runs workflow, invokes RunAgent activity with same message.
4. Activity implementation (`worker/.../RunAgentActivity.kt`) calls `agentInvoke(agentBaseUrl, message)` in `worker/.../client/AgentClient.kt`; Ktor client POSTs to `{AGENT_BASE_URL}/invoke` with `{"message": message}`.
5. Agent (`agent/agent/main.py`) handles `POST /invoke`, runs LangChain executor (`agent/agent/chain.py`), returns `{"reply":"..."}`.
6. Activity returns reply to workflow; workflow returns to API; API responds with `ChatResponse(reply)` to client.

**State Management:**
- Stateless API and Agent. Workflow state and history live in Temporal (Postgres). No in-memory session store.

## Key Abstractions

**AgentWorkflow:**
- Purpose: Temporal workflow interface; single method `run(message: String): String`.
- Examples: `contracts/src/main/kotlin/dev/otel/demo/contracts/AgentWorkflow.kt` (interface), `worker/.../AgentWorkflowImpl.kt` (implementation).
- Pattern: Workflow starts activity stub with timeout; activity does HTTP to agent.

**RunAgentActivityInterface / RunAgentActivity:**
- Purpose: Activity interface and implementation; single unit of work that calls the agent.
- Examples: `worker/.../RunAgentActivityInterface.kt`, `worker/.../RunAgentActivity.kt`, `worker/.../client/AgentClient.kt`.
- Pattern: Interface in worker module; implementation holds `agentBaseUrl` and delegates to `agentInvoke`.

**TemporalClientFactory / AgentWorkflowClient:**
- Purpose: Create Temporal client and workflow stub for API.
- Examples: `api/.../TemporalClientFactory.kt`. Task queue and workflow ID (timestamp-based) set in options.

## Entry Points

**API:**
- Location: `api/src/main/kotlin/dev/otel/demo/api/Main.kt` (mainClass `dev.otel.demo.api.MainKt`).
- Triggers: Process start (`./gradlew run` or equivalent).
- Responsibilities: Init OTel, resolve port (API_PORT or 8080..8089), start Netty server with routing and serialization.

**Worker:**
- Location: `worker/src/main/kotlin/dev/otel/demo/worker/Main.kt` (mainClass `dev.otel.demo.worker.MainKt`).
- Triggers: Process start.
- Responsibilities: Init OTel, connect to Temporal, register workflow and activity, start worker, block.

**Agent:**
- Location: `agent/agent/main.py` (`python -m agent.main`; `app` for uvicorn).
- Triggers: Process start; uvicorn runs `agent.main:app`.
- Responsibilities: Init OTel (if endpoint set), create FastAPI app with lifespan (agent executor), mount routes, listen on AGENT_PORT (default 8000).

## Error Handling

**Strategy:** Exceptions propagate where possible; API chat route uses `runCatching` and rethrows so Ktor returns 500; no central error handler or error DTOs.

**Patterns:**
- API `Main.kt`: Catch `BindException` for port in use; log and rethrow.
- `ChatRoutes.kt`: `runCatching` on receive and workflow run; log to stderr and rethrow.
- Worker/Agent: No explicit error handling in activity or agent; failures surface as workflow failure or HTTP 500.

## Cross-Cutting Concerns

**Logging:** stderr/println in API (e.g. chat route); worker logs startup; no structured logger or log levels.

**Validation:** Pydantic for Agent request body (`InvokeRequest`); Ktor/Jackson for API (`ChatRequest`). No explicit validation lib; missing/invalid body leads to parse error.

**Authentication:** None.

---

*Architecture analysis: 2025-03-03*
