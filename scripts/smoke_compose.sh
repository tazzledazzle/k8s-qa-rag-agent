#!/usr/bin/env bash
# Smoke-test local docker compose: datastores + four app /health endpoints.
# Usage: from repo root, after `docker compose up -d` — ./scripts/smoke_compose.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

bash "$ROOT/tests/fixtures/sample-repo/bootstrap.sh" >/dev/null

wait_http() {
  local url=$1
  local name=$2
  local max=${3:-180}
  local elapsed=0
  while ! curl -sf --max-time 5 "$url" >/dev/null; do
    if (( elapsed >= max )); then
      echo "Timeout waiting for $name ($url)" >&2
      exit 1
    fi
    sleep 3
    elapsed=$((elapsed + 3))
    echo "… waiting for $name (${elapsed}s / ${max}s)"
  done
}

wait_http_200() {
  local url=$1
  local name=$2
  local max=${3:-120}
  local elapsed=0
  local code="000"
  while [[ "$code" != "200" ]]; do
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" || echo "000")
    if [[ "$code" == "200" ]]; then
      return 0
    fi
    if (( elapsed >= max )); then
      echo "Timeout waiting for HTTP 200 on $name ($url) last_code=$code" >&2
      exit 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))
    echo "… waiting for $name (${elapsed}s / ${max}s) (last HTTP $code)"
  done
}

echo "==> Datastores"
wait_redis() {
  local max=${1:-120}
  local elapsed=0
  while ! docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; do
    if (( elapsed >= max )); then
      echo "Timeout waiting for redis (docker compose exec)" >&2
      exit 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))
    echo "… waiting for redis (${elapsed}s / ${max}s)"
  done
}

echo "==> Datastores"
wait_http "http://127.0.0.1:6333/health" "qdrant" 120
wait_http "http://127.0.0.1:9200" "elasticsearch" 180
wait_redis 120

echo "==> Application /health"
for pair in "8000:indexer" "8001:retriever" "8002:qa-agent" "8003:git-watcher"; do
  port="${pair%%:*}"
  name="${pair##*:}"
  wait_http_200 "http://127.0.0.1:${port}/health" "$name" 120
  echo "OK  $name ($port)"
done

echo "smoke_compose: all checks passed."
