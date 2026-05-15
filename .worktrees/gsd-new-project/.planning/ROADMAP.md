## Roadmap: otel-demo-platform

### Overview

This roadmap evolves the otel-demo-platform from a solid single-flow demo into a richer, interview-ready sandbox for OpenTelemetry, Temporal, and LLM workflows. Phases are ordered so that core reliability and observability land first, then more advanced Temporal patterns, agent behaviors, and production-hardening scenarios build on top.

### Phases (Summary)

- [ ] **Phase 1: Demo Foundations & Developer Experience** – Stable, completely functional demo: one-command start (infra + all three apps), preferred defaults, top-level config, Makefile + Gradle/Compose, and CI with e2e smoke.
- [ ] **Phase 2: End-to-End Observability Story** – Turn traces, logs, and metrics into a first-class teaching tool across API, worker, agent, and infra.
- [ ] **Phase 3: Temporal Workflow Patterns** – Expand beyond a single workflow call into richer Temporal patterns and failure modes.
- [ ] **Phase 4: Agent & LLM Experience** – Turn the Python agent into an opinionated, extensible playground for LangChain + Ollama.
- [ ] **Phase 5: Production-Hardening & Security (Advanced)** – Add realistic constraints (auth, limits, safety) for “how would you productionize this?” conversations.

---

### Phase 1: Demo Foundations & Developer Experience

**Goal**: Phase 1 delivers a **stable, completely functional** demo. Anyone can clone the repo, run one command to start infra + all three apps, and complete a chat trace walkthrough within minutes, with preferred defaults and no surprises around ports, logs, or tooling.

**Decisions (locked)**:
- **Preferred defaults:** API port **8080**, Agent port **8000**; document clearly and fail fast with a clear message if port is in use.
- **Configuration:** Single reference at **top-level [CONFIG.md](../CONFIG.md)**; linked from root README, integration README, and agent README.
- **One-command start:** One command starts **infra + all three apps** (Agent, Worker, API) with sensible defaults.
- **Bootstrapping:** Use **Gradle/Compose and Makefile** (both) for local runs.
- **CI:** Unit tests (`:api:test`, `:worker:test`, agent pytest) **plus a single end-to-end smoke** (e.g. health checks + one `POST /chat`) in CI.

**Depends on**: Nothing (first phase)

**Primary components**: API (Ktor), Worker, Agent (FastAPI), repo root docs, integration README, CONFIG.md, Makefile, CI workflow.

**Task order** (execute in this sequence):

1. **Clean up debug and local-only code paths in the API**  
   - Remove or gate hardcoded debug logging (`Main.kt`), machine-specific paths, and session IDs so the API is “clean” by default while still allowing opt-in verbose logs.

2. **Stabilize port and configuration story across services**  
   - Apply preferred defaults (API 8080, Agent 8000); tighten how `API_PORT` / `AGENT_PORT` are documented and used; ensure integration docs and CONFIG.md match.

3. **Create and link the single configuration reference**  
   - Top-level **CONFIG.md** summarizing all env vars and defaults (Temporal, OTEL, Agent, ports); link from root README, integration README, and agent README.

4. **Standardize project bootstrapping**  
   - **Makefile** and **Gradle/Compose** targets that start infra then Agent, Worker, and API (one command = infra + all three apps) with preferred defaults.

5. **Tighten smoke tests and sample requests**  
   - Ensure `test-data` samples and documented curl commands cover the golden-path chat flow and are kept in sync with the API schema and behavior.

6. **Introduce CI with unit tests and one e2e smoke**  
   - CI workflow (e.g. GitHub Actions) runs `:api:test`, `:worker:test`, and agent pytest, **plus a single end-to-end smoke** (health checks + one `POST /chat` or equivalent) to confirm the full stack is functional.

**Outcome**: After Phase 1, the repo is stable and completely functional for demos and interviews; later phases build on this baseline.

**Interview / live-coding fit**:  
Medium. Good for warm-up: walking through repo structure, env vars, CONFIG.md, and quick fixes, but less exciting than later phases for deep system design.

---

### Phase 2: End-to-End Observability Story

**Goal**: Make traces, logs, and a small metrics story (latency + throughput) a compelling, narrative tool that shows how a single chat request flows across API → Temporal → worker → agent → Grafana Tempo.

**Decisions (locked)**:
- **Traces, logs, and metrics**: Deliver traces, structured logs, and a **small metrics story** (latency + throughput) surfaced in Grafana alongside traces.
- **TraceQL primary, UI fallback**: Assume **TraceQL** as the primary interface for this project; document UI-click flows as the fallback for people who prefer the Grafana UI.
- **Broken observability**: Implement a **config flag** (e.g. env var) that deliberately misconfigures observability (wrong OTLP endpoint or disabled exporter). Provide documentation so the interviewer can guide a candidate through diagnosing and fixing it during an interview.

**Depends on**: Phase 1 (stable run experience and docs)

**Primary components**: API/Worker/Agent telemetry code, Grafana Tempo + OTLP collector, metrics (latency/throughput), docs under `docs/` and `integration/`.

**Key tasks (3–8 work items)**:

1. **Verify and, if needed, fix trace context propagation across all hops**  
   - Confirm that API, worker, and agent spans form a single trace in Tempo; fix Ktor client propagation in the worker and FastAPI propagation in the agent if any gaps exist.

2. **Enrich spans with domain-relevant attributes and events**  
   - Add consistent attributes (e.g., high-level message type, workflow ID, Temporal task queue) and key events (e.g., agent invocation start/end) to make traces self-explanatory.

3. **Document a “trace-driven debugging” walkthrough**  
   - Add or extend docs showing how to use **TraceQL** to follow a request, identify which service failed, and reason about latency (TraceQL as primary; UI-click as fallback for this project).

4. **Add structured logging around the main chat path**  
   - Introduce minimal structured logging (service name, trace/span IDs, high-level outcome) in API, worker, and agent to pair with traces during troubleshooting.

5. **Introduce a small metrics story (latency + throughput) in Grafana**  
   - Add high-signal metrics (e.g. chat request count, latency histogram per service) and show how to surface them in Grafana alongside traces.

6. **Add a config-flag “broken observability” scenario for teaching**  
   - Implement a **config flag** (env var) that deliberately misconfigures (e.g. wrong OTLP endpoint or disables exporter). Document how to diagnose and fix missing traces so the interviewer can run this as an interview exercise.

**Plans:** 1 plan

Plans:
- [ ] 02-01-PLAN.md — End-to-end observability: propagation, enriched spans, TraceQL walkthrough, structured logs, metrics, broken-observability flag

**Interview / live-coding fit**:  
High. Great for reasoning about traces, wiring up context, debugging a misconfigured collector (via the config flag), and correlating metrics with traces.

---

### Phase 3: Temporal Workflow Patterns

**Goal**: Move from “single workflow as a black box” to a set of clear Temporal patterns (retries, timeouts, multi-step workflows) that are visible in both code and traces.

**Depends on**: Phase 1 (stable baseline), Phase 2 (good observability to inspect workflows)

**Primary components**: Contracts module, Worker workflows/activities, API Temporal client, Temporal + Postgres infra.

**Key tasks (3–8 work items)**:

1. **Refine the existing workflow contract and implementation**  
   - Make the current `AgentWorkflow` and activity code a clear example of a simple request/response workflow, with explicit timeouts and retry policies wired through.

2. **Add at least one multi-step workflow scenario**  
   - Introduce a new workflow that chains multiple activities (e.g., pre-processing step, agent call, post-processing/logging step) to showcase workflow composition in code and traces.

3. **Demonstrate workflow failure and retry behavior**  
   - Create a controlled failure mode (e.g., agent temporarily unavailable) and document how Temporal retries are configured and how they appear in Tempo and Temporal Web UI.

4. **Expose workflow metadata to callers via the API**  
   - Optionally return or log workflow IDs and task queue names from the API so users can correlate API responses with Temporal Web and Grafana traces.

5. **Add worker-focused tests using Temporal’s testing utilities**  
   - Extend existing worker tests to use the Temporal testing framework for at least one workflow, validating behavior without hitting real Temporal or the agent.

6. **Document Temporal-centric troubleshooting and exploration paths**  
   - Expand docs to show how to inspect workflow histories, identify stuck workflows, and reason about long-running vs. short-running patterns.

**Interview / live-coding fit**:  
Very high. Ideal for exercises involving designing a new workflow, adding an activity, or adjusting retry/timeouts while reading traces and Temporal history.

---

### Phase 4: Agent & LLM Experience

**Goal**: Turn the Python agent into a modular, easy-to-extend LangChain playground that’s safe for local experimentation and great for showcasing tool-based agents.

**Depends on**: Phase 1 (runability), Phase 2 (observability for agent spans), optionally Phase 3 (if new workflows target enhanced agent behavior)

**Primary components**: Agent FastAPI app, LangChain chain/tools, test suite, `docs/LIVE_FEATURE.md` and related interview materials.

**Key tasks (3–8 work items)**:

1. **Refine the existing LangChain chain for clarity and extensibility**  
   - Make the core chain composition easy to understand (clear abstraction boundaries, configuration), and ensure it’s well-documented for people new to LangChain.

2. **Add one or two well-scoped tools with strong demo value**  
   - Introduce tools (e.g., simple in-memory knowledge lookup, deterministic utility) that show off agent tool usage without introducing heavy dependencies.

3. **Tighten testing of agent pipelines and error behavior**  
   - Expand pytest coverage to include more edge cases (invalid input, LLM errors, tool failures) and ensure tests can run without Ollama (using mocks/fixtures).

4. **Improve agent observability and logging context**  
   - Ensure spans and logs in the agent clearly indicate which tools ran, how long they took, and any high-level decision points taken by the agent.

5. **Polish and align live-coding guides with current code**  
   - Update `docs/LIVE_FEATURE.md` and `docs/INTERVIEW_SCRIPT.md` so that “add a new tool/step” flows map directly to the current chain and test layout.

6. **Add a safe “LLM off” mode for constrained environments**  
   - Provide an option to run the demo without a real LLM (e.g., stubbed responses) so the platform can be used where Ollama or GPU access isn’t available.

**Interview / live-coding fit**:  
Very high. Perfect for tasks like “add a new tool,” “change the prompt/chain,” or “improve error handling and tests around the agent.”

---

### Phase 5: Production-Hardening & Security (Advanced)

**Goal**: Layer realistic production concerns (auth, safety, resilience) on top of the demo so it can be used for “how would you take this toward production?” conversations.

**Depends on**: Phases 1–4 (baseline robustness, observability, and core feature set)

**Primary components**: API and Agent routing/middleware, Worker configuration, docker-compose infra, security and scaling docs.

**Key tasks (3–8 work items)**:

1. **Introduce basic authentication/authorization for API and Agent**  
   - Add lightweight auth (e.g., API key, bearer token, or simple OAuth stub) and document how protected endpoints change the story for traces and Temporal workflows.

2. **Harden infrastructure defaults for non-local use**  
   - Improve docker-compose defaults (non-default credentials, updated images where sensible) and clearly separate “demo” vs. “more realistic” configurations.

3. **Add rate limiting and/or simple request budgeting**  
   - Implement basic rate limiting on `POST /chat` to show how to protect the LLM and worker from abuse, and demonstrate how this appears in traces/logs.

4. **Improve graceful shutdown and lifecycle handling**  
   - Ensure worker and agent handle SIGTERM/SIGINT gracefully, stopping Temporal workers and in-flight calls cleanly for a more production-like story.

5. **Add a “productionization checklist” doc**  
   - Summarize key steps (auth, secrets, TLS, scaling, monitoring) someone should take if they wanted to evolve this demo into a real service.

6. **Optional: add structured logging and correlation IDs end-to-end**  
   - Upgrade logging to structured format with correlation IDs and link them clearly to trace IDs for a full observability + operations narrative.

**Interview / live-coding fit**:  
Medium to high. Best for senior-level interviews focused on production readiness, security, and operations rather than core feature implementation.

---

### Interview & Live-Coding Highlights

- **Best for architecture + systems design**:  
  - **Phase 2 (End-to-End Observability Story)** – reasoning about traces, collectors, and service boundaries.  
  - **Phase 3 (Temporal Workflow Patterns)** – designing new workflows, activities, and failure-handling strategies.

- **Best for implementation-heavy live-coding**:  
  - **Phase 4 (Agent & LLM Experience)** – adding tools, adjusting chains, extending tests, and reasoning about LLM behavior.

- **Best for production-readiness and senior interviews**:  
  - **Phase 5 (Production-Hardening & Security)** – applying auth, limits, and operational practices to an existing multi-service system.

