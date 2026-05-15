FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for AST parsing and git
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installable package tree
COPY pyproject.toml .
COPY services /app/services

# Install Python dependencies
RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir -e ".[dev]"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "services.indexer.main:app", "--host", "0.0.0.0", "--port", "8000"]
