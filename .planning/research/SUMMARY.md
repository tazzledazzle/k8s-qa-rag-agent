# Project Research Summary

**Project:** k8s-qa-rag-agent  
**Domain:** Kubernetes-native RAG for internal engineering Q&A  
**Researched:** 2026-05-12  
**Confidence:** HIGH (repo + DESIGN.md grounded)

## Executive Summary

This product is a **self-hosted, hybrid-retrieval assistant** for codebase and operational knowledge. The implemented direction matches common 2025–2026 patterns: **vector + lexical + rerank**, **LangGraph-style agents**, **stateful vector store on Kubernetes**, and **webhook-driven freshness**. The main remaining risk is not architecture diagrams but **proof**: end-to-end behavior, security at the webhook boundary, and honest alignment between docs and running systems.

## Key Findings

### Recommended stack

See `STACK.md`. Core technologies: **FastAPI services**, **Qdrant + Elasticsearch + Redis**, **SentenceTransformers**, **LangGraph agent**, **Kotlin Ktor webhook**, **OpenTelemetry**.

### Expected features

**Must have:** cited code Q&A, runbook retrieval, reindexing, health checks, hybrid retrieval.  
**Should have:** AST-aware chunking, K8s HPA/PDB/OTEL, webhook security.  
**Defer:** full multi-tenant SaaS, rich ACL marketplace.

### Architecture approach

Four-service plus data-plane decomposition (see `ARCHITECTURE.md`). Build order favors **index → retrieve → reason → automate freshness**.

### Critical pitfalls

Top risks: **stale indexes**, **grounding failures**, **OOM/ES instability**, **webhook abuse**, **missing traces** — each with concrete mitigations in `PITFALLS.md`.

## Implications for roadmap

1. **Integration & proof** — demonstrate full path with fixtures and failure modes.  
2. **Security & boundaries** — webhook + secrets + network policy mindset.  
3. **Observability & ops** — SLO-oriented metrics/traces/logs.  
4. **Documentation & release** — close IMPLEMENTATION.md checkboxes; publish reproducible runbooks.
