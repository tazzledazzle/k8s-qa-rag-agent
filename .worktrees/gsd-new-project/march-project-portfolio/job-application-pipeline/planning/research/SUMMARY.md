# Research Summary: job-application-pipeline

**Domain:** AI-assisted job application pipeline (RAG, agents, job discovery, HITL, tracking)  
**Researched:** 2026-04-14  
**Overall confidence:** MEDIUM (HIGH for LangGraph orchestration and HITL fit; MEDIUM for vector and eval tradeoffs; LOW for legal scraping without counsel)

## Executive Summary

This product is best modeled as a **stateful agent workflow** with retrieval-heavy matching and high-stakes outputs (resumes, cover letters, applications). The six-stage pipeline aligns with a **LangGraph-first** runtime: explicit state, checkpoints, interrupts for human review, and cyclical feedback for calibration. LangChain remains the practical integration layer for embeddings, vector stores, tools, and structured extraction; LangGraph owns orchestration, durability, and HITL ([LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview), [interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)).

Vector storage should standardize on **ChromaDB for local and MVP** behind a narrow repository interface so production can swap to **pgvector** (relational plus vectors) or **Qdrant** (hybrid search, strong filtering) without rewriting agents. Tier thresholds (90%, 70%) should be treated as **calibrated policies**, not semantic truth: combine embedding similarity with structured constraints (must-have skills, location, seniority) and LLM deep scoring with **grounded reasons and citations** where possible.

Job discovery is the top feasibility and risk surface. Technically, Scrapy plus Playwright is a common split. Legally and commercially, scraping can violate terms of service and create access and retention risk. The defensible pattern is **API-first ingestion** and explicit policy; scraping only after legal review and with rate limits and minimal retention.

Evaluation should combine offline golden sets with **Ragas-style** retrieval and generation metrics plus human labels on match quality and outcomes. Avoid optimizing purely to LLM-judge scores.

## Key Findings

- **Stack:** Python, LangGraph orchestration, LangChain integrations; Chroma locally; optional pgvector or Qdrant later; Ragas plus optional LangSmith traces.
- **Architecture:** Plugin slots map to bounded interfaces; graph state carries JD normalization, embedding pointers, scores, tier decisions, artifacts, HITL checkpoints, and telemetry for learning.
- **Critical pitfall:** Treating automated job discovery as purely engineering; it is compliance-first. Second: threshold-based autonomy without calibration and structured gating produces expensive mistakes.

## Implications for Roadmap

1. **Phase A — Source of truth and matching core (limited crawling):** Master resume ingestion, chunking, embeddings, skill taxonomy, JD normalization from paste or upload, semantic retrieval, baseline tiering.
2. **Phase B — Orchestration shell and HITL:** LangGraph spanning matching through application prep, interrupts before send, artifact versioning.
3. **Phase C — Job discovery adapters (compliance-first):** API adapters first; optional site-specific extractors behind flags; dedupe and freshness.
4. **Phase D — Tracking and learning loop:** Notion or database as system of record, status monitoring, labeled outcomes feeding threshold calibration and eval sets.

**Phase ordering rationale:** Matching value and HITL trust before scaling ingestion; learning requires stable schemas and labels.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH–MEDIUM | HIGH for LangGraph and HITL fit; MEDIUM for production vector choice |
| Features | MEDIUM | Product shape is clear; tier semantics need product validation |
| Architecture | HIGH | Standard agent and RAG boundaries; interfaces and state model matter most |
| Pitfalls | MEDIUM–LOW | Technical pitfalls are well understood; legal scraping is fact-specific |

## Gaps to Address

- Which job sources are in scope (API partners versus specific sites)?
- Single-user versus multi-tenant (affects PII architecture)?
- Autopilot level: which actions never run without human approval?
- Ground-truth labeling workflow for calibration (who labels, how often)?
