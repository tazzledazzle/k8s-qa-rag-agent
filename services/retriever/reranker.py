"""Cross-encoder reranking."""

from __future__ import annotations

import logging
import os

from sentence_transformers import CrossEncoder

from .models import ChunkHit

logger = logging.getLogger(__name__)

MODEL_NAME = "cross-encoder/mmarco-MiniLMv2-L12-H384-v1"
_FALLBACK = "cross-encoder/ms-marco-MiniLM-L-12-v2"

_model: CrossEncoder | None = None


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        name = os.getenv("RERANKER_MODEL", MODEL_NAME)
        try:
            _model = CrossEncoder(name)
        except Exception:
            logger.warning("Reranker %s failed to load, trying fallback", name)
            _model = CrossEncoder(_FALLBACK)
    return _model


def rerank(query: str, candidates: list[ChunkHit], top_k: int = 5) -> list[ChunkHit]:
    if not candidates:
        return []
    model = _get_model()
    pairs = [(query, c.text) for c in candidates]
    scores = model.predict(pairs, show_progress_bar=False)
    scored = sorted(zip(candidates, scores), key=lambda x: float(x[1]), reverse=True)
    return [c for c, _ in scored[:top_k]]
