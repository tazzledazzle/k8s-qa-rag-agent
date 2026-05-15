# Testing Patterns

**Analysis Date:** 2025-03-03

## Test Framework

**Kotlin:**
- Runner: JUnit 5 (JUnit Platform); `kotlin-test-junit5`, `junit-platform-launcher` in `api/build.gradle.kts` and `worker/build.gradle.kts`.
- Config: `tasks.test { useJUnitPlatform() }` in each Kotlin subproject; no separate JUnit config file.
- API tests use Ktor `testApplication` and `io.ktor:ktor-server-test-host-jvm`; worker tests use `temporal-testing` (dependency only; current worker test does not start a test server).

**Python:**
- Runner: pytest 8+ with pytest-asyncio; `asyncio_mode = "auto"`, `testpaths = ["tests"]` in `agent/pyproject.toml` under `[tool.pytest.ini_options]`.
- Config: `agent/pyproject.toml`; no pytest.ini or pyproject section elsewhere.

**Run commands:**
```bash
# Kotlin (from repo root)
./gradlew :api:test :worker:test

# Python (from agent/)
cd agent && .venv/bin/python -m pytest tests/ -v
# or: pip install -e ".[dev]" then pytest
```

## Test File Organization

**Location:**
- Kotlin: Tests next to source by package; `api/src/test/kotlin/dev/otel/demo/api/routes/`, `worker/src/test/kotlin/dev/otel/demo/worker/`.
- Python: Central `agent/tests/`; no co-location with `agent/agent/`.

**Naming:**
- Kotlin: `*Test.kt` (e.g. `HealthRoutesTest.kt`, `ChatRoutesTest.kt`, `RunAgentActivityTest.kt`).
- Python: `test_*.py` (e.g. `test_main.py`, `test_chain.py`).

**Structure:**
- Kotlin: One test class per file; class name matches subject (e.g. `HealthRoutesTest`).
- Python: Test modules with multiple test functions; fixtures in same file or conftest if needed.

## Test Structure

**Kotlin (API) — testApplication pattern:**
```kotlin
@Test
fun `GET health returns JSON with status and service`() = testApplication {
    application {
        install(ContentNegotiation) { jackson() }
        routing { healthRoutes() }
    }
    val response = client.get("/health")
    assertEquals(200, response.status.value)
    assert(json.contains("ok") && json.contains("otel-demo-api")) { ... }
}
```
- Route tests install only the plugins/routes under test; no full app or Temporal.
- Chat test asserts route registration via `GET /chat` → 405 (method not allowed), not full workflow.

**Kotlin (Worker):**
```kotlin
@Test
fun `RunAgentActivity has run method`() {
    val activity = RunAgentActivity("http://localhost:8000")
    assertTrue(RunAgentActivityInterface::class.java.isInstance(activity))
}
```
- Current test only checks type conformance; no Temporal test server or mocked HTTP.

**Python — pytest + TestClient:**
```python
@pytest.fixture
def client():
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {"output": "Echo: hello"}
    app = create_app(agent=mock_agent)
    app.state.agent = mock_agent
    return TestClient(app)

def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"
```
- FastAPI app created with `create_app(agent=mock_agent)` to avoid real LLM; TestClient for HTTP.
- Chain tests patch `ChatOllama` or `get_llm` and assert executor output.

## Mocking

**Kotlin:**
- No mocks in current tests. API tests use testApplication without real Temporal; ChatRoutesTest does not hit Temporal (only checks 405 for GET /chat). Worker test uses real `RunAgentActivity` instance, no HTTP mock.

**Python:**
- `unittest.mock`: `MagicMock` for agent in test_main; `patch("agent.chain.ChatOllama")` or `patch("agent.chain.get_llm")` in test_chain to avoid Ollama.
- What to mock: LLM and agent executor for unit tests; no mock for OTLP (tests clear `OTEL_EXPORTER_OTLP_ENDPOINT` in test_main to avoid exporter).

**What NOT to mock:**
- Kotlin: Ktor routing and serialization are real in testApplication.
- Python: FastAPI app and chain composition are real; only LLM/invoke side is mocked.

## Fixtures and Factories

**Test data:**
- Sample request bodies: `test-data/sample_requests.json` (used for manual/curl; not loaded in unit tests).
- Python: Fixtures defined in test modules (e.g. `client` fixture in test_main.py). No shared fixtures dir in repo; `agent/tests/fixtures/` mentioned in docs but not required for current tests.

**Location:**
- Kotlin: No fixture files; inline data in tests.
- Python: Fixtures in test files; optional `agent/tests/fixtures/` for mock LLM responses per docs.

## Coverage

**Requirements:** No enforced coverage threshold in Gradle or pytest config.

**View coverage:**
- Kotlin: `./gradlew :api:test :worker:test` (no coverage plugin configured in build files).
- Python: `pytest tests/ -v` (no --cov in pyproject; add manually if desired).

## Test Types

**Unit tests:**
- API: Health and chat route registration / response shape with testApplication; no Temporal.
- Worker: Activity type conformance only.
- Agent: App endpoints with mock agent; chain and tools with mocked LLM.

**Integration tests:**
- No in-repo integration test suite. E2E is manual: start infra + API + worker + agent, then curl; see `integration/README.md` and `docs/TESTING.md`.

**E2E tests:** Not automated; documented in `docs/TESTING.md` and `integration/README.md`.

## Common Patterns

**Async (Python):**
- pytest-asyncio with `asyncio_mode = "auto"`; FastAPI TestClient is synchronous; no async test functions in current tests.

**Error testing:**
- Kotlin: Chat route test uses 405 to prove route exists; no tests for 400/500 or Temporal failure.
- Python: No tests for invalid body or agent exception in current files.

---

*Testing analysis: 2025-03-03*
