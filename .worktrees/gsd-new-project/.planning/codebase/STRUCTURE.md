# Codebase Structure

**Analysis Date:** 2025-03-03

## Directory Layout

```
(repo root)
├── api/                    # Kotlin Ktor API (Temporal client, OTel)
│   ├── src/main/kotlin/dev/otel/demo/api/
│   │   ├── Main.kt
│   │   ├── Telemetry.kt
│   │   ├── TemporalClientFactory.kt
│   │   ├── models/
│   │   ├── plugins/
│   │   └── routes/
│   └── src/test/kotlin/.../api/routes/
├── worker/                 # Kotlin Temporal worker (workflow, activities, HTTP to Agent)
│   ├── src/main/kotlin/dev/otel/demo/worker/
│   │   ├── Main.kt
│   │   ├── Telemetry.kt
│   │   ├── AgentWorkflowImpl.kt
│   │   ├── RunAgentActivity.kt
│   │   ├── RunAgentActivityInterface.kt
│   │   └── client/
│   └── src/test/kotlin/.../worker/
├── agent/                  # Python FastAPI + LangChain + Ollama (OTel)
│   ├── agent/              # Package: main, chain, telemetry
│   └── tests/
├── contracts/              # Shared Temporal workflow interfaces (Kotlin)
│   └── src/main/kotlin/dev/otel/demo/contracts/
├── docs/                   # ARCHITECTURE, USE_CASES, TESTING, INTERVIEW_SCRIPT, LIVE_FEATURE
├── integration/            # E2E run order and verification (README)
├── test-data/              # sample_requests.json, mock_llm_responses.json
├── .planning/codebase/     # This analysis (STACK, INTEGRATIONS, ARCHITECTURE, etc.)
├── build.gradle.kts
├── settings.gradle.kts
└── docker-compose.yml      # Temporal + otel-lgtm + Postgres
```

## Directory Purposes

**api/:**
- Purpose: HTTP API and Temporal workflow client.
- Contains: Ktor app, health/chat routes, OTel init, Temporal client factory, plugins (routing, serialization).
- Key files: `api/src/main/kotlin/dev/otel/demo/api/Main.kt`, `routes/ChatRoutes.kt`, `TemporalClientFactory.kt`, `Telemetry.kt`.

**worker/:**
- Purpose: Temporal worker and activity implementation; HTTP client to Agent.
- Contains: Worker main, workflow impl, activity interface/impl, AgentClient.
- Key files: `worker/src/main/kotlin/dev/otel/demo/worker/Main.kt`, `AgentWorkflowImpl.kt`, `RunAgentActivity.kt`, `client/AgentClient.kt`.

**agent/:**
- Purpose: Python agent service (LangChain + Ollama).
- Contains: FastAPI app, chain/executor, telemetry; tests in `tests/`.
- Key files: `agent/agent/main.py`, `agent/agent/chain.py`, `agent/agent/telemetry.py`.

**contracts/:**
- Purpose: Shared Temporal workflow (and activity) interfaces for API and worker.
- Contains: Single interface `AgentWorkflow`; activity interface lives in worker.
- Key files: `contracts/src/main/kotlin/dev/otel/demo/contracts/AgentWorkflow.kt`.

**docs/:**
- Purpose: Architecture, use cases, testing, interview script, live-coding guide.
- Key files: `docs/ARCHITECTURE.md`, `docs/TESTING.md`, `docs/USE_CASES.md`, `docs/INTERVIEW_SCRIPT.md`, `docs/LIVE_FEATURE.md`.

**integration/:**
- Purpose: E2E run order and smoke checks.
- Key file: `integration/README.md`.

**test-data/:**
- Purpose: Sample request bodies and mock data for manual or scripted tests.
- Key files: `test-data/sample_requests.json`, `test-data/mock_llm_responses.json` (if present).

## Key File Locations

**Entry points:**
- `api/src/main/kotlin/dev/otel/demo/api/Main.kt`: API server.
- `worker/src/main/kotlin/dev/otel/demo/worker/Main.kt`: Temporal worker.
- `agent/agent/main.py`: Agent app and uvicorn entry.

**Configuration:**
- Root: `build.gradle.kts`, `settings.gradle.kts`, `docker-compose.yml`.
- Per service: `api/build.gradle.kts`, `worker/build.gradle.kts`, `contracts/build.gradle.kts`, `agent/pyproject.toml`.

**Core logic:**
- Chat flow: `api/.../routes/ChatRoutes.kt` → `api/.../TemporalClientFactory.kt` → `worker/.../AgentWorkflowImpl.kt` → `worker/.../RunAgentActivity.kt` → `worker/.../client/AgentClient.kt` → `agent/agent/main.py` → `agent/agent/chain.py`.
- Contracts: `contracts/.../AgentWorkflow.kt`; activity interface: `worker/.../RunAgentActivityInterface.kt`.

**Testing:**
- Kotlin: `api/src/test/.../routes/HealthRoutesTest.kt`, `ChatRoutesTest.kt`; `worker/src/test/.../RunAgentActivityTest.kt`.
- Python: `agent/tests/test_main.py`, `agent/tests/test_chain.py`.

## Naming Conventions

**Files:**
- Kotlin: PascalCase for types, e.g. `Main.kt`, `ChatRoutes.kt`, `AgentWorkflowImpl.kt`.
- Python: snake_case modules, e.g. `main.py`, `chain.py`, `telemetry.py`.

**Directories:**
- Kotlin: package path mirrors dirs, e.g. `dev/otel/demo/api/routes/`.
- Agent: package `agent` in `agent/agent/`; tests in `agent/tests/`.

## Where to Add New Code

**New API route:**
- Route: `api/src/main/kotlin/dev/otel/demo/api/routes/` (new or existing file); register in `api/.../plugins/Routing.kt`.
- Models: `api/.../models/Models.kt` or new file under `models/`.
- Tests: `api/src/test/.../routes/` next to existing route tests.

**New worker workflow/activity:**
- Workflow interface: `contracts/` if shared with API; implementation in `worker/.../`.
- Activity interface: `worker/.../RunAgentActivityInterface.kt` or new interface; impl in `worker/.../`.
- Register in `worker/.../Main.kt` (workflow types and activity instances).

**New agent endpoint or chain step:**
- Endpoint: `agent/agent/main.py`; chain/tools in `agent/agent/chain.py`.
- Tests: `agent/tests/` (test_main.py for app, test_chain.py for chain/tools).

**Shared contracts:**
- New workflow/activity interfaces: `contracts/src/main/kotlin/dev/otel/demo/contracts/`; keep worker-only activity interfaces in worker module.

## Special Directories

**api/bin/, worker/bin/, contracts/bin/:**
- Purpose: Gradle-run script and compiled output (e.g. main class).
- Generated: Yes (Gradle).
- Committed: Often no (gitignore); present in tree from local runs.

**agent/.venv/, .pytest_cache/:**
- Purpose: Python venv and pytest cache.
- Generated: Yes.
- Committed: No.

**build/, .gradle/:**
- Purpose: Gradle build output and cache.
- Generated: Yes.
- Committed: No.

---

*Structure analysis: 2025-03-03*
