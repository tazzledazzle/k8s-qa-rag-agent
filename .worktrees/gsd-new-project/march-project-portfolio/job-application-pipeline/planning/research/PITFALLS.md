# Domain Pitfalls

**Domain:** AI-assisted job application pipeline  
**Researched:** 2026-04-14

## Critical Pitfalls

### Legal, terms of service, and access risk (job discovery)

**What goes wrong:** Complaints, account bans, or legal exposure depending on jurisdiction and facts.  
**Why it happens:** Scraping is treated as a pure engineering problem.  
**Consequences:** Shutdown of discovery features, liability, reputational harm.  
**Prevention:** Prefer official APIs and feeds; site-specific legal review; avoid bypassing authentication; minimal retention; internal policy.  
**Detection:** Logged-in-only listings, aggressive anti-bot measures, explicit scraping restrictions in terms.

**Confidence:** LOW to MEDIUM for universal rules; **legal advice required** for production crawling.

### Embedding drift and model version chaos

**What goes wrong:** Tiers and rankings shift when embedding models change.  
**Why it happens:** Unpinned models or mixed versions across resume and JD pipelines.  
**Consequences:** Broken thresholds and user distrust.  
**Prevention:** Pin embedding model versions; store metadata; re-embed in controlled jobs; version policies per model.  
**Detection:** Eval suite regressions; sudden tier distribution shifts.

### LLM scoring hallucinations and ungrounded rankings

**What goes wrong:** The deep scorer invents qualifications or misreads constraints.  
**Why it happens:** LLMs optimize plausibility; long JDs increase error rates.  
**Prevention:** Ground scores in retrieved chunks; structured outputs with citations; deterministic filters for location, authorization, years of experience.  
**Detection:** Disagreement between embedding tier and LLM tier; clustered user overrides.

### PII mishandling (resumes and crawled pages)

**What goes wrong:** Leaks, over-collection, secrets in logs or traces.  
**Why it happens:** RAG pipelines log prompts; resumes contain contact details.  
**Prevention:** Redact logs; minimize stored fields; encrypt at rest; tight token scopes; separate dev and prod data.  
**Detection:** PII alerts in logs; access audits.

## Moderate Pitfalls

- **Evaluation gaming:** Optimizing only to Ragas or LLM-judge metrics that do not correlate with interviews. Mitigation: human labels and outcome tracking.  
- **False positives in matching:** Strong semantic match with wrong seniority or domain. Mitigation: structured JD fields and hybrid retrieval.  
- **Crawler fragility:** Selectors break weekly. Mitigation: per-site modules, health checks, stale listing detection.  
- **Notion as stealth database:** Rate limits and schema rigidity. Mitigation: canonical state in your store; Notion as a projection.

## Phase-Specific Warnings

| Phase | Pitfall | Mitigation |
|-------|---------|------------|
| Discovery | ToS and access risk | API-first; legal review |
| Matching | Embedding-only decisions | Hybrid plus structured gates |
| Prep agents | Over-editing factual resume content | Constraints and diff review |
| HITL | Approval fatigue | Tier defaults and batch review |
| Learning | Overfitting thresholds to noise | Holdout labels; regularization |

## Sources

- LangGraph documentation (state and interrupts)  
- Industry practice on scraping risk (LOW confidence without counsel)
