"""
Embedding service for generating vector embeddings.

@CODE:DATABASE-PKG-010
"""

from __future__ import annotations

import os
import asyncio
import logging
from typing import List, cast

import httpx
import numpy as np

logger = logging.getLogger(__name__)

# OpenAI API settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIMENSIONS = 1536

__all__ = ["EmbeddingService", "EMBEDDING_DIMENSIONS"]

# Try to import optimized embedding service
try:
    from apps.search.vector_engine import EmbeddingService as OptimizedEmbeddingService  # type: ignore[import-not-found]
    OPTIMIZED_EMBEDDING_AVAILABLE = True
except ImportError:
    OPTIMIZED_EMBEDDING_AVAILABLE = False


class EmbeddingService:
    """Embedding generation service (upgraded version)."""

    @staticmethod
    async def generate_embedding(text: str, model: str = "openai") -> List[float]:
        """Generate embedding (use optimized version first)."""
        # Use optimized version (with caching support)
        if OPTIMIZED_EMBEDDING_AVAILABLE:
            try:
                embedding_array = await OptimizedEmbeddingService.generate_embedding(
                    text, model
                )
                return cast(List[float], embedding_array.tolist())
            except Exception as e:
                logger.warning(f"Optimized embedding failed, using fallback: {e}")

        # Fallback: existing method
        if model == "dummy" or not OPENAI_API_KEY:
            logger.info("Using dummy embedding")
            return EmbeddingService._get_dummy_embedding(text)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "input": text[:8000],  # Token limit
                        "model": OPENAI_EMBEDDING_MODEL,
                    },
                    timeout=30.0,
                )

                if response.status_code != 200:
                    logger.error(f"OpenAI API error: {response.status_code}")
                    return EmbeddingService._get_dummy_embedding(text)

                result = response.json()
                return cast(List[float], result["data"][0]["embedding"])

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return EmbeddingService._get_dummy_embedding(text)

    @staticmethod
    def _get_dummy_embedding(text: str) -> List[float]:
        """Generate dummy embedding (for development/testing)."""
        # Text hash-based consistent dummy vector
        seed = hash(text) % (2**32)
        np.random.seed(seed)
        embedding = np.random.normal(0, 1, EMBEDDING_DIMENSIONS)
        # L2 normalization
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return cast(List[float], embedding.tolist())

    @staticmethod
    async def generate_batch_embeddings(
        texts: List[str], batch_size: int = 100
    ) -> List[List[float]]:
        """Generate embeddings in batch."""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_embeddings = []

            for text_content in batch_texts:
                embedding = await EmbeddingService.generate_embedding(text_content)
                batch_embeddings.append(embedding)

            embeddings.extend(batch_embeddings)

            # Consider API rate limits
            if len(batch_texts) > 1:
                await asyncio.sleep(0.1)

        return embeddings
