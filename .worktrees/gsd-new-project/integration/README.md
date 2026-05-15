# Integration / E2E

Full run order and verification steps for the demo. See the [root README](../README.md) for prerequisites and architecture. Env vars and defaults: [CONFIG.md](../CONFIG.md).

## Run order

Preferred ports: **API 8080**, **Agent 8000**. If a port is in use, the process fails with a clear message (no automatic fallback). See [CONFIG.md](../CONFIG.md) for env vars.

1. **Infrastructure:** `docker compose up -d` (from repo root)
2. **Agent:** `cd agent && pip install -r requirements.txt && python -m agent.main` (Ollama + model required)
3. **Worker:** `cd worker && ./gradlew run`
4. **API:** `cd api && ./gradlew run`

### Modes: demo vs hardened

- **Demo mode (default):** `docker compose up -d`
  - Uses clearly-marked demo credentials for Postgres and Grafana (see [CONFIG.md](../CONFIG.md)).
  - Suitable for local exploration, workshops, and E2E tests on a laptop.
- **Hardened mode (illustrative):** `docker compose -f docker-compose.yml -f docker-compose.hardened.yml up -d`
  - Requires you to set non-demo credentials via env vars (Postgres, Grafana).
  - Removes direct host exposure for Postgres and enforces non-default Grafana admin credentials.
  - See [CONFIG.md](../CONFIG.md) and [docs/PRODUCTION_CHECKLIST.md](../docs/PRODUCTION_CHECKLIST.md) for the exact variables.

## Smoke check

Confirm services before sending chat:

- **API:** `GET http://localhost:8080/health`
- **Agent:** `GET http://localhost:8000/health`

Example: `curl -s http://localhost:8080/health && curl -s http://localhost:8000/health`

## Golden-path chat flow

1. Start infra: `docker compose up -d` (or `make infra`).
2. Start Agent, Worker, API in order (or `make run` for one-command start).
3. **Health:** `curl -s http://localhost:8080/health` and `curl -s http://localhost:8000/health` — expect `{"status":"ok"}` (API also returns `"service":"otel-demo-api"`).
4. **Chat:** `curl -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'` — expect 200 and JSON with `"reply"`.

## Send a request

```bash
curl -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'
```

Use port **8080**. More examples in `test-data/sample_requests.json` (each entry has a `body` with `"message"` only).

## View one trace in Grafana

**Primary: TraceQL.** Open http://localhost:3000 (admin / admin) → **Explore** → **Tempo** → **TraceQL** tab. Run `{ resource.service.name="otel-demo-api" }` (quotes required). Pick a trace; you should see spans for API, worker, and agent. Full walkthrough (TraceQL examples, finding failures, latency): [docs/TRACE_WALKTHROUGH.md](../docs/TRACE_WALKTHROUGH.md).

**Alternative: use the UI** — In Explore → Tempo, use the **Search** tab, filter by Service name (e.g. otel-demo-api), run Search, and open a trace.

Expect a JSON response with `reply` from the curl above; the same flow appears as one end-to-end trace in Tempo.

## Inspect workflows in Temporal

**Temporal walkthrough.** To inspect workflow runs, multi-step activity chains (preprocess → agent → postprocess), and retry behavior (e.g. the `fail:` message trigger), use the Temporal-focused guide: [docs/TEMPORAL_WALKTHROUGH.md](../docs/TEMPORAL_WALKTHROUGH.md). The `POST /chat` response includes `workflowId` and `taskQueue` so you can correlate with Temporal Web and Grafana.
