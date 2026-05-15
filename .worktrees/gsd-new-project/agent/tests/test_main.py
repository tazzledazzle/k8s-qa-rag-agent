"""Tests for FastAPI app."""
import json
import os
import re

os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Default client with no forced failures."""
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {"output": "Echo: hello"}
    from agent.main import create_app

    app = create_app(agent=mock_agent)
    app.state.agent = mock_agent  # set before first request (lifespan may run async)
    return TestClient(app)


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "otel-demo-agent"


def test_invoke_returns_reply(client: TestClient):
    r = client.post("/invoke", json={"message": "hello"})
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data
    assert "Echo:" in data["reply"]


def test_invoke_structured_log_trace_id_span_id_are_hex_strings(client: TestClient, capsys: pytest.CaptureFixture):
    """Structured logs must emit trace_id and span_id as strings (hex), not integers."""
    client.post("/invoke", json={"message": "hello"})
    captured = capsys.readouterr()
    stderr = captured.err
    hex_32 = re.compile(r"^[0-9a-f]{32}$")
    hex_16 = re.compile(r"^[0-9a-f]{16}$")
    for line in stderr.strip().split("\n"):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "trace_id" not in obj or "span_id" not in obj:
            continue
        assert isinstance(obj["trace_id"], str), f"trace_id must be string, got {type(obj['trace_id'])}"
        assert isinstance(obj["span_id"], str), f"span_id must be string, got {type(obj['span_id'])}"
        if obj["trace_id"]:
            assert hex_32.match(obj["trace_id"]), f"trace_id must be 32 hex chars, got {obj['trace_id']!r}"
        if obj["span_id"]:
            assert hex_16.match(obj["span_id"]), f"span_id must be 16 hex chars, got {obj['span_id']!r}"


def test_invoke_agent_error_propagates(client: TestClient):
    """When the agent raises, the exception propagates (server would return 500)."""
    client.app.state.agent.invoke.side_effect = RuntimeError("Agent failed")
    with pytest.raises(RuntimeError, match="Agent failed"):
        client.post("/invoke", json={"message": "hello"})


def test_invoke_with_failure_flag_forces_5xx_and_logs_agent_failure(
    capsys: pytest.CaptureFixture,
):
    """With AGENT_FAIL_ALL_REQUESTS enabled, /invoke returns 5xx and logs agent_failure."""
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {"output": "Echo: hello"}  # would be used if not forced to fail

    with patch.dict(os.environ, {"AGENT_FAIL_ALL_REQUESTS": "1"}, clear=False):
        from agent.main import create_app

        app = create_app(agent=mock_agent)
        app.state.agent = mock_agent
        client = TestClient(app)
        response = client.post("/invoke", json={"message": "hello"})

    assert response.status_code >= 500

    captured = capsys.readouterr()
    stderr = captured.err
    error_events = []
    for line in stderr.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("service") != "otel-demo-agent":
            continue
        if obj.get("outcome") != "error":
            continue
        error_events.append(obj)

    assert error_events, "Expected at least one error structured log from otel-demo-agent"
    assert any(e.get("error_type") == "agent_failure" for e in error_events), "Expected error_type=agent_failure in error logs"
