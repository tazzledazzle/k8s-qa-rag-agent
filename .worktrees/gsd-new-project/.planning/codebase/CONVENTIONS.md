# Coding Conventions

**Analysis Date:** 2025-03-03

## Naming Patterns

**Files (Kotlin):**
- One main type per file; file name matches type (e.g. `Main.kt`, `ChatRoutes.kt`, `AgentWorkflowImpl.kt`, `RunAgentActivityInterface.kt`).
- Packages: `dev.otel.demo.api`, `dev.otel.demo.worker`, `dev.otel.demo.contracts`; subpackages `routes`, `plugins`, `models`, `client`.

**Files (Python):**
- Module names snake_case: `main.py`, `chain.py`, `telemetry.py`; package `agent`.

**Functions (Kotlin):**
- camelCase for functions and extension functions (e.g. `configureRouting()`, `healthRoutes()`, `resolvePort()`).
- Extension functions on framework types: `fun Application.configureRouting()`, `fun Routing.healthRoutes()`.

**Variables:**
- Kotlin: camelCase (e.g. `agentBaseUrl`, `taskQueue`, `otelEndpoint`).
- Python: snake_case (e.g. `agent_port_env`, `otlp_endpoint`, `base_url`).

**Types:**
- Kotlin: PascalCase data classes and interfaces (e.g. `ChatRequest`, `HealthResponse`, `AgentWorkflow`).
- Python: PascalCase for Pydantic models and classes (`InvokeRequest`, `InvokeResponse`).

## Code Style

**Formatting:**
- Kotlin: No explicit formatter config in repo (IDE/default).
- Python: No black/ruff config in `pyproject.toml`; standard PEP 8 implied.

**Linting:**
- Kotlin: No ESLint/Detekt config files found in repo.
- Python: No flake8/ruff/pylint config in repo.

## Import Organization

**Kotlin:**
- No strict order enforced; typically standard library then project then third-party. Single-block imports.

**Python:**
- Standard library then third-party then local (e.g. `from agent.chain import ...`). No isort/ruff format in config.

**Path Aliases:**
- Kotlin: None; full package paths.
- Python: Package `agent`; run as `python -m agent.main`; tests import `from agent.main import create_app`, `from agent.chain import ...`.

## Error Handling

**Patterns:**
- Kotlin: `runCatching { ... }.getOrElse { e -> ... throw e }` in routes; let exceptions propagate to Ktor. No custom exception types or error DTOs.
- Python: Let FastAPI and Pydantic handle validation errors; no central exception handler in app.
- Worker activity: No try/catch in `RunAgentActivity` or `agentInvoke`; failures propagate to Temporal.

## Logging

**Framework:** System.err/println (Kotlin); no logger in agent except test/fixture.

**Patterns:**
- Kotlin: `System.err.println(...)` for startup and chat flow; ad-hoc `chatLog("...")` in `ChatRoutes.kt`. No log levels or correlation IDs.
- Python: No structured logging in main or chain code.

## Comments

**When to comment:**
- Port resolution and bind fallback (API, Agent) documented with short comments.
- Docstrings on Python tools and setup functions (e.g. `search` tool, `setup_telemetry`). No project-wide comment policy.

**JSDoc/TSDoc:** Not applicable (Kotlin/Python). KDoc not used; Python docstrings used sparingly for public functions.

## Function Design

**Size:** No strict limit; routes and activities are small (single responsibility). `Main.kt` (API) contains port logic and debug logging in addition to bootstrap.

**Parameters:** Kotlin: minimal (env or constructor for activity). Python: Pydantic for HTTP body; env for config.

**Return values:** Kotlin: data classes for HTTP (e.g. `ChatResponse`, `HealthResponse`); workflow/activity return `String`. Python: Pydantic response models; chain returns dict with `output` key.

## Module Design

**Exports:** Kotlin: public types and top-level functions used across modules (e.g. `configureRouting`, `initOpenTelemetry`). Contracts expose only workflow interface.

**Barrel files:** Not used; direct imports from concrete files.

---

*Convention analysis: 2025-03-03*
