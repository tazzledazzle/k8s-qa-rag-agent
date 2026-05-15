# Testing

## Unit tests

### Kotlin (API and Worker)

From the repo root:

```bash
./gradlew :api:test :worker:test
```

- **API**: `api/src/test/` — health route, chat route registration (Temporal client is not mocked; full flow needs integration test).
- **Worker**: `worker/src/test/` — activity implements interface.

### Python (Agent)

From the `agent/` directory:

```bash
cd agent
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest tests/ -v
```

- **Agent**: `agent/tests/` — tools (search, lookup, echo_repeat), agent executor with mock LLM, FastAPI health and `/invoke` with mock agent. All tests pass without Ollama (mocks and optional `AGENT_LLM_OFF` stub).
- **Run without Ollama:** To run the agent (or e2e) without Ollama, set `AGENT_LLM_OFF=1`. The agent returns a stub reply. See [CONFIG.md](../CONFIG.md) and [agent/README.md](../agent/README.md).

## Integration test (E2E)

Full flow (API → Temporal → Worker → Agent) requires:

1. `docker compose up -d` (Temporal + otel-lgtm)
2. Agent: `cd agent && .venv/bin/python -m agent.main` (and Ollama running with a model)
3. Worker: `cd worker && ./gradlew run`
4. API: `cd api && ./gradlew run`

Then:

```bash
curl -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'
```

Expect 200 and JSON with `"reply"`. Port 8080 is the API default (see [CONFIG.md](../CONFIG.md)). Traces appear in Grafana (http://localhost:3000, Explore → Tempo).

## Test data

- **Sample requests**: `test-data/sample_requests.json` — each entry has a `body` with `"message"` only (matches API `ChatRequest`).
- **Fixtures**: `agent/tests/fixtures/` — mock LLM responses (used via mocks in tests).

## Prerequisites for local/demo

- **Ollama**: Install from [ollama.ai](https://ollama.ai) and run `ollama pull llama3.2` (or another model) for the agent.
- **Docker**: For Temporal and Grafana (otel-lgtm).
