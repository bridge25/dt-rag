"""
BM25 scoring implementation.

@CODE:DATABASE-PKG-009
"""

from __future__ import annotations

import re
from typing import Dict, Any, List

import numpy as np

# BM25 parameters
BM25_K1 = 1.5  # Term frequency adjustment
BM25_B = 0.75  # Document length normalization

__all__ = ["BM25Scorer", "BM25_K1", "BM25_B"]


class BM25Scorer:
    """BM25 scoring implementation."""

    @staticmethod
    def preprocess_text(text: str) -> List[str]:
        """Text preprocessing and tokenization."""
        # Convert to lowercase
        text = text.lower()

        # Remove special characters (keep Korean, English, numbers only)
        text = re.sub(r"[^\w\s가-힣]", " ", text)

        # Remove consecutive spaces
        text = re.sub(r"\s+", " ", text)

        # Tokenize (word-based)
        tokens = text.split()

        # Remove stopwords (basic ones)
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "은",
            "는",
            "이",
            "가",
            "을",
            "를",
            "에",
            "의",
            "와",
            "과",
        }
        tokens = [
            token for token in tokens if token not in stopwords and len(token) > 1
        ]

        return tokens

    @staticmethod
    def calculate_bm25_score(
        query_tokens: List[str], doc_tokens: List[str], corpus_stats: Dict[str, Any]
    ) -> float:
        """Calculate BM25 score."""
        if not query_tokens or not doc_tokens:
            return 0.0

        doc_length = len(doc_tokens)
        avg_doc_length = corpus_stats.get("avg_doc_length", doc_length)
        total_docs = corpus_stats.get("total_docs", 1)

        score = 0.0

        for query_token in query_tokens:
            # Term frequency in document
            tf = doc_tokens.count(query_token)
            if tf == 0:
                continue

            # Inverse document frequency (simplified version)
            doc_freq = corpus_stats.get("term_doc_freq", {}).get(query_token, 1)
            idf = np.log((total_docs - doc_freq + 0.5) / (doc_freq + 0.5))

            # BM25 formula
            normalized_tf = (tf * (BM25_K1 + 1)) / (
                tf + BM25_K1 * (1 - BM25_B + BM25_B * (doc_length / avg_doc_length))
            )

            score += idf * normalized_tf

        return max(0.0, score)
