# Testing (planned)

**Path:** `job-application-pipeline/`  
**Mapped:** 2026-04-14  
**Status:** No test suite or CI configuration in this directory yet.

## Target frameworks

- **pytest** for unit and integration tests.  
- **pytest-asyncio** if async HTTP and LangGraph nodes are used.  
- Optional **httpx** mocking for API adapters.

## What to test first (high value)

1. **JD normalization:** Golden files with messy HTML → expected schema instances.  
2. **Tier policy:** Given fixed scores and structured constraints, expected tier and automation flags.  
3. **Retrieval:** Small Chroma or in-memory fixture; assert top-k chunk IDs for a known corpus.  
4. **Control:** Confidence threshold and mock Slack approval paths do not double-send.

## Evaluation and learning

- **Ragas** (or similar) on a **fixed eval set** when changing chunking, embeddings, or retrievers.  
- **Regression checks** on tier distribution when thresholds or models change (smoke test on labeled set).

## Coverage expectations

- Aim for high coverage on **Transform**, **Control**, and **Intelligence** scoring logic.  
- Crawlers and browser automation: integration tests behind markers; run sparingly in CI due to flake and cost.

## CI (planned)

- Lint on every push.  
- Unit tests on every push.  
- Optional nightly or manual job for Playwright-based smoke tests against a staging fixture.

## Manual testing

- HITL flows: pause graph, approve, resume; verify single artifact write to Output.  
- End-to-end dry run: paste JD, run match, generate draft, do not submit.

Add concrete commands (`pytest`, `ruff check`) once `pyproject.toml` exists.
