# Phase 2: Security & boundaries — Context

**Gathered:** 2026-05-15  
**Status:** **Transitioned** 2026-05-15 — closed with `02-VERIFICATION.md` per `/gsd-transition 2`; current work is **Phase 3** (see `.planning/STATE.md`).

<domain>

## Phase boundary

Deliver **SEC-01**, **SEC-02**, and **SEC-03** from `.planning/REQUIREMENTS.md`: trustworthy **webhook HMAC** behavior with **negative tests**, **no committed plaintext secrets** with manifests and compose aligned to **Secret / env-file** patterns, and **indexer allowlisting** for clone sources (plus documented operator configuration).

Phase 2 does **not** implement correlation IDs (**OBS-01**), OTEL validation (**OBS-02**), runbook drills (**OBS-03**), IMPLEMENTATION/API doc truth (**DOC-01**, **DOC-02**), or image digest policy (**REL-01**) — those are Phases 3–4.

**Trust boundary note:** **SEC-01** applies to the **GitHub → git-watcher** edge. Direct **`POST /index`** on the indexer remains a separate trust surface (internal network / API gateway in real deployments). Phase 2 may document that split; optional indexer auth is **out of scope** unless explicitly pulled into a plan task.

</domain>

<decisions>

## Implementation decisions

### SEC-01 — Webhook HMAC (git-watcher)

- **D-01:** Treat existing behavior as the baseline: **`GithubSignatureVerifier`** uses **HmacSHA256**, **`sha256=`** prefix, hex decode, **`MessageDigest.isEqual`** for MAC compare; **`X-Hub-Signature-256`** required when secret is non-empty; empty **`GITHUB_WEBHOOK_SECRET`** ⇒ verification **fails** (no bypass).
- **D-02:** **`post("/webhook")`** must **not** call **`IndexerClient.triggerIndex`** until signature verification **passes** and event is **`push`** (already true in `GitWatcherApp.kt` — preserve under refactors).
- **D-03:** Add **automated negative tests** (Kotlin/JUnit in `services/git-watcher/`) covering at minimum: **missing** header, **malformed** `sha256=` value, **wrong MAC** for valid payload, **wrong secret** vs good signature, optional **replay/tampered body** (body byte change ⇒ MAC failure). Assert **HTTP 401** (or project-consistent code) and **no** indexer HTTP client invocation (mock `HttpClient` / stub `IndexerClient`).
- **D-04:** Document **GitHub Enterprise / compatible** senders: same **`X-Hub-Signature-256`** contract; if compatibility shims are needed, isolate behind a single verifier module.
- **D-05 (Claude’s discretion):** Whether **`IndexerClient`** failures should change HTTP response from **200 accepted** (today exceptions are caught and printed); default Phase 2 focus stays **SEC-01** signature path unless a plan task explicitly tightens error handling.

### SEC-02 — Secrets posture (repo + k8s + compose)

- **D-06:** Produce a **short inventory** (table or `docs/SECURITY-SECRETS.md`): each secret name, which service consumes it, **K8s Secret** name/key reference, and compose **env-file** / variable name. Cover at minimum: **`OPENAI_API_KEY`**, **`GITHUB_WEBHOOK_SECRET`**, **`GITHUB_TOKEN`** (indexer clone), **Qdrant API key** if used, **Redis** password if used.
- **D-07:** **Kubernetes:** sample manifests under `k8s/` must use **`valueFrom.secretKeyRef`** (or equivalent) for sensitive values — **no** literal API keys in YAML committed to this repo. If **`optional: true`** appears for webhook secret, document risk; **prod overlay** should prefer **required** secrets where operators agree (defer exact overlay diff to plan-phase).
- **D-08:** **Compose / local:** keep using **`.env`** (gitignored) per `.env.example`; README / LOCAL-DEV already warn not to commit `.env` — reinforce in inventory doc.
- **D-09:** Grep-driven hygiene: no `sk-` / example JWT blobs in docs; scrub or redact any copy-paste examples that look like real credentials.

### SEC-03 — Indexer clone allowlist

- **D-10:** Enforce allowlist in **`POST /index`** (`services/indexer/main.py` / `GitClient` boundary **before** network clone): normalize **`repo_url`** to a canonical form (reuse / align with `GitClient` GitHub normalization rules).
- **D-11:** Configuration via environment (names finalized in plan-phase), e.g. comma-separated **`INDEXER_ALLOWED_GITHUB_ORGS`** and/or **`INDEXER_ALLOWED_REPO_URLS`** (exact HTTPS URLs). **Empty list** in **production-oriented** defaults ⇒ **deny all** GitHub HTTPS clones **or** explicitly documented “open dev” mode — pick one default and document in the same PR that adds enforcement (breaking change for unrestricted dev is acceptable if documented).
- **D-12:** **`file://`** remotes (Phase 1 fixture path): **default allow only when** an explicit flag such as **`INDEXER_ALLOW_FILE_REMOTES=true`** is set **and** path matches an optional prefix allowlist (e.g. `/fixtures/` only in compose). **Production default:** **deny** `file://` unless plan-phase chooses otherwise.
- **D-13:** **Git-watcher** should validate **`payload.repository.clone_url`** against the **same policy** before calling the indexer (**defense in depth**), sharing rules via documented env parity or a tiny shared spec in docs (no cross-language shared library required in Phase 2).
- **D-14 (Claude’s discretion):** Whether **`batch_index`** / CronJob path reads allowlist from the same env as HTTP `/index` (recommended: single code path helper).

</decisions>

<canonical_refs>

## Canonical references

**Downstream agents MUST read these before planning or implementing.**

### Requirements & vision

- `.planning/REQUIREMENTS.md` — **SEC-01 … SEC-03**
- `.planning/ROADMAP.md` — Phase 2 success criteria and plans **02-01**, **02-02**
- `.planning/PROJECT.md` — security items still under **Active**
- `docs/DESIGN.md` — security model and threat assumptions

### Prior phase

- `.planning/phases/01-integration-proof/01-VERIFICATION.md` — Phase 1 closure evidence

### Pitfalls

- `.planning/research/PITFALLS.md` — webhook abuse, SSRF on repo URLs (allowlist mitigates)

</canonical_refs>

<code_context>

## Existing code insights

### Git watcher (`services/git-watcher/`)

- **`GitWatcherApp.kt`**: reads **`GITHUB_WEBHOOK_SECRET`**, verifies **`X-Hub-Signature-256`**, ignores non-**`push`** events, parses **`PushPayload`**, calls **`IndexerClient.triggerIndex(clone_url, branch)`**.
- **`GithubSignatureVerifier.kt`**: HMAC-SHA256 implementation suitable for unit testing in isolation.
- **`IndexerClient.kt`**: HTTP **POST** to indexer **`/index`** with JSON body; exceptions caught in route handler today (stdout only).

### Indexer (`services/indexer/`)

- **`main.py` `index_repo`**: accepts any **`IndexRequest.repo_url`** supported by **`GitClient`** (GitHub + **`file://`** from Phase 1) — **no allowlist yet**.
- **`git_client.py`**: GitHub URL normalization and **`file://`** clone path.

### Kubernetes (`k8s/base/`)

- **`qa-agent-deployment.yaml`**: **`OPENAI_API_KEY`** from **`secretKeyRef`** (`llm-secrets`).
- **`git-watcher-deployment.yaml`**: **`GITHUB_WEBHOOK_SECRET`** from **`github-secrets`**, **`optional: true`** on the ref.
- **Indexer** deployment references secrets for webhook-related env (verify in plan-phase for full SEC-02 inventory).

### Compose / env

- **`.env.example`**: documents **`OPENAI_API_KEY`**, **`GITHUB_WEBHOOK_SECRET`**, **`GITHUB_REPOS`** (not yet wired to allowlist enforcement).

</code_context>

<specifics>

## Specific ideas

- Add **`docs/SECURITY-SECRETS.md`** as the SEC-02 deliverable anchor (link from README “Security” one-liner).
- For SEC-03 tests in Python: table-driven cases for allowed vs denied URLs including **`file://`** when flag off/on.
- Consider **`deny`** by default for unknown GitHub org when **`INDEXER_ALLOWED_*`** is set to non-empty; when unset, document “permissive dev” explicitly to satisfy “documented configuration.”

</specifics>

<deferred>

## Deferred ideas

- **mTLS / NetworkPolicy** between git-watcher and indexer — platform layer; not SEC-01 wording.
- **Signed internal requests** to **`/index`** — future hardening if indexer is exposed beyond cluster.
- **Full SSRF audit** beyond Git clone URLs — later security pass.
- **Secrets rotation / ExternalSecrets** — ops enhancement, not Phase 2 minimum.

</deferred>

---

*Phase: 2 — Security & boundaries*  
*Context gathered: 2026-05-15*
