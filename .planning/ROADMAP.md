# Roadmap: k8s-qa-rag-agent

## Overview

Move from **implemented components** to a **credible, demonstrable system**: prove the compose/K8s path, harden webhook and secrets posture, complete observability and ops truth, then lock documentation and release mechanics.

## Phases

- [x] **Phase 1: Integration & proof** — End-to-end path and CI as quality gate  
- [x] **Phase 2: Security & boundaries** — Webhook trust, secrets, clone allowlists  
- [x] **Phase 3: Observability & operations** — Correlation, OTEL validity, runbook drills  
- [x] **Phase 4: Documentation & release** — Honest implementation checklist, API examples, image strategy  

## Phase details

### Phase 1: Integration & proof

**Goal:** Demonstrate the core value on representative data with automated regression signal.  
**Depends on:** Nothing  
**Requirements:** E2E-01, E2E-02, E2E-03  
**UI hint:** no  
**Success criteria** (what must be TRUE):

1. A new contributor can follow docs and reach healthy `/health` (or equivalent) on indexer, retriever, and QA agent using compose or local k8s.  
2. A scripted or manual test shows a question → retrieval → answer path with at least one correct citation.  
3. Default branch CI completes successfully on a clean checkout.

**Plans:** 3 plans (suggested)

Plans:

- [x] 01-01: Compose (or minikube) smoke script + seed repo fixture  
- [x] 01-02: Minimal E2E test or documented runbook for query path  
- [x] 01-03: CI stabilization (failures fixed or jobs scoped honestly)

**Transitioned:** 2026-05-15 — closed with `01-VERIFICATION.md`; next work is **Phase 2** (`.planning/ROADMAP.md`).

### Phase 2: Security & boundaries

**Goal:** Ensure the automation edge (webhook) and credentials cannot be abused in a default deployment.  
**Depends on:** Phase 1  
**Requirements:** SEC-01, SEC-02, SEC-03  
**UI hint:** no  
**Success criteria:**

1. Invalid signatures never enqueue indexing work (verified with negative tests).  
2. No plaintext secrets in repo; sample manifests use Secret references only.  
3. Configuration for allowed repositories is documented and enforced in code.

**Plans:** 2 plans

Plans:

- [x] 02-01: Webhook hardening + tests (Git watcher + indexer contract)  
- [x] 02-02: Secret inventory + kustomize/compose alignment

**Transitioned:** 2026-05-15 — closed with `02-VERIFICATION.md`; next work is **Phase 3** (`.planning/ROADMAP.md`).

### Phase 3: Observability & operations

**Goal:** Operators can detect and mitigate failure modes within DESIGN targets.  
**Depends on:** Phase 2  
**Requirements:** OBS-01, OBS-02, OBS-03  
**UI hint:** no  
**Success criteria:**

1. Single user request can be traced across QA and retriever logs via shared id.  
2. OTEL collector config validates in a cluster dry-run or integration check.  
3. OPERATIONS.md runbook steps are executed once and annotated with results.

**Plans:** 2 plans

Plans:

- [x] 03-01: Logging + trace correlation pass  
- [x] 03-02: OTEL + ops doc drill

**Transitioned:** 2026-05-15 — closed with `03-VERIFICATION.md`; next work is **Phase 4** (`.planning/ROADMAP.md`).

### Phase 4: Documentation & release

**Goal:** Public artifacts tell the truth; releases are reproducible.  
**Depends on:** Phase 3  
**Requirements:** DOC-01, DOC-02, REL-01  
**UI hint:** no  
**Success criteria:**

1. IMPLEMENTATION.md reflects verified status, not aspirational checkboxes.  
2. API.md examples are copy-paste accurate against running services.  
3. All service Dockerfiles build in CI; prod overlay documents tag/digest policy.

**Plans:** 2 plans

Plans:

- [x] 04-01: Documentation sync + OpenAPI/curl alignment  
- [x] 04-02: Image build matrix + tagging doc

**Transitioned:** 2026-05-15 — closed with `04-VERIFICATION.md`; **v1 roadmap complete** (all four phases transitioned).

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|------------------|--------|-----------|
| 1. Integration & proof | 3/3 | **Transitioned** | 2026-05-15 |
| 2. Security & boundaries | 2/2 | **Transitioned** | 2026-05-15 |
| 3. Observability & operations | 2/2 | **Transitioned** | 2026-05-15 |
| 4. Documentation & release | 2/2 | **Transitioned** | 2026-05-15 |

---
*Roadmap created: 2026-05-12*  
*Phase 1 transitioned: 2026-05-15*  
*Phase 2 transitioned: 2026-05-15*  
*Phase 3 transitioned: 2026-05-15*  
*Phase 4 transitioned: 2026-05-15 — v1 milestone complete*
