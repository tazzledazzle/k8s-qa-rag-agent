# Integrations (conceptual / pre-implementation)

**Path:** `job-application-pipeline/`  
**Mapped:** 2026-04-14

## External services (planned)

| Integration | Purpose | Notes |
|-------------|---------|-------|
| LLM APIs (OpenAI, Anthropic, Google, etc.) | JD normalization, filtering, deep scoring, resume and letter generation | Route via Intelligence layer; support multiple providers behind one interface |
| Embedding APIs | Resume and JD embeddings | Pin model version; same model for comparable vectors |
| Notion | Application tracker, status fields | REST API for production; MCP for interactive dev workflows |
| Slack (optional) | Approval gates and alerts | Control layer notifications |
| Vector databases | Pinecone, Weaviate, Qdrant, Milvus, pgvector | Swappable Storage layer; Chroma for local dev |

## Data sources for ingestion

| Source type | Examples | Risk / note |
|-------------|----------|---------------|
| Official APIs and job feeds | Partner APIs, RSS | Preferred default |
| Employer career sites | HTML and JSON | May require Playwright for JS rendering |
| User-provided | Paste, upload PDF or HTML | Lowest legal surface for discovery |
| Streaming | Kafka | Enterprise or high-volume ingestion; not required for MVP |

## Auth and secrets

- API keys stored in environment variables or a secrets manager (not in repo).  
- Notion and Slack OAuth or integration tokens scoped to minimum required pages and channels.

## Webhooks and exports

- **Webhook POST** and **S3 / file write** as Output layer options for external systems and backups.  
- Idempotency keys for webhook POSTs to avoid duplicate application records.

## MCP (Model Context Protocol)

- **Notion MCP** and **Google Drive MCP** are valid Output implementations for agent-centric tooling.  
- Document the distinction: MCP for developer workflows versus long-running service credentials for production.

Update this file when first real client modules and credentials handling are implemented.
