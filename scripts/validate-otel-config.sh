#!/usr/bin/env bash
# Validate OpenTelemetry Collector config (OBS-02). Requires Docker.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="${ROOT}/scripts/otel/otel-collector-config.yaml"
IMAGE="${OTEL_COLLECTOR_IMAGE:-otel/opentelemetry-collector-k8s:0.99.0}"
exec docker run --rm -v "${CONFIG}:/etc/otel/config.yaml:ro" "${IMAGE}" validate --config=/etc/otel/config.yaml
