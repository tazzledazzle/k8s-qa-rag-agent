# Pitfalls Research

**Domain:** Audio-first music recommendation discovery engine (track-to-track similarity)
**Researched:** 2026-03-19
**Confidence:** MEDIUM-HIGH

## Critical Pitfalls

### Pitfall 1: Evaluation leakage (artist/album duplicates across splits)

**What goes wrong:**
Offline Recall@K looks strong, but production quality collapses because the model learned artist/production signatures instead of transferable musical similarity.

**Why it happens:**
Teams use random track-level splits, so the same artist/album (or even near-duplicate versions) appears in both train and test.

**How to avoid:**
Use strict artist-grouped and album-grouped splits for all model benchmarking. Add a second "unseen-artist" eval slice as a hard gate before model promotion. Keep a duplicate/near-duplicate filter in dataset prep.

**Warning signs:**
- Big metric drop when evaluated on unseen artists
- Retrieved neighbors are often same artist/album even for diverse queries
- Manual listening says "same production style" more than "same musical feel"

**Phase to address:**
Phase 1 (Data and evaluation foundations), enforced again in Phase 3 (model benchmarking).

---

### Pitfall 2: Optimizing only for embedding loss and ANN recall, not human similarity

**What goes wrong:**
System returns technically close vectors that do not sound meaningfully similar to listeners, so trust drops quickly.

**Why it happens:**
Teams treat ANN recall and training loss as product quality proxies, and skip calibrated listening evaluations for "top 20 similar songs."

**How to avoid:**
Define product-facing quality gates early: blinded listening panels, pairwise "is this actually similar?" tests, and failure taxonomies (tempo mismatch, mood mismatch, vocal mismatch). Keep ANN recall as infra metric, not user metric.

**Warning signs:**
- ANN recall improves but user acceptance of recommendations is flat/down
- Internal demos require heavy cherry-picking
- Frequent complaints: "These are close in embedding space but wrong musically"

**Phase to address:**
Phase 2 (quality rubric and human eval protocol) before large-scale model/index iteration.

---

### Pitfall 3: Vocal dominance masking overall song similarity

**What goes wrong:**
Queries with vocals retrieve tracks by vocal timbre/gender similarity while rhythm/harmony/energy mismatch badly.

**Why it happens:**
Single mixed-audio embedding overweights voice cues in many pretrained models, especially when no metadata is available to rebalance.

**How to avoid:**
Use multi-view embeddings: at minimum compute (a) full-mix embedding and (b) accompaniment-focused or source-separated embedding, then blend scores. Add a vocal-presence-aware reranker and evaluate vocal vs instrumental queries separately.

**Warning signs:**
- Vocal queries cluster by singer character over genre/mood
- Instrumental queries perform much better than vocal queries
- Error analysis shows consistent "same singer vibe, wrong song vibe"

**Phase to address:**
Phase 3 (representation strategy) and Phase 4 (reranking and score fusion).

---

### Pitfall 4: Treating audio fingerprinting as similarity retrieval

**What goes wrong:**
System excels at exact/near-exact track identification but fails at "find similar songs."

**Why it happens:**
Fingerprinting technology is designed for identity matching, not perceptual similarity ranking.

**How to avoid:**
Use fingerprinting only for deduplication/canonicalization at ingest; keep recommendation retrieval on learned embeddings built for semantic/perceptual similarity.

**Warning signs:**
- Great performance on cover/duplicate detection but poor discovery quality
- Top results are alternate versions/encodes/remasters, not musically similar neighbors
- Team conflates "same recording" with "similar track"

**Phase to address:**
Phase 1 (ingest architecture decisions) and Phase 3 (retrieval objective definition).

---

### Pitfall 5: ANN index configured once, then left untuned as corpus grows

**What goes wrong:**
Latency/cost or quality slowly degrades as catalog size increases; no one notices until recommendations feel worse at scale.

**Why it happens:**
HNSW parameters (`M`, `ef_construction`, `ef_search`) are fixed early, without periodic retuning against growth and SLO changes.

**How to avoid:**
Make ANN tuning a recurring benchmark track: monthly sweep of recall-latency-memory tradeoffs on representative workloads. Version index configs and require canary rollout + rollback plan.

**Warning signs:**
- Recall drift as catalog grows despite unchanged model
- Query p95 latency and memory climb together
- Rebuild windows become operational bottlenecks

**Phase to address:**
Phase 4 (serving/indexing) with ongoing Phase 6 (operations and scaling).

---

### Pitfall 6: No explicit diversity/novelty controls in top-20 output

**What goes wrong:**
Recommendations are over-specialized and repetitive; user discovery value is low even when "similarity" is accurate.

**Why it happens:**
Pure nearest-neighbor ranking maximizes local similarity without any set-level constraints for diversity, novelty, or serendipity.

**How to avoid:**
Add post-retrieval diversification (e.g., MMR-style re-ranking) and caps on artist/album repetition. Track set-level metrics in addition to per-item relevance.

**Warning signs:**
- Multiple tracks from same artist/album dominate top 20
- Users report "all recommendations sound the same"
- High short-term acceptance but weak repeated-session retention

**Phase to address:**
Phase 5 (ranking policy and UX quality controls).

---

### Pitfall 7: Throughput and cost blind spots in audio feature extraction

**What goes wrong:**
Inference queues grow, ingestion lags behind catalog updates, and per-track compute cost breaks target economics.

**Why it happens:**
Pretrained model choice is made for quality only; no profiling of real-time + batch paths for file upload, URL ingest, and internal IDs.

**How to avoid:**
Define explicit QoS budgets per input type (latency and cost). Build two-tier extraction: fast-path embeddings for immediate results, deferred high-quality re-embed jobs. Cache intermediate features aggressively.

**Warning signs:**
- Backlog growth in embedding jobs
- p95 ingest-to-searchable latency exceeds SLA
- Unit economics worsen with catalog growth

**Phase to address:**
Phase 2 (benchmarking and budget targets) and Phase 4 (production pipeline design).

---

### Pitfall 8: Ignoring rights/licensing constraints for training/evaluation audio

**What goes wrong:**
A technically sound system cannot be shipped or scaled legally due to unclear rights for training data, derived embeddings, or commercial use.

**Why it happens:**
Prototype datasets and open assets are assumed production-safe without legal review; licensing terms (especially non-commercial datasets) are missed.

**How to avoid:**
Track license provenance for every source at ingest. Separate research-only and production-eligible corpora from day one. Add legal checkpoint before Phase 4 deployment commitments.

**Warning signs:**
- Unknown provenance for a non-trivial % of training/eval tracks
- Terms prohibit commercial use but assets still in core pipeline
- Late-stage legal blockers after engineering investment

**Phase to address:**
Phase 1 (data governance) and Phase 3 (model training corpus curation).

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Single embedding per track, no segment store | Fast MVP | Hard migration to segment-level retrieval later | Acceptable in V1 only if schema reserves segment table now |
| One global ANN config forever | Easy ops | Silent recall/latency decay at scale | Never |
| "Random split is fine for now" | Faster experimentation | Invalid quality signals, wrong model chosen | Never |
| No canonicalization/dedup at ingest | Simpler pipeline | Redundant storage and repetitive recommendations | Only for first internal prototype week |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| File upload ingest | Trusting client audio metadata | Decode and normalize server-side, compute deterministic fingerprints and checksums |
| URL ingest | Synchronous download+feature extraction in request path | Use async job queue with status polling and retry/idempotency keys |
| Vector DB / ANN service | No versioning for embeddings/index | Version embeddings, index params, and similarity metric together; rollback atomically |
| Open-source model assets | Pulling arbitrary checkpoints without reproducibility | Pin model hash/version and keep model card + license in registry |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Full-catalog brute-force similarity search | Rising p95 and infra bill | Move to ANN + periodic exact-eval calibration | Usually beyond ~100k-1M tracks |
| Re-embedding whole catalog for every model tweak | Multi-day backfills, stale index | Incremental backfill strategy + dual-index serving | Around first few million tracks |
| CPU-only feature extraction for all paths | Queue spikes under bursts | Mixed CPU/GPU pools and batching | Burst traffic or >10 QPS ingest |
| No cache for repeated popular queries | Duplicate compute work | Query/result cache with TTL and invalidation | Early, often <10k daily queries |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Unvalidated remote URL ingestion | SSRF, malware payload fetch | Strict URL allow/deny lists, content-type validation, sandboxed fetchers |
| Accepting arbitrary media codecs blindly | Decoder exploits, crashes | Constrain codec/container support and transcode in isolated workers |
| Leaking source URLs in logs | Partner/privacy exposure | Redact signed URLs and sensitive query params in logs/traces |
| Publicly exposing track embeddings | Model/data leakage and unauthorized similarity mining | Authz for embedding endpoints and rate limits; avoid raw vector egress |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Returning 20 near-identical tracks | Discovery feels shallow | Enforce artist/album diversity constraints in final list |
| No explanation for similarity | Low trust in results | Provide concise rationale tags (e.g., "similar tempo + mood") |
| Mixing ingest statuses with final results | Confusing interaction | Explicit states: processing, partial, final; avoid silent fallbacks |
| Same ranking regardless of query type | Perceived inconsistency | Query-type-aware policies (file/URL/ID) and normalization |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Similarity model:** Often missing unseen-artist evaluation — verify artist-grouped and album-grouped test slices.
- [ ] **Top-20 retrieval:** Often missing diversity guardrails — verify max-per-artist and near-duplicate suppression.
- [ ] **Serving stack:** Often missing index/version rollback — verify one-click fallback to prior embedding+index bundle.
- [ ] **Ingest pipeline:** Often missing idempotency — verify repeated URL/file submissions do not duplicate work.
- [ ] **Legal readiness:** Often missing license provenance ledger — verify every training/eval source has usage status.

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Leakage-tainted evaluation | MEDIUM | Freeze model promotion, rebuild clean grouped splits, rerun benchmark matrix, replace offline baselines |
| ANN quality drift at scale | MEDIUM | Launch index tuning canary, adjust `ef_search`/`M`, rebuild index, compare against exact-search sample |
| Vocal-dominant false similarity | HIGH | Add dual-view embeddings, retrain score fusion, re-evaluate on vocal-heavy challenge set |
| License non-compliance discovered late | HIGH | Quarantine affected assets, retrain on cleared corpus, legal sign-off gate before redeploy |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Evaluation leakage | Phase 1 | CI check fails if same artist/album appears across train/test |
| Wrong objective metrics | Phase 2 | Promotion requires human listening pass + offline metric bundle |
| Vocal dominance | Phase 3 | Separate vocal/instrumental eval slices meet thresholds |
| Fingerprinting confusion | Phase 1 | Architecture docs separate dedup and recommendation pipelines |
| ANN drift and cost blowups | Phase 4 (+ Phase 6 ongoing) | Monthly recall-latency-memory benchmark report |
| Low-diversity top 20 | Phase 5 | Production dashboard includes diversity/novelty guardrail metrics |
| Ingest throughput failures | Phase 2 + 4 | SLA dashboards and queue depth alarms in place |
| Rights/licensing blockers | Phase 1 + 3 | Data provenance audit passes before production dataset freeze |

## Sources

- Spotify Engineering, "Introducing Voyager: Spotify's New Nearest-Neighbor Search Library" (2023) - production ANN tradeoffs (speed/accuracy/cost, stateless operation): https://engineering.atspotify.com/2023/10/introducing-voyager-spotifys-new-nearest-neighbor-search-library/ (HIGH)
- Google Research, "Deep Neural Networks for YouTube Recommendations" (RecSys 2016) - candidate generation vs ranking separation, large-scale recommender lessons: https://research.google/pubs/pub45530/ (HIGH)
- Elastic Search Labs, "HNSW graph: How to improve Elasticsearch performance" (2025) - `M`/`ef_construction` tradeoffs and recall implications: https://www.elastic.co/search-labs/blog/hnsw-graph (MEDIUM)
- ANN-Benchmarks - recall vs queries/sec as explicit tradeoff surface for ANN methods: http://ann-benchmarks.com/ (MEDIUM)
- MTG-Jamendo dataset documentation - artist-based filtering and split practices for music ML datasets; also non-commercial license caveat: https://mtg.github.io/mtg-jamendo-dataset/ (HIGH)
- Sturm, "The GTZAN dataset: its contents, its faults..." (arXiv:1306.1461) - dataset faults and artist repetition impacting evaluation validity: https://arxiv.org/pdf/1306.1461 (HIGH)
- MusicBrainz Fingerprinting docs - fingerprinting purpose is identification/lookup, not similarity recommendation: https://musicbrainz.org/doc/Fingerprinting (MEDIUM)
- Zhang et al., "Auralist: Introducing Serendipity into Music Recommendation" (WSDM 2012) - overspecialization/filter-bubble risk and diversity/novelty/serendipity balancing: https://dmice.ohsu.edu/bedricks/courses/cs606-ir/papers/zhang_2012.pdf (MEDIUM)

---
*Pitfalls research for: audio-first music recommendation discovery engine*
*Researched: 2026-03-19*
