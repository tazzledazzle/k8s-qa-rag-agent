# Phase 4: Documentation & release — Context

**Gathered:** 2026-05-15  
**Status:** Transitioned **2026-05-15** — **`04-VERIFICATION.md`** (**passed**); v1 roadmap complete.

<domain>

## Phase boundary

Deliver **DOC-01**, **DOC-02**, and **REL-01** from `.planning/REQUIREMENTS.md`:

- **DOC-01:** `docs/IMPLEMENTATION.md` **execution checklist** reflects **verified reality** (what is implemented vs aspirational / historical), after a verification-oriented pass — not marketing copy.
- **DOC-02:** `docs/API.md` includes **curl** (or equivalent) examples for **query** (`POST /ask`), **retrieve** (`POST /search`), and **reindex** (`POST /index`) that match **running** services (compose ports, JSON field names, required vs optional fields, realistic responses or documented failure modes).
- **REL-01:** All **four** service container images **build in CI** (already true in `.github/workflows/ci.yml` **`build`** job); **prod overlay** (or linked release doc) documents **immutable tags or digests** policy — today **`kustomization.yaml`** `images:` entries still use **`latest`** for app images in **base**; **prod** overlay does **not** yet pin `newTag` to SHA/semver for `qa-agent` / `retriever` / `indexer` / `git-watcher` (collector is pinned separately in `qa-agent-deployment.yaml`).

Phase 4 does **not** mandate Helm charts, managed registry automation, semantic-release bots, or **TROUBLESHOOTING.md** unless a plan explicitly pulls them in. **OpenAPI** may stay **served by FastAPI** (`/openapi.json`); optional follow-up is a **checked-in** artifact only if plan-phase proves maintainability.

**Minimum doc scope:** **`docs/IMPLEMENTATION.md`**, **`docs/API.md`**, and **one** concise **release / image strategy** surface (`README.md` subsection, `docs/RELEASE.md`, or `docs/SECURITY-SECRETS.md` cross-link + prod overlay comments) sufficient for **REL-01** closure if verifier can trace policy end-to-end.

</domain>

<decisions>

## Implementation decisions (for plan-phase)

### DOC-01 — IMPLEMENTATION.md truth

- **D-01:** Add a **short “Current status (verified)”** section **above** the legacy “Days 1–14 / Phase 0–6” narrative **or** replace the **Execution Checklist** / success-metrics tables with a **single GSD-aligned matrix**: rows = major capabilities (indexer, retriever, qa-agent, git-watcher, k8s base, CI, observability); columns = **Done / Partial / Not in v1** with pointer to tests or `NN-VERIFICATION.md`.
- **D-02:** The historical **Phase 6** bullets in `IMPLEMENTATION.md` that claim **`OPERATIONS.md` / `API.md` “→ Phase 6”** are **false** relative to repo today — **OPERATIONS.md** and **API.md** **exist** and evolved in Phases 1–3. Plan-phase must **reconcile** (strike-through, archive note, or delete redundant lines) so readers are not misled.
- **D-03:** **`TROUBLESHOOTING.md`** and **“Helm optional”** remain **out of scope** unless explicitly added to **04-01** scope with owner and acceptance test.

### DOC-02 — API.md alignment

- **D-04:** **Canonical ports** for examples: **8000** indexer, **8001** retriever, **8002** qa-agent, **8003** git-watcher — must match **`docker-compose.yml`** and **`docs/LOCAL-DEV.md`**. Any **Kubernetes** DNS names belong in a **short subsection** or cross-link to **`README.md`**, not mixed into compose examples without labels.
- **D-05:** **Bodies** must match **Pydantic** models in code (e.g. `AskRequest.question`, optional `session_id`; `SearchRequest.query`, optional `language`; `IndexRequest.repo_url`, `branch`, optional glob lists). Plan-phase should run **`curl`** against **`docker compose`** (or document “verified from OpenAPI export on commit SHA …”) and capture **expected HTTP status** for minimal calls (`/health` always; `/ask` may **502** without `OPENAI_API_KEY` — document honestly).
- **D-06:** **Git watcher:** document **`POST /webhook`** headers (`X-Hub-Signature-256`, `X-GitHub-Event`) and that **non-push** events are ignored — align with **`docs/SECURITY-SECRETS.md`** without duplicating secret values.

### REL-01 — Image builds + prod posture

- **D-07:** **CI evidence:** **`build`** job already builds four Dockerfiles — **04-02** verification should cite workflow lines + optional local **`docker build`** parity. No change strictly required if documentation states the contract clearly.
- **D-08:** **Prod tagging policy (minimum):** document how operators should set image references (e.g. **CI-produced digest** or **`${GITHUB_SHA}`** pattern) and, if code changes are in scope, add **`images:`** entries to **`k8s/overlays/prod/kustomization.yaml`** for **`qa-agent`**, **`retriever`**, **`indexer`**, **`git-watcher`** with **`newTag`** placeholder or **commented example** — **or** document **external** image updater (Flux, CD) as the source of truth. **REL-01** closes when **verifier** can answer: “What tag do I put in prod and where?”
- **D-09:** **Qdrant** upstream image **`qdrant/qdrant:latest`** in base is a **known drift risk** — either pin in **prod** overlay with rationale or document “portfolio dev default” explicitly in **REL** doc.

</decisions>

<canonical_refs>

## Canonical references

**Downstream agents MUST read these before planning or implementing.**

### Requirements & vision

- `.planning/REQUIREMENTS.md` — **DOC-01**, **DOC-02**, **REL-01**
- `.planning/ROADMAP.md` — Phase 4 success criteria; plans **04-01**, **04-02**
- `.planning/STATE.md` — current phase pointer

### Prior verification (truth sources)

- `.planning/phases/03-observability-operations/03-VERIFICATION.md` — observability + ops baseline
- `.planning/phases/02-security-boundaries/02-VERIFICATION.md` — webhook + secrets
- `.planning/phases/01-integration-proof/01-VERIFICATION.md` — CI + smoke baseline

### Live docs & config

- `docs/IMPLEMENTATION.md` — legacy phased roadmap + stale checklist (DOC-01 target)
- `docs/API.md` — HTTP tables + curl (DOC-02 target)
- `docs/LOCAL-DEV.md`, `README.md` — ports and compose vs k8s discovery
- `docs/OPERATIONS.md`, `docs/SECURITY-SECRETS.md` — cross-links for webhook / secrets language in API doc
- `.github/workflows/ci.yml` — **`test`**, **`otel-config`**, **`git-watcher`**, **`build`**
- `k8s/base/kustomization.yaml` — `images:` **latest** for four apps
- `k8s/overlays/prod/kustomization.yaml` — replicas, HPA, PDB, CPU patches; **no** app image pin block today

### Code (request shapes)

- `services/indexer/models.py` — **`IndexRequest`**
- `services/retriever/models.py` — **`SearchRequest`**
- `services/qa_agent/models.py` — **`AskRequest`**, **`AskResponse`**

</canonical_refs>

<code_context>

## Existing doc / code gaps (evidence)

### `docs/IMPLEMENTATION.md`

- Still framed as **14-day phased build** with **unchecked** “Execution Checklist” (Phases 1–6, docker-compose, CI) despite **Phases 1–3 GSD** completion and substantial implementation.
- **Phase 6** section lists **`OPERATIONS.md`**, **`API.md`** as unchecked / “Phase 6” even though both files exist and **OPERATIONS** was expanded for **OBS-03**.
- **Success Metrics** table marks Phases 1–6 as **→** (in progress) — contradicts indexer/retriever/qa-agent code presence and **pytest** coverage.

### `docs/API.md`

- Generally aligned on **paths** and **ports** with compose.
- **Risk:** Examples assume **happy-path** **`/ask`** without stating **502** / LLM dependency; optional fields may drift from Pydantic defaults over time without a mechanical check.
- **OpenAPI:** states FastAPI exposes **`/openapi.json`** — true; no committed frozen OpenAPI bundle today.

### Release / Kustomize

- **Base** `images:` uses **`newTag: latest`** for all four built services.
- **Prod** overlay **does not** override those image tags to immutable references (**REL-01** gap vs requirement wording).
- **OTEL collector** image is **pinned** in `k8s/base/qa-agent-deployment.yaml` (**0.99.0**) — good precedent for **D-08/D-09** narrative.

</code_context>

<specifics>

## Specific ideas (for plan-phase)

### 04-01 — Documentation sync + OpenAPI/curl alignment

- Rewrite **top** of **`IMPLEMENTATION.md`** with **verified** matrix + link to **`04-VERIFICATION.md`** after **`/gsd-verify-phase 4`**.
- Sweep **`API.md`**: add **Prerequisites** (compose up, env vars), **failure notes** for `/ask`, optional **`kubectl` port-forward** variant for one endpoint.
- Optional: small script **`scripts/export_openapi.sh`** (curl four `/openapi.json` URLs) — only if **04-01** wants machine-generated drift detection.

### 04-02 — Image build matrix + tagging doc

- Add **`docs/RELEASE.md`** (or README section **“Images & prod”**): table of **Dockerfile paths**, **CI job**, recommended **`kustomize edit set image`** or **`images:`** patch for prod.
- If implementing code-side **REL-01**: **`k8s/overlays/prod/kustomization.yaml`** `images:` block with **`newName`/`newTag`** pattern documented; consider **Qdrant** pin.

</specifics>

<deferred>

## Deferred (not Phase 4 minimum)

- Full **Helm** chart for the stack
- **TROUBLESHOOTING.md** unless explicitly scheduled
- **Auto-publish** of docs site (MkDocs, GitHub Pages)
- **SBOM** / **Cosign** signing for images

</deferred>
