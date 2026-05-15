# Technology Stack

**Project:** job-application-pipeline  
**Researched:** 2026-04-14

## Recommended Stack (Python-first)

### Core orchestration and integration

| Technology | Role | Why |
|------------|------|-----|
| Python 3.12+ | Runtime | Strong ecosystem for agents, RAG, and scraping; pin version per deploy |
| LangGraph | Orchestration | Durable graphs, cycles, [interrupts for HITL](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| LangChain | Integrations | Embeddings, vector stores, tools, structured outputs |
| Pydantic v2 | Schemas | JD normalization, artifacts, configuration validation |

### Data and AI

| Technology | Role | Why |
|------------|------|-----|
| ChromaDB | Vector store (MVP, local) | Fast iteration; swap behind an interface for production |
| OpenAI-compatible embeddings | Resume and JD embeddings | Ecosystem fit; pin model version for reproducibility |
| Instructor (optional) | Structured extraction | Schema-constrained outputs for JD normalization |

**Production vector alternatives (when constraints appear):**

- **pgvector:** One database for relational data and vectors; transactional semantics.
- **Qdrant:** Hybrid retrieval, filtering, and operational simplicity at scale.

### Job discovery (swappable ingestion)

| Technology | Role | Why |
|------------|------|-----|
| Scrapy | Batch crawling | Mature when static HTML and polite fetch are enough |
| Playwright | Headless browser | JavaScript-heavy career sites and SPAs |
| httpx / aiohttp | HTTP clients | Prefer official APIs and feeds when available |

### Scheduling and background work

| Technology | Role | Why |
|------------|------|-----|
| APScheduler | In-process scheduling | Simple for single-user or single-tenant MVP |
| Celery + Redis | Distributed queues | When you outgrow in-process scheduling |

### Output and tracking

| Technology | Role | Why |
|------------|------|-----|
| Notion API | Application CRM | MCP helps in dev; production should use scoped integration tokens |
| Slack SDK (optional) | Approval notifications | Fast HITL routing |

### Observability and evaluation

| Technology | Role | Why |
|------------|------|-----|
| Ragas | RAG and quality metrics | [Ragas docs](https://docs.ragas.io/) |
| LangSmith (optional) | Tracing and experiments | Pairs well with LangGraph debugging |

## Alternatives Considered

| Category | Recommended | Alternative | Typical reason to defer alternative |
|----------|-------------|-------------|-------------------------------------|
| Orchestration | LangGraph | Pure LangChain chains only | Cycles, HITL, and feedback need a graph |
| Vector DB (MVP) | Chroma | Pinecone, Weaviate | Add managed cost and ops when needed |
| Crawler default | Scrapy plus Playwright | Playwright only | Throughput and cost for static pages |
| Scheduler | APScheduler | Kubernetes CronJob | Match deploy complexity to actual needs |

## Installation (illustrative)

```bash
uv venv && source .venv/bin/activate
uv pip install -U langgraph langchain chromadb pydantic httpx apscheduler ragas
# Optional: scrapy playwright instructor
# playwright install
```

## Sources

- LangGraph overview: https://docs.langchain.com/oss/python/langgraph/overview  
- LangGraph interrupts: https://docs.langchain.com/oss/python/langgraph/interrupts  
- Ragas: https://docs.ragas.io/
