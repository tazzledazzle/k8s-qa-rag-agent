# Local development (Phase 1)

Bring up the full stack on **Docker Compose** and verify health. Kubernetes users can apply `k8s/overlays/dev` separately; this doc focuses on compose.

## Prerequisites

- Docker with Compose v2 (`docker compose`)
- Optional: `OPENAI_API_KEY` in the environment (or `.env`) for QA `/ask` — not required for health-only smoke

## One-time: fixture git repo

The indexer accepts **`file:///absolute/path`** only for **git** directories (with `.git`). Initialize the bundled fixture:

```bash
bash tests/fixtures/sample-repo/bootstrap.sh
```

## Start services

From the repository root (`k8s-qa-rag-agent/`):

```bash
docker compose up -d
```

**Ports (host):**

| Service       | Port | Health URL                    |
|---------------|------|-------------------------------|
| indexer       | 8000 | http://127.0.0.1:8000/health  |
| retriever     | 8001 | http://127.0.0.1:8001/health  |
| qa-agent      | 8002 | http://127.0.0.1:8002/health  |
| git-watcher   | 8003 | http://127.0.0.1:8003/health  |

Compose service names use hyphens (`qa-agent`); Python import paths use underscores (`services.qa_agent`).

## Smoke check

After containers are up (Elasticsearch may take ~1–2 minutes on first boot):

```bash
bash scripts/smoke_compose.sh
```

The script waits for Qdrant, Elasticsearch, Redis (via `docker compose exec`), then checks all four application `/health` endpoints.

## Next

For **index → ask → citation** proof steps, see [PHASE1-RUNBOOK.md](PHASE1-RUNBOOK.md).
