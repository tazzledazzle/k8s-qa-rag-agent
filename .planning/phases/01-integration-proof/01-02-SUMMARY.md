# Plan 01-02 summary — Query path & citations

**Executed:** 2026-05-15  
**Requirements:** E2E-02

## Delivered

- `services/qa_agent/agent.py` — `citations_from_tool_messages()` parses retriever JSON from `ToolMessage` bodies into `AskResponse.citations` (deduped by file + line span).
- `docs/PHASE1-RUNBOOK.md` — numbered `curl` steps: `POST /index` with `file:///fixtures/sample-repo`, `POST /ask`, citation checks; documents CI does not require `OPENAI_API_KEY`.
- `tests/test_citations_from_tools.py` — unit tests for citation extraction.
- `tests/test_integration_compose_optional.py` — `@pytest.mark.integration` health check when `RUN_COMPOSE_INTEGRATION=1`.

## Verification

- `pytest tests/` — citation unit tests pass; integration test skipped by default.

## Not done (explicit)

- Optional **`e2e-llm` GitHub Actions job** (compose + OpenAI) — omitted to avoid long/flaky default CI; runbook remains source of truth for LLM path.
