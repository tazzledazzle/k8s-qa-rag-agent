# Feature Landscape

**Domain:** AI-assisted job application pipeline  
**Researched:** 2026-04-14

## Table Stakes

Features users expect from a serious job copilot.

| Feature | Why expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Single source of truth for resumes | Consistency across applications | Medium | Versioning and audit trail |
| Job intake without crawling (at first) | Pipeline must run on day one | Low | Paste, upload, or API |
| Semantic search and ranking | Best matches first | Medium | Combine hybrid retrieval with structured filters |
| Editable outputs and diffs | Trust and control | Medium | Show changes versus master resume |
| Application status tracking | Users live in workflows | Low | Notion, SQL, or spreadsheet-backed CRM |
| Privacy posture | Resume data is sensitive | Medium | Encryption at rest, least-privilege tokens |

## Differentiators

| Feature | Value | Complexity | Notes |
|---------|-------|------------|-------|
| Ten-layer plugin architecture | Swap implementations without rewriting core | High | Intentional abstraction tax |
| Six-stage explicit workflow | Debuggability and governance | Medium | Each stage is testable in isolation |
| Tiered autonomy with explainable tiers | Predictable risk and effort | Medium | Tiers need “why” not only “score” |
| HITL gates before external actions | Prevents catastrophic sends | Medium | LangGraph interrupts fit well |
| Calibration feedback loop | Improves policies from outcomes | High | Requires disciplined labeling |
| JD normalization to a canonical schema | Fairer matching and analytics | Medium | Makes embeddings comparable |

## Anti-Features

| Anti-feature | Why avoid | Instead |
|--------------|-----------|---------|
| Fully autonomous applications | Harm, bans, reputation risk | Human approval for early sends and sensitive employers |
| Scraping-first discovery without policy | Legal and ops liability | APIs, feeds, then reviewed extractors |
| Opaque match percentage | Users cannot trust or fix it | Decompose score: retrieval, constraints, LLM critique |
| Storing unnecessary PII | Compliance debt | Minimize fields, retention limits |
| Multi-tenant SaaS on day one | Slows validation | Single-user hardening first |

## Feature Dependencies

```
Master resume and embeddings → skill taxonomy and retrieval
JD text → normalization → embeddings → matching
Matching → tier router → prep agents → HITL → submission
Outcomes and labels → calibration → updated thresholds and policies
```

## MVP Recommendation

Prioritize:

1. Manual JD and resume ingestion with normalized JD schema.  
2. Retrieval and scoring with explainable features and HITL on outputs.  
3. Tracker integration (Notion API or SQL) for statuses.

Defer: broad crawlers, auto-submit, automatic threshold tuning without labels.

## Sources

- Product narrative (stages and layers in repository README)  
- Category norms (MEDIUM confidence)
