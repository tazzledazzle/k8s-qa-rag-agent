# Music Recommendation Discovery Engine

## What This Is

An audio-first music recommendation system that returns similar songs for any input track. The v1 product focuses on whole-track similarity retrieval and accepts multiple input types: file upload, audio URL, and internal track ID. It is designed to start with high-quality Top 20 recommendations and later extend to richer explanations and segment-level matching.

## Core Value

Given any track input, return a strong Top 20 list of songs that feel genuinely similar.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] User can submit an input track as file upload, URL, or internal track ID.
- [ ] System returns Top 20 similar songs for the input track.
- [ ] Similarity is computed at whole-track level in v1.
- [ ] Retrieval balances quality, system simplicity/cost, and throughput.

### Out of Scope

- Segment-level recommendation and retrieval by specific song moments — deferred to a later version after whole-track baseline is stable.
- Advanced recommendation explanations in v1 UI/API output — defer until retrieval quality baseline is proven.

## Context

- Domain: music recommendation.
- Available inputs initially have no pre-existing metadata dependency; metadata/tags/lyrics should be extracted/processed from audio.
- Vocals are common, so lyrics-derived semantics are a useful feature path.
- Open-source pretrained models are preferred for feature extraction and embedding generation.
- Initial target is retrieval effectiveness for track-to-track discovery, not instant response.

## Constraints

- **Modeling approach**: Pretrained open-source models first — avoids custom training overhead in v1.
- **Scope**: Whole-track retrieval for v1 — keeps implementation constrained and measurable.
- **Input compatibility**: Must support upload, URL, and internal ID — enables broader ingest paths from day one.
- **Priority tradeoff**: Balanced quality/cost/throughput — avoids over-optimizing one dimension too early.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build a track-to-track similarity engine for v1 | Fastest path to core user value | — Pending |
| Return Top 20 similar songs as v1 success target | Concrete, testable output for quality iteration | — Pending |
| Support multiple input types (upload, URL, track ID) | Reduces integration friction for early usage | — Pending |
| Use whole-track retrieval before segment-level retrieval | Simplifies pipeline and indexing for first launch | — Pending |
| Use pretrained open-source models for audio/lyrics feature extraction | Practical starting point without labeled in-house data | — Pending |

---
*Last updated: 2026-03-18 after initialization*
