# Operations

This document summarizes how to run and operate **k8s-qa-rag-agent** in development and Kubernetes. See also [DESIGN.md](DESIGN.md) for architecture and SLO tables.

## Dependencies

| Dependency | Used by | Notes |
|------------|---------|--------|
| Qdrant | Indexer, Retriever | Default collection `code_chunks`, cosine vectors |
| Elasticsearch | Indexer, Retriever | Default index `code_chunks` |
| Redis | Retriever | Search cache, TTL 10 minutes |
| OpenAI API | QA Agent | Model from `OPENAI_MODEL` (default `gpt-4o-mini`) |

## Environment variables

| Variable | Service | Purpose |
|----------|---------|---------|
| `QDRANT_HOST`, `QDRANT_PORT` or `QDRANT_URL` | Indexer, Retriever | Vector store |
| `QDRANT_COLLECTION` | Indexer, Retriever | Collection name (default `code_chunks`) |
| `ELASTICSEARCH_URL` | Indexer, Retriever | ES HTTP URL |
| `ES_INDEX` | Indexer, Retriever | Index name (default `code_chunks`) |
| `REDIS_HOST`, `REDIS_PORT` | Retriever | Cache |
| `GITHUB_TOKEN` | Indexer | Private GitHub clone HTTPS |
| `INDEXER_REPO_CACHE` | Indexer | Clone cache directory (default `/app/repos`) |
| `RETRIEVER_HOST`, `RETRIEVER_PORT` | QA Agent | Retriever base URL |
| `OPENAI_API_KEY` | QA Agent | Required for `/ask` |
| `GITHUB_WEBHOOK_SECRET` | Git Watcher | HMAC key for `X-Hub-Signature-256` |
| `INDEXER_HOST`, `INDEXER_PORT` | Git Watcher | Target for `POST /index` |

### Correlation IDs (OBS-01)

Every HTTP request receives a **`correlation_id`**: taken from the **`X-Correlation-ID`** header when present, otherwise a new UUID. It is attached to structured JSON logs and propagated on outbound retriever calls from the QA agent. Use the same header when tracing a request across services.

### OpenTelemetry (OBS-02)

Export is **off** unless **`OTEL_EXPORTER_OTLP_ENDPOINT`** is set (unit tests clear it). The QA agent and retriever use **gRPC OTLP** to that endpoint when set.

| Variable | Meaning | Docker Compose | Kubernetes (qa-agent pod) |
|----------|---------|------------------|---------------------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP gRPC target for traces | Not set by default in `docker-compose.yml`; set manually if you run a local collector (e.g. `http://127.0.0.1:4317`) | **`http://127.0.0.1:4317`** — same pod network as the **`otel-collector-sidecar`** listening on **4317** |
| `OTEL_SERVICE_NAME` | `service.name` on spans | Optional override | **`qa-agent`** on the QA deployment (set in `k8s/base/qa-agent-deployment.yaml`) |
| `OTEL_RESOURCE_ATTRIBUTES` | Extra resource key/values | Optional | Optional (not set in base) |

**Ports:** **4317** = OTLP **gRPC**; **4318** = OTLP **HTTP** (receiver enabled in `k8s/base/configmap-otel.yaml` for future HTTP exporters). Python export in this repo uses **gRPC** on **4317**.

**Config sources:** In-cluster collector YAML lives in **`k8s/base/configmap-otel.yaml`** (key **`otel-collector-config.yaml`**). A mirror for CI and local validation is **`scripts/otel/otel-collector-config.yaml`** — keep them in sync. Validate locally (requires Docker):

```bash
bash scripts/validate-otel-config.sh
```

**Dry-run (cluster):** After deploy, confirm the sidecar received spans (the **`logging`** exporter prints trace/span summaries to the collector container log):

```bash
kubectl -n rag-system port-forward deploy/qa-agent-deployment 8002:8002
curl -sS http://127.0.0.1:8002/health >/dev/null
kubectl -n rag-system logs deploy/qa-agent-deployment -c otel-collector-sidecar --tail=200
```

Look for **TraceId** / span lines from the **`logging`** exporter. Spans include a **`correlation_id`** attribute when the request carried or generated one.

## Local development

From the project root (`k8s-qa-rag-agent`):

```bash
python -m pip install -e ".[dev]"
docker compose up --build
```

Bring up Qdrant, Elasticsearch, Redis, and all services. Index a repo with `POST /index` (see [API.md](API.md)).

## Index rebuild

1. Optionally delete Qdrant collection and Elasticsearch index (or use new `QDRANT_COLLECTION` / `ES_INDEX`).
2. Re-run `POST /index` for each repository and branch.

## Retriever degradation

If dense (Qdrant) or BM25 (Elasticsearch) fails, the retriever logs a warning and continues with the branch that succeeded. If both fail, `/search` returns an empty chunk list after reranking.

## Index lag

**Symptoms:** Answers cite old files or missing recent commits; stakeholders report “stale” knowledge.

**Checks:**

1. **Indexer CronJob / manual runs** — `kubectl -n rag-system get cronjobs,jobs` and recent job logs for the indexer.
2. **Git watcher** — logs for signature failures (see [SECURITY-SECRETS.md](SECURITY-SECRETS.md)) or skipped pushes.
3. **Manual re-index** — `POST /index` per [API.md](API.md) for the affected repo/branch.

```bash
kubectl -n rag-system logs deployment/indexer-deployment --tail=200
kubectl -n rag-system logs deployment/git-watcher-deployment --tail=200
```

## Elasticsearch cluster yellow

**Typical causes (single-node dev/staging):** unassigned replicas (expected on one node), disk watermark, or pending allocation.

**Checks:**

```bash
curl -sS "http://<elasticsearch-host>:9200/_cluster/health?pretty"
```

If **status** is **yellow** on a **single-node** cluster, it is often due to replica shards; for production, follow your ES ops guide (add nodes or set `number_of_replicas` appropriately). If **red**, check disk watermarks and shard allocation:

```bash
curl -sS "http://<elasticsearch-host>:9200/_cat/allocation?v"
```

## Qdrant disk pressure and collection growth

**Symptoms:** Qdrant pod evictions, `No space left on device`, or slow vector search.

**Checks:** PVC usage (`kubectl describe pvc` in the app namespace), Qdrant logs, collection size in Qdrant API/dashboard.

**Mitigation:** Grow the volume if supported; delete and re-index a collection only after confirming backups and indexer can rebuild (see **Index rebuild** above). Prefer **re-index** over manual partial deletes unless you understand chunk IDs.

## Alerts (suggested)

- QA Agent 5xx rate elevated
- Retriever cache miss ratio with high ES/Qdrant latency
- Indexer job duration or failure count
- Git watcher signature failure rate (possible misconfiguration or attack)

Webhook secret misconfiguration and safe handling of credentials are covered in **[SECURITY-SECRETS.md](SECURITY-SECRETS.md)**.

## Runbook checklist (**Validated** updated in `/gsd-verify-phase 3`)

| Failure mode | Detection | Mitigation | Validated |
|--------------|-----------|------------|-----------|
| Index lag / stale answers | User reports; diff vs `main` | Fix watcher/indexer; `POST /index` | 2026-05-15 — procedure + manifest review (no live drill) |
| Elasticsearch yellow/red | `_cluster/health`, logs | Replicas / disk / allocation | 2026-05-15 — procedure + manifest review (no live drill) |
| Qdrant disk pressure | PVC full; slow `/search` | Expand volume; re-index | 2026-05-15 — procedure + manifest review (no live drill) |
| OTEL sidecar misconfig | No spans in collector logs | `kubectl logs … otel-collector-sidecar`; fix ConfigMap; `bash scripts/validate-otel-config.sh` | 2026-05-15 — `kubectl kustomize` base + dev/staging/prod OK; CI **`otel-config`** runs `validate` on mirror; **local Docker validate not run** (engine paused) |
| Retriever partial failure | Warnings in retriever JSON logs | Fix ES or Qdrant branch; see **Retriever degradation** | 2026-05-15 — pytest + code/doc review |

*Live cluster execution of kubectl log inspection and `scripts/validate-otel-config.sh` on this host is documented in **`.planning/phases/03-observability-operations/03-VERIFICATION.md`** (gaps). Re-run those when Docker and a cluster are available.*

## Disaster recovery

- **RTO / RPO:** Targets are defined in [DESIGN.md](DESIGN.md).
- Re-index from Git after restoring vector/text stores; embeddings are deterministic for the same model and chunk boundaries.
