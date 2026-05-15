# Phase 1 — Query path proof (E2E-02)

Prerequisites: [LOCAL-DEV.md](LOCAL-DEV.md) (compose up, fixture `bootstrap.sh`, optional `OPENAI_API_KEY` for `/ask`).

Indexer inside compose mounts the fixture at **`/fixtures/sample-repo`** (read-only). Use branch **`main`**.

## 1. Index the fixture

```bash
curl -sS -X POST "http://127.0.0.1:8000/index" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "file:///fixtures/sample-repo",
    "branch": "main"
  }' | jq .
```

Expect `"status": "ok"` and `chunks_indexed` > 0. First indexer boot loads the embedding model and can take several minutes.

## 2. Ask the QA agent

Use a question that forces retrieval against the fixture (requires **`OPENAI_API_KEY`** for the LLM):

```bash
export OPENAI_API_KEY="${OPENAI_API_KEY:?set OPENAI_API_KEY}"
curl -sS -X POST "http://127.0.0.1:8002/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What does phase1_verification_answer return in sample_module.py?"}' | jq .
```

## 3. Verify citation

In the JSON response:

- **`answer`** should mention the return value **42** (or the function’s purpose).
- **`citations`** should include at least one object whose **`file_path`** contains **`sample_module.py`** (paths may be relative to the cloned repo).

If `citations` is empty but the answer cites the file in prose, re-run after confirming the agent called `search_codebase` (check indexer/retriever logs); citation extraction reads retriever JSON from tool messages.

## CI note

Pull-request CI does **not** require `OPENAI_API_KEY`. Full LLM path proof is **manual** (this runbook) unless you add an optional workflow job with a repository secret.
