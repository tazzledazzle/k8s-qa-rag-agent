# Plan 01-03 summary — CI honesty

**Executed:** 2026-05-15  
**Requirements:** E2E-03

## Decisions

- **Mypy Path A:** Fixed eight reported issues (redis payload typing, tree-sitter legacy stubs, Qdrant `search` stub gap, retriever JSON cast, ES bulk error typing, `ChatOpenAI` + `SecretStr` for API key). **`mypy services` is now required** in CI — removed `|| true`.
- **Compose-smoke CI:** Not added; would add ~minutes of ES startup per PR on ubuntu-latest. Local `scripts/smoke_compose.sh` + runbook cover proof.

## Delivered

- `.github/workflows/ci.yml` — blocking `mypy services`; `black --check` includes **`tests/`**.
- `.planning/REQUIREMENTS.md` — E2E-03 text lists flake8, black, mypy, pytest, docker builds explicitly.

## Verification

- `mypy services`, `black --check services tests`, `pytest tests/`, flake8 hard selectors — all pass locally.
