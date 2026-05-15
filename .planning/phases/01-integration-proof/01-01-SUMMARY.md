# Plan 01-01 summary — Integration smoke & fixture

**Executed:** 2026-05-15  
**Requirements:** E2E-01

## Delivered

- `tests/fixtures/sample-repo/` — minimal Python module with `phase1_verification_answer` and `bootstrap.sh` to create `main` branch git metadata locally.
- `services/indexer/git_client.py` — `file:///absolute/path` remotes clone into cache under `cache_dir/file/<hash>/`; GitHub behavior unchanged.
- `docker-compose.yml` — read-only mount `./tests/fixtures/sample-repo` → `/fixtures/sample-repo` on **indexer**.
- `scripts/smoke_compose.sh` — waits for Qdrant, ES, Redis (`docker compose exec`), curls `/health` on ports **8000–8003**; runs fixture bootstrap idempotently.
- `docs/LOCAL-DEV.md` — contributor bring-up; README links to it and the runbook.

## Verification

- `pytest tests/` (includes `test_git_client_file_url.py`).
- Manual: `docker compose up -d` then `bash scripts/smoke_compose.sh` (not run in this session).

## Follow-ups

- Optional compose-smoke CI job deferred (runner time / ES flake); see `01-03-SUMMARY.md`.
