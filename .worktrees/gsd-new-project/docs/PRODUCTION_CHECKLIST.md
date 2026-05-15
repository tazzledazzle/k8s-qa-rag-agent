# Production checklist (illustrative)

This repo is a teaching/demo platform, not a turnkey production deployment. Use this checklist as a starting point for hardening decisions.

## Auth

- **API auth (`POST /chat`)**
  - Enable simple token auth via `API_AUTH_ENABLED=true` and set a non-demo `API_AUTH_TOKEN`.
  - Rotate the token in your secret manager and restart the API when rotating.
  - Decide which clients are allowed to call `/chat` and how they obtain the token.
- **Agent auth (`/invoke`)**
  - Enable auth on the Agent via `AGENT_AUTH_ENABLED=true` and `AGENT_AUTH_TOKEN` (see `agent/README.md`).
  - Keep API and Agent tokens separate unless you explicitly want a shared credential.

## Rate limiting

- **API in-process limiter**
  - Enable basic rate limiting via `CHAT_RATE_LIMIT_ENABLED=true`.
  - Set `CHAT_RATE_LIMIT_PER_MINUTE` to a realistic per-instance budget (e.g. 30–120) based on LLM/infra capacity.
  - Treat 429 responses as a signal to add upstream throttling (API gateway, load balancer, etc.).

## Temporal & DB

- **Temporal availability**
  - API `POST /chat` now returns `503 Service Unavailable` with `{"error":"temporal_unavailable", ...}` when it cannot talk to Temporal.
  - Worker logs a structured `temporal_unavailable` message and fails fast if it cannot connect to Temporal on startup.
  - Use the `/ready` endpoint to gate traffic on Temporal reachability (see **Observability** and **Operations** below).
- **Temporal + Postgres configuration**
  - Set non-demo credentials for the Temporal Postgres DB (`TEMPORAL_DB_USER`, `TEMPORAL_DB_PASSWORD`, `TEMPORAL_DB_NAME`) when using the hardened compose file.
  - Decide on backup/restore strategy for Temporal’s DB (snapshots, PITR, or managed service features).
  - Consider separate Postgres instances or schemas if you co-locate other workloads.

## Docker/Infra defaults

- **Credentials**
  - **Postgres (Temporal DB):**
    - Set non-demo credentials via env vars: `TEMPORAL_DB_USER`, `TEMPORAL_DB_PASSWORD`, and (optionally) `TEMPORAL_DB_NAME`.
    - Avoid using the demo defaults (`temporal_demo` / `temporal_demo`) outside local development.
  - **Grafana (otel-lgtm):**
    - Set non-default admin credentials via `OTEL_LGTM_ADMIN_USER` and `OTEL_LGTM_ADMIN_PASSWORD`.
    - Do not use `admin` / `admin` in shared or long-lived environments.

- **Port exposure**
  - For local demos, `docker compose up -d` exposes Postgres on `5432` for convenience.
  - For more realistic environments, run with the hardened overrides:
    - `docker compose -f docker-compose.yml -f docker-compose.hardened.yml up -d`
    - This configuration removes direct Postgres host exposure; access goes through Temporal only.

- **Mode selection**
  - **Demo mode (default):** `docker compose up -d`
    - Fast local setup with clearly-marked demo credentials.
  - **Hardened mode (illustrative):** `docker compose -f docker-compose.yml -f docker-compose.hardened.yml up -d`
    - Requires non-demo credentials for Postgres and Grafana.
    - Intended as a teaching example of safer defaults, not a complete security review.

For a real deployment, you should also review:

- Network boundaries (VPCs, security groups, firewall rules).
- Secret management (Vault, cloud secret managers, or similar) instead of raw env vars.
- Backup/restore for Postgres and Temporal.
- Observability storage retention and access controls for Grafana/Tempo.

## Observability

- **Traces and logs**
  - Keep `OTEL_EXPORTER_OTLP_ENDPOINT` aligned across API, worker, and agent (default `http://localhost:4317`).
  - Ensure `OTEL_DISABLE_TRACING` is **not** set in production; it is used in this repo to simulate broken observability (see `docs/BROKEN_OBSERVABILITY.md`).
  - Use `TRACE_WALKTHROUGH.md` to follow `POST /chat` traces end-to-end and confirm spans include `workflow.id`, `task.queue`, and Temporal error details.
- **Health vs readiness**
  - `/health` is intentionally simple and always returns an `ok` status when the API process is up.
  - `/ready` returns `200 ready` when the Temporal probe passes and `503 degraded` when the probe fails, including a `temporal` field in the JSON body.
  - In real deployments, wire `/ready` into your orchestrator or load balancer for readiness checks, and keep `/health` for lightweight liveness.

## Operations

- **Run order and lifecycle**
  - Start infra (`docker compose up -d`), then Agent, then worker, then API (see `CONFIG.md` and integration docs).
  - Plan for how you will restart or roll out each component (API, worker, agent, infra) without dropping in-flight requests more than acceptable.
- **Incident handling**
  - Define playbooks for common issues (Temporal/DB outage, broken observability, LLM unavailability) and capture them in `docs/INCIDENTS.md`.
  - During a Temporal or DB outage, expect `/chat` to return 503 and worker logs to show `temporal_unavailable`; use that as a trigger for paging or traffic shifting.
  - Use Grafana Tempo + logs to confirm where failures occur and to validate recovery after an incident.

