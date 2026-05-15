# Project Research Summary

**Project:** Audio-first Music Recommendations
**Domain:** Track-to-track music discovery and similarity retrieval
**Researched:** 2026-03-19
**Confidence:** MEDIUM-HIGH

## Executive Summary

This project is a retrieval-first recommendation engine: given a seed track (upload, URL, or track ID), return a high-quality top-20 similar set quickly and consistently. The strongest pattern across the research is to treat this as an audio embedding + ANN retrieval problem with a two-stage ranking pipeline, not a metadata recommender and not an "AI DJ" product in V1. Experts build this by separating online query serving from offline indexing, then layering controlled reranking and evaluation gates.

The recommended approach is Python 3.11/3.12 with PyTorch/torchaudio inference, Qdrant-backed ANN retrieval, and FastAPI service boundaries around input normalization, embedding, retrieval, and rerank. V1 scope should prioritize unified seed input, deterministic whole-track embeddings, top-20 retrieval, diversity/freshness rerank, and feedback event capture. This creates a measurable core loop before investing in advanced controls like vocal-aware weighting or segment-level retrieval.

The key risk is false confidence from technical metrics that do not reflect listener-perceived similarity. Closely related risks are evaluation leakage (artist/album overlap), ANN drift at scale, and rights/licensing blockers. Mitigation is clear: enforce grouped eval splits and human listening gates early, version embeddings/index artifacts with rollback, tune ANN as an ongoing operations track, and keep license provenance as a phase-1 non-negotiable.

## Key Findings

### Recommended Stack

The stack is mature and implementation-ready for this domain. The combination of Python + PyTorch + Qdrant + FastAPI optimizes for ecosystem compatibility, operational simplicity, and quality/latency balance in vector retrieval systems. Supporting tools like FFmpeg, Faiss (offline benchmarking), and observability instrumentation are not optional extras; they are critical for reliability and iteration speed.

**Core technologies:**
- **Python 3.11/3.12:** Core application/runtime for ingestion, inference, indexing, and APIs - best compatibility with the audio ML ecosystem.
- **PyTorch + torchaudio (`torch==2.10.0`):** Embedding inference runtime - broad support for open music/audio checkpoints and GPU acceleration.
- **Qdrant (`1.14+`) + `qdrant-client==1.17.1`:** Primary ANN retrieval engine - strong HNSW recall/latency with payload filtering and pragmatic operations.
- **FastAPI (`0.135.1`) + Uvicorn (`0.42.0`):** Service layer for retrieval APIs - high-throughput ASGI baseline with low integration friction.

### Expected Features

Research converges on a clear V1: fast top-20 similar-track retrieval from flexible seed inputs, plus enough reranking and UX context to make results usable and trustworthy. Differentiators are best added only after this baseline proves quality and throughput.

**Must have (table stakes):**
- Unified seed input (`upload`, `url`, `track_id`) with canonicalization.
- Whole-track top-20 similar retrieval with deterministic ranking and confidence.
- Basic diversity/freshness reranking to avoid near-duplicate result sets.
- Result cards with playable context and basic metadata.
- Explicit feedback capture (`like`, `skip`, `not similar`) for offline tuning.

**Should have (competitive):**
- Familiar <-> Discover tuning control via reranking parameters.
- Vocal-aware retrieval mode/weighting for vocal-heavy queries.
- Retrieval confidence thresholds and low-confidence fallback behavior.
- Session continuation ("next 20") once repeated usage is validated.

**Defer (v2+):**
- Segment-level retrieval and timestamped match explanation.
- Conversational "AI DJ" interaction layer.
- Heavy social graph/discovery feed mechanics.

### Architecture Approach

The architecture should use strict boundaries: input API -> audio normalization -> embedding service -> ANN retrieval -> reranker -> response, with offline indexing and evaluation as separate pipelines. Two patterns are foundational from day one: (1) two-stage retrieval (ANN then rerank) and (2) immutable versioned artifacts for preprocessing/model/embedding/index bundles. This gives controllable quality iteration and safe rollback while protecting online latency from indexing workloads.

**Major components:**
1. **Input and normalization layer:** Resolve upload/URL/ID into canonical audio and deterministic preprocessing.
2. **Embedding + retrieval layer:** Generate track vectors and perform low-latency ANN candidate search.
3. **Reranking + policy layer:** Apply diversity, quality thresholds, and business constraints to produce final top-20.
4. **Offline indexing/eval layer:** Bulk embed, build/publish index versions, run recall + listening-based gates.

### Critical Pitfalls

1. **Evaluation leakage via naive splits** - prevent with artist/album-grouped splits and unseen-artist hard gates.
2. **Optimizing for ANN/embedding metrics instead of listener quality** - require human listening rubric before promotion.
3. **Vocal dominance distorting similarity** - add dual-view embeddings and vocal/instrumental-specific eval slices.
4. **Unversioned embeddings/index artifacts** - enforce immutable version bundles and atomic rollback pointers.
5. **Licensing/provenance gaps** - separate research vs production corpora and gate deployment on legal audit pass.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Foundations - Data Governance, Canonical Ingest, Evaluation Integrity
**Rationale:** Every later decision depends on trusted data and valid evaluation.  
**Delivers:** Canonical input pipeline, dedupe/fingerprinting for identity only, license provenance ledger, artist/album-grouped eval splits.  
**Addresses:** Unified seed input requirement and cold-start audio-first constraints.  
**Avoids:** Evaluation leakage, fingerprinting misuse, legal non-compliance.

### Phase 2: Baseline Retrieval Core - Embedding + Top-20 ANN
**Rationale:** Prove the core product loop before adding controls and UX complexity.  
**Delivers:** Deterministic whole-track embedding service, ANN index/search, top-20 endpoint from internal IDs first, initial latency/cost budgets.  
**Uses:** PyTorch/torchaudio, Qdrant, FastAPI.  
**Implements:** Embedding service + vector retrieval service boundary.

### Phase 3: Quality System - Human Evaluation and Representation Upgrades
**Rationale:** Technical retrieval must be translated into perceived musical similarity.  
**Delivers:** Listening-panel quality gates, failure taxonomy, vocal/instrumental challenge sets, optional dual-view representation path for vocal-heavy errors.  
**Addresses:** Quality trust and vocal-aware differentiation.  
**Avoids:** Metric-only optimization and vocal dominance failure modes.

### Phase 4: Production Hardening - Reranking, Versioning, Safe Release
**Rationale:** Move from "works" to "operates reliably under change."  
**Delivers:** Diversity/freshness rerank, confidence thresholds/fallbacks, immutable embedding/index versioning, canary publish + rollback, async URL ingest queue.  
**Addresses:** Table-stakes diversity plus confidence guardrails.  
**Avoids:** ANN drift surprises, repetitive top-20 sets, request-path ingest bottlenecks.

### Phase 5: Product Differentiation - Controls and Session Discovery
**Rationale:** Add user-facing advantage after baseline quality and reliability are stable.  
**Delivers:** Familiar-vs-discover control, session continuation ("next 20"), improved explanation tags, targeted vocal-aware controls where validated.  
**Addresses:** Differentiators in FEATURES.md with lower risk.  
**Avoids:** Premature scope creep into AI DJ/social features.

### Phase 6: Scale and Economics - Continuous ANN and Throughput Optimization
**Rationale:** Growth changes the best ANN/inference settings; this must become continuous discipline.  
**Delivers:** Monthly ANN tuning sweeps, cost/perf dashboards, CPU/GPU pool optimization, cache strategy, multi-region/sharding path as needed.  
**Addresses:** Operational sustainability at larger catalog/query volumes.  
**Avoids:** Silent latency/recall decay and margin erosion.

### Phase Ordering Rationale

- Dependencies are strict: canonical ingest/eval integrity must precede model and index benchmarking.
- Architecture supports this order naturally: offline pipelines and artifact versioning mature before advanced UX features.
- Pitfalls map cleanly to phase gates, turning known failure modes into explicit acceptance criteria.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3:** Representation strategy for vocal-heavy retrieval (multi-view fusion design + evaluation protocol details).
- **Phase 6:** Large-scale ANN operating envelope (sharding/quantization choices by target catalog and SLA).

Phases with standard patterns (skip research-phase):
- **Phase 1:** Ingest normalization, grouped split hygiene, provenance tracking are well-understood.
- **Phase 2:** Baseline embedding + ANN + API stack has strong documented patterns.
- **Phase 4:** Versioned artifacts, canary/rollback, and async ingest are established production practices.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions and compatibility are concrete and sourced from official docs/package registries. |
| Features | MEDIUM-HIGH | Strong competitor pattern alignment; exact differentiation payoff still needs product validation. |
| Architecture | MEDIUM | Patterns are solid, but specific infra boundaries depend on expected traffic/profile not yet quantified. |
| Pitfalls | HIGH | Risks are concrete, recurring in this domain, and paired with actionable prevention/verification steps. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Embedding checkpoint choice (MERT/CLAP variants):** Run a controlled bake-off on your catalog before freezing Phase 2 baselines.
- **Target scale assumptions:** Define expected catalog size, QPS, and SLA early to finalize ANN/index topology decisions.
- **Legal envelope for commercial use:** Confirm production-eligible corpus boundaries before major model/index investment.
- **Human evaluation operations:** Decide panel process/ownership so quality gates are executable, not aspirational.

## Sources

### Primary (HIGH confidence)
- https://pytorch.org/get-started/locally/ - PyTorch compatibility baseline
- https://pypi.org/project/torch/ - torch version verification
- https://pypi.org/project/fastapi/ - FastAPI version verification
- https://pypi.org/project/uvicorn/ - Uvicorn version verification
- https://qdrant.tech/documentation/ - Qdrant capabilities and operations
- https://pypi.org/project/qdrant-client/ - client release verification
- https://support.spotify.com/ca-en/article/spotify-radio/ - table-stakes radio/discovery UX
- https://support.google.com/youtubemusic/answer/15165061?hl=en - personalization/tuner patterns
- https://support.apple.com/en-us/HT204944 - seeded station behavior
- https://mtg.github.io/mtg-jamendo-dataset/ - split and licensing caveats
- https://arxiv.org/pdf/1306.1461 - dataset leakage/eval quality risks

### Secondary (MEDIUM confidence)
- https://github.com/facebookresearch/faiss - ANN baseline implementation reference
- https://milvus.io/docs/v2.5.x/audio_similarity_search.md - alternative vector architecture context
- https://engineering.atspotify.com/2023/10/introducing-voyager-spotifys-new-nearest-neighbor-search-library/ - ANN tradeoff framing
- http://ann-benchmarks.com/ - recall/latency tradeoff benchmarks
- https://github.com/LAION-AI/CLAP - audio embedding model reference
- https://huggingface.co/m-a-p/MERT-v1-330M - music embedding model card
- https://musicbrainz.org/doc/Fingerprinting - fingerprinting scope limitations

### Tertiary (LOW confidence)
- No critical roadmap decisions currently depend on low-confidence-only sources.

---
*Research completed: 2026-03-19*
*Ready for roadmap: yes*
