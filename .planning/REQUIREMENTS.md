# Requirements: k8s-qa-rag-agent

**Defined:** 2026-05-12  
**Core Value:** An engineer gets a cited, trustworthy answer about the current codebase or runbooks within seconds, backed by fresh indexes and observable behavior on Kubernetes.

## v1 Requirements

### Integration & quality

- [x] **E2E-01**: Operator can bring up the stack via `docker-compose` (or documented equivalent) and reach healthy endpoints for indexer, retriever, and QA agent.
- [x] **E2E-02**: Given a seeded repository in the index, a user receives an answer to a natural-language code question that includes at least one correct file path citation.
- [x] **E2E-03**: CI pipeline runs **flake8** (hard-error selectors), **black --check**, **mypy services**, **pytest**, and **docker build** for all four service images on every push to `main` / `develop`, and fails on regressions.

### Security & boundaries

- [x] **SEC-01**: GitHub (or compatible) webhook requests without valid HMAC are rejected without triggering indexing work.
- [x] **SEC-02**: Secrets for LLM and backing stores are referenced via Kubernetes Secrets or compose env files that are not committed as plaintext.
- [x] **SEC-03**: Indexer only clones from an allowlisted set of repository URLs or organizations (documented configuration).

### Observability & operations

- [x] **OBS-01**: QA agent and retriever emit structured logs that include a correlation id per HTTP request.
- [x] **OBS-02**: OpenTelemetry configuration in-cluster matches documented ports/exporters (no broken collector config in prod overlay).
- [x] **OBS-03**: `docs/OPERATIONS.md` describes failure modes (index lag, ES yellow, Qdrant disk pressure) with concrete remediation steps validated once manually.

### Documentation & release

- [x] **DOC-01**: `docs/IMPLEMENTATION.md` execution checklist reflects reality (what is done vs stubbed) after verification pass.
- [x] **DOC-02**: `docs/API.md` includes curl examples for query, retrieve, and reindex endpoints that match running services.
- [x] **REL-01**: Container images for all four services build successfully in CI and use immutable tags or digests in prod overlay examples.

## v2 Requirements

### Platform

- **PLAT-01**: Multi-repository tenancy with per-team ACLs on chunks.
- **PLAT-02**: Helm umbrella chart wrapping subcharts for data stores.

### Experience

- **UX-01**: Web UI for query history and saved searches.
- **UX-02**: Slack or Teams bot integration.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full SaaS billing and org management | Portfolio scope; keep deployment model simple |
| Replacing self-hosted ES with managed-only search | Would change cost/ops story; defer unless required |
| Fine-tuned domain-specific embedding models | Default embeddings sufficient for v1 credibility |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| E2E-01 | Phase 1 | Done |
| E2E-02 | Phase 1 | Done |
| E2E-03 | Phase 1 | Done |
| SEC-01 | Phase 2 | Done |
| SEC-02 | Phase 2 | Done |
| SEC-03 | Phase 2 | Done |
| OBS-01 | Phase 3 | Done |
| OBS-02 | Phase 3 | Done |
| OBS-03 | Phase 3 | Done |
| DOC-01 | Phase 4 | Done |
| DOC-02 | Phase 4 | Done |
| REL-01 | Phase 4 | Done |

**Coverage:**

- v1 requirements: 11 total  
- Mapped to phases: 11  
- Unmapped: 0 ✓

---
*Requirements defined: 2026-05-12*  
*Last updated: 2026-05-15 after Phase 4 verification (`04-VERIFICATION.md`; DOC-01…REL-01 satisfied). All v1 requirements complete.*
