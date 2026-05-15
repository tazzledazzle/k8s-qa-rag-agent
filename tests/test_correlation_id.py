"""OBS-01: correlation id on QA agent and retriever."""

from __future__ import annotations

import logging
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from services.qa_agent.models import AskResponse


@pytest.fixture(autouse=True)
def _no_otel_exporter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)


def _correlation_ids_from_caplog(caplog: pytest.LogCaptureFixture) -> list[str]:
    out: list[str] = []
    for rec in caplog.records:
        cid = getattr(rec, "correlation_id", None)
        if cid:
            out.append(str(cid))
    return out


def test_retriever_search_emits_correlation_id_json(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    from services.retriever import main as retriever_main

    with (
        patch.object(retriever_main.dense_search, "dense_search", return_value=[]),
        patch.object(retriever_main.bm25_search, "bm25_search", return_value=[]),
        patch.object(retriever_main.reranker, "rerank", side_effect=lambda q, m, k: m[:k]),
        patch.object(retriever_main.cache, "get_cached", return_value=None),
        patch.object(retriever_main.cache, "set_cached", return_value=None),
    ):
        with TestClient(retriever_main.app) as client:
            r = client.post("/search", json={"query": "hello"})
    assert r.status_code == 200
    ids = _correlation_ids_from_caplog(caplog)
    assert any(ids), caplog.text


def test_retriever_search_respects_x_correlation_id_header(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    from services.retriever import main as retriever_main

    with (
        patch.object(retriever_main.dense_search, "dense_search", return_value=[]),
        patch.object(retriever_main.bm25_search, "bm25_search", return_value=[]),
        patch.object(retriever_main.reranker, "rerank", side_effect=lambda q, m, k: m[:k]),
        patch.object(retriever_main.cache, "get_cached", return_value=None),
        patch.object(retriever_main.cache, "set_cached", return_value=None),
    ):
        with TestClient(retriever_main.app) as client:
            r = client.post(
                "/search",
                json={"query": "hello"},
                headers={"X-Correlation-ID": "fixed-test-correlation"},
            )
    assert r.status_code == 200
    assert "fixed-test-correlation" in _correlation_ids_from_caplog(caplog)


def test_ask_propagates_x_correlation_id_to_retriever(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    captured: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(dict(request.headers))
        return httpx.Response(200, json={"chunks": []})

    transport = httpx.MockTransport(handler)

    class RecordingClient(httpx.Client):
        def __init__(self, *args, **kwargs) -> None:
            kwargs.setdefault("transport", transport)
            super().__init__(*args, **kwargs)

    fake_response = AskResponse(answer="ok", citations=[])

    def run_then_search(question: str) -> AskResponse:
        from services.qa_agent.tools import _search

        _search("nested-query")
        return fake_response

    with patch("services.qa_agent.main.run_agent", side_effect=run_then_search):
        with patch("services.qa_agent.tools.httpx.Client", RecordingClient):
            from services.qa_agent.main import app

            with TestClient(app) as client:
                r = client.post("/ask", json={"question": "what is up?"})
    assert r.status_code == 200
    assert captured, "expected outbound call to retriever"
    assert any(h.get("x-correlation-id") or h.get("X-Correlation-ID") for h in captured), captured
