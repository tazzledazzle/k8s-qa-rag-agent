# Conventions (planned)

**Path:** `job-application-pipeline/`  
**Mapped:** 2026-04-14  
**Status:** No application code yet; conventions below are targets for the first implementation pass.

## Language and style

- **Python 3.12+** with type hints on public functions and data models.  
- Formatter and linter: **Ruff** (or Black + Ruff) once `pyproject.toml` exists.  
- Line length: 100 characters unless a project standard overrides.

## Naming

- Modules and packages: `snake_case`.  
- Classes: `PascalCase`.  
- Constants: `UPPER_SNAKE_CASE`.  
- Environment variables: `SCREAMING_SNAKE_CASE` with a clear prefix (for example `JAP_` for job-application-pipeline).

## Architecture rules

- **Ports and adapters:** Each layer (ingestion, storage, and so on) exposes a small interface; implementations are swappable.  
- **No business logic in crawlers:** Spiders return raw or lightly normalized records; Transform owns normalization.  
- **Structured outputs:** JD normalization returns Pydantic models, not loose dicts, when using LLMs.

## Error handling

- Raise domain-specific exceptions for recoverable versus fatal errors.  
- Log structured fields (job_id, stage, correlation_id) without raw resume text in production logs.

## Security

- Never log full API keys or OAuth tokens.  
- Redact phone numbers and emails in traces unless explicitly required for debugging in a secure environment.

## Documentation

- Docstrings on public graph nodes and integration adapters.  
- README remains the source of truth for layer options until a separate user guide is needed.

Revisit after the first pull request with code.
