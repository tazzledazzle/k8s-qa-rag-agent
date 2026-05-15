# Phase 1: Integration & proof — Context

**Gathered:** 2026-05-14  
**Status:** **Transitioned** 2026-05-15 — Phase 1 closed; current phase is **Phase 2** (see `.planning/STATE.md`).

<domain>

## Phase boundary

Prove **E2E-01**, **E2E-02**, and **E2E-03** from `.planning/REQUIREMENTS.md`: a contributor can bring up the stack, run a **question → retrieval → cited answer** path on **representative** indexed data, and **default-branch CI** is an honest regression gate.

Phase 1 does **not** implement webhook HMAC hardening beyond what already exists (**SEC-01**), secrets inventory (**SEC-02**), repo allowlists (**SEC-03**), structured log correlation (**OBS-01**), OTEL validation (**OBS-02**), runbook drills (**OBS-03**), or documentation/release truth passes (**DOC-01**, **DOC-02**, **REL-01**) — those are Phases 2–4.

</domain>

<decisions>

## Implementation decisions

### Proof environments

- **D-01:** Primary bring-up path is **`docker compose`** (repo-root `docker-compose.yml`). Documented alternate: **Kubernetes** via `kubectl apply -k k8s/overlays/dev` (or equivalent documented command) for contributors who skip compose.
- **D-02:** “Healthy endpoints” means **HTTP 200** on **`GET /health`** for **indexer** (8000), **retriever** (8001), **qa_agent** (8002), and **git-watcher** (8003) under compose port mapping. Health payloads may differ per service; success is **reachable + 200**.

### Fixtures & indexing

- **D-03:** Ship a **small in-repo fixture repository** (e.g. under `tests/fixtures/sample-repo/` or `e2e/fixtures/sample-repo/`) with a few files and **at least one stable, greppable symbol** so citations can be asserted without network clones.
- **D-04:** Indexing for the fixture uses the existing **`POST /index`** contract on the indexer (`services/indexer/main.py`). Exact JSON body and env defaults are left to plan-phase, but the fixture path must be **self-contained** (no dependency on private GitHub repos for Phase 1 proof).

### Query path & LLM

- **D-05:** E2E-02 “cited answer” is validated against the **qa_agent** HTTP API (exact route from `services/qa_agent/main.py` / `docs/API.md` — plan-phase names the canonical `curl` sequence).
- **D-06:** **LLM calls require `OPENAI_API_KEY`** (or whatever env the qa_agent already reads). **CI:** if no org/repo secret is configured, a **non-secret** job proves health + indexer + retriever wiring; a **separate optional workflow job** (gated on presence of `OPENAI_API_KEY`) or **documented manual runbook** satisfies E2E-02 for Phase 1. Do not pretend unattended CI proves the LLM path without a key or a deterministic substitute — document which path was used in the proof artifact or README section.

### Automation surface

- **D-07:** Deliver a **single smoke script** (e.g. `scripts/smoke_compose.sh` or `make smoke`) that: waits for datastore health, curls **all four** `/health` endpoints, and exits non-zero on failure.
- **D-08:** Deliver either a **minimal automated test** (pytest) that hits the stack when compose is up, **or** a **numbered runbook** (markdown under `docs/` or `.planning/phases/01-integration-proof/`) with copy-paste curls for index → query → citation check — roadmap already allows “minimal E2E test **or** documented runbook”; pick one as primary and keep the other as optional only if cost is low.

### CI contract (E2E-03)

- **D-09:** **`pytest tests/`** remains **required green** on push to `main` / `develop` (as today).
- **D-10:** **`flake8`** hard-error selectors and **`black --check`** remain **required green**.
- **D-11:** **`mypy services || true`** is **not** an honest regression gate — Phase 1 must **either** remove `|| true` after fixing/suppressing errors in a controlled way, **or** replace with an explicit **informational** job name and update REQUIREMENTS wording in the same phase if the project intentionally defers strict mypy. Default intent for this discuss-phase: **tighten toward failing CI** once error budget is understood (delegate specifics to plan 01-03).
- **D-12:** **`docker build`** for all **four** Dockerfiles in the `build` job remains in scope; failures must remain blocking.

### Claude’s discretion

- Fixture directory name, smoke script language (bash vs `just`), exact pytest markers (`@pytest.mark.integration`), optional `docker compose up --wait` usage, and whether to add a tiny **httpx**-level test vs full stack test.

</decisions>

<canonical_refs>

## Canonical references

**Downstream agents MUST read these before planning or implementing.**

### Requirements & vision

- `.planning/PROJECT.md` — brownfield status, validated vs active work
- `.planning/REQUIREMENTS.md` — E2E-01 … E2E-03 (Phase 1)
- `.planning/ROADMAP.md` — Phase 1 success criteria and suggested plans 01-01 … 01-03
- `docs/DESIGN.md` — architecture and NFR intent (do not expand scope into Phase 2+ features)

### Pitfalls

- `.planning/research/PITFALLS.md` — stale indexes, grounding, resource blow-ups (relevant when choosing fixture size and timeouts)

### Stack & research

- `.planning/research/SUMMARY.md`, `STACK.md`, `ARCHITECTURE.md` — technology choices and decomposition

</canonical_refs>

<code_context>

## Existing code insights

### Reusable assets

- **Compose:** `docker-compose.yml` wires **Qdrant, Redis, Elasticsearch**, then **indexer, retriever, qa-agent, git-watcher** with env pointing at internal hosts.
- **Health routes:** `GET /health` exists on Python FastAPI apps (`services/*/main.py` for indexer, retriever, qa_agent) and Ktor git-watcher (`GitWatcherApp.kt`); git-watcher Dockerfile uses **`curl` against `http://localhost:8003/health`**.
- **Indexer API:** `POST /index` on indexer (`services/indexer/main.py`).
- **CI:** `.github/workflows/ci.yml` — Python **3.10**, `pip install -e ".[dev]"`, lint/format/pytest, then **four** `docker build` commands. Working directory assumes **`may-portfolio-projects/k8s-qa-rag-agent`** under a parent checkout (monorepo layout).

### Established patterns

- Tests today are **import/smoke only** (`tests/test_imports.py`) — Phase 1 must add **integration or runbook** coverage per D-07/D-08.

### Integration points

- Phase 2 will add **negative webhook tests** and secrets posture; Phase 1 should avoid baking insecure shortcuts into the smoke script (e.g. do not disable signature checks “for demo”).

</code_context>

<specifics>

## Specific ideas

- Align README “getting started” with **actual** compose service names (`qa-agent` vs `qa_agent` import path) and ports **8000–8003** so E2E-01 matches docs.
- Consider **`docker compose up --wait`** (Compose v2) in the smoke script to reduce flake from slow ES startup.
- If CI LLM gating is used, document in workflow comments that **E2E-02 proof** is conditional so contributors know why a job is skipped.

</specifics>

<deferred>

## Deferred ideas

- **Webhook HMAC negative tests, secret scanning, allowlist enforcement** — Phase 2.
- **Correlation IDs, OTEL collector dry-run, OPERATIONS.md drills** — Phase 3.
- **IMPLEMENTATION.md / API.md / image digest policy** — Phase 4.
- **Helm umbrella, multi-tenant ACLs, Slack bot** — v2 / out of scope per `REQUIREMENTS.md`.

</deferred>

---

*Phase: 1 — Integration & proof*  
*Context gathered: 2026-05-14*
