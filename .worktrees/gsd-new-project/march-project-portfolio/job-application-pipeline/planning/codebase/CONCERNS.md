# Concerns and technical debt

**Path:** `job-application-pipeline/`  
**Mapped:** 2026-04-14

## Current state

- **No executable code** in this directory; risk is **specification drift** between README, research, and future implementation.  
- **Single README** carries both product narrative and exhaustive layer options; may need splitting once code exists.

## Security and compliance

- **Job site scraping** can create legal and terms-of-service risk; product defaults should favor APIs and user-provided JDs until policy is explicit.  
- **PII** in resumes and application logs requires redaction and least-privilege access from day one of coding.  
- **Secrets** must not appear in `.planning/` documents; grep before commit (see GSD map workflow).

## Reliability

- **LLM scoring** can hallucinate strengths or miss hard requirements; mitigation is structured JD fields plus grounded retrieval.  
- **Embedding model changes** can invalidate tier thresholds; versioning and re-calibration must be first-class.

## Operational

- **Notion rate limits** and schema rigidity may push canonical state into a local database with Notion as a projection.  
- **Cost:** Running large models on every listing is expensive; two-stage filtering (cheap then expensive) is required.

## Fragile areas once built

- **Site-specific crawlers** break when selectors change; need health checks and per-source adapters.  
- **Auto-approval** in Control layer can cause spam applications; default to conservative policies.

## Monitoring (future)

- Track tier distribution, approval rates, and outcome labels (interview, reject) to detect drift.  
- Alert on sudden drops in Tier 1 rate or spikes in user overrides.

Review this file after MVP implementation and quarterly thereafter.
