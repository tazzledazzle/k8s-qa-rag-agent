# Repository structure

**Path:** `job-application-pipeline/`  
**Mapped:** 2026-04-14

## Current layout

```
job-application-pipeline/
├── README.md                 # Product documentation: stages, layers, options
├── docs/
│   └── ai-job-pipeline.png   # Six-stage pipeline diagram
├── planning/                 # Tracked research + codebase map (see README)
│   ├── research/
│   └── codebase/
└── .planning/                # Optional mirror for GSD tools; ignored by root .gitignore
    ├── research/
    └── codebase/
```

## Planned layout (not yet created)

When implementation begins, a reasonable structure would be:

```
src/
  job_application_pipeline/
    ingestion/       # Connectors: Scrapy, Playwright, APIs
    transform/       # Normalization, chunking
    storage/         # Vector and document stores
    retrieval/       # Hybrid search, rerankers
    orchestration/   # LangGraph graphs, state definitions
    intelligence/    # Embeddings, scorers, LLM calls
    control/         # Policies, tiers, HITL hooks
    output/          # Notion, webhooks, files
    scheduling/      # Job definitions
    learning/        # Eval hooks, calibration
tests/
config/
```

Naming: **snake_case** for Python modules; **kebab-case** only for docs and static assets.

## Documentation conventions

- User-facing architecture: `README.md` and `docs/`.  
- Tracked internal planning: `planning/research/` and `planning/codebase/`.  
- Optional tool mirror: `.planning/` (same content; may be gitignored at monorepo root).  
- Do not commit secrets; reference environment variable names only.

## Git

- Project may be tracked as part of a larger monorepo (`march-project-portfolio`); this folder is the product root for the pipeline.

Update this file when `src/` or `tests/` first appear.
