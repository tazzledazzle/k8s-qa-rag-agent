# Research — Features (codebase Q&A / SRE assistant)

**Researched:** 2026-05-12

## Table stakes (must work for credibility)

- Natural-language **code Q&A** with **file path + line citations**
- **Runbook / markdown** retrieval for “how do I respond to alert X”
- **Re-index** on push (webhook) + scheduled safety net (CronJob)
- **Health endpoints** per service for K8s probes
- **Hybrid retrieval** (dense + lexical) with reranking

## Differentiators (portfolio)

- **AST-aware chunking** for Python (tree-sitter / AST paths per DESIGN)
- **Full Kubernetes** story: HPA, PDB, OTEL wiring, overlays
- **Kotlin webhook edge** with HMAC verification

## Anti-features / defer

- Full enterprise IAM / ABAC across all repos (start with single-tenant or simple ACL)
- Arbitrary plugin marketplace for tools
- Real-time collaborative chat UI

## Dependencies between features

Indexing must precede trustworthy retrieval; retriever quality gates agent usefulness; webhook triggers depend on indexer idempotency.
