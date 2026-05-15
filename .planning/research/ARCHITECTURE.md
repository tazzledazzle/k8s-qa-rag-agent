# Research — Architecture

**Researched:** 2026-05-12

## Major components

1. **Git watcher** — Receives GitHub webhooks, verifies signatures, triggers indexer jobs/API.
2. **Indexer** — Clone/pull repo, chunk, embed, upsert vectors + BM25 docs.
3. **Retriever** — Fuses dense + sparse candidates, reranks, caches hot queries.
4. **QA agent** — LangGraph loop: plan → tool calls → synthesize answer with citations.
5. **Data plane** — Qdrant (vectors), Elasticsearch (BM25), Redis (cache); optional Postgres for sessions per DESIGN.

## Data flow (happy path)

GitHub push → **Git watcher** → indexer reindex API → **Qdrant/ES** updated → user question → **Retriever** → **QA agent** → HTTP JSON answer.

## Suggested build order (already largely built)

1. Data stores up (compose or cluster)  
2. Indexer correctness on sample repo  
3. Retriever fusion + rerank validation  
4. Agent E2E with tools  
5. Webhook → indexer integration in staging  
6. Observability dashboards + SLO probes

## Boundaries

- Retriever never calls LLM directly; QA agent owns model calls.
- Indexer does not expose public internet without auth/TLS termination at ingress.
