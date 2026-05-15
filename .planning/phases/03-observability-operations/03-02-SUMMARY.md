# Plan 03-02 summary — OBS-02 / OBS-03 (OTEL collector + ops)

**Executed:** 2026-05-15  
**Requirements:** OBS-02, OBS-03

## Decisions

- **Collector config:** OTLP in → **batch** → **logging** exporter only (no OTLP loop to localhost). Mirrors: `k8s/base/configmap-otel.yaml` and `scripts/otel/otel-collector-config.yaml`.
- **Sidecar:** `otel/opentelemetry-collector-k8s:0.99.0` with explicit `--config`, ConfigMap volume mount; QA agent uses **`http://127.0.0.1:4317`** + `OTEL_SERVICE_NAME=qa-agent`.
- **CI:** `otel-config` job runs `scripts/validate-otel-config.sh` (Docker `validate` on the mirror file).
- **Spans:** `correlation_id` added as a span attribute via `FastAPIInstrumentor` `server_request_hook` when OTEL is enabled.

## Delivered

- `k8s/base/configmap-otel.yaml`, `scripts/otel/otel-collector-config.yaml`, `scripts/validate-otel-config.sh`
- `k8s/base/qa-agent-deployment.yaml` — volumes, sidecar args, OTEL env, **ClusterIP Service** for qa-agent (aligned with retriever manifest pattern)
- `.github/workflows/ci.yml` — `otel-config` job; `build` depends on it
- `docs/OPERATIONS.md` — correlation, OTEL env table, index lag / ES yellow / Qdrant disk, runbook checklist (**Validated**: `Not run` until verify phase)
- `k8s/overlays/prod/kustomization.yaml` — comment documenting pinned collector tag in base

## Verification

- `kubectl kustomize k8s/base` (and overlays as needed).
- `bash scripts/validate-otel-config.sh` when Docker is available; CI `otel-config` job on push/PR.
- Manual cluster dry-run steps documented in `docs/OPERATIONS.md` — run under **`/gsd-verify-phase 3`**.
