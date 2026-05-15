# k8s-qa-rag-agent

Kubernetes-oriented RAG stack for **codebase Q&A**: index a Git repo into **Qdrant** (dense vectors) and **Elasticsearch** (BM25), retrieve with hybrid search + reranking, and answer questions via a **LangGraph** ReAct agent (**OpenAI**). A **Kotlin** GitHub webhook service triggers re-indexing on `push`.

Long-form design and requirements live under [docs/DESIGN.md](docs/DESIGN.md) and [.planning/](.planning/).

**Phase 1 proof:** [docs/LOCAL-DEV.md](docs/LOCAL-DEV.md) (compose + smoke), [docs/PHASE1-RUNBOOK.md](docs/PHASE1-RUNBOOK.md) (fixture `file://` index + `/ask` + citations).

---

## Quick start (local)

Prerequisites: **Docker** with Compose, an **OpenAI API key**, and enough RAM for embedding models (see service Dockerfiles).

1. Copy the environment template and set secrets:

   ```bash
   cp .env.example .env
   # Set OPENAI_API_KEY (and optionally QDRANT_API_KEY, GITHUB_WEBHOOK_SECRET)
   ```

2. Start the stack:

   ```bash
   docker compose up --build
   ```

3. Index a public repo, then query (see [docs/API.md](docs/API.md) for full request bodies):

   ```bash
   curl -s -X POST http://localhost:8000/index \
     -H "Content-Type: application/json" \
     -d '{"repo_url":"https://github.com/octocat/Hello-World","branch":"master"}'

   curl -s -X POST http://localhost:8001/search \
     -H "Content-Type: application/json" \
     -d '{"query":"README","language":null}'

   curl -s -X POST http://localhost:8002/ask \
     -H "Content-Type: application/json" \
     -d '{"question":"What does this repository do?"}'
   ```

Default ports: **8000** indexer, **8001** retriever, **8002** qa-agent, **8003** git-watcher, **6333** Qdrant, **9200** Elasticsearch, **6379** Redis.

---

## Repository layout

```
k8s-qa-rag-agent/
├── docker-compose.yml          # Local stack (authoritative for dev wiring)
├── .env.example
├── pyproject.toml
├── services/
│   ├── indexer/                # FastAPI: POST /index, GET /health
│   ├── retriever/              # FastAPI: POST /search, GET /health
│   ├── qa_agent/               # FastAPI: POST /ask, GET /health (OpenAI + tools)
│   └── git-watcher/            # Ktor: POST /webhook, GET /health → calls indexer /index
├── k8s/
│   ├── base/                   # Kustomize base (namespace rag-system)
│   └── overlays/               # dev, staging, prod
└── docs/                       # API, operations, design
```

There is **no** Helm chart or Terraform tree in this repository; add them in your own platform layer if needed.

---

## HTTP API (summary)

| Service       | Port (compose) | Method | Path        | Notes                                      |
|---------------|----------------|--------|-------------|--------------------------------------------|
| Indexer       | 8000           | POST   | `/index`    | Body: `repo_url`, `branch`, optional globs |
| Retriever     | 8001           | POST   | `/search`   | Body: `query`, optional `language`         |
| QA agent      | 8002           | POST   | `/ask`      | Body: `question`, optional `session_id`    |
| Git watcher   | 8003           | POST   | `/webhook`  | GitHub `push`; `X-Hub-Signature-256`       |

Interactive OpenAPI: `http://localhost:8000/docs` (and equivalent ports for other Python services).

Runbook-style detail: [docs/API.md](docs/API.md), [docs/OPERATIONS.md](docs/OPERATIONS.md).

---

## Configuration

- **Images & prod tagging:** [docs/RELEASE.md](docs/RELEASE.md) — CI build matrix, prod Kustomize pins, `kustomize edit set image` examples.
- **Secrets inventory:** [docs/SECURITY-SECRETS.md](docs/SECURITY-SECRETS.md) — env vars, compose vs Kubernetes, allowlist parity.
- **Compose**: service discovery uses Docker Compose **service names** (`qdrant`, `elasticsearch`, `redis`, `indexer`, `retriever`, …). See [docker-compose.yml](docker-compose.yml).
- **Kubernetes**: base manifests use cluster DNS names such as `qdrant-service`, `elasticsearch`, `redis`, `retriever-service`, **`qa-agent-service`**, **`indexer-service`** (for the git-watcher → indexer hop). Set `OPENAI_API_KEY` via the `llm-secrets` secret expected by [k8s/base/qa-agent-deployment.yaml](k8s/base/qa-agent-deployment.yaml).

Indexer and retriever read **`ELASTICSEARCH_URL`** (default in code: `http://localhost:9200`). In-cluster base sets `http://elasticsearch:9200`.

**Scheduled indexing (CronJob)** runs `python -m services.indexer.batch_index`. Repository URL and branch come from the **`indexer-batch-config`** ConfigMap (`INDEX_REPO_URL`, `INDEX_BRANCH`); override in an overlay or patch before relying on it in production.

---

## Kubernetes (Kustomize)

- **Namespace**: `rag-system` (see [k8s/base/namespace.yaml](k8s/base/namespace.yaml)).
- **Base resources** include: Qdrant StatefulSet + Service, **Elasticsearch** Deployment + Service, **Redis** Deployment + Service, indexer Deployment + **Service (`indexer-service`)** + PVC, retriever + QA agent + git-watcher Deployments (with Services where applicable), OpenTelemetry ConfigMap, indexer **CronJob**, and the batch ConfigMap above.

Build manifests:

```bash
kubectl kustomize k8s/base
kubectl kustomize k8s/overlays/prod
```

Overlays live under [k8s/overlays/](k8s/overlays/) (`dev`, `staging`, `prod`). Prod uses `namePrefix: prod-` and HPAs/PDBs as defined in those files—not the illustrative snippets from older revisions of this README.

**Elasticsearch in Kubernetes** uses an `emptyDir` volume in the base manifest for simplicity; indexes are lost if the pod is rescheduled. For durable clusters, replace it with a PVC or a managed search service and patch `ELASTICSEARCH_URL` accordingly.

**Node/kernel note:** Elasticsearch may require `vm.max_map_count` on worker nodes (see Elastic’s documentation). If pods crash-loop with memory-map errors, raise that sysctl or use a managed Elasticsearch.

---

## Architecture (implemented)

- **Chunking**: Tree-sitter–aware chunking in `services/indexer/chunker.py` (not the legacy AST pseudocode from early drafts).
- **Embeddings**: `sentence-transformers` in `services/indexer/embeddings.py`.
- **Retriever**: Hybrid dense + BM25, dedupe, cross-encoder rerank, Redis cache (TTL 600s)—see `services/retriever/`.
- **QA agent**: LangGraph `create_react_agent` with tools calling the retriever over HTTP—see `services/qa_agent/` (**OpenAI**, not Anthropic).
- **Runbooks**: There is no separate “runbook-agent” deployment; runbook-style content is retrieved via the same index and tool paths as code where applicable.

---

## Trade-offs (engineering targets)

| Area            | Choice in this repo / design docs     | Rationale (short)                          |
|-----------------|----------------------------------------|--------------------------------------------|
| Vector store    | Qdrant                                 | Simple StatefulSet operation               |
| BM25            | Elasticsearch                          | Familiar stack, good full-text           |
| Reranking       | Local cross-encoder                    | Avoids extra SaaS dependency             |
| Agent framework | LangGraph ReAct                        | Tool loop + observability hooks            |
| LLM             | OpenAI (`langchain-openai`)            | Matches `pyproject.toml` + QA deployment   |

Latency and capacity numbers in [docs/DESIGN.md](docs/DESIGN.md) are **targets**, not guarantees from this repo alone.

---

## Agent / contributor notes

GSD workflow and artifact pointers: [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md).

---

## License / status

Portfolio / reference implementation. Verify behaviour in your environment before production use.
