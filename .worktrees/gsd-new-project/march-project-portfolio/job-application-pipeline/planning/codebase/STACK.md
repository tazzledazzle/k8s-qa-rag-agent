# Stack (conceptual / pre-implementation)

**Path:** `job-application-pipeline/`  
**Mapped:** 2026-04-14  
**Evidence:** Repository currently contains documentation and planning artifacts only; no application `pyproject.toml` or `package.json` yet. This document reflects the **intended** stack from `.planning/research/STACK.md` and the product README.

## Intended languages and runtime

| Layer | Choice | Status |
|-------|--------|--------|
| Application language | Python 3.12+ | Planned |
| Config and schemas | Pydantic v2 | Planned |
| Orchestration | LangGraph | Planned |
| Integrations | LangChain | Planned |

## Core dependencies (planned)

- **LangGraph:** Stateful graphs, cycles, human-in-the-loop via interrupts.  
- **LangChain:** Vector store adapters, tools, model calls, document loaders.  
- **ChromaDB:** Local vector store for MVP; abstraction behind a storage port for later swap.  
- **Ragas:** Evaluation metrics for retrieval and generation quality.  
- **APScheduler:** In-process scheduling for monitors and batch jobs until a larger queue is justified.

## Optional components by feature

- **Scrapy / Playwright:** Job discovery when not using APIs or manual paste.  
- **httpx:** HTTP client for API-based ingestion.  
- **Instructor:** Structured extraction for JD normalization.  
- **Notion API:** Application tracking (MCP useful in development; API for production automation).

## Configuration

- Environment variables for API keys and database URLs (not yet committed).  
- Layered configuration: per-environment defaults plus optional `config.yaml` or Pydantic settings class when code lands.

## Version pinning strategy

- Pin **embedding model** and **LLM** versions in config for reproducible scores and tiers.  
- Record embedding model ID alongside vectors in storage metadata.

This file should be refreshed after the first committed `pyproject.toml` or `requirements.lock` appears.
