# Architecture Research

**Domain:** audio-first music recommendation (track-to-track retrieval)
**Researched:** 2026-03-19
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Online Query Layer                              │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌─────────────────┐   ┌──────────────────────────┐  │
│  │ Input API    │→→ │ Query Processor │→→ │ ANN Retrieval Service    │  │
│  │ (file/url/id)│   │ (decode+embed)  │   │ (top-K candidate search) │  │
│  └──────────────┘   └─────────────────┘   └──────────────┬───────────┘  │
│                                                           │              │
│                          ┌──────────────────────────┐     │              │
│                          │ Re-ranker / Post-filter  │←←←←┘              │
│                          │ (diversity, quality)     │                    │
│                          └──────────────┬───────────┘                    │
│                                         ↓                                │
│                                 Top-20 Response API                      │
├──────────────────────────────────────────────────────────────────────────┤
│                         Offline Indexing Layer                           │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌─────────────────┐   ┌──────────────────────────┐  │
│  │ Catalog      │→→ │ Batch Embedding │→→ │ Vector Index Builder     │  │
│  │ Ingestion    │   │ Pipeline        │   │ (HNSW/IVF/PQ)            │  │
│  └──────────────┘   └─────────────────┘   └──────────────┬───────────┘  │
│                                                           │              │
│                     ┌─────────────────────────────────────┴───────────┐  │
│                     │ Vector Store + Metadata Store + Artifact Store  │  │
│                     └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Input API | Accept file upload, URL fetch, or internal track ID; enforce limits and auth | FastAPI/Node API gateway with async jobs for large files |
| Audio normalization service | Decode, resample, loudness normalize, trim silence, standardize duration windows | `ffmpeg` + `torchaudio` transforms |
| Embedding service | Produce fixed-length track embeddings from pretrained audio models | PyTorch inference worker using MERT/CLAP-style encoders |
| Vector index service | Store and query nearest neighbors at low latency | FAISS (embedded) or dedicated vector DB (Qdrant/Milvus) |
| Candidate re-ranker | Re-score top-N by business rules and robustness heuristics | Lightweight ranking stage with feature fusion |
| Offline indexing pipeline | Bulk ingest catalog and periodically rebuild or incrementally update index | Batch jobs (Python workers + queue/scheduler) |
| Metadata/lineage store | Track track IDs, model version, embedding version, index version | Postgres + object storage for artifacts |
| Evaluation/monitoring | Track recall@K, latency, drift, and failures | Offline eval suite + runtime metrics/alerts |

## Recommended Project Structure

```
src/
├── api/                     # HTTP endpoints, request validation, auth
│   ├── routes/              # /recommend, /index, /health
│   └── schemas/             # input/output DTOs
├── audio/                   # deterministic audio preprocessing
│   ├── decode/              # URL/file/ID resolution + decode
│   └── transforms/          # resample, normalization, chunking
├── embedding/               # model wrappers and inference orchestration
│   ├── models/              # pretrained model adapters (MERT, CLAP)
│   └── pooling/             # frame->track pooling strategies
├── retrieval/               # vector index abstraction + ANN query
│   ├── index/               # FAISS/Qdrant/Milvus client adapters
│   └── rerank/              # post-retrieval scoring + filters
├── indexing/                # offline ingest and index build/update jobs
│   ├── pipelines/           # batch workflows
│   └── versioning/          # embedding/index artifact lineage
├── eval/                    # offline metrics, golden sets, regression checks
└── infra/                   # config, queues, observability wiring
```

### Structure Rationale

- **`audio/` and `embedding/` split:** keeps signal processing deterministic and model logic replaceable.
- **`retrieval/` as boundary:** allows swapping FAISS local index to managed vector DB without API changes.
- **`indexing/` separate from online path:** protects query latency from bulk indexing workload.
- **`eval/` first-class:** retrieval quality degrades silently without continuous offline checks.

## Architectural Patterns

### Pattern 1: Two-Stage Retrieval (ANN then Re-rank)

**What:** Use ANN to retrieve fast top-N candidates, then re-rank with additional signals.
**When to use:** Always for top-20 similarity at production latency.
**Trade-offs:** Slightly more system complexity; significantly better quality/latency balance.

**Example:**
```typescript
const q = embedTrack(inputAudio);
const candidates = annIndex.search(q, 200); // fast recall-oriented
const scored = rerank(candidates, {tempoPenalty, artistDiversity, vocalProfile});
return scored.slice(0, 20);
```

### Pattern 2: Versioned Embedding and Index Artifacts

**What:** Treat model weights, preprocessing config, embeddings, and index as immutable versioned artifacts.
**When to use:** From day one to avoid untraceable retrieval regressions.
**Trade-offs:** More storage and release process overhead; dramatically easier rollback/debugging.

**Example:**
```typescript
const embeddingVersion = "mert-v1-330m_pool-v2";
const indexVersion = `hnsw_cosine_${embeddingVersion}_2026-03-19`;
writeEmbedding(trackId, vector, embeddingVersion);
publishActiveIndex(indexVersion);
```

### Pattern 3: Asynchronous Multi-Source Input Resolution

**What:** Normalize file upload, URL, and track ID inputs into one canonical audio blob before inference.
**When to use:** Required for mixed input types and stable quality.
**Trade-offs:** More queue/orchestration logic; prevents online timeout and duplicate processing code.

## Data Flow

### Request Flow (Online)

```
Client input (file | URL | internal ID)
    ↓
Input API validates request + resolves source
    ↓
Audio normalization (decode -> resample -> normalize)
    ↓
Embedding service (pretrained model + pooling -> track vector)
    ↓
ANN retrieval (top-200)
    ↓
Re-ranker and safety filters
    ↓
Top-20 similar tracks response (with scores + trace IDs)
```

### Indexing Flow (Offline)

```
Catalog ingest
    ↓
Batch audio preprocessing
    ↓
Batch embedding extraction
    ↓
Index build/update (HNSW/IVF/PQ)
    ↓
Validation (recall@K + latency checks)
    ↓
Atomic index publish + rollback pointer retained
```

### Key Data Flows

1. **Query-time retrieval:** strict p95 latency path; no heavy computation beyond one embedding pass.
2. **Index refresh:** throughput path; optimized for cost and reproducibility, not latency.
3. **Evaluation loop:** compare candidate quality across embedding/index versions before promotion.

## Suggested Build Order (Roadmap Implications)

1. **Canonical audio pipeline + single embedding model wrapper**
   - Establish deterministic preprocessing and one stable embedding baseline.
2. **Offline indexing and ANN retrieval baseline**
   - Build end-to-end top-20 from internal track ID first; file/URL later.
3. **Unified online query path for all input types**
   - Add source resolution and async handling for file upload and URL ingestion.
4. **Re-ranking + business constraints**
   - Add diversity and quality heuristics only after retrieval baseline metrics exist.
5. **Artifact versioning + evaluation gates**
   - Require offline regression checks before index/model promotions.
6. **Scale and cost tuning**
   - Introduce quantization, sharding, GPU inference pools, and caching based on observed bottlenecks.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k users | Single service + FAISS index on one node; nightly rebuilds are fine |
| 1k-100k users | Split online query and offline indexing workers; move to managed/vector DB; add async URL ingestion queue |
| 100k+ users | Sharded vector index, GPU inference pool autoscaling, multi-region read replicas, strict canary rollout for index versions |

### Scaling Priorities

1. **First bottleneck: embedding inference latency** — mitigate with batching, model quantization, and warm worker pools.
2. **Second bottleneck: ANN memory/recall trade-off** — tune HNSW/IVF params and introduce product quantization when catalog grows.

## Anti-Patterns

### Anti-Pattern 1: Mixing Online Query and Bulk Re-indexing in One Worker Pool

**What people do:** share compute between user queries and full-catalog embedding/index jobs.
**Why it's wrong:** query latency spikes and SLO instability during reindex windows.
**Do this instead:** isolate online inference/retrieval workers from offline indexing workers.

### Anti-Pattern 2: Treating Embeddings as Stable Without Versioning

**What people do:** overwrite vectors in place after model/preprocessing changes.
**Why it's wrong:** impossible to explain quality regressions or roll back safely.
**Do this instead:** immutable embedding/index versions with explicit active pointer.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Object storage (audio/artifacts) | Signed URL read/write + immutable artifact paths | Keep original and normalized audio for reproducibility |
| Vector engine (FAISS/Qdrant/Milvus) | Adapter interface (`search`, `upsert`, `publish`) | Avoid engine-specific logic leaking into API layer |
| Message queue/scheduler | Async indexing and URL ingestion jobs | Essential once URL/file ingestion volume increases |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `api` ↔ `audio` | synchronous function/API call | Keep normalization deterministic and side-effect free |
| `embedding` ↔ `retrieval` | typed vector contract | Contract should include embedding/model version |
| `indexing` ↔ `retrieval` | artifact publish event | Use atomic pointer switch to activate new index |

## Sources

- [FAISS GitHub (official)](https://github.com/facebookresearch/faiss) — efficient dense vector similarity search (MEDIUM confidence via official repo page).
- [Qdrant Documentation](https://qdrant.tech/documentation/) — vector search and distributed scaling guidance (MEDIUM confidence via official docs).
- [Milvus audio similarity docs/search references](https://milvus.io/docs/v2.5.x/audio_similarity_search.md) and [Milvus repository](https://github.com/milvus-io/milvus) (MEDIUM confidence; one docs fetch timed out, recommendation cross-checked with official repo and ecosystem usage).
- [MERT model card](https://huggingface.co/m-a-p/MERT-v1-330M) — pretrained music representations and operational model details (MEDIUM confidence; official model card).
- [LAION CLAP repository](https://github.com/LAION-AI/CLAP) — open audio-text embedding model commonly used for audio embeddings (MEDIUM confidence).
- [Essentia documentation](https://essentia.upf.edu/documentation.html) — MIR-focused audio descriptor extraction toolkit (MEDIUM confidence).
- [Torchaudio feature extraction docs](https://pytorch.org/audio/stable/tutorials/audio_feature_extractions_tutorial.html) — canonical preprocessing and spectral feature ops (HIGH confidence, official docs).

---
*Architecture research for: music recommendation track-to-track retrieval*
*Researched: 2026-03-19*
