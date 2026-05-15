# Populate Services and Docs — Design (Approved)

**Date:** 2026-05-11  
**Status:** Approved  
**Sources:** `docs/IMPLEMENTATION.md`, `docs/DESIGN.md`, repository audit (empty / missing files)

## Goal

Implement all empty service modules and Phase 6 documentation, add missing roadmap files (`services/indexer/main.py`, `services/qa_agent/models.py`), and fix the QA agent Python package path so Docker imports match the filesystem.

## Scope

### In scope

- **Indexer:** `vector_db.py`, `text_search.py`, `requirements.txt`; **create** `main.py` with FastAPI `/health`, `/index` wired to existing `git_client`, `chunker`, `embeddings`, and new Qdrant/ES clients. Deterministic chunk IDs, batch embedding size 32, payloads per IMPLEMENTATION.
- **Retriever:** All previously empty modules + `requirements.txt`; hybrid search (dense top 20, BM25 top 20), cross-encoder rerank to top 5, Redis cache TTL 10 minutes, merge/dedup.
- **QA Agent:** All previously empty modules + `requirements.txt`; **create** `models.py`. LangGraph ReAct, tools calling retriever HTTP, max 5 iterations, temperature 0.3.
- **Git Watcher:** Kotlin/Ktor implementation of listed components; Gradle project (`build.gradle.kts`, `settings.gradle.kts`) with `src/main/kotlin` layout so `services/git-watcher/Dockerfile` builds.
- **Docs:** `docs/OPERATIONS.md`, `docs/API.md`, `docs/TROUBLESHOOTING.md` from DESIGN + IMPLEMENTATION Phase 6 bullets.

### Out of scope (this design)

- New Helm chart, full OTEL instrumentation in application code, PostgreSQL session store (optional in DESIGN only).

## Execution strategy

**Strict phase order** (Indexer → Retriever → QA Agent → Git Watcher → docs), with a **checkpoint** after Retriever: smoke hybrid search before deep LangGraph work.

**API.md:** Fixed outline + placeholders where needed; replace with concrete curls/OpenAPI references once routes exist.

## Critical repo fix

Rename **`services/qa-agent` → `services/qa_agent`** so `uvicorn services.qa_agent.main:app` is valid.

Update:

- `services/qa_agent/Dockerfile` (COPY paths)
- `docker-compose.yml` (build context, volumes)
- `.github/workflows/ci.yml` (docker build path)
- `README.md` (path references to the service folder)

Keep Kubernetes **resource names** and labels such as `app: qa-agent` unchanged where they refer to the workload, not the source folder.

## Service contracts (summary)

| Service | Port | Notes |
|---------|------|--------|
| Indexer | 8000 | `HealthResponse`, `IndexRequest`/`IndexResponse`; Qdrant + Elasticsearch connectivity in health |
| Retriever | 8001 | `POST /search` (or equivalent); cache key from stable `hash(query + language)`; dedup: high string similarity (e.g. rapidfuzz ratio > 0.8) — IMPLEMENTATION “Levenshtein < 0.8” interpreted as similarity threshold |
| QA Agent | 8002 | State: question, tool_calls, results, reasoning, answer, iterations, `answer_complete`; tools: `search_codebase`, `search_runbooks` |
| Git Watcher | 8003 | HMAC-SHA256 `X-Hub-Signature-256`; **push** events only; `POST` indexer `/index`, 10s client timeout; `GET /health` |

## Configuration

Per-service Pydantic Settings: Qdrant URL, ES URL, Redis URL, OpenAI key, GitHub webhook secret, internal HTTP URLs (retriever, indexer), model IDs with defaults from IMPLEMENTATION/DESIGN.

## Errors (policy)

- **Indexer:** Fail index on dual-write or embedding failure; surface dependency errors in response/logs.
- **Retriever:** Prefer documented behavior: optional degrade if one search backend fails (document in OPERATIONS).
- **Git watcher:** 401 on bad signature; respond quickly after firing indexer request.

## Testing (minimal)

- Unit tests where low-cost: deterministic chunk ID, cache key, webhook signature golden case.
- Heavy model tests optional or marked slow; document in TROUBLESHOOTING.

## Next step

Implementation plan: `docs/plans/2026-05-11-populate-services-and-docs.md` (writing-plans output).
