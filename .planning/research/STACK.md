# Research — Stack (k8s-qa-rag-agent)

**Researched:** 2026-05-12  
**Confidence:** HIGH (aligned with implemented repo + DESIGN.md)

## Recommended stack

| Layer | Choice | Role | Notes |
|-------|--------|------|-------|
| Agent orchestration | LangGraph + LangChain | ReAct loop, tool routing | Matches `services/qa_agent/` |
| HTTP | FastAPI (Python 3.11+) | Indexer, retriever, QA APIs | Async-friendly, OpenAPI |
| Vectors | Qdrant | Dense retrieval, StatefulSet-friendly | Version pin in k8s manifests |
| Lexical | Elasticsearch 8.x | BM25 on code/prose | docker-compose + cluster |
| Cache | Redis 7 | Deduped retrieval TTL | `services/retriever/cache.py` |
| Embeddings | `BAAI/bge-base-en-v1.5` | Local CPU/GPU embedding | SentenceTransformers |
| Rerank | Cross-encoder (e.g. MS MARCO family) | Final ordering | Trade latency for precision |
| Edge ingress | K8s Service + future Ingress class | Internal cluster first | Kong/Envoy optional later |
| Webhook service | Kotlin + Ktor + Netty | GitHub signature verify | `services/git-watcher/` |
| Observability | OpenTelemetry collector sidecar / ConfigMap | Traces/metrics/logs | `k8s/base/configmap-otel.yaml` |

## What NOT to use (for this scope)

- **Managed-only vector DB** as hard dependency — conflicts with “runs on k8s” story unless explicitly hybrid.
- **Single sparse-only or single dense-only** retrieval — underserves code Q&A quality goals.

## Version hygiene

Pin Qdrant, ES, and OTEL collector images in prod overlays; verify against upstream release notes before upgrades.
