"""Elasticsearch BM25 indexing for code chunks."""

from __future__ import annotations

import logging
import os
from typing import Any

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

logger = logging.getLogger(__name__)


def _es_url() -> str:
    return os.getenv("ELASTICSEARCH_URL", "http://localhost:9200").rstrip("/")


def _index_name() -> str:
    return os.getenv("ES_INDEX", "code_chunks")


def get_client() -> Elasticsearch:
    return Elasticsearch(_es_url(), request_timeout=60)


def ensure_index(client: Elasticsearch) -> None:
    idx = _index_name()
    if client.indices.exists(index=idx):
        return
    logger.info("Creating Elasticsearch index %s", idx)
    client.indices.create(
        index=idx,
        settings={"analysis": {"analyzer": {"code": {"type": "standard"}}}},
        mappings={
            "properties": {
                "chunk_id": {"type": "long"},
                "file_path": {"type": "keyword"},
                "language": {"type": "keyword"},
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"},
                "text": {"type": "text", "analyzer": "standard"},
            }
        },
    )


def bulk_index(client: Elasticsearch, documents: list[dict[str, Any]]) -> int:
    """
    Index documents. Each doc: chunk_id, file_path, language, start_line, end_line, text.
    Returns number of successfully indexed operations (best-effort from bulk helper).
    """
    if not documents:
        return 0
    idx = _index_name()

    def gen():
        for d in documents:
            yield {
                "_index": idx,
                "_id": str(d["chunk_id"]),
                "_source": {
                    "chunk_id": d["chunk_id"],
                    "file_path": d["file_path"],
                    "language": d["language"],
                    "start_line": d["start_line"],
                    "end_line": d["end_line"],
                    "text": d["text"],
                },
            }

    ok, errors = bulk(client, gen(), refresh="wait_for", raise_on_error=False)
    if errors:
        err_list = errors if isinstance(errors, list) else [errors]
        logger.error("Elasticsearch bulk errors: %s", err_list[:5])
    return int(ok)


def ping(client: Elasticsearch) -> bool:
    try:
        return bool(client.ping())
    except Exception as e:
        logger.warning("Elasticsearch ping failed: %s", e)
        return False
