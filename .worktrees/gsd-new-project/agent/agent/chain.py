"""LangChain pipeline: tool-calling agent with Ollama and in-memory tools.

Observability: each tool invocation adds a span event agent.tool.invoke with
tool.name; the invoke span gets agent.tools_used (list of tool names) when present.

Tools (all in-memory, no DB/network):
- search(query): stub search returning a fixed string.
- lookup(key): in-memory DEMO_KNOWLEDGE lookup (e.g. otel -> OpenTelemetry).
- echo_repeat(text, times): returns (text + " ") * times trimmed.

The agent uses a tool-calling flow: LLM with tools bound; when the model
returns tool_calls we execute them and re-invoke until we get a final reply.
See CONFIG.md for OLLAMA_* and AGENT_LLM_OFF.
"""
import os
from opentelemetry import trace
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


# In-memory knowledge for lookup tool (no I/O).
DEMO_KNOWLEDGE = {
    "otel": "OpenTelemetry",
    "temporal": "Temporal workflow engine",
}


@tool
def search(query: str) -> str:
    """Search for information. (Stub for demo.)"""
    return f"[stub search result for: {query}]"


@tool
def lookup(key: str) -> str:
    """Look up a term in the demo knowledge base. Returns the value or 'not found'."""
    key_lower = key.strip().lower()
    return DEMO_KNOWLEDGE.get(key_lower, "not found")


@tool
def echo_repeat(text: str, times: int = 1) -> str:
    """Echo the text repeated the given number of times (space-separated)."""
    if times < 1:
        times = 1
    return (((text or "") + " ") * times).strip()


TOOLS = [search, lookup, echo_repeat]


def get_llm():
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    return ChatOllama(base_url=base_url, model=model, temperature=0)


def _agent_loop(llm, tools, user_input: str, max_steps: int = 10):
    """Run tool-calling loop: invoke LLM; on tool_calls, run tools and re-invoke until done."""
    span = trace.get_current_span()
    tools_used = []
    llm_with_tools = llm.bind_tools(tools)
    name_to_tool = {t.name: t for t in tools}
    messages = [HumanMessage(content=user_input)]
    for _ in range(max_steps):
        response = llm_with_tools.invoke(messages)
        if not getattr(response, "tool_calls", None):
            if tools_used:
                span.set_attribute("agent.tools_used", tools_used)
            content = response.content
            if isinstance(content, list):
                content = "".join(str(block) for block in content) if content else ""
            return content or ""
        for tc in response.tool_calls:
            name = tc.get("name") or tc.get("name_")
            args = tc.get("args") or {}
            span.add_event("agent.tool.invoke", attributes={"tool.name": name or "unknown"})
            tools_used.append(name or "unknown")
            tool_fn = name_to_tool.get(name)
            if tool_fn:
                result = tool_fn.invoke(args)
            else:
                result = f"Unknown tool: {name}"
            messages.append(response)
            messages.append(
                ToolMessage(content=str(result), tool_call_id=tc.get("id") or "")
            )
    if tools_used:
        span.set_attribute("agent.tools_used", tools_used)
    return "[max steps reached]"


def get_agent_executor():
    """Return a runnable with .invoke(inputs) -> {"output": "<reply string>"}.

    When AGENT_LLM_OFF=1 or true, returns a stub executor (no Ollama). See CONFIG.md.
    """
    if os.environ.get("AGENT_LLM_OFF", "").strip().lower() in ("1", "true"):
        return _StubExecutor()
    llm = get_llm()
    return _Executor(llm, TOOLS)


class _Executor:
    """Executor that runs the tool-calling agent and returns {"output": content}."""

    def __init__(self, llm, tools):
        self._llm = llm
        self._tools = tools

    def invoke(self, inputs: dict) -> dict:
        user_input = (inputs.get("input") or "").strip()
        content = _agent_loop(self._llm, self._tools, user_input or "Hello")
        return {"output": content}


class _StubExecutor:
    """Stub executor when AGENT_LLM_OFF=1: no Ollama, returns fixed reply."""

    def invoke(self, inputs: dict) -> dict:
        raw = (inputs.get("input") or "").strip()
        reply = f" [LLM off] You said: {raw}" if raw else " [LLM off] Stub reply."
        return {"output": reply}
