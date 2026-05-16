"""Redis cache for retriever responses."""

from __future__ import annotations

import hashlib
import json
import logging
import os

import redis  # type: ignore[import-not-found]

from .models import ChunkHit, SearchResponse

logger = logging.getLogger(__name__)

_TTL = 600


def _redis() -> redis.Redis:
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    return redis.Redis(host=host, port=port, db=db, decode_responses=True)


def cache_key(query: str, language: str | None) -> str:
    raw = f"{query}\0{language or ''}".encode("utf-8")
    return "retriever:" + hashlib.sha256(raw).hexdigest()


def get_cached(query: str, language: str | None) -> SearchResponse | None:
    try:
        r = _redis()
        raw = r.get(cache_key(query, language))
        if raw is None:
            return None
        if not isinstance(raw, str):
            logger.warning("Unexpected Redis payload type: %s", type(raw))
            return None
        payload = json.loads(raw)
        chunks = [ChunkHit(**c) for c in payload.get("chunks", [])]
        return SearchResponse(chunks=chunks)
    except Exception as e:
        logger.warning("Redis get failed: %s", e)
        return None


def set_cached(query: str, language: str | None, response: SearchResponse) -> None:
    try:
        r = _redis()
        body = json.dumps({"chunks": [c.model_dump() for c in response.chunks]})
        r.setex(cache_key(query, language), _TTL, body)
    except Exception as e:
        logger.warning("Redis set failed: %s", e)


def ping() -> bool:
    try:
        return bool(_redis().ping())
    except Exception as e:
        logger.warning("Redis ping failed: %s", e)
        return False
