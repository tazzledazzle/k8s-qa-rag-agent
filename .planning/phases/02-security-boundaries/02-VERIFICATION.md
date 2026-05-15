---
phase: 02-security-boundaries
verified: 2026-05-15T12:00:00Z
status: passed
notes: "Docker image builds not re-run on verifier host; same contract as Phase 1 — trust CI `build` job or run four `docker build` lines locally."
---

# Phase 2: Security & boundaries — Verification report

**Phase goal:** Satisfy **SEC-01**, **SEC-02**, **SEC-03** (`.planning/REQUIREMENTS.md`) — webhook HMAC trust, secrets inventory + manifest/compose alignment, indexer (and batch) clone allowlists with documented env parity on git-watcher.

**Verified:** 2026-05-15 (local agent run)  
**Status:** **passed** (automated + static review)

## Requirements coverage

| Requirement | Status | Evidence |
|---------------|--------|----------|
| **SEC-01** | ✓ SATISFIED | `GithubSignatureVerifier` + `GitWatcherApp` verify `X-Hub-Signature-256` before any `IndexTrigger`; non-`push` returns 202 ignored without trigger. **Kotlin:** `GithubSignatureVerifierTest` (7 cases), `WebhookRouteTest` — missing/wrong signature → **401** and **no** trigger; valid push → trigger once; allowlist deny → **403** without trigger (`services/git-watcher/src/test/kotlin/...`). |
| **SEC-02** | ✓ SATISFIED | `docs/SECURITY-SECRETS.md` — matrix for `OPENAI_API_KEY`, `GITHUB_WEBHOOK_SECRET`, `GITHUB_TOKEN`, `QDRANT_API_KEY`, Redis password note, allowlist envs; Compose vs `secretKeyRef`; **D-07** (`optional: true` risks + prod patch). `README.md` links inventory under Configuration. `k8s/base/indexer-deployment.yaml` has **no** `GITHUB_WEBHOOK_SECRET` (removed — indexer does not read it). Sample manifests use `valueFrom.secretKeyRef` for secrets (spot-checked base Deployments / Qdrant). `rg` for `sk-[A-Za-z0-9]{10,}` on `k8s/`, `docs/`, `.planning/phases/02-security-boundaries/` — **no hits**. |
| **SEC-03** | ✓ SATISFIED | `services/indexer/repo_allowlist.py` — `assert_repo_url_allowed` / `is_repo_url_allowed`; **`main.py`** calls guard before index (**403** on `ValueError`); **`batch_index.py`** same helper before clone. **`file://`** gated by `INDEXER_ALLOW_FILE_REMOTES` + path prefixes; compose sets allow for `/fixtures`. **Defense in depth:** `services/git-watcher/.../RepoAllowlist.kt` + route check before trigger. **Python:** `tests/test_repo_allowlist.py` (12 tests). |

**Coverage:** 3/3 Phase 2 requirements satisfied per evidence above.

## ROADMAP success criteria (Phase 2)

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Invalid signatures never enqueue indexing work (negative tests) | ✓ | `WebhookRouteTest` + `GithubSignatureVerifierTest`; injectable `IndexTrigger` stub proves no call on 401 paths |
| 2 | No plaintext secrets in repo; manifests use Secret references | ✓ | Inventory doc + k8s grep; no `sk-` literals in audited paths |
| 3 | Allowed-repo configuration documented and enforced | ✓ | `SECURITY-SECRETS.md`, `.env.example`, `repo_allowlist.py` + tests, Kotlin `RepoAllowlist` |

## Prod overlay spot-check

- `kubectl kustomize k8s/overlays/prod` succeeds (deprecation warnings from Kustomize schema only).
- Rendered **git-watcher** `GITHUB_WEBHOOK_SECRET` → `secretKeyRef.optional: **false**` (prod hardening per **02-02**).

## Automated commands (this verification)

```text
python3 -m pytest tests/ -q          # 18 passed, 1 skipped
python3 -m flake8 services tests --count --select=E9,F63,F7,F82 --statistics   # 0 errors
python3 -m black --check services tests   # OK
python3 -m mypy services             # Success: no issues found (25 source files)
cd services/git-watcher && gradle test --no-daemon --rerun-tasks   # BUILD SUCCESSFUL; 18 JVM tests (7+5+6)
kubectl kustomize k8s/overlays/prod >/dev/null   # OK
rg -n "sk-[A-Za-z0-9]{10,}" k8s docs .planning/phases/02-security-boundaries   # no matches (exit 1 = no hits)
```

## Environment gaps (non-blocking for “passed”)

| Check | Result | Follow-up |
|-------|--------|-----------|
| `docker build` ×4 (CI `build` job) | **Not re-run** this session | Same as Phase 1: run locally or rely on GitHub Actions after push. |
| Live webhook against running git-watcher | **Not run** | Unit/integration tests cover contract; optional manual GitHub “Redeliver” against a test hook. |

## Artifacts checklist (Phase 2 deliverables)

| Artifact | Status |
|----------|--------|
| `docs/SECURITY-SECRETS.md` | ✓ |
| `services/indexer/repo_allowlist.py` + `tests/test_repo_allowlist.py` | ✓ |
| `services/git-watcher/` — `RepoAllowlist.kt`, `IndexTrigger.kt`, tests, `GitWatcherApp.kt` wiring | ✓ |
| `02-01-SUMMARY.md`, `02-02-SUMMARY.md` | ✓ |
| `.github/workflows/ci.yml` — `git-watcher` Gradle job | ✓ |
| `docker-compose.yml` indexer `INDEXER_ALLOW_FILE_REMOTES` / path prefixes | ✓ |
| `k8s/overlays/prod` webhook `optional: false` patch | ✓ |

## Gaps summary

No **code** or **documentation** gaps identified for Phase 2 scope. **Runtime** Docker image builds were not repeated here; align with CI or local builds when the daemon is available.

## Verification metadata

**Approach:** Goal-backward against `.planning/REQUIREMENTS.md` SEC-01…SEC-03 + `.planning/ROADMAP.md` Phase 2 success criteria + `02-CONTEXT.md` decisions **D-01…D-14** (in-scope items).  
**Automated checks:** Command block above.  
**Human checks suggested:** Optional end-to-end webhook delivery to a dev ingress with a real secret rotation drill.

---
*Verified: 2026-05-15*  
*Phase transitioned: 2026-05-15 (`/gsd-transition 2`)*
