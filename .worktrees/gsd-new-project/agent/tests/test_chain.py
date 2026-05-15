"""Tests for LangChain pipeline with mock LLM. All tests pass without Ollama."""
import os
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage

os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")


def test_search_tool():
    from agent.chain import search
    assert search.invoke("test query") == "[stub search result for: test query]"


def test_lookup_tool():
    from agent.chain import lookup
    assert lookup.invoke({"key": "otel"}) == "OpenTelemetry"
    assert lookup.invoke({"key": "temporal"}) == "Temporal workflow engine"
    assert lookup.invoke({"key": "unknown"}) == "not found"


def test_echo_repeat_tool():
    from agent.chain import echo_repeat
    assert echo_repeat.invoke({"text": "hi", "times": 2}) == "hi hi"
    assert echo_repeat.invoke({"text": "x", "times": 1}) == "x"


def test_get_agent_executor_returns_executor():
    with patch("agent.chain.ChatOllama") as mock_ollama:
        mock_ollama.return_value = MagicMock()
        from agent.chain import get_agent_executor
        ex = get_agent_executor()
        assert ex is not None
        assert hasattr(ex, "invoke")
        mock_ollama.assert_called_once()


def test_executor_invoke():
    """Executor invoke returns dict with 'output'; mock uses bind_tools."""
    with patch("agent.chain.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.return_value = AIMessage(content="Hello back")
        mock_get_llm.return_value = mock_llm
        from agent.chain import get_agent_executor
        ex = get_agent_executor()
        out = ex.invoke({"input": "hi"})
        assert "output" in out
        assert out["output"] == "Hello back"


def test_chain_includes_summarize_step():
    """Tool-calling agent returns output from LLM (mock has bind_tools)."""
    with patch("agent.chain.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.return_value = AIMessage(content="Summarized reply")
        mock_get_llm.return_value = mock_llm
        from agent.chain import get_agent_executor
        ex = get_agent_executor()
        out = ex.invoke({"input": "hello"})
        assert "output" in out
        assert out["output"] == "Summarized reply"


def test_executor_empty_input_uses_default():
    """Empty or missing input is handled; executor defaults to 'Hello' for empty string."""
    with patch("agent.chain.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.return_value = AIMessage(content="Hi there")
        mock_get_llm.return_value = mock_llm
        from agent.chain import get_agent_executor
        ex = get_agent_executor()
        out = ex.invoke({"input": ""})
        assert "output" in out
        out_missing = ex.invoke({})
        assert "output" in out_missing


def test_executor_invoke_returns_dict_with_output():
    """get_agent_executor().invoke() returns a dict with 'output' key."""
    with patch("agent.chain.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.return_value = AIMessage(content="Reply")
        mock_get_llm.return_value = mock_llm
        from agent.chain import get_agent_executor
        ex = get_agent_executor()
        result = ex.invoke({"input": "test"})
        assert isinstance(result, dict)
        assert "output" in result
        assert result["output"] == "Reply"


def test_agent_llm_off_returns_stub():
    """When AGENT_LLM_OFF=1, invoke returns stub reply without calling Ollama."""
    with patch.dict(os.environ, {"AGENT_LLM_OFF": "1"}, clear=False):
        from agent.chain import get_agent_executor
        ex = get_agent_executor()
        out = ex.invoke({"input": "hello"})
        assert "output" in out
        assert "[LLM off]" in out["output"]
        assert "hello" in out["output"]


def test_executor_llm_raise_propagates():
    """When the LLM/invoke raises, the exception propagates from executor.invoke."""
    with patch("agent.chain.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value.invoke.side_effect = RuntimeError("LLM failed")
        mock_get_llm.return_value = mock_llm
        from agent.chain import get_agent_executor
        ex = get_agent_executor()
        with pytest.raises(RuntimeError, match="LLM failed"):
            ex.invoke({"input": "test"})
