"""FastAPI entrypoint for the indexer service."""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException  # type: ignore[import-not-found]

from .chunker import ChunkingError, chunk_file
from .embeddings import EmbeddingsError, EmbeddingsGenerator
from .git_client import BranchNotFoundError, GitClient, GitClientError, RepositoryNotFoundError
from .models import ChunkMetadata, HealthResponse, IndexRequest, IndexResponse
from . import repo_allowlist
from . import text_search
from . import vector_db

logger = logging.getLogger(__name__)

_embedder: EmbeddingsGenerator | None = None


class IndexWriteError(Exception):
    """Raised when Qdrant or Elasticsearch persistence fails."""


def perform_index(req: IndexRequest, embedder: EmbeddingsGenerator) -> IndexResponse:
    """Clone/update repo, chunk, embed, and upsert into Qdrant + Elasticsearch (sync)."""
    started = time.perf_counter()
    cache_dir = os.getenv("INDEXER_REPO_CACHE", "/app/repos")
    git = GitClient(cache_dir=cache_dir)
    qc = vector_db.get_client()
    ec = text_search.get_client()

    try:
        repo_path = git.clone_or_update(req.repo_url, req.branch)
    except RepositoryNotFoundError:
        raise
    except BranchNotFoundError:
        raise
    except GitClientError:
        raise

    files = git.get_files(repo_path, req.include_patterns, req.exclude_patterns)
    chunks: list[ChunkMetadata] = []
    for fp in files:
        try:
            lang = git.get_file_language(fp)
            if lang == "unknown":
                continue
            content = fp.read_text(encoding="utf-8", errors="replace")
            for ch in chunk_file(fp, lang, content):
                chunks.append(ch)
        except (OSError, UnicodeError, ChunkingError) as e:
            logger.warning("Skip file %s: %s", fp, e)

    if not chunks:
        duration = time.perf_counter() - started
        return IndexResponse(
            status="ok",
            chunks_indexed=0,
            total_files=len(files),
            duration_seconds=duration,
            repo_url=req.repo_url,
        )

    vector_db.ensure_collection(qc, embedder.EMBEDDING_DIM)
    text_search.ensure_index(ec)

    texts = [c.chunk_text for c in chunks]
    batch_size = embedder.BATCH_SIZE
    all_vectors: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        all_vectors.extend(embedder.embed_texts(batch, batch_size=batch_size))

    q_points: list[dict] = []
    es_docs: list[dict] = []
    for c, vec in zip(chunks, all_vectors):
        q_points.append(
            {
                "id": c.deterministic_id,
                "vector": vec,
                "payload": {
                    "file_path": c.file_path,
                    "language": c.language,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "text": c.chunk_text,
                },
            }
        )
        es_docs.append(
            {
                "chunk_id": c.deterministic_id,
                "file_path": c.file_path,
                "language": c.language,
                "start_line": c.start_line,
                "end_line": c.end_line,
                "text": c.chunk_text,
            }
        )

    try:
        vector_db.upsert_points(qc, q_points)
        text_search.bulk_index(ec, es_docs)
    except Exception as e:
        logger.exception("Index write failed")
        raise IndexWriteError(str(e)) from e

    duration = time.perf_counter() - started
    return IndexResponse(
        status="ok",
        chunks_indexed=len(chunks),
        total_files=len(files),
        duration_seconds=duration,
        repo_url=req.repo_url,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _embedder
    device = os.getenv("EMBEDDING_DEVICE", "cpu")
    try:
        _embedder = EmbeddingsGenerator(device=device)
    except EmbeddingsError as e:
        logger.error("Failed to load embeddings model: %s", e)
        _embedder = None
    yield
    _embedder = None


app = FastAPI(title="Indexer", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    qc = vector_db.get_client()
    ec = text_search.get_client()
    return HealthResponse(
        status="ok",
        qdrant_connected=vector_db.ping(qc),
        elasticsearch_connected=text_search.ping(ec),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/index", response_model=IndexResponse)
def index_repo(req: IndexRequest) -> IndexResponse:
    if _embedder is None:
        raise HTTPException(status_code=503, detail="Embedding model not loaded")

    try:
        repo_allowlist.assert_repo_url_allowed(req.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e

    try:
        return perform_index(req, _embedder)
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except BranchNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except GitClientError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except IndexWriteError as e:
        raise HTTPException(status_code=502, detail=f"Index write failed: {e}") from e
