# Feature Research

**Domain:** music recommendation discovery engine (audio-first, track-to-track retrieval)
**Researched:** 2026-03-19
**Confidence:** MEDIUM-HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Input from track seed (file upload, URL, or catalog ID) | Competitors let users start discovery from any song/context (song radio or station flows) | MEDIUM | Normalize all inputs to a single internal audio asset pipeline; URL ingestion needs robust resolver/fallback logic. |
| Similar-track retrieval with ranked results | "Song Radio/Station" behavior is now baseline in major products | HIGH | Core v1 requirement: return top 20 similar tracks with stable ranking and confidence score. |
| Continuous discovery flow from a seed | Endless or refreshed discovery streams are common (radio/autoplay patterns) | MEDIUM | After top-20 list, support "continue from result" action to chain discovery sessions. |
| Fast, playable result cards (preview + metadata) | Discovery UX depends on immediate listening and quick relevance judgment | MEDIUM | At minimum: title/artist/duration/artwork/preview link; full playback can remain external in v1. |
| Basic feedback loop (like/dislike/skip or hide) | Users expect to steer recommendations when matches miss | MEDIUM | Capture explicit feedback events even if model retraining is batch/offline initially. |
| Freshness + diversity control at session level | Users expect discovery not to get stuck in near-duplicates | MEDIUM | Apply post-retrieval re-ranking for artist/album spread and replay suppression. |
| Transparent recommendation context (light explainability) | Platforms increasingly expose "why this track" cues to build trust | LOW-MEDIUM | Simple reason tags (e.g., "similar timbre + tempo") are sufficient for v1. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Vocal-aware similarity controls | Better matches for vocal-heavy inputs where timbre, delivery, and mix matter | HIGH | Use embeddings/features that preserve vocal characteristics; expose "vocals weight" slider or mode. |
| User-tunable discovery intent (Familiar ↔ Discover) | Gives explicit control over novelty vs safety, matching modern tuner patterns | MEDIUM | Implement as re-ranking parameter over candidate pool, not a separate model. |
| Multi-objective ranking modes (quality/cost/latency presets) | Product can optimize recommendations for different operational goals | MEDIUM-HIGH | Presets such as `best_match`, `balanced`, `fast`; useful for API and internal ops. |
| Retrieval confidence and quality guardrails | Prevents low-similarity junk in top results, increasing trust in top 20 | MEDIUM | Add minimum similarity threshold and fallback behavior ("insufficient confident matches"). |
| Cold-start resilience from audio-only signals | Works even when metadata is missing/incomplete | HIGH | Critical for your context: prioritize robust audio feature extraction over metadata dependencies. |
| Reusable embedding index API | Enables future segment-level and playlist use cases without rewrite | HIGH | Keep retrieval service modular: ingest -> embed -> index -> retrieve -> rerank pipeline boundaries. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full conversational "AI DJ" in v1 | Feels innovative and marketable | Adds LLM complexity/cost before core retrieval quality is proven | Ship deterministic reason tags + lightweight controls first. |
| Segment-level retrieval in initial release | Promise of finer-grained matching | Major pipeline and indexing complexity; delays validation of core whole-track relevance | Nail whole-track top-20 quality first, then add segment indexing in v1.x. |
| Heavy social layer (follows, feeds, sharing graph) | Seen in consumer music apps | Distracts from core recommendation engine; high moderation/product overhead | Export/share result list URLs later; keep core B2B-style utility first. |
| Manual tagging workflow as primary signal | Seems like quick quality fix | Does not scale and conflicts with audio-first/no-metadata constraint | Use pretrained embeddings + optional metadata enrichment when available. |
| Real-time online retraining from every interaction | Promises instant personalization | Operationally expensive and hard to debug early on | Start with event logging + scheduled retraining + configurable reranking weights. |

## Feature Dependencies

```
[Audio ingestion + normalization]
    └──requires──> [Unified input adapters: upload/URL/internal ID]
                       └──requires──> [Track identity resolution + dedupe]

[Top-20 similar retrieval]
    └──requires──> [Audio embeddings extraction]
                       └──requires──> [Pretrained model selection + feature pipeline]
                           └──requires──> [Vector index + ANN search]

[Diversity/freshness reranking]
    └──requires──> [Base retrieval candidates]

[User feedback loop]
    └──enhances──> [Reranking and personalization]

[Vocal-aware controls]
    └──enhances──> [Top-20 retrieval quality for vocal tracks]

[Segment-level retrieval]
    └──requires──> [Whole-track retrieval stability]
    └──conflicts (timeline)──> [v1 speed-to-validation]
```

### Dependency Notes

- **Top-20 retrieval requires embeddings + vector index:** Without stable audio embeddings and ANN retrieval, everything else is UI polish on weak relevance.
- **Reranking depends on candidate quality:** Diversity controls improve results only after base nearest-neighbor quality is acceptable.
- **Feedback loop enhances, not replaces, core model:** Explicit feedback should first tune reranking and curation rules before full model retraining.
- **Segment-level conflicts with v1 timeline:** It is valuable, but should be gated behind proof that whole-track retrieval meets quality and throughput targets.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] Unified seed input (`upload`, `url`, `track_id`) -> canonical track asset
- [ ] Audio embedding extraction pipeline (pretrained OSS model) for whole tracks
- [ ] Top-20 similar track retrieval endpoint with deterministic ranking
- [ ] Basic diversity/freshness reranking (artist repetition limits)
- [ ] Result payload with playable context (metadata + preview link where available)
- [ ] Feedback event capture (`like`, `skip`, `not similar`) for offline tuning

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] Familiar-vs-discover tuning control — trigger: stable offline relevance baseline
- [ ] Vocal-aware retrieval mode — trigger: measurable lift on vocal-heavy evaluation set
- [ ] Confidence thresholding/fallback UX — trigger: identified low-confidence failure buckets
- [ ] Session continuation ("generate next 20") — trigger: repeated usage patterns

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Segment-level retrieval and timestamped match explanations — defer until v1 throughput/quality is consistently met
- [ ] Conversational curation layer (AI DJ / natural-language steering) — defer until core recommendation quality is trusted
- [ ] Social/discovery graph features — defer unless product direction shifts consumer-social

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Top-20 similar retrieval (whole-track) | HIGH | HIGH | P1 |
| Unified input adapters (upload/URL/ID) | HIGH | MEDIUM | P1 |
| Diversity/freshness reranking | HIGH | MEDIUM | P1 |
| Feedback capture events | MEDIUM-HIGH | MEDIUM | P1 |
| Familiar-vs-discover tuning | MEDIUM-HIGH | MEDIUM | P2 |
| Vocal-aware retrieval mode | HIGH | HIGH | P2 |
| Segment-level retrieval | MEDIUM-HIGH | HIGH | P3 |
| Conversational AI DJ layer | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Competitor A | Competitor B | Our Approach |
|---------|--------------|--------------|--------------|
| Seeded discovery from track | Spotify Song Radio | SoundCloud Station from track/search/library | Treat any input seed as first-class and normalize into one retrieval path. |
| Continuous personalized mixes | YouTube Music custom/personal mixes (tuner) | Spotify daylist + Smart Shuffle | Start with deterministic top-20 and add tunable continuation in v1.x. |
| User control over recommendation direction | YouTube Music Music Tuner + Ask Music | Deezer Flow Tuner | Expose low-cost controls (novelty and vocal weighting) before full conversational control. |
| Similarity surface | Last.fm `track.getSimilar` API/listening-data similarities | Apple Music custom station from song/artist | Combine audio-first similarity with light contextual explainability tags. |

## Sources

- Spotify Support — Spotify Radio (official help): https://support.spotify.com/ca-en/article/spotify-radio/ (HIGH)
- Spotify Support — Autoplay tracks (official help): https://support.spotify.com/ca-en/article/autoplay/ (HIGH)
- Spotify Newsroom — Smart Shuffle (official announcement): https://newsroom.spotify.com/2023-03-08/smart-shuffle-new-life-spotify-playlists/ (HIGH)
- Spotify Newsroom — daylist (official announcement): https://newsroom.spotify.com/2023-09-12/ever-changing-playlist-daylist-music-for-all-day/ (HIGH)
- YouTube Blog — YouTube Music getting started (official): https://blog.youtube/news-and-events/get-started-youtube-music/ (HIGH)
- YouTube Music Help — personal/custom mix + Music Tuner + Ask Music: https://support.google.com/youtubemusic/answer/15165061?hl=en (HIGH)
- Apple Support — create station from song/artist in Music app: https://support.apple.com/en-us/HT204944 (HIGH)
- SoundCloud Help — Stations and how they work: https://help.soundcloud.com/hc/en-us/articles/115003565208-Stations-and-how-they-work (HIGH)
- Last.fm API — `track.getSimilar`: https://www.last.fm/api/show/track.getSimilar (HIGH)
- Deezer Newsroom — Flow Tuner personalization controls (official): https://newsroom-deezer.com/2026/02/deezer-launches-flow-tuner-personalized-recommendations/ (MEDIUM-HIGH)

---
*Feature research for: audio-first music recommendation discovery engine*
*Researched: 2026-03-19*
