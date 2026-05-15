# Phase 3: Observability & operations — Context

**Gathered:** 2026-05-15  
**Status:** Plan-phase complete — executable plans **`03-01-PLAN.md`**, **`03-02-PLAN.md`**; ready for `/gsd-execute-phase 3`.

<domain>

## Phase boundary

Deliver **OBS-01**, **OBS-02**, and **OBS-03** from `.planning/REQUIREMENTS.md`:

- **OBS-01:** QA agent and retriever emit **structured logs** that include a **correlation id per HTTP request** (and that id is visible on both sides of the QA → retriever hop).
- **OBS-02:** **OpenTelemetry** configuration **in-cluster** matches **documented** ports/exporters — no broken collector wiring in base or **prod** overlay (validation is part of the proof).
- **OBS-03:** `docs/OPERATIONS.md` describes **failure modes** called out in roadmap success criteria (**index lag**, **Elasticsearch yellow**, **Qdrant disk pressure**) with **concrete remediation** steps, and those steps are **validated once manually** (evidence recorded in verification or the doc itself).

Phase 3 does **not** ship a full observability backend (managed Grafana/Loki/Tempo SaaS), define production SLO burn alerts as code, or complete **DOC-01** / **DOC-02** / **REL-01** — those remain **Phase 4** unless explicitly pulled in during plan-phase.

**Minimum service scope (OBS-01 wording):** **QA agent** + **retriever** are in scope for correlation/logging. **Indexer** and **git-watcher** may receive best-effort correlation in a follow-up wave only if **03-01** / **03-02** plans explicitly add them without blowing scope.

</domain>

<decisions>

## Implementation decisions

### OBS-01 — Structured logs + correlation id

- **D-01:** Generate a **per-request correlation id** at the **HTTP boundary** (FastAPI middleware or equivalent) for **`POST /ask`** (qa-agent) and **`POST /search`** (retriever). Prefer **UUIDv4** or ULID; log field name **`correlation_id`** (snake_case) for consistency across services.
- **D-02:** **Propagate** the same id on the **QA agent → retriever** HTTP call: e.g. header **`X-Correlation-ID`** on `httpx` requests in `services/qa_agent/tools.py` (`_search`). Retriever middleware reads the header (or generates one if absent for non-QA callers) and attaches it to logs.
- **D-03:** **Structured logs** = **JSON lines** to stdout (Kubernetes-friendly) for the two Python services, at least for **request-scoped** log records (start/end, errors, retriever branch warnings). Implementation detail (stdlib `logging` + JSON formatter vs `structlog`) is left to **plan-phase**; avoid introducing heavy new deps without justification.
- **D-04:** **Optional:** Echo **`correlation_id`** in selected **HTTP response headers** or response body fields only if it helps debugging and does not leak into stable public API contracts without version bump — default **logs + outbound header only**.

### OBS-02 — OTEL collector + app instrumentation

- **D-05:** Today **`k8s/base/configmap-otel.yaml`** exists and is listed in **`kustomization.yaml`**, but the **qa-agent** Deployment’s **otel sidecar** has **no** `args`/`command`, **no** `volumeMount` for the ConfigMap, and the embedded collector YAML exports OTLP to **`localhost:4317`** (likely a **self-loop / noop** relative to a real upstream). **Plan-phase** must decide: either **wire** the ConfigMap correctly + fix pipelines, or **replace** with a minimal known-good config (e.g. `debug` + `prometheus` only until a real backend exists).
- **D-06:** **Document** in-repo the expected **`OTEL_EXPORTER_OTLP_ENDPOINT`** (and gRPC vs HTTP) for **compose** and **Kubernetes** (sidecar `127.0.0.1:4317` vs cluster collector Service). **Prod overlay** must not contradict base docs (ports, image tags).
- **D-07:** **Python instrumentation:** prefer official **`opentelemetry-instrumentation-asgi`** / FastAPI auto-instrumentation **or** manual spans around `/ask` and `/search` — enough to prove traces reach the collector in a **dry-run** (`kubectl` apply + pod logs, or `docker compose` with collector).
- **D-08:** **CI / automation:** add a **non-flaky** check that the collector config **parses** (`otelcol validate` with the built image, or upstream validate action). Full e2e trace export to Jaeger is **optional**; config validity is **mandatory** for OBS-02 closure.
- **D-09:** **Image pins:** prod-oriented work should avoid naked **`latest`** for collector where overlays claim production posture (align with **REL-01** spirit without implementing full digest policy).

### OBS-03 — OPERATIONS.md + manual validation

- **D-10:** Extend **`docs/OPERATIONS.md`** with explicit subsections (table or numbered lists): **index lag** (symptoms, check indexer logs/CronJob, reindex, webhook path), **Elasticsearch yellow** (allocation, disk, shard count, single-node caveats from README), **Qdrant disk / collection growth** (volume, pruning strategy, re-embed cost), plus pointers to existing **retriever degradation** section.
- **D-11:** **Validation record:** after authoring steps, **execute each remediation path once** in a realistic environment (local compose **or** documented `kubectl` flow) and capture **date + outcome** in **`03-VERIFICATION.md`** or a short **“Validated”** subsection in `OPERATIONS.md` — avoid “paper runbooks” with zero proof.
- **D-12:** **Git-watcher / indexer ops** (webhook failure rate, signature misconfig) may **cross-link** to `docs/SECURITY-SECRETS.md` and Phase 2 artifacts rather than duplicating secrets guidance.

</decisions>

<canonical_refs>

## Canonical references

**Downstream agents MUST read these before planning or implementing.**

### Requirements & vision

- `.planning/REQUIREMENTS.md` — **OBS-01 … OBS-03**
- `.planning/ROADMAP.md` — Phase 3 success criteria; plans **03-01**, **03-02**
- `.planning/PROJECT.md` — operations item under **Active** until Phase 3 completes
- `docs/DESIGN.md` — observability intent, SLO / trace bullets (targets, not guarantees)

### Prior phases

- `.planning/phases/02-security-boundaries/02-VERIFICATION.md` — trust boundaries for `/index` vs webhook
- `.planning/phases/01-integration-proof/01-VERIFICATION.md` — CI and smoke baseline

### Pitfalls

- `.planning/research/PITFALLS.md` — **trace correlation** from HTTP → retriever → stores; prevention notes (`trace_id`, structured logs)

</canonical_refs>

<code_context>

## Existing code insights

### QA agent (`services/qa_agent/`)

- **`main.py`:** FastAPI app with `/health`, **`POST /ask`** → `run_agent()`; uses stdlib **`logging`**; **no** middleware, **no** correlation id, **no** OTEL.
- **`tools.py`:** **`httpx.Client.post`** to retriever `/search` — no custom headers today.

### Retriever (`services/retriever/`)

- **`main.py`:** FastAPI **`/search`** (async), **`/health`**; stdlib logging; warnings on dense/BM25 partial failure; **no** correlation id.

### Indexer / git-watcher

- Stdlib logging in indexer paths; **Kotlin** git-watcher uses stdout-style errors; **not** required by OBS-01 text but noted for optional extension.

### Kubernetes

- **`k8s/base/configmap-otel.yaml`:** OTLP **receiver** on `4317`/`4318`; **exporter** `otlp` endpoint **`localhost:4317`** (suspicious for real export); `logging` exporter at **debug**.
- **`k8s/base/qa-agent-deployment.yaml`:** Second container **`otel-collector-sidecar`** (`otel/opentelemetry-collector-k8s:latest`) exposes `4317` — **no** config volume, **no** `args`, so sidecar likely runs **defaults**, not this repo’s ConfigMap.
- **`kustomization.yaml`** includes `configmap-otel.yaml` — ConfigMap is currently **orphaned** from workloads (grep shows no `otel-collector-config` volume reference elsewhere under `k8s/`).

### Operations doc

- **`docs/OPERATIONS.md`:** Dependencies, env table, local dev, index rebuild, retriever degradation, **suggested** alerts, DR summary — **missing** deep dives for **index lag**, **ES cluster health**, **Qdrant disk pressure** required by roadmap success criteria.

</code_context>

<specifics>

## Specific ideas (for plan-phase)

- **03-01 split:** Middleware + JSON logging + `X-Correlation-ID` propagation + a **single pytest** that asserts retriever logs (or response metadata in test hook) contain the same id when calling through tools with header set.
- **03-02 split:** Fix OTEL ConfigMap + mount + `qa-agent` env; add **`otelcol validate`** to CI; document compose env for optional local collector container if added.
- **OBS-03:** Add a **runbook drill checklist** table at bottom of `OPERATIONS.md` with columns: *Failure mode | Detection | Mitigation | Validated (Y/N/date)*.

</specifics>

<deferred>

## Deferred (not Phase 3 minimum)

- Full **PrometheusRule** / Alertmanager bundles as code
- **Distributed tracing** across indexer → ES/Qdrant (nice-to-have once QA↔retriever path is solid)
- **Cost / usage** telemetry for OpenAI tokens (product metric, not ops minimum)
- **NetworkPolicy** dashboards and packet-level debugging

</deferred>

---

*Phase: 3 — Observability & operations*  
*Next command: `/gsd-execute-phase 3`*
