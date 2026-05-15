# Phase 2: End-to-End Observability — Context & Locked Decisions

Used when planning or executing Phase 2. See [ROADMAP.md](../../ROADMAP.md) for full phase description.

## Locked decisions

- **Traces, logs, and metrics**  
  Deliver traces, structured logs, and a **small metrics story** (latency + throughput) in Grafana alongside traces. Metrics are in scope, not optional.

- **TraceQL primary, UI fallback**  
  For this project, **TraceQL** is the primary interface for trace-driven debugging. Document UI-click flows as the fallback for users who prefer the Grafana UI.

- **Broken observability**  
  Implement a **config flag** (e.g. env var) that deliberately misconfigures observability (wrong OTLP endpoint or disabled exporter). Provide docs so the interviewer can guide a candidate through diagnosing and fixing it during an interview.

## Implications for the plan

- Walkthrough docs: lead with TraceQL examples and queries; add “Alternative: use the UI” where relevant.
- Metrics: include at least latency (e.g. histogram) and throughput (e.g. counter) and how to view them in Grafana with traces.
- Broken scenario: one env var or flag toggles the misconfiguration; one doc section describes “how to diagnose and fix” for the interview script.
