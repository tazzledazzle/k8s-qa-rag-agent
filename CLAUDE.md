# CLAUDE.md — GSD workflow (k8s-qa-rag-agent)

This project uses **Get Shit Done (GSD)** planning under `.planning/`.

## Artifacts

| Artifact | Path |
|----------|------|
| Project context | `.planning/PROJECT.md` |
| Workflow config | `.planning/config.json` |
| Research | `.planning/research/` |
| Requirements | `.planning/REQUIREMENTS.md` |
| Roadmap | `.planning/ROADMAP.md` |
| State | `.planning/STATE.md` |

## Config snapshot

- **Mode:** yolo  
- **Granularity:** standard  
- **Parallel plans:** enabled  
- **Planning docs in git:** yes (`commit_docs: true`)  
- **Workflow agents:** research, plan check, verifier, Nyquist validation — enabled  

## Recommended flow

**Phase 1 (closed):** discuss → plan → execute → verify → **transition** — all complete; see `.planning/phases/01-integration-proof/`.

**Phase 2 (closed):** discuss → plan → execute → verify → **transition** — all complete; see `.planning/phases/02-security-boundaries/` (`02-VERIFICATION.md`).

**Phase 3 (closed):** discuss → plan → execute → verify → **transition** — all complete; see `.planning/phases/03-observability-operations/` (`03-VERIFICATION.md`).

**Phase 4 (closed):** discuss → plan → execute → verify → **transition** — all complete; see `.planning/phases/04-documentation-release/` (`04-VERIFICATION.md`).

**v1 milestone:** All four roadmap phases transitioned (`.planning/ROADMAP.md`). v2 requirements remain optional in `.planning/REQUIREMENTS.md`.

## Cursor note

`AGENTS.md` mirrors this guide for Cursor-specific tooling. Prefer updating both if workflow instructions change.
