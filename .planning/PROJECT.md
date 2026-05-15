# k8s-qa-rag-agent

## What This Is

A **Kubernetes-native RAG stack** that lets engineers ask natural-language questions about **live code and runbooks**, with answers grounded in the repository and operational docs. It targets hybrid retrieval (dense + BM25 + reranking), LangGraph agents, webhook-driven reindexing, and GitOps-friendly manifests for portfolio-grade operations.

## Core Value

**An engineer gets a cited, trustworthy answer about the current codebase or runbooks within seconds**, backed by fresh indexes and observable behavior on Kubernetes.

## Requirements

### Validated

- ✓ **Monorepo layout** — `services/` (indexer, retriever, qa_agent, git-watcher), `k8s/`, `docs/`, CI — existing
- ✓ **Indexer pipeline (Python)** — Git client, AST-aware chunking, embeddings, Qdrant + Elasticsearch paths — code present under `services/indexer/`
- ✓ **Retriever (Python)** — hybrid search modules, cache, reranker — `services/retriever/`
- ✓ **QA agent (Python)** — LangGraph-style agent, tools, FastAPI entry — `services/qa_agent/`
- ✓ **Git watcher (Kotlin/Ktor)** — webhook path, signature verification, indexer client — `services/git-watcher/`
- ✓ **Kubernetes base + overlays** — Qdrant StatefulSet, deployments, CronJob, OTEL ConfigMap, HPA/PDB overlays — `k8s/`
- ✓ **Local orchestration** — `docker-compose.yml` for dependent services
- ✓ **Design authority** — `docs/DESIGN.md` captures architecture, NFRs, security model

- ✓ **Phase 1 integration proof (E2E-01…E2E-03)** — compose smoke script, in-repo `file://` fixture indexing, QA citation extraction from tool payloads, `docs/LOCAL-DEV.md` + `docs/PHASE1-RUNBOOK.md`, CI: flake8/black/mypy/pytest + four Docker builds (2026-05-15)

- ✓ **Phase 2 security & boundaries (SEC-01…SEC-03)** — git-watcher HMAC + negative tests, `docs/SECURITY-SECRETS.md`, indexer/batch `repo_allowlist`, git-watcher `RepoAllowlist` parity, k8s/compose/prod webhook hardening (`02-VERIFICATION.md`, 2026-05-15)

### Active

- [ ] Close gaps between **design vs implementation** (IMPLEMENTATION checklist, optional components like Postgres session store)
- [ ] **Operations**: SLO-aligned dashboards, alert hooks, and runbook ↔ behavior parity
- [ ] **Release quality**: image tagging strategy, documented upgrade path (CI + docker build gates landed in Phase 1)

### Out of Scope

- **Full multi-tenant SaaS product** — portfolio scope; ACL model may stay simplified
- **Replacing Elasticsearch with Typesense** — documented trade-off; no mandate unless explicitly prioritized
- **Mobile or desktop clients** — HTTP API consumers only for v1

## Context

Brownfield initialization (`/gsd/new-project`): substantial Python services, Kotlin git-watcher, and Kustomize layouts already exist. `README.md` and `docs/DESIGN.md` define intent: sub-minute staleness via webhooks, hybrid retrieval, OTEL, HPA. External dependencies (Redis, Elasticsearch, LLM keys) are expected via env/Secrets.

## Constraints

- **Kubernetes-first**: manifests and health probes must remain first-class
- **Portfolio credibility**: docs, tests, and reproducible local dev must stay honest (no “demo-only” gaps where design claims prod behavior)
- **Resource realism**: embedding + reranker memory/CPU assumptions per DESIGN capacity notes

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Hybrid retrieval (Qdrant + BM25 + cross-encoder) | Maximizes recall/precision on code + prose | ✓ Phase 1 — fixture + runbook proof (`docs/PHASE1-RUNBOOK.md`) |
| LangGraph for QA agent | Controlled tool loop, observable steps | ✓ Phase 1 — `/ask` + tool citations (`01-VERIFICATION.md`) |
| Kotlin git-watcher | Isolated webhook edge, JVM ecosystem for HMAC/crypto clarity | ✓ Good — code present |
| Kustomize overlays (dev/staging/prod) | GitOps-friendly environment promotion | — Pending cluster apply verification |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):

1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):

1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-15 after `/gsd-transition 4` (v1 roadmap Phases 1–4 complete)*
