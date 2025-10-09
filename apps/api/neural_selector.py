"""
Neural Case Selector - Vector similarity search for CaseBank

@SPEC:NEURAL-001 @IMPL:NEURAL-001:0.1
Implements pgvector-based similarity search and hybrid score fusion.

Performance targets:
- Vector search latency: < 100ms
- Hybrid score calculation: < 10ms
- Memory overhead: < 100MB per search
"""

import asyncio
import logging
import time
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


class NeuralSearchTimeoutError(Exception):
    """Raised when vector search exceeds timeout"""

    pass


class EmbeddingGenerationError(Exception):
    """Raised when embedding generation fails"""

    pass


# @IMPL:NEURAL-001:0.1
async def vector_similarity_search(
    session: AsyncSession,
    query_embedding: List[float],
    limit: int = 10,
    timeout: float = 0.1,
) -> List[Dict[str, Any]]:
    """
    Perform pgvector cosine similarity search on CaseBank

    Args:
        session: Async database session
        query_embedding: Query embedding vector (1536 dimensions)
        limit: Maximum results to return
        timeout: Search timeout in seconds (default 100ms)

    Returns:
        List of cases sorted by cosine similarity (descending)

    Raises:
        asyncio.TimeoutError: If search exceeds timeout
        ValueError: If query_embedding is not 1536 dimensions

    Examples:
        >>> async with async_session() as session:
        ...     embedding = [0.1] * 1536
        ...     results = await vector_similarity_search(session, embedding, limit=5)
        ...     print(f"Found {len(results)} similar cases")
    """
    # Input validation
    if not query_embedding or len(query_embedding) != 1536:
        raise ValueError(
            f"Query embedding must be 1536 dimensions, got {len(query_embedding) if query_embedding else 0}"
        )

    start_time = time.time()

    # Build vector search query
    vector_query = text("""
        SELECT
            case_id,
            query,
            response_text,
            category_path,
            1.0 - (query_vector <=> :query_vector::vector) AS score
        FROM case_bank
        WHERE query_vector IS NOT NULL
        ORDER BY query_vector <=> :query_vector::vector
        LIMIT :limit
    """)

    # Convert Python list to pgvector string format
    vector_str = _format_vector_for_postgres(query_embedding)

    try:
        # Execute with timeout
        result = await asyncio.wait_for(
            session.execute(vector_query, {"query_vector": vector_str, "limit": limit}),
            timeout=timeout,
        )

        rows = result.fetchall()

        # Convert to dict format
        results = []
        for row in rows:
            results.append(
                {
                    "case_id": row[0],
                    "query": row[1],
                    "response_text": row[2],
                    "category_path": row[3],
                    "score": float(row[4]),
                }
            )

        # Log performance metrics
        latency = time.time() - start_time
        logger.info(
            "Vector search completed",
            extra={
                "latency_ms": latency * 1000,
                "results_count": len(results),
                "limit": limit,
                "timeout_ms": timeout * 1000,
            },
        )

        return results

    except asyncio.TimeoutError:
        latency = time.time() - start_time
        logger.warning(
            "Vector search timeout exceeded",
            extra={
                "timeout_ms": timeout * 1000,
                "latency_ms": latency * 1000,
                "limit": limit,
            },
        )
        raise NeuralSearchTimeoutError(f"Vector search timeout after {timeout}s")


# @IMPL:NEURAL-001:0.2
def normalize_scores(scores: List[float]) -> List[float]:
    """
    Min-Max normalization to [0, 1] range

    Args:
        scores: Raw scores to normalize

    Returns:
        Normalized scores in [0, 1] range

    Examples:
        >>> normalize_scores([0.1, 0.5, 0.9])
        [0.0, 0.5, 1.0]

        >>> normalize_scores([0.7, 0.7, 0.7])
        [1.0, 1.0, 1.0]
    """
    if not scores:
        return []

    if len(scores) == 1:
        return [1.0]

    min_score = min(scores)
    max_score = max(scores)

    # Handle identical scores (avoid division by zero)
    if min_score == max_score:
        return [1.0] * len(scores)

    # Min-Max scaling
    return [(s - min_score) / (max_score - min_score) for s in scores]


# @IMPL:NEURAL-001:0.3
def calculate_hybrid_score(
    vector_scores: List[float],
    bm25_scores: List[float],
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
) -> List[float]:
    """
    Calculate hybrid scores by combining vector and BM25 scores

    Args:
        vector_scores: Vector similarity scores
        bm25_scores: BM25 relevance scores
        vector_weight: Weight for vector scores (default 0.7)
        bm25_weight: Weight for BM25 scores (default 0.3)

    Returns:
        Hybrid scores (weighted combination)

    Examples:
        >>> vector = [0.9, 0.7, 0.5]
        >>> bm25 = [0.6, 0.8, 0.4]
        >>> calculate_hybrid_score(vector, bm25)
        [0.85, 0.65, 0.0]  # After normalization and weighting
    """
    if not vector_scores or not bm25_scores:
        return []

    # Normalize both score sets
    normalized_vector = normalize_scores(vector_scores)
    normalized_bm25 = normalize_scores(bm25_scores)

    # Apply weighted combination
    hybrid = [
        vector_weight * v + bm25_weight * b
        for v, b in zip(normalized_vector, normalized_bm25)
    ]

    return hybrid


# @IMPL:NEURAL-001:0.5.2
def _format_vector_for_postgres(vector: List[float]) -> str:
    """
    Convert Python list to PostgreSQL vector string format

    Args:
        vector: Python list of floats

    Returns:
        String in format '[0.1,0.2,0.3]'
    """
    return "[" + ",".join(map(str, vector)) + "]"


# @IMPL:NEURAL-001:0.5.1
def _build_vector_search_query() -> str:
    """
    Build pgvector cosine similarity search SQL query

    Returns:
        SQL query string with pgvector operators
    """
    return """
        SELECT
            case_id,
            query,
            response_text,
            category_path,
            1.0 - (query_vector <=> :query_vector::vector) AS score
        FROM case_bank
        WHERE query_vector IS NOT NULL
        ORDER BY query_vector <=> :query_vector::vector
        LIMIT :limit
    """
