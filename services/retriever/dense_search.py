"""Dense vector search against Qdrant."""

from __future__ import annotations

import logging
import os

from qdrant_client import QdrantClient  # type: ignore[import-not-found]
from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]

from .models import ChunkHit

logger = logging.getLogger(__name__)

MODEL_NAME = "BAAI/bge-base-en-v1.5"
_TOP = 20

_model: SentenceTransformer | None = None


def _client() -> QdrantClient:
    url = os.getenv("QDRANT_URL")
    if not url:
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        url = f"http://{host}:{port}"
    api_key = os.getenv("QDRANT_API_KEY") or None
    return QdrantClient(url=url.rstrip("/"), api_key=api_key)


def _collection() -> str:
    return os.getenv("QDRANT_COLLECTION", "code_chunks")


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        device = os.getenv("EMBEDDING_DEVICE", "cpu")
        logger.info("Loading dense query model %s on %s", MODEL_NAME, device)
        _model = SentenceTransformer(MODEL_NAME, device=device)
    return _model


def ping() -> bool:
    try:
        _client().get_collections()
        return True
    except Exception as e:
        logger.warning("Qdrant ping failed: %s", e)
        return False


def dense_search(query: str, limit: int = _TOP) -> list[ChunkHit]:
    vec = _get_model().encode(query, show_progress_bar=False)
    if hasattr(vec, "tolist"):
        qvec = vec.tolist()
    else:
        qvec = list(vec)

    client = _client()
    res = client.search(  # type: ignore[attr-defined]
        collection_name=_collection(),
        query_vector=qvec,
        limit=limit,
        with_payload=True,
    )
    hits: list[ChunkHit] = []
    for r in res:
        pl = r.payload or {}
        hits.append(
            ChunkHit(
                chunk_id=int(r.id),
                score=float(r.score),
                file_path=str(pl.get("file_path", "")),
                language=str(pl.get("language", "")),
                start_line=int(pl.get("start_line", 0)),
                end_line=int(pl.get("end_line", 0)),
                text=str(pl.get("text", "")),
            )
        )
    return hits
