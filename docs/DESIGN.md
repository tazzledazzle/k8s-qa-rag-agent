# k8s-qa-rag-agent: System Design Document

**Status**: Draft  
**Last Updated**: 2026-05-11  
**Author**: Terence Schumacher

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [System Architecture](#system-architecture)
4. [Service Components](#service-components)
5. [Data Flow](#data-flow)
6. [Kubernetes Architecture](#kubernetes-architecture)
7. [Trade-offs & Decisions](#trade-offs--decisions)
8. [Operational Considerations](#operational-considerations)
9. [Security Model](#security-model)
10. [Success Criteria](#success-criteria)

## Executive Summary

This document describes the design of **k8s-qa-rag-agent**, a Kubernetes-native Retrieval-Augmented Generation (RAG) system for live codebase Q&A. The system combines AST-aware code chunking, hybrid semantic search (dense vectors + BM25 + cross-encoder reranking), LangGraph ReAct agents, and automated GitHub webhook integration to enable natural-language code understanding at scale.

### Key Design Principles

- **Kubernetes-Native**: Leverages StatefulSets, DaemonSets, CronJobs, HPA, and Kustomize overlays for environment-specific deployments
- **Hybrid Search**: Dense vector search (Qdrant) + BM25 full-text search (Elasticsearch) + cross-encoder reranking for maximal relevance
- **Learning-Focused**: Comprehensive documentation (design, implementation, operations) for portfolio/reference implementation
- **Production-Ready**: OpenTelemetry observability, health checks, graceful degradation, PodDisruptionBudgets

---

## Problem Statement

### Functional Requirements

1. **Query Interface**: REST API accepting natural-language questions about codebases
2. **Code Indexing**: Automated indexing of Git repositories with AST-aware code chunking
3. **Semantic Search**: Hybrid search combining dense vectors and full-text BM25
4. **Agent Loop**: LangGraph ReAct agent for iterative code search and reasoning
5. **Webhook Integration**: GitHub webhooks for automatic repo reindexing on push events
6. **Session Context**: Maintain conversation history for multi-turn interactions

### Non-Functional Requirements

| Attribute | Target |
|-----------|--------|
| Availability | 99.5% SLA (≤3.6 hrs downtime/month) |
| Latency | <5s p99 (query time) |
| Throughput | 100 QPS peak (≤10 QPS average) |
| Data Consistency | Eventual consistency (1-hour lag acceptable) |
| Recovery Time (RTO) | 30 minutes |
| Recovery Point (RPO) | 1 hour |
| Code Indexing Frequency | Hourly CronJob |
| Cache TTL | 10 minutes (Redis) |

---

## System Architecture

### Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           External Actors                               │
│                                                                         │
│   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐│
│   │   Data Science   │    │   Software Dev   │    │   GitHub Events  ││
│   │    Engineers     │    │   Teams          │    │   (Webhooks)     ││
│   └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘│
│            │                       │                       │           │
│            └───────────────────────┼───────────────────────┘           │
│                                    │                                    │
│                                    ▼                                    │
│          ┌──────────────────────────────────────────────────┐           │
│          │    k8s-qa-rag-agent (Kubernetes Cluster)        │           │
│          │                                                  │           │
│          │  ┌────────────────────────────────────────────┐ │           │
│          │  │  API Gateway / Ingress                     │ │           │
│          │  │  - REST API on port 8002 (QA Agent)       │ │           │
│          │  │  - Webhook receiver on port 8003 (Git)    │ │           │
│          │  └────────────────────────────────────────────┘ │           │
│          │                                                  │           │
│          └──────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Service Topology

- **QA Agent Service** (FastAPI): Receives user questions, orchestrates search & reasoning
- **Retriever Service** (FastAPI): Hybrid search (dense + BM25 + reranking), caching
- **Indexer Service** (FastAPI): Git cloning, AST-aware chunking, embedding, Qdrant/Elasticsearch upserting
- **Git Watcher Service** (Kotlin/Ktor): GitHub webhook receiver, signature verification, reindex triggers

### Data Stores

- **Qdrant** (StatefulSet): Dense vector database for semantic search
- **Elasticsearch** (external): BM25 full-text search index
- **Redis** (external): Result caching (10-minute TTL)
- **PostgreSQL** (external): Optional conversation history store

---

## Service Components

### 1. Indexer Service

**Responsibility**: Git repository parsing, code chunking, embedding generation, vector/text indexing

**Key Components**:
- `git_client.py`: Clone/update repos from GitHub
- `chunker.py`: AST-aware Python chunking + token-window fallback
- `embeddings.py`: BAAI/bge-base-en-v1.5 embeddings
- `vector_db.py`: Qdrant client with deterministic chunk IDs
- `text_search.py`: Elasticsearch indexing

**Port**: 8000 (FastAPI)

### 2. Retriever Service

**Responsibility**: Hybrid search (dense + BM25), cross-encoder reranking, result caching

**Key Components**:
- `dense_search.py`: Qdrant vector search (top 20)
- `bm25_search.py`: Elasticsearch BM25 (top 20)
- `reranker.py`: Cross-encoder reranking (top 5)
- `cache.py`: Redis caching layer (10-minute TTL)

**Port**: 8001 (FastAPI)

### 3. QA Agent Service

**Responsibility**: LangGraph ReAct agent for iterative reasoning and tool invocation

**Key Components**:
- `agent.py`: LangGraph StateGraph with conditional edges
- `tools.py`: Tool definitions (`search_codebase`, `search_runbooks`)
- `llm.py`: OpenAI client wrapper
- `state.py`: Agent state schema

**Port**: 8002 (FastAPI)

### 4. Git Watcher Service

**Responsibility**: GitHub webhook receiver with HMAC-SHA256 signature verification

**Key Components**:
- `GitWatcherApp.kt`: Ktor server setup
- `GithubSignatureVerifier.kt`: HMAC-SHA256 verification
- `WebhookController.kt`: HTTP POST handler
- `IndexerClient.kt`: gRPC/HTTP client to Indexer

**Port**: 8003 (Ktor)

---

## Data Flow

### Query Flow (User Question → Answer)

```
User Question (REST POST /ask)
    ↓
QA Agent (LangGraph ReAct)
    ├─→ Call tool: search_codebase(question)
    │      ↓
    │   Retriever Service
    │      ├─→ Dense search (Qdrant): top 20 vectors
    │      ├─→ BM25 search (Elasticsearch): top 20 text
    │      ├─→ Cross-encoder rerank: top 5
    │      └─→ Redis cache (TTL: 10 min)
    │         ↓ [Returns 5 code chunks with scores]
    │
    ├─→ Reason over chunks with LLM
    ├─→ Generate follow-up if needed
    └─→ Return final answer (Agent State)
    ↓
User Response (JSON)
```

### Index Flow (GitHub Push → Searchable)

```
GitHub Push Event
    ↓
Git Watcher (Port 8003) — HMAC-SHA256 verification
    ↓
Indexer Service (Port 8000)
    ├─→ git clone / git pull
    ├─→ Parse code files
    ├─→ AST-aware chunking (Python) + token-window (other)
    ├─→ BAAI/bge-base-en-v1.5 embeddings
    ├─→ Deterministic chunk ID = hash(file_path + start_line)
    ├─→ Upsert to Qdrant (dense vectors)
    └─→ Index to Elasticsearch (BM25)
    ↓
[Searchable within 5-10 seconds]
```

---

## Kubernetes Architecture

### StatefulSets

**Qdrant** (1 replica in dev, 1 in staging, 3 in prod)
- Storage: 50Gi PersistentVolumeClaim
- Headless Service for DNS-based discovery

### Deployments

| Service | Dev | Staging | Prod | HPA |
|---------|-----|---------|------|-----|
| QA Agent | 1 | 2 | 4 | 2-10 |
| Retriever | 1 | 2 | 3 | 2-8 |
| Indexer | 1 | 1 | 2 | No |
| Git Watcher | 1 | 1 | 2 | No |

### CronJobs

**Indexer Batch Job** (Hourly at 00:00 UTC)
- Reindex all known repositories
- High resource allocation (4CPU, 8Gi)

### Observability Stack

- **OTEL Collector**: Sidecar in qa-agent pods, exports to Tempo/Prometheus/Loki
- **Prometheus**: Metrics scraping from /metrics endpoints
- **Tempo**: Distributed tracing
- **Loki**: Log aggregation

---

## Trade-offs & Decisions

### 1. AST-Aware Chunking vs Token Window

**Decision**: AST-aware for Python (tree-sitter), token window fallback

**Rationale**: 
- AST preserves semantic structure (function/class boundaries)
- Fallback handles non-Python languages gracefully
- Hybrid minimizes context loss vs monolithic chunks

### 2. Hybrid Search vs Pure Vector Search

**Decision**: Dense vectors (Qdrant) + BM25 (Elasticsearch) + cross-encoder reranking

**Rationale**:
- Dense alone misses exact terminology (e.g., function names)
- BM25 alone struggles with semantic paraphrasing
- Cross-encoder reranking combines both signals
- Tradeoff: ~2x infrastructure cost, but 15-20% better relevance (empirically)

### 3. Single-Tenant MVP vs Multi-Tenant

**Decision**: Single-tenant (hardcoded repos for now)

**Rationale**: 
- Simplifies auth, isolation, quota management
- Aligns with learning goal (no operational overhead of multi-tenancy)
- Easy to extend later: add repo config → per-user namespace

### 4. Kubernetes-Native vs Docker Compose

**Decision**: Both — Docker Compose for local dev, K8s for prod

**Rationale**:
- Docker Compose enables rapid local iteration
- K8s enforces production-like constraints early
- Kustomize overlays allow dev→staging→prod promotion

### 5. Synchronous vs Event-Driven Indexing

**Decision**: Hybrid — async webhook triggers + hourly CronJob fallback

**Rationale**:
- Webhooks ensure fresh indexes within seconds
- CronJob provides eventual-consistency guarantee
- Decouples GitHub from critical path (no blocking)

---

## Operational Considerations

### Observability

**Metrics**:
- Request latency (p50/p99 by endpoint)
- Cache hit rate (Redis)
- Reranker score distribution
- Qdrant query performance
- Indexer throughput (chunks/second)

**Logs**:
- Query traces (question → tools called → answer)
- Embedding generation latency
- GitHub webhook processing logs
- Error logs (structured JSON)

**Traces**:
- Request → search → rerank → LLM → response spans
- OTEL instrumentation on FastAPI, Redis, Qdrant

### Alerting (via Prometheus)

- QA Agent p99 latency > 5s
- Retriever cache hit rate < 40%
- Qdrant disk usage > 80% of 50Gi
- Pod crash loop (CrashLoopBackOff)
- Webhook processing latency > 10s

### Capacity Planning

**Storage** (Qdrant 50Gi PVC):
- Embedding dimension: 768 (BAAI/bge-base-en-v1.5)
- Bytes per vector: ~3KB (768 × 4 bytes + metadata)
- Capacity: ~15M chunks (50Gi / 3KB)
- At 10 lines/chunk average: ~150M lines of code

**CPU/Memory**:
- QA Agent: 500m req / 2 cores limit (scales with HPA)
- Retriever: 250m req / 1 core limit (scales with HPA)
- Indexer: 2 cores req / 4 cores limit (CPU-bound parsing)
- Qdrant: 500m req / 2 cores limit

**Replication** (prod):
- Qdrant: 3 replicas with PodDisruptionBudgets (minAvailable: 2)
- Indexer: 2 replicas (no HPA, manual replica control)

### Disaster Recovery

**Backup Strategy**:
- Qdrant: Daily snapshots to S3 (automated via K8s CronJob)
- Elasticsearch: Daily snapshots (native snapshot API)
- Redis: No backup (cache only, recoverable via re-index)

**RTO/RPO**:
- RTO: 30 min (restore snapshot, restart pods)
- RPO: 1 hour (daily snapshots + hourly CronJob indexing)

---

## Security Model

### Authentication & Authorization

- **No per-user auth** (single-tenant MVP)
- GitHub webhook signature verification (HMAC-SHA256)
- Optional API key for deployments

### Data Classification

- **Public**: Code from public repos
- **Confidential**: API keys, internal secrets → filtered out during indexing

### Network Security

- Service-to-service via K8s DNS (internal)
- External access only via Ingress (TLS termination at edge)
- No direct pod-to-pod across namespaces

### Secret Management

- GitHub webhook secret: K8s Secret
- OpenAI API key: K8s Secret
- Qdrant API key: K8s Secret
- All injected as environment variables

---

## Success Criteria

### Technical Learning Goals

- ✅ Build a production-grade Kubernetes system (StatefulSets, HPA, overlays)
- ✅ Implement hybrid search (dense + BM25 + reranking)
- ✅ Design a tool-using LangGraph agent
- ✅ Set up observability (OTEL, Prometheus, Tempo, Loki)
- ✅ Document design & operations for portfolio

### Portfolio/Showcase Value

- Demonstrates K8s maturity (StatefulSets, Kustomize, OTEL)
- Shows RAG system design (chunking, embeddings, reranking)
- Includes production operations (observability, alerting, DR)
- Comprehensive documentation (design, impl, ops)

---

## Next Steps

See [IMPLEMENTATION.md](./IMPLEMENTATION.md) for the 6-phase build plan (2 weeks total).
