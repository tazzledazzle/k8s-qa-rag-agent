# GSD Workflow Guide

This project uses Get Shit Done (GSD) planning artifacts under `.planning/`.

## Project Artifacts

- Project context: `.planning/PROJECT.md`
- Workflow config: `.planning/config.json`
- Research: `.planning/research/`
- Scoped requirements: `.planning/REQUIREMENTS.md`
- Execution roadmap: `.planning/ROADMAP.md`
- Project memory/state: `.planning/STATE.md`

## Operating Mode

- Mode: `yolo`
- Granularity: `standard`
- Parallel plans: `true`
- Planning docs committed: `true` (tracked under `.planning/`)
- Workflow agents:
  - Research: enabled
  - Plan check: enabled
  - Verifier: enabled
  - Nyquist validation: enabled

## Recommended Command Flow

**Phase 1:** complete (see `.planning/phases/01-integration-proof/`).

**Phase 2 — Security & boundaries:** complete (see `.planning/phases/02-security-boundaries/`, `02-VERIFICATION.md`).

**Phase 3 — Observability & operations:** complete (see `.planning/phases/03-observability-operations/`, `03-VERIFICATION.md`).

**Phase 4 — Documentation & release:** complete (see `.planning/phases/04-documentation-release/`, `04-VERIFICATION.md`).

**v1 roadmap:** Phases **1–4** transitioned — see `.planning/ROADMAP.md`. Optional v2: `.planning/REQUIREMENTS.md` (PLAT-*, UX-*).

## Project Intent

Build a Kubernetes-native engineering assistant that answers codebase and runbook questions from fresh indexed sources with citations, operational reliability, and permission-aware retrieval.

See `CLAUDE.md` for the same GSD workflow summary (kept in sync for Claude-oriented tooling).
