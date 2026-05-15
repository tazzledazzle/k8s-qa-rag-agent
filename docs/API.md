# HTTP API reference

## Prerequisites

- **Stack running:** from repo root, `docker compose up --build` (see [LOCAL-DEV.md](LOCAL-DEV.md) for ports **8000–8003**).
- **`POST /index`:** for **private** GitHub repos, set **`GITHUB_TOKEN`** (see [SECURITY-SECRETS.md](SECURITY-SECRETS.md)). Public repos work without it.
- **`POST /ask`:** a successful answer requires **`OPENAI_API_KEY`**; without it (or on LLM/retriever errors) the QA agent returns **HTTP 502** with a JSON error body — do not assume **200** for the curl examples below unless the key is set.
- **OpenAPI:** Python services expose **`/docs`** and **`/openapi.json`** on their respective ports.

Base URLs in the sections below use **localhost** and **compose** ports. For **Kubernetes** DNS and in-cluster URLs, see [Kubernetes (cluster DNS)](#kubernetes-cluster-dns).

---

## Indexer (port 8000)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Qdrant and Elasticsearch connectivity |
| POST | `/index` | Clone/update repo, chunk, embed, upsert Qdrant + ES |

**Index body (JSON)** — matches `services/indexer/models.py` **`IndexRequest`**:

```json
{
  "repo_url": "https://github.com/org/repo",
  "branch": "main",
  "include_patterns": null,
  "exclude_patterns": null
}
```

- **`branch`** defaults to **`"main"`** if omitted.
- **`include_patterns`** / **`exclude_patterns`** are optional lists of glob strings.

**Example:**

```bash
curl -s -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/octocat/Hello-World","branch":"master"}'
```

Interactive docs: `http://localhost:8000/docs`

---

## Retriever (port 8001)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Qdrant, Elasticsearch, Redis |
| POST | `/search` | Hybrid dense + BM25, dedup, rerank, cache |

**Search body** — matches `services/retriever/models.py` **`SearchRequest`**:

```json
{ "query": "how is auth handled?", "language": null }
```

- **`query`** is required (min length 1).
- **`language`** is optional (cache / filter hint).

**Example:**

```bash
curl -s -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query":"deployment","language":null}'
```

---

## QA Agent (port 8002)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness (**200** JSON; does not call OpenAI) |
| POST | `/ask` | LangGraph ReAct agent using retriever tools |

**Ask body** — matches `services/qa_agent/models.py` **`AskRequest`**:

```json
{ "question": "Where is the retriever cache configured?", "session_id": null }
```

- **`question`** is required (min length 1).
- **`session_id`** is optional.

**Example (requires `OPENAI_API_KEY` for success):**

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8002/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Summarize the retriever flow"}'
```

**Responses:** **200** with `AskResponse` JSON (`answer`, `citations`) on success; **502** if the agent or LLM path fails (missing key, retriever error, etc.). **`GET /health`** remains the lightweight check when OpenAI is unavailable.

---

## Git Watcher (port 8003)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Plain text `ok` |
| POST | `/webhook` | GitHub-compatible webhook; **`push`** events trigger indexer |

**Headers (typical GitHub delivery):**

| Header | Purpose |
|--------|---------|
| **`X-Hub-Signature-256`** | HMAC-SHA256 of the raw body; required for accepted pushes (see [SECURITY-SECRETS.md](SECURITY-SECRETS.md) for **`GITHUB_WEBHOOK_SECRET`**) |
| **`X-GitHub-Event`** | Event type; **`push`** is processed; other events (e.g. **`ping`**) are acknowledged without indexing |

Configure GitHub to send JSON payloads with a secret matching **`GITHUB_WEBHOOK_SECRET`**. Do not paste real secrets into docs or shell history.

---

## Kubernetes (cluster DNS)

Compose examples above use **`http://localhost:<port>`**. In-cluster, use **Kubernetes Service** hostnames (namespace **`rag-system`** in base manifests). Examples:

```bash
# From a debug pod in the same namespace (illustrative)
curl -sS "http://indexer-service:8000/health"
curl -sS "http://retriever-service:8001/health"
curl -sS "http://qa-agent-service:8002/health"
```

Full DNS names and wiring are summarized under **Configuration** in [README.md](../README.md).

---

## OpenAPI

FastAPI services expose OpenAPI at **`/docs`** and **`/openapi.json`** on ports **8000**, **8001**, and **8002** respectively.
