# Phase 4: Agent & LLM Experience — Context & Discussion

Used when planning or executing Phase 4. See [ROADMAP.md](../../ROADMAP.md) for the full phase description.

## Goal (from ROADMAP)

Turn the Python agent into a **modular, easy-to-extend LangChain playground** that’s safe for local experimentation and great for showcasing **tool-based agents**.

## Current state (pre–Phase 4)

- **Chain** (`agent/agent/chain.py`): `prompt | llm | _summarize_step`; one stub tool `search` (not wired into an agent executor). Custom `_Executor` invokes the chain and returns `{ "output": content }`; no `create_tool_calling_agent` yet.
- **Docs**: `docs/LIVE_FEATURE.md` (add new tool or chain step, show in Grafana) and `docs/INTERVIEW_SCRIPT.md` (one-hour script including live-coding block 7) exist and reference the current pipeline.
- **Tests**: `tests/test_chain.py` (search tool, get_agent_executor, executor invoke, summarize step with mock LLM); `tests/test_main.py` (health, invoke with mock agent). No tests for LLM errors, tool failures, or invalid input.
- **Observability**: Phase 2 added span attributes/events and structured logs on `/invoke`; no per-tool or per-step span detail yet.

## Decisions to lock (discuss and confirm)

Choose one option per bullet (or state a variant); once locked, the Phase 4 plan will assume these.

1. **Tool-calling agent vs. simple chain**  
   - **A)** Introduce a real **tool-calling agent** (e.g. `create_tool_calling_agent` with `search` + 1–2 new tools) so the model can choose when to call tools. Better demo value for “tool-based agents” but more moving parts.  
   - **B)** Keep the **simple chain** (prompt | llm | step) and add 1–2 **stub tools** that are invoked only in tests or via a separate path (e.g. “tool playground” endpoint). LIVE_FEATURE stays “add a tool + wire later.”  
   - **C)** **Hybrid**: one tool-calling agent path (e.g. env or flag) and one simple chain path for “no tools” / LLM-off mode.

2. **Scope of new tools**  
   - ROADMAP: “one or two well-scoped tools with strong demo value (e.g. simple in-memory knowledge lookup, deterministic utility).”  
   - **Confirm:** In-memory only (no DB/network), or is a single read-only external call (e.g. public API) acceptable for one tool?

3. **“LLM off” mode**  
   - **A)** Env var (e.g. `AGENT_LLM_OFF=1`) that makes `get_agent_executor()` return a stub executor (fixed or configurable responses, no Ollama).  
   - **B)** Stub only in tests (no runtime flag); CI and constrained environments rely on mocks in pytest.  
   - **C)** Both: runtime stub for demos/CI **and** pytest mocks for unit tests.

4. **Agent observability depth**  
   - **A)** Spans/logs at **invoke boundary only** (current): one span per `/invoke`, attributes/events for start/end/outcome.  
   - **B)** **Per-tool / per-step**: each tool call or major chain step gets its own span (or clear attributes/events), so “which tools ran and how long” is visible in Tempo without code changes later.

5. **LIVE_FEATURE.md and INTERVIEW_SCRIPT.md**  
   - **A)** Update to match Phase 4 code (e.g. “add a new tool” points at real tool list and agent factory; “add a chain step” points at current chain).  
   - **B)** Minimal edits; keep narrative and only fix file/function names if they change.  
   - **C)** Expand with a short “Phase 4 additions” section (LLM-off, tool list, observability) and keep existing live-coding flow.

6. **Testing without Ollama**  
   - **Requirement:** All agent tests (chain + main) must pass without a running Ollama.  
   - **Confirm:** Only mocks (patch LLM / executor), or do we want one integration-style test that uses the real stub executor when `AGENT_LLM_OFF=1` (no real LLM)?

## Suggested defaults (if you want to move fast)

- **1:** A (tool-calling agent) for best interview/demo value.  
- **2:** In-memory only for both tools.  
- **3:** C (runtime LLM-off + pytest mocks).  
- **4:** B (per-tool/per-step visibility).  
- **5:** A (align docs to Phase 4 code).  
- **6:** Mocks only; optional separate script or doc for “run with LLM_OFF” manual check.

## Dependencies

- **Phase 1:** Runability, CONFIG, one-command start.  
- **Phase 2:** Agent spans and logs so new tools/steps show up in traces.  
- **Phase 3:** Optional; only if we add workflows that call “enhanced” agent behavior (e.g. tool results in workflow payload).

## Outcome after Phase 4

- Clear, documented chain (or agent) composition; 1–2 demo tools; tests for pipeline and error cases without Ollama; optional LLM-off mode; observability that shows which tools ran; LIVE_FEATURE and INTERVIEW_SCRIPT aligned with code for “add a tool / change the chain” live-coding.

---

**Plan generated:** 04-01-PLAN.md uses the **suggested defaults** above (tool-calling agent, in-memory tools, LLM-off + mocks, per-tool observability, docs aligned). To lock different choices, add a "Locked decisions" section with your options and date, then regenerate or edit the plan.

*Update this file with locked decisions and date when you finalize; then run /gsd:plan-phase 4 to generate or regenerate 04-01-PLAN.md.*
