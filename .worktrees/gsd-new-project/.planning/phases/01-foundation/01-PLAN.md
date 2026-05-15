---
phase: 01-foundation
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - api/src/main/kotlin/dev/otel/demo/api/Main.kt
  - agent/agent/main.py
  - CONFIG.md
  - README.md
  - integration/README.md
  - agent/README.md
  - test-data/sample_requests.json
  - Makefile
  - .github/workflows/ci.yml
autonomous: true

must_haves:
  truths:
    - "API starts clean (no debug logging or machine-specific paths by default)"
    - "API binds to 8080 when API_PORT unset and fails fast with clear message if port in use"
    - "Agent binds to 8000 when AGENT_PORT unset and fails fast with clear message if port in use"
    - "CONFIG.md exists and all three READMEs link to it"
    - "One command starts infra then Agent, Worker, API in that order"
    - "test-data and documented curl match API schema; golden-path chat is documented"
    - "CI runs unit tests and one e2e smoke (health + POST /chat)"
  artifacts:
    - path: api/src/main/kotlin/dev/otel/demo/api/Main.kt
      provides: "Clean API bootstrap and port handling"
    - path: CONFIG.md
      provides: "Single config reference"
    - path: Makefile
      provides: "One-command bootstrap"
    - path: .github/workflows/ci.yml
      provides: "CI with unit tests and e2e smoke"
  key_links:
    - from: README.md
      to: CONFIG.md
      via: "markdown link"
    - from: integration/README.md
      to: CONFIG.md
      via: "markdown link"
    - from: agent/README.md
      to: CONFIG.md
      via: "markdown link"
---

<objective>
Phase 1 delivers a stable, completely functional demo: one-command start (infra + Agent + Worker + API), preferred defaults (API 8080, Agent 8000), single config reference, and CI with unit tests plus one e2e smoke.
</objective>

<execution_context>
Execute tasks in order 1–6. Each task has explicit files, action, verify, and done criteria.
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/codebase/STACK.md
@.planning/codebase/ARCHITECTURE.md
@.planning/codebase/STRUCTURE.md
@.planning/codebase/CONVENTIONS.md
@.planning/codebase/TESTING.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Clean up debug and local-only code in the API</name>
  <files>api/src/main/kotlin/dev/otel/demo/api/Main.kt</files>
  <action>
- Remove entirely: `debugLog` function, `DEBUG_LOG_PATH`, `debugMapper`, and all `#region agent log` blocks (calls to debugLog and the region comments).
- Keep: `resolvePort()`, `portAvailable()`, BindException catch with the existing clear stderr message, OTel init, and embeddedServer bootstrap.
- Do not add new logging libraries; keep startup message to stderr ("API starting on http://0.0.0.0:$port ...").
- Result: Main.kt has no machine-specific paths, no session/hypothesis/run IDs, and no debug file writes. API is clean by default.
  </action>
  <verify>./gradlew :api:test passes; grep -r debugLog DEBUG_LOG_PATH "591c58" "agent log" api/src/main/kotlin returns no matches</verify>
  <done>Main.kt contains no debug logging, no hardcoded paths, and no session IDs; API tests pass.</done>
</task>

<task type="auto">
  <name>Task 2: Stabilize port and configuration story</name>
  <files>api/src/main/kotlin/dev/otel/demo/api/Main.kt, agent/agent/main.py, CONFIG.md, integration/README.md</files>
  <action>
- API (Main.kt): When API_PORT is unset, use 8080 only (no 8080..8089 fallback). If port 8080 is in use, catch BindException and print: "API could not bind to port 8080. Set API_PORT to a different port or stop the other process." then rethrow. When API_PORT is set, use that value (or 8080 if invalid). Remove the port-availability loop so we fail fast on 8080 when unset.
- Agent (agent/agent/main.py): When AGENT_PORT is unset, use 8000 only (no 8001..8009 fallback). If 8000 is in use, exit with a clear message to stderr (e.g. "Agent could not bind to port 8000. Set AGENT_PORT to a different port or stop the other process.") and non-zero exit. When AGENT_PORT is set, use that value (or 8000 if invalid).
- CONFIG.md: Ensure the "Preferred defaults" line and API_PORT/AGENT_PORT rows state that preferred is 8080/8000 and that if the port is in use the process fails with a clear message (no automatic fallback). Align wording with the new behavior.
- integration/README.md: Under "Run order" or "Smoke check", mention that preferred ports are 8080 (API) and 8000 (Agent) and that both fail fast with a clear message if the port is in use; point to CONFIG.md for env vars.
  </action>
  <verify>With nothing on 8080: API starts on 8080; with another process on 8080: API fails with message mentioning 8080 and API_PORT. Same for Agent on 8000. CONFIG.md and integration/README.md read consistently.</verify>
  <done>API uses 8080 when API_PORT unset and fails fast with clear message if 8080 in use; Agent uses 8000 when AGENT_PORT unset and fails fast if 8000 in use; docs match.</done>
</task>

<task type="auto">
  <name>Task 3: Verify CONFIG.md and links</name>
  <files>CONFIG.md, README.md, integration/README.md, agent/README.md</files>
  <action>
- Confirm CONFIG.md exists at repo root and contains: preferred defaults (API 8080, Agent 8000), API env vars (API_PORT, OTEL_EXPORTER_OTLP_ENDPOINT), Worker env vars, Agent env vars, Infrastructure (Docker Compose) ports, and run order.
- Verify README.md links to CONFIG.md (e.g. "[CONFIG.md](CONFIG.md)" or under a "Configuration" section).
- Verify integration/README.md links to CONFIG.md (e.g. "Env vars and defaults: [CONFIG.md](../CONFIG.md)" or equivalent).
- Verify agent/README.md links to CONFIG.md (e.g. "Full config reference: [CONFIG.md](../CONFIG.md)").
- If any link or section is missing, add it. Do not duplicate CONFIG.md content into READMEs; link only.
  </action>
  <verify>CONFIG.md exists; grep -l "CONFIG.md" README.md integration/README.md agent/README.md returns all three files; links resolve (relative path correct from each file).</verify>
  <done>CONFIG.md exists at root; all three READMEs contain a working link to CONFIG.md.</done>
</task>

<task type="auto">
  <name>Task 4: Standardize bootstrapping (Makefile and one-command start)</name>
  <files>Makefile</files>
  <action>
- Create a top-level Makefile (repo root). Implement:
  - `infra` or `up-infra`: run `docker compose up -d` (from repo root). Use `docker compose` (space) for compatibility.
  - `run-agent`: start Agent in foreground (for debugging) with `cd agent && python -m agent.main` (or `uv run python -m agent.main` if project standard is uv). Do not assume venv path; document in comments that user should have deps installed (pip install -e ".[dev]" or equivalent).
  - `run-worker`: start Worker with `./gradlew :worker:run` from repo root (so Gradle is invoked from root).
  - `run-api`: start API with `./gradlew :api:run` from repo root.
  - `run` or `start-all`: one-command start. Order MUST be: (1) infra, (2) Agent, (3) Worker, (4) API. Implementation: (1) run `docker compose up -d`; (2) start Agent in background (e.g. `(cd agent && python -m agent.main) &` or use a small script that backgrounds the process and logs to a file); (3) start Worker in background (e.g. `./gradlew :worker:run &`); (4) start API in foreground so the terminal shows API logs and user can Ctrl+C to stop (optionally document that stopping will leave Agent and Worker running unless they use a shared process group). Alternatively, start all three apps in background and print "API: http://localhost:8080, Agent: http://localhost:8000. Run 'make logs' to tail or kill background jobs." — choose one approach and document. Recommended: infra + start Agent and Worker in background, then API in foreground so one command gives a runnable demo and Ctrl+C stops at least the API.
- Use preferred defaults: no API_PORT/AGENT_PORT in the Makefile so 8080 and 8000 are used; document in CONFIG.md or Makefile comments that ports can be overridden by setting env vars before `make run`.
- Add a target `e2e-smoke` or `smoke` that: brings up infra, starts Agent then Worker then API in background, waits a few seconds for startup, then runs `curl -sf http://localhost:8080/health` and `curl -sf -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'` (or equivalent), then exits. This can be used by CI (Task 6). If Makefile does not background reliably in CI, CI can call a script that does the same steps; document in the plan that CI may invoke `make smoke` or a script under integration/ or .github/.
- Gradle: No Gradle Compose plugin in use. Keep using Gradle for :api:run and :worker:run only. The "Gradle/Compose" requirement is satisfied by: Compose for infra (docker compose), Gradle for running API and Worker; Makefile orchestrates both.
  </action>
  <verify>From repo root: `make infra` (or `make up-infra`) brings up containers; `make run` starts infra then Agent (bg), Worker (bg), API (fg), and API responds on 8080. Health and POST /chat work. `make smoke` (or equivalent) runs and exits with success after health + POST /chat.</verify>
  <done>One command (e.g. make run) starts infra then Agent, Worker, API in order; Makefile documents how to run each component and how to run e2e smoke.</done>
</task>

<task type="auto">
  <name>Task 5: Tighten smoke tests and sample requests</name>
  <files>test-data/sample_requests.json, README.md, integration/README.md, docs/TESTING.md (if present)</files>
  <action>
- Ensure test-data/sample_requests.json is valid JSON and each entry has a "body" object that matches API schema: ChatRequest has a single field "message" (string). Current format is already correct; verify and add one more example if useful (e.g. empty message or long message for edge case). Do not change the schema; keep {"message": "..."}.
- Ensure README.md "Send a request" section uses exactly: `curl -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'` (port 8080 per preferred default). Remove or update any text that says "port the API prints" or "8081, 8082" fallback now that we fail fast on 8080.
- integration/README.md "Send a request": same curl command with 8080; reference test-data/sample_requests.json for more examples.
- If docs/TESTING.md exists, align its curl and sample data references with the above and with CONFIG.md ports.
- Document the golden-path chat flow in one place (e.g. integration/README or README): start infra, start Agent/Worker/API, GET /health on API and Agent, POST /chat with {"message":"Hello"}, expect 200 and JSON with "reply".
  </action>
  <verify>sample_requests.json validates (e.g. jq . test-data/sample_requests.json); each body has "message" only. README and integration README curl use 8080 and same JSON shape. Golden path is clearly stated.</verify>
  <done>test-data and documented curl match API schema; golden-path chat is documented and uses port 8080.</done>
</task>

<task type="auto">
  <name>Task 6: CI with unit tests and one e2e smoke</name>
  <files>.github/workflows/ci.yml</files>
  <action>
- Create .github/workflows/ci.yml (GitHub Actions). If the repo uses another CI (e.g. GitLab), use the equivalent config file location and syntax; assume GitHub Actions unless stated.
- Jobs or steps:
  1. Unit tests: run `./gradlew :api:test :worker:test` (no daemon for CI: add `--no-daemon` if desired). Run agent tests with `cd agent && pip install -e ".[dev]" && python -m pytest tests/ -v` (or uv equivalent). Use a single job with multiple steps or a matrix; ensure Java 17 and Python 3.11+ are set (e.g. actions/setup-java, actions/setup-python).
  2. E2E smoke: one job or step that (a) starts infrastructure (`docker compose up -d`), (b) waits for Temporal/Postgres/otel-lgtm to be ready (e.g. sleep 15–30 or poll health), (c) starts Agent in background (e.g. run in background step or nohup), (d) starts Worker in background, (e) starts API in background, (f) waits a few seconds, (g) runs `curl -sf http://localhost:8080/health` and expects 200 and "otel-demo-api", (h) runs `curl -sf -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'` and expects 200 and a JSON body with "reply", (i) exits with 0 on success. Set a timeout for the e2e job (e.g. 5 minutes). If Ollama is not available in CI, the POST /chat may fail (worker calls agent, agent needs LLM); in that case document that e2e smoke requires Ollama or use a mock. Option: run e2e only when Ollama is available, or stub the agent in e2e (complex). Simpler: run e2e with real stack and document that CI needs Ollama/agent for full smoke; or run health-only e2e and one POST /chat that may 500 if agent is down — then consider "e2e smoke" as "health checks pass and API is reachable; POST /chat returns 200 when agent is available." Specify in the workflow: e2e step fails if health fails; POST /chat failure can be acceptable in environments without Ollama (optional step or allow failure with comment). Prefer: run full smoke (health + POST /chat) and require Ollama in CI or use a job that runs only when Ollama is set up (e.g. self-hosted runner with Ollama). For maximum portability, implement: (1) health checks must pass, (2) POST /chat is attempted; if it returns 200 and has "reply", pass; if it returns 5xx (e.g. agent unreachable), log and optionally fail the e2e step unless an env var says "e2e_allow_no_ollama". Keep it simple: health + POST /chat; if POST /chat fails due to agent/LLM, fail the e2e with a clear message so maintainers know to add Ollama or skip that step.
- Summary: CI workflow file at .github/workflows/ci.yml; runs :api:test, :worker:test, agent pytest; runs one e2e smoke that starts services then curl health + POST /chat with timeout.
  </action>
  <verify>Push or run workflow: unit test job passes; e2e smoke job starts infra and apps, then curl health and POST /chat; workflow file is valid YAML and has sensible timeout and Java/Python versions.</verify>
  <done>CI runs unit tests for API, worker, and agent; CI runs one e2e smoke (health checks + one POST /chat) with clear pass/fail.</done>
</task>

</tasks>

<verification>
- All six tasks completed in order.
- No debug or machine-specific code in API Main.kt.
- API and Agent use 8080/8000 by default and fail fast with clear message if port in use.
- CONFIG.md present and linked from README, integration/README, agent/README.
- make run (or equivalent) starts infra then Agent, Worker, API; health and POST /chat succeed.
- test-data and curl docs match ChatRequest schema; golden path documented.
- GitHub Actions workflow runs unit tests and e2e smoke.
</verification>

<success_criteria>
- Phase 1 goal achieved: stable, completely functional demo; one-command start; preferred defaults 8080/8000; single config reference; CI with unit tests and one e2e smoke.
- An executor can implement Phase 1 without ambiguity using this plan.
</success_criteria>

<output>
After completion, create .planning/phases/01-foundation/01-foundation-01-SUMMARY.md (or 01-SUMMARY.md) summarizing what was implemented and any deviations.
</output>
