# Troubleshooting

## Python import errors (`ModuleNotFoundError: services.qa_agent`)

The QA service package directory must be **`services/qa_agent`** (underscore), matching `uvicorn services.qa_agent.main:app`. Install from the repo root:

```bash
cd k8s-qa-rag-agent
pip install -e .
```

Ensure `services/__init__.py` and `services/qa_agent/__init__.py` exist.

## Qdrant / Elasticsearch connection refused

- **Docker:** Confirm `docker compose ps` shows healthy Qdrant and Elasticsearch.
- **URLs:** Indexer and Retriever use `QDRANT_HOST`/`QDRANT_PORT` or `QDRANT_URL`, and `ELASTICSEARCH_URL` (e.g. `http://elasticsearch:9200` inside Compose).

## Redis errors

Retriever caches search results. If Redis is down, cache helpers log a warning; searches still run but are not cached.

## First request slow (models)

Indexer, Retriever, and QA Agent download **sentence-transformers** / **cross-encoder** weights on first use. Allow time and disk; use persistent volumes in Kubernetes.

## Cross-encoder model name

Default reranker id is `cross-encoder/mmarco-MiniLMv2-L12-H384-v1`. If download fails, the service falls back to `cross-encoder/ms-marco-MiniLM-L-12-v2`. Override with `RERANKER_MODEL`.

## GitHub webhook 401

- Secret must match `GITHUB_WEBHOOK_SECRET`.
- Signature header must be `X-Hub-Signature-256` with form `sha256=<hex>`.
- Body must be the raw payload GitHub signed (UTF-8 JSON for normal deliveries).

## Gradle / Docker build for Git Watcher

Build uses the **Shadow** plugin to produce `app.jar`. From `services/git-watcher`:

```bash
gradle shadowJar -x test
```

Docker build context must be the **repository root** (see `.github/workflows/ci.yml`).

## Elasticsearch healthcheck in Compose

The first start can take longer than the healthcheck `start_period`. Increase `start_period` if Elasticsearch is marked unhealthy on slow machines.
