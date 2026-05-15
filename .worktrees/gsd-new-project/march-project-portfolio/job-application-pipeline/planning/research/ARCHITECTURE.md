# Architecture Patterns

**Domain:** AI-assisted job application pipeline  
**Researched:** 2026-04-14

## Recommended Architecture (conceptual)

**Single orchestration brain:** a LangGraph graph implements state, checkpoints, retries, and interrupts for HITL ([LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)).

### Plugin boundaries (ten layers)

| Layer | Responsibility | Communicates with |
|-------|----------------|-------------------|
| Ingestion | Resumes, JDs, APIs, crawlers | Transform |
| Transform | Clean, chunk, dedupe, canonicalize JD | Storage |
| Storage | Documents, embeddings, metadata | Retrieval |
| Retrieval | Vector and optional keyword or hybrid search | Intelligence |
| Orchestration | Stage machine, policies, routing | All layers |
| Intelligence | Embeddings, rerankers, LLM scorers, extractors | Control |
| Control | Thresholds, tier routing, safety | Output |
| Output | Artifacts, Notion, exports | Scheduling |
| Scheduling | Cron, refresh jobs | Ingestion and Intelligence |
| Learning | Eval sets, metrics, calibration | Control and Intelligence |

### Six-stage mapping

1. **Source of truth:** Document store, embedding jobs, skill taxonomy (structured plus vector artifacts).  
2. **Job discovery:** Connector registry (API-first), optional Scrapy or Playwright, dedupe and freshness.  
3. **Matching engine:** JD embedding, retriever, optional hybrid retrieval, reranker, LLM critique with citations.  
4. **Threshold decision:** Policy engine mapping scores to tiers; separate “quality tier” from “automation allowed.”  
5. **Application prep:** Resume tailor, cover letter, diff model for review.  
6. **Tracking and feedback:** Notion or DB sync, status monitor, labels, calibration jobs.

### Data flow (happy path)

```
Resume docs → chunk and embed → vector store
JD → normalize → embed → retrieve evidence → score → tier
Tier → prep agents → HITL interrupt → approved artifacts → tracker
Outcomes → label store → calibration → policy update
```

### Where HITL fits

At minimum: before any **external send or submit**. Use LangGraph **interrupts** with checkpointing so approvals can take hours ([interrupt docs](https://docs.langchain.com/oss/python/langgraph/interrupts)). Pair with Slack or email for notifications.

**Notion MCP versus API:** MCP accelerates development; long-lived automation should use the **Notion REST API** with scoped tokens.

### Feedback loop for score calibration

Separate:

1. **Model drift** from embedding model changes → pin versions and planned re-embed jobs.  
2. **Policy calibration** from labeled outcomes → threshold and weight updates with holdout validation.  
3. **Retrieval quality** → Ragas or similar on fixed suites when chunking or retrievers change.

Closed loop: labels and outcomes → offline eval → proposed policy change → shadow or canary → promote.

## Patterns to Follow

- **Evidence-first ranking:** Retrieval returns chunk IDs; scorers cite evidence.  
- **Two-stage autonomy:** Cheap retrieval filter first; expensive LLM critique on top-K only.

## Anti-Patterns

- **One embedding score as truth:** Add structured must-have gates.  
- **Unbounded crawler sprawl:** Per-source connectors, kill switches, health checks.

## Scalability

| Concern | MVP | Growth | SaaS scale |
|---------|-----|--------|------------|
| Vectors | Chroma embedded | pgvector or Qdrant | Managed vector plus tenancy |
| Crawl throughput | Sequential polite fetch | Queued workers | Distributed spiders plus cache |
| Eval | Manual labels | Ragas plus CI gates | Automated eval and drift monitors |

## Sources

- LangGraph documentation (links above)
