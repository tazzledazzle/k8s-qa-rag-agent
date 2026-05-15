# Security: secrets and sensitive configuration

This document lists **sensitive or security-relevant environment variables**, which services consume them, and how **Docker Compose** vs **Kubernetes** supply them. Parity with code is intentional: if something is missing here, treat it as a documentation bug.

For repo URL policy (allowlists, `file://` rules), see the **Indexer allowlist** row below and [docs/LOCAL-DEV.md](LOCAL-DEV.md) / Phase 1 runbook for fixture paths.

## Operator matrix

| Variable | Service(s) | Purpose | Compose source | Kubernetes (base) |
|----------|--------------|---------|----------------|-------------------|
| `OPENAI_API_KEY` | qa-agent | LLM calls for `/ask` | `.env` → `docker-compose.yml` (`${OPENAI_API_KEY:-}`) | `secretKeyRef` → `llm-secrets` / `openai-api-key` (**optional: true** — pod starts; `/ask` fails without a key) |
| `GITHUB_WEBHOOK_SECRET` | git-watcher | HMAC-SHA256 verification of `X-Hub-Signature-256` | `.env` → compose `GITHUB_WEBHOOK_SECRET` | `secretKeyRef` → `github-secrets` / `webhook-secret` (**optional: true** in base) |
| `GITHUB_TOKEN` | indexer | Optional HTTPS token for **private** GitHub clones (`git_client`) | Not set in default `docker-compose.yml`; set in `.env` if needed | **N/A in base** — inject via `env` patch / extra secret if you use private repos in-cluster |
| `QDRANT_API_KEY` | qdrant (server), indexer, retriever | Qdrant HTTP API key when enabled | Compose: `QDRANT_API_KEY` for qdrant; indexer/retriever read same env if you wire it | StatefulSet: `secretKeyRef` → `qdrant-secrets` / `api-key` (**optional: true**). Python clients use env if set |
| `REDIS_PASSWORD` | (reserved) | **Not read** by current Python services; Redis client uses host/port/db only | `.env.example` documents for future / ops consistency | **N/A** — Redis Deployment in base has no auth secret |
| `INDEXER_ALLOWED_GITHUB_ORGS` | indexer, git-watcher | CSV of GitHub org **owners** (lowercase). With `INDEXER_ALLOWED_REPO_URLS`, empty both = permissive for `https://github.com/...` only | `.env` or compose `environment` | Set via ConfigMap/Deployment env patch as needed |
| `INDEXER_ALLOWED_REPO_URLS` | indexer, git-watcher | CSV of repo URLs (normalized to `https://github.com/owner/repo`). Restrictive mode = union logic with orgs (both conditions when both lists set) | same | same |
| `INDEXER_ALLOW_FILE_REMOTES` | indexer only | `1` / `true` / `yes` to allow `file://` indexing | Compose **sets `true`** for indexer; git-watcher **always rejects** `file://` | **Off** unless you explicitly set (avoid in prod) |
| `INDEXER_ALLOWED_FILE_PATH_PREFIXES` | indexer | Comma-separated path prefixes for `file://` URLs (default `/fixtures`) | Compose sets `/fixtures` | Set if you use file remotes in-cluster |

**Indexer note:** The indexer **does not** verify GitHub webhooks; `GITHUB_WEBHOOK_SECRET` was removed from `k8s/base/indexer-deployment.yaml` so manifests match code.

## Misconfiguration risks

- **`optional: true` on `secretKeyRef` (base):** If the Secret or key is missing, the env var is **unset** rather than failing scheduling. For `GITHUB_WEBHOOK_SECRET`, that yields an **empty** secret at runtime: **every signature check fails** (safe default), but misconfiguration can look like “webhooks never work” without a clear crash. For `OPENAI_API_KEY`, `/health` can pass while `/ask` fails at runtime.
- **Prod overlay:** `k8s/overlays/prod` sets `GITHUB_WEBHOOK_SECRET`’s `secretKeyRef.optional` to **`false`** for git-watcher so the Deployment **fails to schedule** if the secret key is absent (**D-07**).

## Allowlist parity (git-watcher vs indexer)

- Both normalize GitHub HTTPS / `git@github.com:` / `owner/repo` shorthand the same way (conceptually aligned with `repo_allowlist.py`).
- **git-watcher** never allows `file://` (webhooks should only carry GitHub HTTPS clone URLs).
- **indexer** enforces `file://` only when `INDEXER_ALLOW_FILE_REMOTES` is enabled and the path is under configured prefixes.

## Auditing manifests

- Prefer **`valueFrom.secretKeyRef`** for secrets; avoid inline secret strings in YAML checked into git.
- Grep for accidental literals, e.g. `sk-` OpenAI-style prefixes, in `docs/` and `k8s/` before release.
