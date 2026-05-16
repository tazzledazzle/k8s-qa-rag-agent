"""BM25 full-text search via Elasticsearch."""

from __future__ import annotations

import logging
import os

from elasticsearch import Elasticsearch  # type: ignore[import-not-found]

from .models import ChunkHit

logger = logging.getLogger(__name__)
_TOP = 20


def _client() -> Elasticsearch:
    return Elasticsearch(os.getenv("ELASTICSEARCH_URL", "http://localhost:9200").rstrip("/"))


def _index() -> str:
    return os.getenv("ES_INDEX", "code_chunks")


def ping() -> bool:
    try:
        return bool(_client().ping())
    except Exception as e:
        logger.warning("Elasticsearch ping failed: %s", e)
        return False


def bm25_search(query: str, limit: int = _TOP) -> list[ChunkHit]:
    client = _client()
    resp = client.search(
        index=_index(),
        size=limit,
        query={
            "multi_match": {
                "query": query,
                "fields": ["text^2", "file_path"],
                "type": "best_fields",
            }
        },
    )
    raw = resp.body if hasattr(resp, "body") else resp
    hits_raw = raw.get("hits", {}).get("hits", []) if isinstance(raw, dict) else []
    hits: list[ChunkHit] = []
    for h in hits_raw:
        src = h.get("_source", {})
        cid = src.get("chunk_id")
        if cid is None:
            try:
                cid = int(h.get("_id", 0))
            except (TypeError, ValueError):
                cid = 0
        hits.append(
            ChunkHit(
                chunk_id=int(cid),
                score=float(h.get("_score", 0.0)),
                file_path=str(src.get("file_path", "")),
                language=str(src.get("language", "")),
                start_line=int(src.get("start_line", 0)),
                end_line=int(src.get("end_line", 0)),
                text=str(src.get("text", "")),
            )
        )
    return hits
