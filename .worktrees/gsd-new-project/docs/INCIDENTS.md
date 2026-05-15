# Incident 1: Agent / LLM error spike

**Scenario:** The Agent or underlying LLM starts failing most or all requests, causing a spike in 5xx responses from the Agent service and failed chat requests end‑to‑end.

## How to reproduce locally

- Start the stack as usual (infra + Agent + worker + API).
- Enable the demo failure flag on the Agent, for example:
  - `export AGENT_FAIL_ALL_REQUESTS=1`
  - then start the Agent: `cd agent && python -m agent.main`
- With the API running on port 8080, send a chat request:
  - `curl -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'`

## What the user sees

- The worker calls `/invoke` on the Agent, but the Agent immediately returns **5xx** for every request while `AGENT_FAIL_ALL_REQUESTS=1` is set.
- Depending on how the worker and API propagate the error, `POST /chat` will return a 5xx response and not a normal chat reply.

## What traces and logs show

- **Agent traces**
  - The `/invoke` span is marked with `status=ERROR`.
  - Span attributes include:
    - `error.type="agent_failure"`
    - `agent.failure.mode="forced_all_requests"`
  - An event `agent.failure.forced` is added when the failure flag is active.
- **Agent logs**
  - Structured stderr logs from the agent include JSON lines like:
    - `{"service":"otel-demo-agent","trace_id":"...","span_id":"...","outcome":"error","error_type":"agent_failure","failure_mode":"forced_all_requests"}`
- **API / worker traces**
  - The worker activity and API spans record exceptions from the Agent call; use `TRACE_WALKTHROUGH.md` to find traces with `status=error` tied to the Agent service.

## Mitigations and follow‑ups

- **Short term**
  - Treat a sudden spike in Agent 5xx responses and `error_type":"agent_failure"` logs as an indication that the Agent/LLM is unhealthy (or that the demo flag is accidentally left on).
  - Roll back the flag (`unset AGENT_FAIL_ALL_REQUESTS`) and restart the Agent, or deploy a previous known-good version of the Agent/LLM configuration.
- **Medium term**
  - Add alerts on:
    - 5xx rate for `/invoke` and/or `/chat`.
    - Agent logs containing `error_type":"agent_failure"`.
  - Consider adding a degraded mode where the API can short‑circuit and return a stubbed response when the Agent is unavailable.
- **Long term (design discussions)**
  - Discuss SLOs for the Agent/LLM layer (error rate, latency) and how they influence when to trip circuit breakers, fall back to cached/cheaper behavior, or shed load.
  - Explore separating the LLM service from the Agent API for clearer failure domains.

## Incident 2: Temporal / infra outage

**Scenario:** Temporal or its Postgres DB is unavailable while users are sending chat requests through the API.

### How to reproduce locally

- Stop Temporal (and its DB) while leaving the API running, for example:
  - `docker compose stop temporal` (or stop the Temporal + Postgres containers from your compose stack).
- With the API still running on port 8080, send a chat request:
  - `curl -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'`

### What the user sees

- `POST /chat` returns **`503 Service Unavailable`**.
- The response body contains a structured error indicating Temporal is down, for example:
  - `{"error":"temporal_unavailable","message":"Temporal service is unavailable; please try again later."}`
- Existing `/health` continues to report `{"status":"ok","service":"otel-demo-api"}` because the API process itself is still up.
- The new `/ready` endpoint reports degraded status while Temporal is unreachable:
  - `GET /ready` → `503` with JSON like `{"status":"degraded","service":"otel-demo-api","temporal":"unavailable"}`.

### What traces and logs show

- **API traces**
  - The `POST /chat` span is marked with `status=ERROR` and an exception event when the Temporal client cannot connect.
  - Span attributes include:
    - `message.type="chat"`
    - `temporal.status="unavailable"` on failure.
  - Structured logs on stderr include a JSON line with outcome `temporal_unavailable`, for example:
    - `{"service":"otel-demo-api","trace_id":"...","span_id":"...","outcome":"temporal_unavailable"}`
- **Worker logs**
  - On startup, if the worker cannot connect to Temporal, it logs a structured JSON line and fails fast:
    - `{"service":"otel-demo-worker","event":"temporal_unavailable","message":"Failed to start worker due to Temporal connectivity","error":"<exception>"}`
  - This makes the failure explicit instead of silently retrying forever without clear signals.
- **Grafana / Tempo**
  - Use `TRACE_WALKTHROUGH.md` to find failing traces, e.g.:
    - `{ resource.service.name="otel-demo-api" && status=error }`
  - You can see that the failure happens at the API’s Temporal call, before the worker workflow starts.

### Mitigations and follow‑ups

- **Short term**
  - Treat `503 temporal_unavailable` responses and `temporal_unavailable` logs as alerts that Temporal or its DB is down.
  - Pause user traffic to `/chat` (via feature flag, gateway, or UI) while the incident is investigated.
  - Restore Temporal and its Postgres DB (restart containers, fix credentials, or resolve infrastructure outage).
  - Verify recovery:
    - `GET /ready` returns `200` with `{"status":"ready","temporal":"available",...}`.
    - `POST /chat` returns `200` and traces show both API and worker spans again.
- **Medium term**
  - Wire `/ready` into your orchestrator or load balancer so that the API is considered **not ready** when Temporal is unreachable.
  - Add alerts on:
    - 503 rate for `/chat` with `error="temporal_unavailable"`.
    - Worker logs containing `event":"temporal_unavailable"`.
  - Consider a user-facing status page or banner when Temporal downtime is detected.
- **Long term (design discussions)**
  - Decide whether some requests can be queued or degraded (e.g. local stubbed responses) during short Temporal outages.
  - Evaluate high‑availability options for Temporal and its Postgres DB (multi‑AZ, managed services, or replicas).
  - Document an explicit RTO/RPO and SLOs for the chat feature so outage impact is well understood.

