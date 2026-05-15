"""Scheduled full indexing entrypoint (Kubernetes CronJob: `python -m services.indexer.batch_index`)."""

from __future__ import annotations

import logging
import os
import sys

from .embeddings import EmbeddingsError, EmbeddingsGenerator
from .git_client import BranchNotFoundError, GitClientError, RepositoryNotFoundError
from .main import IndexWriteError, perform_index
from .models import IndexRequest
from . import repo_allowlist

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    repo_url = os.getenv("INDEX_REPO_URL", "").strip()
    if not repo_url:
        logger.error("INDEX_REPO_URL is required (set via ConfigMap indexer-batch-config or env).")
        return 1
    try:
        repo_allowlist.assert_repo_url_allowed(repo_url)
    except ValueError as e:
        logger.error("%s", e)
        return 1
    branch = (os.getenv("INDEX_BRANCH", "main") or "main").strip()
    device = os.getenv("EMBEDDING_DEVICE", "cpu")
    try:
        embedder = EmbeddingsGenerator(device=device)
    except EmbeddingsError as e:
        logger.error("Embeddings model failed to load: %s", e)
        return 1

    req = IndexRequest(repo_url=repo_url, branch=branch)
    try:
        resp = perform_index(req, embedder)
    except RepositoryNotFoundError as e:
        logger.error("Repository not found: %s", e)
        return 1
    except BranchNotFoundError as e:
        logger.error("Branch not found: %s", e)
        return 1
    except GitClientError as e:
        logger.error("Git client error: %s", e)
        return 1
    except IndexWriteError as e:
        logger.error("Index write failed: %s", e)
        return 1

    logger.info(
        "Indexed repo_url=%s chunks=%s files=%s duration_s=%.2f",
        resp.repo_url,
        resp.chunks_indexed,
        resp.total_files,
        resp.duration_seconds,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
