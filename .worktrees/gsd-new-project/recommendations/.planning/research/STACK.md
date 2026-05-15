# Stack Research

**Domain:** audio-first music recommendation discovery engine (track-to-track retrieval)
**Researched:** 2026-03-19
**Confidence:** MEDIUM-HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11 or 3.12 | Core language for feature extraction, model inference, indexing, and API | Best compatibility across PyTorch/audio ecosystem while keeping modern performance and typing support. |
| PyTorch + torchaudio | `torch==2.10.0` | Embedding inference and audio model runtime | Current stable from official channels; broadest support for open audio checkpoints and GPU acceleration. |
| Qdrant + qdrant-client | Qdrant server `1.14+` (recommended), `qdrant-client==1.17.1` | Production ANN vector retrieval | Strong default for high-recall HNSW + payload filtering with straightforward ops and excellent Python SDK ergonomics. |
| FastAPI + Uvicorn | `fastapi==0.135.1`, `uvicorn==0.42.0` | Retrieval API service layer | Standard Python ML-serving stack with high throughput, async I/O, and low integration friction. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `transformers` | `5.3.0` | Loading pretrained open-source audio/music checkpoints | Use for model-card-driven loading of MERT/CLAP-family checkpoints and consistent preprocessing APIs. |
| `librosa` | `0.11.0` | Audio loading/feature utilities and analysis helpers | Use for feature QA, diagnostics, and fallback DSP utilities (not as primary high-throughput inference runtime). |
| `faiss-cpu` (or custom Faiss GPU build) | `1.13.2` | Offline evaluation, candidate mining, large-batch ANN experiments | Use in offline pipelines to benchmark recall@K and to tune ANN settings before pushing to online Qdrant collections. |
| FFmpeg | latest stable package for your OS | Robust decode/transcode from uploads/URLs | Use as canonical ingest decoder to normalize sample rate, channels, and codec edge cases before embedding extraction. |
| Essentia | `2.1-beta6-dev` docs branch | MIR descriptors and production-hardened music DSP primitives | Use when adding handcrafted MIR features for reranking or explainability; optional for V1 pure embedding retrieval. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Docker + Compose | Reproducible local stack (API + vector DB + workers) | Keep inference and retrieval services in separate containers for independent scaling. |
| `pytest` + `pytest-benchmark` | Correctness and latency/throughput regressions | Track `recall@20`, p95 latency, and ingestion throughput as release gates. |
| Prometheus + Grafana | Runtime visibility for retrieval quality and system health | Instrument embedding extraction latency, ANN latency, and cache hit/miss per endpoint. |

## Installation

```bash
# Core
pip install torch==2.10.0 torchaudio qdrant-client==1.17.1 fastapi==0.135.1 uvicorn==0.42.0

# Supporting
pip install transformers==5.3.0 librosa==0.11.0 faiss-cpu==1.13.2

# Dev dependencies
pip install -D pytest pytest-benchmark
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Qdrant | Milvus (`pymilvus==2.6.10`) | Choose Milvus if your org already runs Milvus 2.6 infrastructure and has in-house expertise for its operational model. |
| Qdrant online serving | Postgres + pgvector | Choose pgvector only for small scale (<~1M vectors) when minimizing infra count is more important than top-end ANN performance. |
| FastAPI | gRPC-only serving | Choose gRPC-only when you control all clients and need strict contract/perf optimization over HTTP ecosystem compatibility. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Metadata-only recommenders as V1 core | Project context explicitly assumes metadata may be missing; this creates brittle cold-start behavior. | Audio-embedding-first retrieval pipeline with optional metadata filters as secondary signals. |
| Elasticsearch/OpenSearch as primary ANN for this use case | Works, but for high-recall track-to-track vector retrieval, dedicated vector engines are typically simpler to tune and operate. | Qdrant (or Milvus if already standardized). |
| Mandatory source separation (e.g., always splitting vocals/instruments in V1) | Adds major preprocessing cost/latency and error modes; vocals are expected in inputs and modern embeddings already handle mixed content reasonably. | Whole-track embeddings first; add selective separation only after measured retrieval failures justify it. |

## Stack Patterns by Variant

**If V1 dataset is up to ~5M tracks and single region:**
- Use Qdrant HNSW collections with scalar quantization.
- Because this gives strong recall/latency tradeoff with lower operational complexity.

**If moving toward 10M+ tracks or multi-region traffic:**
- Keep online serving in Qdrant, and add offline Faiss pipelines for large-scale index experiments and periodic distillation.
- Because it separates online reliability from heavy experimentation and keeps iteration speed high.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `torch==2.10.0` | Python `>=3.10` | PyTorch official install page confirms Python 3.10+ support; prefer 3.11/3.12 for ecosystem stability. |
| `fastapi==0.135.1` | Python `>=3.10`, `uvicorn==0.42.0` | Current mainstream ASGI pairing for ML services. |
| `qdrant-client==1.17.1` | Python `>=3.10`, Qdrant server `1.x` | Client includes async/grpc support; pin minor for reproducibility. |
| `pymilvus==2.6.10` (alternative) | Milvus `2.6.x` | Official compatibility matrix recommends matching 2.6 client/server line. |

## Confidence Notes (by recommendation)

- **HIGH:** Python 3.11/3.12 + PyTorch + FastAPI/Uvicorn as the serving/inference baseline.
- **HIGH:** Qdrant as a strong default for ANN retrieval in this project profile.
- **MEDIUM:** Milvus as primary alternative (excellent at scale, but higher ops complexity for greenfield teams).
- **MEDIUM:** MERT/CLAP-family checkpoint strategy as V1 embedding backbone (strong practice, but exact checkpoint choice still requires empirical bake-off on your catalog).
- **MEDIUM:** Deferring source separation to post-V1 unless evaluation demonstrates clear gains.

## Sources

- https://pytorch.org/get-started/locally/ — verified stable line and Python compatibility (`2.7.0` shown on install matrix, Python 3.10+ requirement).
- https://pypi.org/project/torch/ — verified current package release (`2.10.0`).
- https://pypi.org/project/fastapi/ — verified current package release (`0.135.1`).
- https://pypi.org/project/uvicorn/ — verified current package release (`0.42.0`).
- https://qdrant.tech/documentation/ — verified Qdrant capabilities/docs.
- https://pypi.org/project/qdrant-client/ — verified client release (`1.17.1`).
- https://pypi.org/project/pymilvus/ — verified Milvus Python SDK release (`2.6.10`) and compatibility table.
- https://pypi.org/project/faiss-cpu/ — verified Faiss wheel release (`1.13.2`) and GPU wheel caveat.
- https://pypi.org/project/librosa/ — verified release (`0.11.0`).
- https://essentia.upf.edu/documentation.html — verified current Essentia docs line (`2.1-beta6-dev`) and MIR scope.
- https://huggingface.co/m-a-p/MERT-v1-330M — verified open pretrained music model availability and usage.
- https://huggingface.co/laion/clap-htsat-unfused — verified open CLAP checkpoint availability and usage.

---
*Stack research for: music recommendation discovery (track-to-track retrieval)*
*Researched: 2026-03-19*
