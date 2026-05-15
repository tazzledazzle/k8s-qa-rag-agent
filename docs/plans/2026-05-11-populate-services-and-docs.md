# Populate Services and Docs Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fill all empty service modules and Phase 6 docs per the approved design in `docs/plans/2026-05-11-populate-services-and-docs-design.md`, add missing `indexer/main.py` and `qa_agent/models.py`, and rename `services/qa-agent` to `services/qa_agent` so Python imports match Docker.

**Architecture:** Phase-strict delivery: Indexer (Git → chunk → embed → Qdrant/ES) first, then Retriever (parallel dense + BM25 → rerank → Redis cache), then QA Agent (LangGraph → HTTP tools → retriever), then Git Watcher (Ktor + HMAC + indexer client), then OPERATIONS/API/TROUBLESHOOTING docs.

**Tech Stack:** Python 3.10, FastAPI, Pydantic v2, Qdrant client, Elasticsearch 8.x, Redis, sentence-transformers, LangGraph/OpenAI, Kotlin/Ktor, Gradle 8.

**Prerequisite:** Read `docs/plans/2026-05-11-populate-services-and-docs-design.md` and `docs/IMPLEMENTATION.md` Phases 1–4 and 6.

---

### Task 1: Rename QA agent package directory

**Files:**
- Move: `services/qa-agent/` → `services/qa_agent/` (entire directory)
- Modify: `services/qa_agent/Dockerfile` — `COPY services/qa_agent /app/services/qa_agent`
- Modify: `docker-compose.yml` — `dockerfile`, `context`, volume paths for qa agent
- Modify: `.github/workflows/ci.yml` — `docker build` path for qa-agent image
- Modify: `README.md` — any `services/qa-agent` path references

**Step 1:** Rename directory (git mv preserves history).

```bash
cd may-portfolio-projects/k8s-qa-rag-agent && git mv services/qa-agent services/qa_agent
```

**Step 2:** Grep for remaining `qa-agent` path strings that refer to the **folder** (not K8s app labels) and fix.

Run: `rg 'services/qa-agent' may-portfolio-projects/k8s-qa-rag-agent`

Expected: No matches (or only intentional comments updated).

**Step 3:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent may-portfolio-projects/k8s-qa-rag-agent/docker-compose.yml may-portfolio-projects/k8s-qa-rag-agent/.github/workflows/ci.yml may-portfolio-projects/k8s-qa-rag-agent/README.md
git commit -m "refactor: rename qa-agent service folder to qa_agent for valid imports"
```

---

### Task 2: Add rapidfuzz for retriever deduplication

**Files:**
- Modify: `may-portfolio-projects/k8s-qa-rag-agent/pyproject.toml` — add `rapidfuzz>=3.0.0` under `dependencies`

**Step 1:** Add dependency line after existing util deps.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/pyproject.toml
git commit -m "deps: add rapidfuzz for retriever chunk deduplication"
```

---

### Task 3: Indexer — `vector_db.py`

**Files:**
- Create/Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/indexer/vector_db.py`

**Step 1:** Implement a small class or module functions:

- Read `QDRANT_URL`, collection name from env (e.g. `QDRANT_COLLECTION`, default `code_chunks`).
- `ensure_collection(vector_size: int)` — create collection if missing (cosine distance).
- `upsert_points(points: list)` where each point has `id: int` (deterministic, `hash(file_path + start_line) % 2**63`), `vector: list[float]`, payload: `file_path`, `language`, `start_line`, `end_line`, `text`.

**Step 2:** Manual sanity: `python -c "from services.indexer.vector_db import ..."` from repo root with `PYTHONPATH=.` or editable install.

**Step 3:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/indexer/vector_db.py
git commit -m "feat(indexer): add Qdrant upsert client with deterministic ids"
```

---

### Task 4: Indexer — `text_search.py`

**Files:**
- Create/Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/indexer/text_search.py`

**Step 1:** Elasticsearch async or sync client from `ELASTICSEARCH_URL`; index name env `ES_INDEX` default `code_chunks`.

- `ensure_index()` — create index with mapping: text field for chunk body, keyword for `file_path`, integers for lines, optional `chunk_id` / `language`.
- `bulk_index(documents: list[dict])` aligned with retriever’s expected query fields.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/indexer/text_search.py
git commit -m "feat(indexer): add Elasticsearch bulk indexing client"
```

---

### Task 5: Indexer — `requirements.txt`

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/indexer/requirements.txt`

**Step 1:** Either single comment `# Installed via root pyproject.toml (pip install -e .)` or pin only indexer-only extras not in root. Prefer **comment-only** to avoid drift with root `pyproject.toml`.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/indexer/requirements.txt
git commit -m "chore(indexer): document dependency source in requirements.txt"
```

---

### Task 6: Indexer — `main.py` (FastAPI)

**Files:**
- Create: `may-portfolio-projects/k8s-qa-rag-agent/services/indexer/main.py`

**Step 1:** Implement:

- `app = FastAPI(title="Indexer")`
- `GET /health` → instantiate Qdrant + ES clients, ping both, return `HealthResponse` from `models.py`.
- `POST /index` → `IndexRequest` → `git_client` clone/update → walk files (respect include/exclude globs from request or defaults) → `chunker` → `embeddings.encode_batch` (batch 32) → `vector_db.upsert` + `text_search.bulk_index` → `IndexResponse` with counts and duration.

**Step 2:** Run locally (optional): `uvicorn services.indexer.main:app --reload --port 8000` from repo root with deps and env vars pointed at local Qdrant/ES (or skip if no containers).

**Step 3:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/indexer/main.py
git commit -m "feat(indexer): add FastAPI app with health and index endpoints"
```

---

### Task 7: Retriever — `models.py`

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/retriever/models.py`

**Step 1:** Define Pydantic models: `SearchRequest` (query, optional language), `ChunkHit` (id, score, file_path, language, start_line, end_line, text), `SearchResponse` (chunks: list[ChunkHit]).

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/retriever/models.py
git commit -m "feat(retriever): add search request and response schemas"
```

---

### Task 8: Retriever — `dense_search.py`

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/retriever/dense_search.py`

**Step 1:** Qdrant client search: embed query with same model id as indexer (env `EMBEDDING_MODEL`, default `BAAI/bge-base-en-v1.5` via shared sentence-transformers or query endpoint if indexer exposes one — **prefer local embedder in retriever** for simplicity). `search(query_vector, limit=20)` return `list[ChunkHit]`.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/retriever/dense_search.py
git commit -m "feat(retriever): add Qdrant dense vector search top-20"
```

---

### Task 9: Retriever — `bm25_search.py`

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/retriever/bm25_search.py`

**Step 1:** ES `multi_match` or `match` on chunk text, size 20, map hits to `ChunkHit`.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/retriever/bm25_search.py
git commit -m "feat(retriever): add Elasticsearch BM25 search top-20"
```

---

### Task 10: Retriever — `reranker.py`

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/retriever/reranker.py`

**Step 1:** Load `cross-encoder/mmarco-MiniLMv2-L12-H384-v1`; function `rerank(query: str, candidates: list[ChunkHit], top_k: int = 5) -> list[ChunkHit]` sorted by cross-encoder score.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/retriever/reranker.py
git commit -m "feat(retriever): add cross-encoder reranking to top-5"
```

---

### Task 11: Retriever — `cache.py`

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/retriever/cache.py`

**Step 1:** Redis client; key `sha256(f"{query}\0{language or ''}")` hex digest; JSON-serialize `SearchResponse`; TTL 600 seconds; `get` / `set` helpers.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/retriever/cache.py
git commit -m "feat(retriever): add Redis search result cache with 10m TTL"
```

---

### Task 12: Retriever — `main.py`

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/retriever/main.py`

**Step 1:** FastAPI app:

- `GET /health` — ping Qdrant, ES, Redis (optional ping).
- `POST /search` — check cache; if miss, run dense + BM25 in parallel (`asyncio.gather`); merge by id; **dedup** chunks with `rapidfuzz.fuzz.token_sort_ratio` ≥ 80 on `text`; rerank; cache set; return `SearchResponse`.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/retriever/main.py
git commit -m "feat(retriever): add FastAPI hybrid search with cache and dedup"
```

---

### Task 13: Retriever — `requirements.txt`

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/retriever/requirements.txt`

**Step 1:** Same pattern as indexer (comment pointing to root package).

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/retriever/requirements.txt
git commit -m "chore(retriever): document dependency source in requirements.txt"
```

---

### Task 14: Checkpoint — retriever smoke (optional)

**Step 1:** With docker-compose or local services, `curl -s localhost:8001/health` and `curl -s -X POST localhost:8001/search -H 'Content-Type: application/json' -d '{"query":"test"}'`.

Expected: JSON response shape matches `SearchResponse` (may be empty chunks if index empty).

---

### Task 15: QA Agent — `models.py`

**Files:**
- Create: `may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent/models.py`

**Step 1:** `AskRequest` (question: str, optional session_id), `AskResponse` (answer: str, optional citations: list, optional debug: dict).

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent/models.py
git commit -m "feat(qa-agent): add ask API pydantic models"
```

---

### Task 16: QA Agent — `state.py`

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent/state.py`

**Step 1:** TypedDict or Pydantic model for LangGraph state: `question`, `messages` or `tool_calls`, `retrieved_chunks`, `reasoning`, `answer`, `iterations`, `answer_complete`.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent/state.py
git commit -m "feat(qa-agent): define LangGraph agent state schema"
```

---

### Task 17: QA Agent — `llm.py`

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent/llm.py`

**Step 1:** OpenAI client wrapper: `chat(messages, temperature=0.3)` reading `OPENAI_API_KEY` and optional `OPENAI_MODEL` from env.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent/llm.py
git commit -m "feat(qa-agent): add OpenAI chat wrapper with fixed temperature"
```

---

### Task 18: QA Agent — `tools.py`

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent/tools.py`

**Step 1:** LangChain `@tool` or LangGraph tool defs: `search_codebase(query: str)`, `search_runbooks(query: str)` — both HTTP `POST` to `{RETRIEVER_BASE_URL}/search` with JSON body (runbooks may use same index with different filter env — **YAGNI:** same endpoint with optional `source=runbook` query param if index supports it; else identical stub calling same search).

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent/tools.py
git commit -m "feat(qa-agent): add retriever-backed search tools"
```

---

### Task 19: QA Agent — `agent.py`

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent/agent.py`

**Step 1:** Build LangGraph `StateGraph`: agent node calls LLM with tools bound; conditional edge: if tool calls, execute tools (parallel if multiple); if final answer or `iterations >= 5` or model signals done, END. Export compiled graph or invoker function `run_agent(question: str) -> AskResponse`.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent/agent.py
git commit -m "feat(qa-agent): add LangGraph ReAct loop with iteration cap"
```

---

### Task 20: QA Agent — `main.py`

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent/main.py`

**Step 1:** FastAPI: `GET /health`, `POST /ask` body `AskRequest` → `run_agent` → `AskResponse`.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent/main.py
git commit -m "feat(qa-agent): add FastAPI entrypoint for ask and health"
```

---

### Task 21: QA Agent — `requirements.txt`

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent/requirements.txt`

**Step 1:** Comment referencing root `pyproject.toml`.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/qa_agent/requirements.txt
git commit -m "chore(qa-agent): document dependency source in requirements.txt"
```

---

### Task 22: Git Watcher — Gradle scaffold

**Files:**
- Create: `may-portfolio-projects/k8s-qa-rag-agent/services/git-watcher/settings.gradle.kts`
- Create: `may-portfolio-projects/k8s-qa-rag-agent/services/git-watcher/build.gradle.kts`
- Move: `*.kt` from `services/git-watcher/` → `services/git-watcher/src/main/kotlin/com/k8sqarag/gitwatcher/` (adjust package declarations)

**Step 1:** `build.gradle.kts`: Ktor, Kotlin JVM 21, application plugin, fat jar or shadow if needed for `java -jar app.jar`.

**Step 2:** From `services/git-watcher`: `gradle build -x test` succeeds.

**Step 3:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/git-watcher
git commit -m "build(git-watcher): add Gradle Ktor project layout"
```

---

### Task 23: Git Watcher — Kotlin implementation

**Files:**
- Implement under `src/main/kotlin/...`: `GitWatcherApp.kt`, `GithubSignatureVerifier.kt`, `WebhookController.kt`, `IndexerClient.kt`, `models.kt`

**Step 1:** HMAC-SHA256 verification for `X-Hub-Signature-256` prefix `sha256=`; parse push JSON for `repository.clone_url` (or ssh_url) and `ref` → branch name; `IndexerClient.postIndex(repoUrl, branch)` with 10s timeout; routes `POST /webhook`, `GET /health`.

**Step 2:** `gradle build -x test`

**Step 3:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/services/git-watcher
git commit -m "feat(git-watcher): implement webhook verify and indexer trigger"
```

---

### Task 24: Docs — OPERATIONS.md

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/docs/OPERATIONS.md`

**Step 1:** Sections: overview, SLOs (from DESIGN table), dependencies (Qdrant, ES, Redis), secrets/env checklist, reindex/rebuild procedure, alert ideas, retriever degradation note.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/docs/OPERATIONS.md
git commit -m "docs: add operations runbook outline"
```

---

### Task 25: Docs — API.md

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/docs/API.md`

**Step 1:** Tables for ports 8000–8003 endpoints; curl examples for `/health`, `/index`, `/search`, `/ask`, `/webhook`; note OpenAPI at `/docs` for FastAPI services.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/docs/API.md
git commit -m "docs: add API reference and curl examples"
```

---

### Task 26: Docs — TROUBLESHOOTING.md

**Files:**
- Fill: `may-portfolio-projects/k8s-qa-rag-agent/docs/TROUBLESHOOTING.md`

**Step 1:** Common issues: import/path (`qa_agent`), Qdrant/ES connection refused, Redis auth, model download size/time, webhook signature mismatch, LangGraph iteration limit.

**Step 2:** Commit

```bash
git add may-portfolio-projects/k8s-qa-rag-agent/docs/TROUBLESHOOTING.md
git commit -m "docs: add troubleshooting guide"
```

---

### Task 27: Cross-check setuptools packages

**Files:**
- Modify: `may-portfolio-projects/k8s-qa-rag-agent/pyproject.toml` `[tool.setuptools.packages.find]` if needed so `services.qa_agent` is discovered (folder rename may suffice).

**Step 1:** `pip install -e may-portfolio-projects/k8s-qa-rag-agent` then `python -c "import services.qa_agent.main"`

**Step 2:** Commit only if `pyproject.toml` changed.

---

### Task 28: Update IMPLEMENTATION.md checkboxes (optional)

**Files:**
- Modify: `may-portfolio-projects/k8s-qa-rag-agent/docs/IMPLEMENTATION.md` — mark Phase 1–4 / doc items done where accurate.

**Step 1:** Single commit if you want docs to reflect status.

---

## Verification commands (end state)

```bash
cd may-portfolio-projects/k8s-qa-rag-agent
pip install -e ".[dev]"
ruff check services  # if configured
pytest tests -q  # add tests incrementally per tasks above
docker compose build
```

Expected: All service images build; FastAPI modules import.

---

## Execution handoff

Plan complete and saved to `docs/plans/2026-05-11-populate-services-and-docs.md`. Design saved to `docs/plans/2026-05-11-populate-services-and-docs-design.md`.

**Two execution options:**

1. **Subagent-Driven (this session)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. **REQUIRED SUB-SKILL:** superpowers:subagent-driven-development.

2. **Parallel Session (separate)** — New session with **superpowers:executing-plans**, batch execution with checkpoints.

**Which approach do you want?**
