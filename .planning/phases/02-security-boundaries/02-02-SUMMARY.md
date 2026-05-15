# Plan 02-02 summary — Secrets inventory + indexer SEC-03

**Executed:** 2026-05-15  
**Requirements:** SEC-02, SEC-03 (indexer / batch)

## Decisions

- **Indexer manifest:** Removed unused `GITHUB_WEBHOOK_SECRET` from `k8s/base/indexer-deployment.yaml` so Kubernetes matches what the indexer reads.
- **Prod webhook secret:** `k8s/overlays/prod` JSON6902 patch sets `secretKeyRef.optional` to **`false`** for git-watcher so a missing secret fails scheduling instead of silently rejecting every webhook.
- **Local compose:** Indexer gets `INDEXER_ALLOW_FILE_REMOTES=true` and `INDEXER_ALLOWED_FILE_PATH_PREFIXES=/fixtures` so Phase 1 `file:///fixtures/...` flows keep working.

## Delivered

- `docs/SECURITY-SECRETS.md` — operator matrix (OpenAI, GitHub webhook, `GITHUB_TOKEN`, Qdrant, Redis password note, allowlist envs); README link under Configuration.
- `services/indexer/repo_allowlist.py` — case-insensitive `git@github.com:` normalization; `assert_repo_url_allowed` / HTTP + batch integration (from wave 1).
- `tests/test_repo_allowlist.py` — table-style pytest with `monkeypatch`.
- `.env.example` — `GITHUB_TOKEN` + allowlist variables documented.
- `.github/workflows/ci.yml` — **`git-watcher`** job runs `gradle test` in `services/git-watcher/`; `build` depends on it.

## Verification

- `pytest tests/test_repo_allowlist.py -v`
- `kubectl kustomize k8s/overlays/prod` (JSON patch applies cleanly)
- `rg` pass for suspicious `sk-` literals in `k8s/` and `docs/` (human spot-check per plan).
