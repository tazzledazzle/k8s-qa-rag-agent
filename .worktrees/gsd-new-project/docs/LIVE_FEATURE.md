# Live-Coding: New Pipeline Step (Python Agent)

Use this as a step-by-step fallback for the "implement a new feature" segment (~20 min). See **INTERVIEW_SCRIPT.md** block 7 for timing.

## Where it fits

1. **Request path:** API → Worker → RunAgent activity → Agent `POST /invoke` → LangChain pipeline (`agent/agent/chain.py`). See **ARCHITECTURE.md** for the full request path.

2. **Pipeline location:** The **Python agent** is a **tool-calling agent** in `agent/agent/chain.py`. The agent uses `get_agent_executor()` which returns an invokable that runs a tool-calling loop (`_agent_loop`): the LLM can call tools when helpful. New steps are added either as **new tools** (added to the `TOOLS` list and thus available to the model) or by changing the agent loop / composition in `chain.py`.

3. **Observability:** The `/invoke` span includes per-tool visibility: each tool call adds an event `agent.tool.invoke` with `tool.name`, and the span attribute `agent.tools_used` lists which tools ran. See **TRACE_WALKTHROUGH.md** or Grafana (Tempo) to inspect traces.

---

## Tools (Phase 4)

Defined in `agent/agent/chain.py`:

- **search(query)** — Stub search; returns a fixed string for demo.
- **lookup(key)** — In-memory lookup (e.g. `otel` → OpenTelemetry, `temporal` → Temporal workflow engine).
- **echo_repeat(text, times)** — Echoes `text` repeated `times` (space-separated).

All tools are in-memory only (no DB/network). The agent factory is `get_agent_executor()`; the tool list is `TOOLS` in `chain.py`.

---

## Goal

Add one new step in the Python agent that appears as new span(s) or tool usage in Grafana.

## Option A: Add a new tool

1. **Add the tool** in `agent/agent/chain.py`:
   - Define a new `@tool` function, e.g. `get_weather(location: str) -> str` that returns a fixed string (e.g. `"Sunny, 72°F"`).
   - Append it to the `TOOLS` list: `TOOLS = [search, lookup, echo_repeat, get_weather]`. The agent uses `TOOLS` in `get_agent_executor()`, so the model can call the new tool when relevant.

2. **Add a test** in `agent/tests/test_chain.py`: e.g. `test_get_weather_tool()` that invokes the new tool and asserts the return value.

3. **Run** the agent, send a request that might trigger the tool, open Grafana and show the trace; the invoke span will show `agent.tools_used` and events for each tool call.

**Where it fits:** The new tool is registered in `TOOLS` and is available to the tool-calling agent; when the model calls it, it appears in the trace.

## Option B: Change the chain / prompt

1. **Agent composition** lives in `agent/agent/chain.py`: `get_agent_executor()` builds the executor, and `_agent_loop()` runs the LLM-with-tools loop. To change behavior you can:
   - Add a system message or alter the message list passed to the LLM in `_agent_loop`.
   - Post-process the final content before returning (e.g. in `_Executor.invoke()`).
2. **Add a test** that the executor still returns `{"output": "<string>"}` and (optionally) contains expected text.
3. **Run** and show the updated behavior and spans in Grafana.

**Where it fits:** Changes in `_agent_loop` or `_Executor` affect how the agent responds; observability remains on the existing `/invoke` span and tool events.

---

## Phase 4 additions

- **LLM-off mode:** Set `AGENT_LLM_OFF=1` (or `true`) so the agent uses a stub executor and does not call Ollama. Use for CI or environments without GPU/Ollama. See **CONFIG.md** (Agent section).
- **Running without Ollama:** Start the agent with `AGENT_LLM_OFF=1`; `POST /invoke` returns a stub reply. All agent tests pass without Ollama (mocks and this stub).
- **Tool observability:** Traces for `/invoke` include `agent.tools_used` and `agent.tool.invoke` events so which tools ran is visible in Tempo. See **TRACE_WALKTHROUGH.md** for trace details.

---

## Suggested order for the 20 min

1. Add the new tool or change the chain in `chain.py` (5 min).
2. Add a short pytest in `agent/tests/test_chain.py` (3 min).
3. Run tests: `cd agent && uv run pytest tests/ -v` (1 min).
4. Start the stack and send one request (3 min).
5. Open Grafana and show the new span / tool usage (5 min).
6. Buffer for questions (3 min).
