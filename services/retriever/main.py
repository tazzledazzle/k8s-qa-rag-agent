"""FastAPI retriever: hybrid search, dedup, rerank, cache."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from rapidfuzz import fuzz

from services.common.observability import (
    CorrelationIdMiddleware,
    correlation_id_var,
    create_app_lifespan,
)

from . import bm25_search, cache, dense_search, reranker
from .models import ChunkHit, RetrieverHealthResponse, SearchRequest, SearchResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="Retriever", lifespan=create_app_lifespan("retriever"))
app.add_middleware(CorrelationIdMiddleware, service="retriever")


def _dedup_similar(chunks: list[ChunkHit], ratio_threshold: int = 80) -> list[ChunkHit]:
    """Drop chunks whose text is very similar to a higher-scoring retained chunk."""
    ordered = sorted(chunks, key=lambda c: c.score, reverse=True)
    kept: list[ChunkHit] = []
    for c in ordered:
        if any(fuzz.token_sort_ratio(c.text, k.text) >= ratio_threshold for k in kept):
            continue
        kept.append(c)
    return kept


def _merge_scores(dense: list[ChunkHit], bm25: list[ChunkHit]) -> list[ChunkHit]:
    by_id: dict[int, ChunkHit] = {}
    for h in dense:
        by_id[h.chunk_id] = h
    for h in bm25:
        if h.chunk_id in by_id:
            prev = by_id[h.chunk_id]
            combined = max(prev.score, h.score)
            by_id[h.chunk_id] = ChunkHit(
                chunk_id=h.chunk_id,
                score=combined,
                file_path=h.file_path or prev.file_path,
                language=h.language or prev.language,
                start_line=h.start_line or prev.start_line,
                end_line=h.end_line or prev.end_line,
                text=h.text or prev.text,
            )
        else:
            by_id[h.chunk_id] = h
    return list(by_id.values())


def _log_extra() -> dict[str, str]:
    cid = correlation_id_var.get()
    return {"correlation_id": cid} if cid else {}


@app.get("/health", response_model=RetrieverHealthResponse)
def health() -> RetrieverHealthResponse:
    return RetrieverHealthResponse(
        status="ok",
        qdrant_connected=dense_search.ping(),
        elasticsearch_connected=bm25_search.ping(),
        redis_connected=cache.ping(),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


async def _hybrid_search(req: SearchRequest) -> SearchResponse:
    dense_task = asyncio.to_thread(dense_search.dense_search, req.query)
    bm_task = asyncio.to_thread(bm25_search.bm25_search, req.query)
    dense_hits, bm_hits = await asyncio.gather(dense_task, bm_task, return_exceptions=True)

    dense_list: list[ChunkHit] = [] if isinstance(dense_hits, BaseException) else dense_hits
    bm_list: list[ChunkHit] = [] if isinstance(bm_hits, BaseException) else bm_hits
    if isinstance(dense_hits, BaseException):
        logger.warning("Dense search failed: %s", dense_hits, extra=_log_extra())
    if isinstance(bm_hits, BaseException):
        logger.warning("BM25 search failed: %s", bm_hits, extra=_log_extra())

    merged = _merge_scores(dense_list, bm_list)
    merged = _dedup_similar(merged)
    ranked = await asyncio.to_thread(reranker.rerank, req.query, merged, 5)
    return SearchResponse(chunks=ranked)


@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    cached = cache.get_cached(req.query, req.language)
    if cached is not None:
        return cached
    result = await _hybrid_search(req)
    cache.set_cached(req.query, req.language, result)
    return result
