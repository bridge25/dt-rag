"""
DT-RAG Search Module v1.8.1

High-performance hybrid search engine combining:
- BM25 keyword search using PostgreSQL Full-text Search
- Vector similarity search using pgvector
- Advanced score normalization and fusion algorithms
- Cross-encoder reranking for result quality improvement
- Intelligent caching and performance optimization

Performance targets:
- Recall@10 ≥ 0.85
- Search latency p95 ≤ 1s
- Cost ≤ ₩3/search
"""

__version__ = "1.8.1"

# Export main components
try:
    from .hybrid_search_engine import (
        HybridSearchEngine,
        SearchResult,
        SearchMetrics,
        ScoreNormalizer,
        HybridScoreFusion,
        CrossEncoderReranker,
        ResultCache,
        hybrid_search,
        keyword_search,
        vector_search,
        get_search_engine_config,
        update_search_engine_config,
        clear_search_cache,
        get_search_statistics
    )

    __all__ = [
        "HybridSearchEngine",
        "SearchResult",
        "SearchMetrics",
        "ScoreNormalizer",
        "HybridScoreFusion",
        "CrossEncoderReranker",
        "ResultCache",
        "hybrid_search",
        "keyword_search",
        "vector_search",
        "get_search_engine_config",
        "update_search_engine_config",
        "clear_search_cache",
        "get_search_statistics"
    ]

except ImportError as e:
    # Graceful degradation if dependencies not available
    import logging
    logging.getLogger(__name__).warning(f"Hybrid search engine components not available: {e}")

    __all__ = []