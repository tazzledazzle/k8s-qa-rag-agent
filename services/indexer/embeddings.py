"""Embedding generation using sentence-transformers."""

import logging
from typing import Optional
import numpy as np  # type: ignore[import-not-found]

from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)


class EmbeddingsError(Exception):
    """Base exception for embedding operations."""

    pass


class EmbeddingsGenerator:
    """Generates vector embeddings for code chunks."""

    MODEL_NAME = "BAAI/bge-base-en-v1.5"
    BATCH_SIZE = 32
    EMBEDDING_DIM = 768  # BGE-base-en-v1.5 embedding dimension

    def __init__(self, device: str = "cpu"):
        """
        Initialize embeddings generator.

        Args:
            device: Torch device ('cpu' or 'cuda'). Auto-detects CUDA if available.

        Raises:
            EmbeddingsError: If model cannot be loaded.
        """
        try:
            logger.info(f"Loading embedding model {self.MODEL_NAME} on device {device}")
            self.model = SentenceTransformer(self.MODEL_NAME, device=device)
            logger.info(f"Model loaded successfully. Embedding dimension: {self.EMBEDDING_DIM}")
        except Exception as e:
            raise EmbeddingsError(f"Failed to load embedding model: {str(e)}") from e

    def embed_texts(self, texts: list[str], batch_size: Optional[int] = None) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts.

        Args:
            texts: List of text strings to embed.
            batch_size: Batch size for processing. Uses self.BATCH_SIZE if not specified.

        Returns:
            List of embedding vectors (list of floats).

        Raises:
            EmbeddingsError: If embedding generation fails.
        """
        if not texts:
            return []

        if batch_size is None:
            batch_size = self.BATCH_SIZE

        try:
            logger.info(
                f"Generating embeddings for {len(texts)} texts with batch size {batch_size}"
            )
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=False,  # Keep as tensors for consistency
            )

            # Convert to list of lists for JSON serialization
            result = [embedding.tolist() for embedding in embeddings]
            logger.info(f"Generated {len(result)} embeddings")
            return result

        except Exception as e:
            raise EmbeddingsError(f"Embedding generation failed: {str(e)}") from e

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text string to embed.

        Returns:
            Embedding vector as list of floats.

        Raises:
            EmbeddingsError: If embedding generation fails.
        """
        return self.embed_texts([text], batch_size=1)[0]

    @staticmethod
    def compute_similarity(
        embedding1: list[float], embedding2: list[float], metric: str = "cosine"
    ) -> float:
        """
        Compute similarity between two embeddings.

        Args:
            embedding1: First embedding vector.
            embedding2: Second embedding vector.
            metric: Similarity metric ('cosine' or 'euclidean').

        Returns:
            Similarity score (higher is more similar).

        Raises:
            ValueError: If metric is unknown.
        """
        v1 = np.array(embedding1, dtype=np.float32)
        v2 = np.array(embedding2, dtype=np.float32)

        if metric == "cosine":
            # Cosine similarity: dot product of normalized vectors
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(np.dot(v1, v2) / (norm1 * norm2))
        elif metric == "euclidean":
            # Euclidean distance: negative distance (smaller distance = higher similarity)
            distance = np.linalg.norm(v1 - v2)
            return float(-distance)
        else:
            raise ValueError(f"Unknown similarity metric: {metric}")

    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model metadata.
        """
        return {
            "model_name": self.MODEL_NAME,
            "embedding_dimension": self.EMBEDDING_DIM,
            "batch_size": self.BATCH_SIZE,
            "max_seq_length": self.model.get_max_seq_length(),
        }
