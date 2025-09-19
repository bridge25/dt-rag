"""
하이브리드 검색 시스템 패키지 초기화
"""

from .hybrid_search_engine import (
    HybridSearchEngine,
    SearchConfig,
    SearchResult,
    SearchResponse,
    SearchEngineFactory,
    get_search_engine,
    set_search_engine
)

from .bm25_engine import BM25Engine, OptimizedBM25
from .vector_engine import VectorEngine, OptimizedVectorEngine, EmbeddingService
from .hybrid_fusion import (
    HybridScoreFusion,
    AdaptiveFusion,
    FusionMethod,
    NormalizationMethod,
    SearchCandidate
)
from .cross_encoder_reranker import (
    CrossEncoderReranker,
    MultiStageReranker,
    RerankingCandidate
)
from .optimization import (
    SearchCache,
    CacheConfig,
    QueryOptimizer,
    IndexOptimizer,
    BatchProcessor,
    PerformanceMonitor,
    get_cache,
    get_performance_monitor,
    cache_result
)

__version__ = "1.0.0"
__author__ = "DT-RAG Team"

__all__ = [
    # Main engine
    "HybridSearchEngine",
    "SearchConfig",
    "SearchResult",
    "SearchResponse",
    "SearchEngineFactory",
    "get_search_engine",
    "set_search_engine",

    # Search engines
    "BM25Engine",
    "OptimizedBM25",
    "VectorEngine",
    "OptimizedVectorEngine",
    "EmbeddingService",

    # Fusion
    "HybridScoreFusion",
    "AdaptiveFusion",
    "FusionMethod",
    "NormalizationMethod",
    "SearchCandidate",

    # Reranking
    "CrossEncoderReranker",
    "MultiStageReranker",
    "RerankingCandidate",

    # Optimization
    "SearchCache",
    "CacheConfig",
    "QueryOptimizer",
    "IndexOptimizer",
    "BatchProcessor",
    "PerformanceMonitor",
    "get_cache",
    "get_performance_monitor",
    "cache_result"
]