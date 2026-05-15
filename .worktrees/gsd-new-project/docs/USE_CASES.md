# Use Cases

This demo supports a ~1hr interview: explain architecture, demo trace, and implement one feature. For how the system works, see [ARCHITECTURE.md](ARCHITECTURE.md). For how to run the session, see [INTERVIEW_SCRIPT.md](INTERVIEW_SCRIPT.md).

## Why OpenTelemetry (OTel)

- **Single trace across the stack:** One request produces one trace spanning the Kotlin API, Kotlin worker, and Python agent (and LangChain steps). No correlation IDs to stitch manually.
- **Vendor-neutral:** We use Grafana otel-lgtm (OTLP); the same instrumentation works with any OTLP-capable backend.
- **W3C propagation:** Trace context is propagated on HTTP (API↔client, activity↔agent) and via Temporal (API→worker), so one request = one trace in Tempo.

## Why Temporal

- **Durable workflow and activities:** AgentWorkflow and RunAgent activity run on Temporal; retries and history are managed by the engine, same mental model as production.
- **Visibility:** Task queue, workflow runs, and activity execution are visible in the Temporal Web UI—useful for explaining and debugging.

## Value of trace visibility

In Grafana (Tempo), one trace shows the full request path: API → worker → agent → LangChain model and tool calls. That visibility supports debugging and demonstrates observability for agentic workflows (e.g. mapping to LangSmith, OTel, or custom dashboards in production).

## Use cases (what we demo)

1. **OTel and trace propagation** — Full OpenTelemetry instrumentation and W3C propagation across Kotlin API, Kotlin worker, and Python agent; one request → one trace in Tempo spanning all services and LangChain steps.

2. **Temporal workflow + activities** — Real Temporal usage: AgentWorkflow, RunAgent activity, task queue, and (optionally) Temporal Web UI for run history and retries.

3. **LLM/agent observability** — LangChain + Ollama instrumented so each model and tool call appears as spans; discuss observability for agentic workflows.

4. **Live-coding in an interview** — Add a new pipeline step (e.g. a new tool or chain step) in the Python agent in ~20 minutes, run a request, show the new span(s) in Grafana.
