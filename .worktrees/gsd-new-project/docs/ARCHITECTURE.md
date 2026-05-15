# Architecture

## Overview

The OTel Demo Platform is a small multi-service app for demonstrating OpenTelemetry, W3C trace propagation, Temporal workflows, and LLM observability. For why we built this and the value of the demo, see [USE_CASES.md](USE_CASES.md). For how to run the system, see the [README](../README.md) in the repo root.

## Components

| Component             | Language         | Role                                                                                              |
|-----------------------|------------------|---------------------------------------------------------------------------------------------------|
| **API**               | Kotlin (Ktor)    | Entrypoint; `POST /chat` starts a Temporal workflow and returns the result.                       |
| **Worker**            | Kotlin           | Temporal worker; runs `AgentWorkflow` and `RunAgent` activity; activity calls the Agent via HTTP. |
| **Agent**             | Python (FastAPI) | LangChain + Ollama; `POST /invoke`; produces spans for model and tool calls.                      |
| **Temporal**          | Docker           | Workflow engine (temporalio/auto-setup).                                                          |
| **Grafana otel-lgtm** | Docker           | OTel Collector + Tempo + Grafana (single image).                                                  |

## Data flow

1. Client sends `POST /chat` with `{"message":"..."}` to the API.
2. API starts a Temporal workflow (AgentWorkflow) with the message.
3. Worker picks up the workflow and runs the RunAgent activity.
4. Activity HTTP-calls the Agent `POST /invoke` with the message.
5. Agent runs the LangChain pipeline (Ollama + tools) and returns `{"reply":"..."}`.
6. Activity returns the reply to the workflow; workflow completes; API returns the reply to the client.

## Request path

One trace follows this end-to-end path: **Client** → **POST /chat** → **API** (starts workflow) → **Temporal** → **Worker** (picks workflow, runs RunAgent activity) → **Activity** HTTP to Agent **POST /invoke** → **Agent** (LangChain + Ollama) → response back through activity and workflow to the API, which returns the reply to the client. Trace context is propagated at each hop so a single trace ID spans API, worker, agent, and LangChain steps in Grafana Tempo.

## Observability (OTel)

- **Instrumentation:** All services (API, Worker, Agent) are instrumented with OpenTelemetry. The agent also instruments LangChain so model and tool calls appear as spans.
- **Propagation:** W3C trace context is propagated on HTTP (API↔client, activity↔agent) and via Temporal (API→worker), so one request produces one trace.
- **Export:** All services export OTLP (gRPC) to the collector. The demo uses Grafana otel-lgtm as the collector (OTLP receiver → Tempo).
- **Result:** One trace in Tempo spans the API, worker, agent, and LangChain steps—suitable for explaining observability and debugging agentic workflows.

## Temporal mapping

- **Workflow**: Durable orchestration (AgentWorkflow); retries and history managed by Temporal.
- **Activity**: Single unit of work (RunAgent); calls the Python agent over HTTP.
- Same mental model as production Temporal: workflows, activities, task queue, visibility in the Temporal UI.
