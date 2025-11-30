"""
Cross-encoder reranking implementation.

@CODE:DATABASE-PKG-011
"""

from __future__ import annotations

from typing import Dict, Any, List

__all__ = ["CrossEncoderReranker", "BM25_WEIGHT", "VECTOR_WEIGHT"]

# Hybrid search weights
BM25_WEIGHT = 0.5
VECTOR_WEIGHT = 0.5


class CrossEncoderReranker:
    """Cross-encoder based reranking."""

    @staticmethod
    def rerank_results(
        query: str, search_results: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Rerank search results (simplified version)."""
        if not search_results:
            return []

        # In actual implementation, use BERT-based cross-encoder
        # Here, hybrid score-based reranking

        for result in search_results:
            bm25_score = result.get("metadata", {}).get("bm25_score", 0.0)
            vector_score = result.get("metadata", {}).get("vector_score", 0.0)

            # Calculate hybrid score
            hybrid_score = BM25_WEIGHT * bm25_score + VECTOR_WEIGHT * vector_score

            # Text length correction (penalty for too short or too long text)
            text_length = len(result.get("text", ""))
            length_penalty = 1.0
            if text_length < 50:
                length_penalty = 0.8
            elif text_length > 1000:
                length_penalty = 0.9

            # Query overlap bonus
            query_overlap = CrossEncoderReranker._calculate_query_overlap(
                query.lower(), result.get("text", "").lower()
            )

            # Final score
            final_score = hybrid_score * length_penalty * (1 + 0.1 * query_overlap)
            result["score"] = final_score

        # Sort by score and return top K
        reranked = sorted(search_results, key=lambda x: x["score"], reverse=True)
        return reranked[:top_k]

    @staticmethod
    def _calculate_query_overlap(query: str, text: str) -> float:
        """Calculate overlap between query and text."""
        query_words = set(query.split())
        text_words = set(text.split())

        if not query_words:
            return 0.0

        overlap = len(query_words.intersection(text_words))
        return overlap / len(query_words)
