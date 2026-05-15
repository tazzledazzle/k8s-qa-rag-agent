# k8s-qa-rag-agent: Implementation Roadmap

## Current status (verified)

GSD Phases **1–3** are **transitioned** with verification reports; Phase **4** tracks documentation and release truth (**DOC-01**, **DOC-02**, **REL-01**). See also [RELEASE.md](RELEASE.md) for image tagging.

| Area | Status | Evidence |
|------|--------|----------|
| Indexer (FastAPI `/index`, batch, allowlist) | **Done** | `services/indexer/`; [02-VERIFICATION.md](../.planning/phases/02-security-boundaries/02-VERIFICATION.md); tests under `tests/` |
| Retriever (hybrid search, cache) | **Done** | `services/retriever/`; [01-VERIFICATION.md](../.planning/phases/01-integration-proof/01-VERIFICATION.md) |
| QA agent (LangGraph `/ask`) | **Done** | `services/qa_agent/`; correlation + tools in `tests/test_correlation_id.py` |
| Git watcher (Ktor webhook → indexer) | **Done** | `services/git-watcher/`; [02-VERIFICATION.md](../.planning/phases/02-security-boundaries/02-VERIFICATION.md) |
| Kubernetes base + overlays | **Done** | `k8s/`; `kubectl kustomize` used in phase verifications |
| CI (lint, types, tests, OTEL config validate, four `docker build`s) | **Done** | [.github/workflows/ci.yml](../.github/workflows/ci.yml); [01-VERIFICATION.md](../.planning/phases/01-integration-proof/01-VERIFICATION.md) |
| Observability (JSON logs, correlation id, OTEL sidecar + docs) | **Done** | [03-VERIFICATION.md](../.planning/phases/03-observability-operations/03-VERIFICATION.md); `docs/OPERATIONS.md` |
| DESIGN / API / OPERATIONS docs | **Done** | `docs/DESIGN.md`, `docs/API.md`, `docs/OPERATIONS.md` |
| Prometheus ServiceMonitor / Loki scrape bundles in-repo | **Not in v1** | Not shipped as YAML in this repo; OTEL uses `logging` exporter in portfolio config |
| Helm chart | **Not in v1** | See [README.md](../README.md) |

**Regression signal:** `pytest tests/`, `mypy services`, `black --check`, flake8 hard selectors — per CI `test` job.

The sections **Phase 0** onward below are **historical** planning notes (original day-by-day roadmap). They are useful context but **not** an unchecked backlog: deliverables above already exist unless explicitly marked *Not in v1*.

---

**Original timeline framing:** 2 weeks (Days 1–14), 6 internal “doc phases” (Phase 0 = setup, Phases 1–6 = core implementation).

## Phase 0: Project Structure & Setup (Days 1-2)

**Goal**: Establish project skeleton and infrastructure foundation

### Deliverables

- [x] Directory structure (services/, k8s/, docs/, .github/)
- [x] Dockerfile stubs for 4 services
- [x] Kubernetes base manifests (Deployments, StatefulSet, CronJob)
- [x] Kustomize overlays (dev, staging, prod)
- [x] GitHub Actions workflow stubs (ci.yml, deploy.yml)
- [x] Docker Compose template for local dev
- [x] Documentation file structure
- [x] Root config files (.env.example, pyproject.toml, .gitignore)

### Tasks

1. Create directory structure ✅
2. Write Dockerfiles for all services ✅
3. Create K8s base manifests ✅
4. Create Kustomize overlays ✅
5. Create GitHub Actions stubs ✅
6. Create Docker Compose template ✅
7. Initialize .env.example and pyproject.toml ✅

---

## Phase 1: Indexer Service (Days 3-5)

**Goal**: Implement Git repository indexing with AST-aware chunking and embeddings

### Deliverables

- Indexer FastAPI service with health endpoint
- Git client for cloning/updating repositories
- AST-aware Python code chunking (tree-sitter)
- Token-window fallback for non-Python code
- BAAI/bge-base-en-v1.5 embeddings generation
- Qdrant vector upsertion with deterministic IDs
- Elasticsearch BM25 text indexing

### Key Files to Create

```
services/indexer/
├── main.py              # FastAPI app, health check
├── git_client.py        # Clone/update repos
├── chunker.py           # AST parsing + token window
├── embeddings.py        # SentenceTransformer wrapper
├── vector_db.py         # Qdrant client
├── text_search.py       # Elasticsearch client
├── models.py            # Pydantic schemas
└── requirements.txt     # Service-specific dependencies
```

### Implementation Notes

- AST chunking: tree-sitter for Python, fallback to 512-token windows
- Deterministic chunk ID: `hash(file_path + start_line) % 2^63`
- Embedding batch size: 32 (optimize for latency)
- Qdrant payload: file_path, language, start_line, end_line, text
- Elasticsearch mapping: dynamic, analyzer for code

---

## Phase 2: Retriever Service (Days 6-7)

**Goal**: Implement hybrid search with dense vectors, BM25, and cross-encoder reranking

### Deliverables

- Retriever FastAPI service
- Dense vector search (Qdrant top 20)
- BM25 full-text search (Elasticsearch top 20)
- Cross-encoder reranking (top 5)
- Redis caching (10-minute TTL)
- Result deduplication

### Key Files to Create

```
services/retriever/
├── main.py              # FastAPI app
├── dense_search.py      # Qdrant client
├── bm25_search.py       # Elasticsearch client
├── reranker.py          # Cross-encoder (sentence-transformers)
├── cache.py             # Redis wrapper
├── models.py            # Pydantic schemas
└── requirements.txt
```

### Implementation Notes

- Dense search: Top 20 vectors via Qdrant
- BM25 search: Top 20 matches via Elasticsearch
- Reranker: `cross-encoder/mmarco-MiniLMv2-L12-H384-v1` (lightweight)
- Cache key: `hash(query + language)` → (results, timestamp)
- Dedup: Remove chunks with Levenshtein distance < 0.8

---

## Phase 3: QA Agent Service (Days 8-9)

**Goal**: Implement LangGraph ReAct agent for iterative reasoning

### Deliverables

- QA Agent FastAPI service
- LangGraph StateGraph with conditional edges
- Tool definitions (search_codebase, search_runbooks)
- OpenAI LLM integration
- Conversation history management
- Agent loop orchestration

### Key Files to Create

```
services/qa_agent/
├── main.py              # FastAPI app
├── agent.py             # LangGraph StateGraph
├── tools.py             # Tool definitions
├── llm.py               # OpenAI wrapper
├── state.py             # Agent state schema
├── models.py            # Pydantic schemas
└── requirements.txt
```

### Implementation Notes

- State: {question, tool_calls, results, reasoning, answer}
- Conditional edge: If answer_complete, goto END; else invoke tools
- Tool invocation: Parallel calls to retriever
- Max iterations: 5 (prevent infinite loops)
- Temperature: 0.3 (deterministic reasoning)

---

## Phase 4: Git Watcher Service (Day 10)

**Goal**: Implement GitHub webhook receiver with signature verification

### Deliverables

- Git Watcher Kotlin/Ktor service
- GitHub webhook signature verification (HMAC-SHA256)
- Webhook handler (push, pull_request events)
- HTTP client to Indexer service
- Request queuing (if needed)

### Key Files to Create

```
services/git-watcher/
├── build.gradle.kts     # Gradle config
├── src/main/
│   ├── kotlin/
│   │   ├── GitWatcherApp.kt
│   │   ├── GithubSignatureVerifier.kt
│   │   ├── WebhookController.kt
│   │   ├── IndexerClient.kt
│   │   └── models.kt
```

### Implementation Notes

- Signature verification: HMAC-SHA256 with "X-Hub-Signature-256" header
- Webhook events: only "push" (for now)
- Indexer trigger: POST /index with repo_url, branch
- Timeout: 10 seconds (don't block webhook response)

---

## Phase 5: Kubernetes Manifests & Observability (Days 11-12)

**Goal**: Complete K8s manifests, OTEL setup, and StatefulSet for Qdrant

### Deliverables

- All K8s manifests (services, deployments, statefulsets)
- Kustomize base fully implemented
- Environment-specific overlays (dev, staging, prod)
- OTEL collector ConfigMap
- Prometheus ServiceMonitor configs
- Loki log scrape configs
- Pod networking (service discovery)
- Secrets and ConfigMaps for env vars

### Key Files to Verify/Create

```
k8s/base/
├── namespace.yaml       ✅ Created
├── qa-agent-deployment.yaml     ✅ Created
├── retriever-deployment.yaml    ✅ Created
├── indexer-deployment.yaml      ✅ Created
├── git-watcher-deployment.yaml  ✅ Created
├── qdrant-statefulset.yaml      ✅ Created
├── qdrant-service.yaml          ✅ Created
├── indexer-cronjob.yaml         ✅ Created
├── configmap-otel.yaml          ✅ Created
└── kustomization.yaml           ✅ Created

k8s/overlays/dev/kustomization.yaml         ✅ Created
k8s/overlays/staging/kustomization.yaml     ✅ Created
k8s/overlays/staging/hpa-qa-agent.yaml      ✅ Created
k8s/overlays/prod/kustomization.yaml        ✅ Created
k8s/overlays/prod/hpa-*.yaml                ✅ Created
k8s/overlays/prod/pod-disruption-budget.yaml ✅ Created
```

### Implementation Notes

- Service discovery: K8s DNS (e.g., qdrant-service:6333)
- Secrets: Create manually or via sealed-secrets
- HPA: v2 (ResourceMetrics with cpu/memory targets)
- OTEL: Sidecar pattern in qa-agent pods
- PVCs: One per Indexer, one per Qdrant

---

## Phase 6: Documentation & CI/CD (Days 13-14)

**Goal**: Complete documentation and set up CI/CD pipelines

### Deliverables (as of GSD Phase 4 execute)

- [x] DESIGN.md (comprehensive architecture)
- [x] IMPLEMENTATION.md (this file — now includes **Current status** matrix at top)
- [x] OPERATIONS.md (runbooks, alerts, failure modes — see OBS-03)
- [x] API.md (curl examples, prerequisites — see DOC-02)
- [ ] TROUBLESHOOTING.md (deferred — not required for v1 roadmap)
- [x] GitHub Actions ci.yml (test, lint, build, otel-config, git-watcher)
- [x] GitHub Actions deploy.yml (k8s deploy)
- [ ] Helm chart (optional, advanced — out of scope for v1)

### Key files (reality)

```
docs/
├── DESIGN.md            ✅
├── IMPLEMENTATION.md    ✅ (this file)
├── OPERATIONS.md        ✅
├── API.md               ✅
├── RELEASE.md           ✅ (image matrix + prod pin policy)
└── images/              → Optional diagrams only

.github/workflows/
├── ci.yml               ✅
└── deploy.yml           ✅
```

### Implementation Notes

- OPERATIONS.md: includes index lag, ES yellow, Qdrant disk, OTEL runbook — see **Phase 3** verification.
- API.md: curl examples aligned with Pydantic models; `/ask` documents **502** without LLM key.
- TROUBLESHOOTING.md: track separately if needed.

---

## Testing Strategy

### Unit Tests (Phase 1-4)

- Chunker: Test AST vs token-window on Python/Go/JS
- Embeddings: Verify deterministic output for same input
- Retriever: Mock Qdrant/Elasticsearch, test ranking
- Agent: Test state transitions, tool invocation

### Integration Tests (Phase 5)

- End-to-end: Question → Search → Ranking → LLM → Answer
- K8s: Pod readiness, service discovery, HPA scaling
- Webhook: GitHub signature verification, reindex trigger

### Load Tests (Phase 6, optional)

- 100 QPS for 5 minutes (retriever)
- Indexing throughput: 1000 chunks/second
- HPA scaling time: <2 minutes to reach max replicas

---

## Success Metrics

| Phase | Metric | Target | Status |
|-------|--------|--------|--------|
| 0 | All files created | 100% | ✅ |
| 1 | Indexer fully working | 100% | ✅ (core paths + tests) |
| 2 | Retriever fully working | 100% | ✅ |
| 3 | Agent fully working | 100% | ✅ |
| 4 | Git Watcher fully working | 100% | ✅ |
| 5 | K8s manifests complete | 100% | ✅ (core workloads; no in-repo ServiceMonitor/Loki) |
| 6 | v1 docs + CI gates | 100% | ✅ (see **Current status** matrix) |

---

## Execution Checklist

Use the **[Current status (verified)](#current-status-verified)** table as the source of truth. Legacy items:

- [x] Phase 0: All files created
- [x] Phase 1: Indexer service implemented (`services/indexer/`, tests)
- [x] Phase 2: Retriever service implemented (`services/retriever/`, tests)
- [x] Phase 3: Agent service implemented (`services/qa_agent/`, tests)
- [x] Phase 4: Git Watcher service implemented (`services/git-watcher/`, Gradle tests)
- [x] Phase 5: Core K8s manifests and overlays (`k8s/`)
- [x] Phase 6: v1 documentation + CI (this matrix, `docs/API.md`, `docs/OPERATIONS.md`, `docs/RELEASE.md`, `.github/workflows/ci.yml`)
- [x] Docker build succeeds for all services (CI `build` job)
- [x] GitHub Actions CI contract (see workflow; local parity: `pytest`, `mypy`, `black`, flake8)
- [x] Local `docker compose up` path documented ([LOCAL-DEV.md](LOCAL-DEV.md), [PHASE1-RUNBOOK.md](PHASE1-RUNBOOK.md))

---

## Notes

- Start with `docker-compose up` for rapid local iteration
- After Phase 2, test full query flow locally
- Move to K8s (minikube) after Phase 4
- Use `kustomize build k8s/overlays/dev` to validate manifests
