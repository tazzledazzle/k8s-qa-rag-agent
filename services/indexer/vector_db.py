"""Qdrant vector store for code chunk embeddings."""

from __future__ import annotations

import logging
import os
from typing import Any

from qdrant_client import QdrantClient  # type: ignore[import-not-found]
from qdrant_client.http import models as qm  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)


def _qdrant_url() -> str:
    url = os.getenv("QDRANT_URL")
    if url:
        return url.rstrip("/")
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    return f"http://{host}:{port}"


def _collection_name() -> str:
    return os.getenv("QDRANT_COLLECTION", "code_chunks")


def get_client() -> QdrantClient:
    url = _qdrant_url()
    api_key = os.getenv("QDRANT_API_KEY") or None
    return QdrantClient(url=url, api_key=api_key)


def ensure_collection(client: QdrantClient, vector_size: int) -> None:
    name = _collection_name()
    existing = {c.name for c in client.get_collections().collections}
    if name in existing:
        return
    logger.info("Creating Qdrant collection %s dim=%s", name, vector_size)
    client.create_collection(
        collection_name=name,
        vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
    )


def upsert_points(
    client: QdrantClient,
    points: list[dict[str, Any]],
) -> None:
    """
    Upsert points. Each point dict: id (int), vector (list[float]),
    payload keys: file_path, language, start_line, end_line, text.
    """
    if not points:
        return
    name = _collection_name()
    batch = [
        qm.PointStruct(
            id=p["id"],
            vector=p["vector"],
            payload={
                "file_path": p["payload"]["file_path"],
                "language": p["payload"]["language"],
                "start_line": p["payload"]["start_line"],
                "end_line": p["payload"]["end_line"],
                "text": p["payload"]["text"],
            },
        )
        for p in points
    ]
    client.upsert(collection_name=name, points=batch, wait=True)


def ping(client: QdrantClient) -> bool:
    try:
        client.get_collections()
        return True
    except Exception as e:
        logger.warning("Qdrant ping failed: %s", e)
        return False
