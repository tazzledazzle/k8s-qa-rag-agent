"""Optional live compose checks — off by default in CI."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("RUN_COMPOSE_INTEGRATION") != "1",
    reason="Set RUN_COMPOSE_INTEGRATION=1 and start docker compose; see docs/PHASE1-RUNBOOK.md",
)
def test_compose_indexer_health() -> None:
    import httpx

    r = httpx.get("http://127.0.0.1:8000/health", timeout=10.0)
    assert r.status_code == 200
