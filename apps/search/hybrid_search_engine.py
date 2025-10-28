"""
Hybrid Search Engine Implementation for DT-RAG v1.8.1

Combines BM25 keyword search with vector similarity search using:
- PostgreSQL Full-text Search for BM25
- pgvector for efficient vector similarity computation
- Cross-encoder reranking for result quality improvement
- Advanced score normalization and fusion algorithms

Performance targets:
- Recall@10 ≥ 0.85
- Search latency p95 ≤ 1s
- Cost ≤ ₩3/search
"""

# @CODE:SEARCH-001 | SPEC: .moai/specs/SPEC-SEARCH-001/spec.md | TEST: tests/test_hybrid_search.py

import time
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass, field
import json
import hashlib

# PostgreSQL and pgvector imports
from sqlalchemy import text

# Direct imports (순환 참조 해결: core.db_session 분리)
from ..api.embedding_service import embedding_service


# Lazy import to avoid circular dependency
# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
def _get_db_manager() -> Any:
    from ..api.database import db_manager

    return db_manager


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
def _get_search_metrics() -> Any:
    from ..api.database import search_metrics

    return search_metrics


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
def _get_search_dao() -> Any:
    from ..api.database import SearchDAO

    return SearchDAO


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sentry monitoring integration
try:
    from ..api.monitoring.sentry_reporter import (
        report_search_failure,
        report_score_normalization_error,
        report_reranker_error,
        add_search_breadcrumb,
    )

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logger.debug("Sentry monitoring not available")


@dataclass
class SearchResult:
    chunk_id: str
    text: str
    title: Optional[str] = None
    source_url: Optional[str] = None
    taxonomy_path: List[str] = field(default_factory=list)
    bm25_score: float = 0.0
    vector_score: float = 0.0
    hybrid_score: float = 0.0
    rerank_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchMetrics:
    total_time: float = 0.0
    bm25_time: float = 0.0
    vector_time: float = 0.0
    embedding_time: float = 0.0
    fusion_time: float = 0.0
    rerank_time: float = 0.0
    bm25_candidates: int = 0
    vector_candidates: int = 0
    final_results: int = 0
    cache_hit: bool = False


class ScoreNormalizer:

    @staticmethod
    def min_max_normalize(scores: List[float]) -> List[float]:
        try:
            if not scores or len(scores) == 1:
                return scores

            min_score = min(scores)
            max_score = max(scores)

            if max_score == min_score:
                return [1.0] * len(scores)

            return [(score - min_score) / (max_score - min_score) for score in scores]
        except Exception as e:
            logger.error(f"Min-max normalization failed: {e}")
            if SENTRY_AVAILABLE:
                report_score_normalization_error(
                    error=e,
                    scores=scores,
                    normalization_method="min_max",
                    context={"operation": "min_max_normalize"},
                )
            return scores  # Fallback: return original scores

    @staticmethod
    def z_score_normalize(scores: List[float]) -> List[float]:
        try:
            if not scores or len(scores) == 1:
                return scores

            mean_score = np.mean(scores)
            std_score = np.std(scores)

            if std_score == 0:
                return [0.0] * len(scores)

            return [(score - mean_score) / std_score for score in scores]
        except Exception as e:
            logger.error(f"Z-score normalization failed: {e}")
            if SENTRY_AVAILABLE:
                report_score_normalization_error(
                    error=e,
                    scores=scores,
                    normalization_method="z_score",
                    context={"operation": "z_score_normalize"},
                )
            return scores  # Fallback: return original scores

    @staticmethod
    def reciprocal_rank_normalize(scores: List[float]) -> List[float]:
        """Reciprocal rank fusion normalization"""
        try:
            # Sort indices by scores (descending)
            sorted_indices = sorted(
                range(len(scores)), key=lambda i: scores[i], reverse=True
            )

            # Calculate reciprocal ranks
            normalized = [0.0] * len(scores)
            for rank, idx in enumerate(sorted_indices):
                normalized[idx] = 1.0 / (rank + 60)  # RRF constant k=60

            return normalized
        except Exception as e:
            logger.error(f"RRF normalization failed: {e}")
            if SENTRY_AVAILABLE:
                report_score_normalization_error(
                    error=e,
                    scores=scores,
                    normalization_method="reciprocal_rank",
                    context={"operation": "reciprocal_rank_normalize"},
                )
            return scores  # Fallback: return original scores


class HybridScoreFusion:
    """Advanced score fusion algorithms"""

    def __init__(
        self,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
        normalization: str = "min_max",
    ):
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.normalization = normalization

        # Ensure weights sum to 1.0
        total_weight = bm25_weight + vector_weight
        if total_weight != 1.0:
            self.bm25_weight = bm25_weight / total_weight
            self.vector_weight = vector_weight / total_weight

    def fuse_scores(
        self, bm25_scores: List[float], vector_scores: List[float]
    ) -> List[float]:
        """Fuse BM25 and vector scores with advanced normalization"""
        if len(bm25_scores) != len(vector_scores):
            raise ValueError("Score lists must have equal length")

        # Apply normalization
        if self.normalization == "min_max":
            norm_bm25 = ScoreNormalizer.min_max_normalize(bm25_scores)
            norm_vector = ScoreNormalizer.min_max_normalize(vector_scores)
        elif self.normalization == "z_score":
            norm_bm25 = ScoreNormalizer.z_score_normalize(bm25_scores)
            norm_vector = ScoreNormalizer.z_score_normalize(vector_scores)
        elif self.normalization == "rrf":
            norm_bm25 = ScoreNormalizer.reciprocal_rank_normalize(bm25_scores)
            norm_vector = ScoreNormalizer.reciprocal_rank_normalize(vector_scores)
        else:
            norm_bm25 = bm25_scores
            norm_vector = vector_scores

        # Weighted combination
        hybrid_scores = [
            self.bm25_weight * bm25 + self.vector_weight * vector
            for bm25, vector in zip(norm_bm25, norm_vector)
        ]

        return hybrid_scores

    def adaptive_fusion(
        self,
        bm25_scores: List[float],
        vector_scores: List[float],
        query_characteristics: Dict[str, float],
    ) -> List[float]:
        """Adaptive fusion based on query characteristics"""
        # Analyze query characteristics
        query_length = query_characteristics.get("length", 1.0)
        has_exact_terms = query_characteristics.get("exact_terms", False)
        semantic_complexity = query_characteristics.get("semantic_complexity", 0.5)

        # Adjust weights based on query characteristics
        if query_length <= 3 and has_exact_terms:
            # Short, specific queries favor BM25
            adaptive_bm25_weight = min(0.8, self.bm25_weight + 0.2)
            adaptive_vector_weight = 1.0 - adaptive_bm25_weight
        elif semantic_complexity > 0.7:
            # Complex semantic queries favor vector search
            adaptive_vector_weight = min(0.8, self.vector_weight + 0.2)
            adaptive_bm25_weight = 1.0 - adaptive_vector_weight
        else:
            # Balanced approach
            adaptive_bm25_weight = self.bm25_weight
            adaptive_vector_weight = self.vector_weight

        # Apply adaptive weights
        norm_bm25 = ScoreNormalizer.min_max_normalize(bm25_scores)
        norm_vector = ScoreNormalizer.min_max_normalize(vector_scores)

        hybrid_scores = [
            adaptive_bm25_weight * bm25 + adaptive_vector_weight * vector
            for bm25, vector in zip(norm_bm25, norm_vector)
        ]

        return hybrid_scores


class CrossEncoderReranker:
    """Cross-encoder reranking for result quality improvement"""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        self.model_name = model_name
        self.model = None
        self._load_model()

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def _load_model(self) -> None:
        """Load cross-encoder model"""
        try:
            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(self.model_name)
            logger.info(f"Cross-encoder model {self.model_name} loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load cross-encoder model: {e}")
            self.model = None

    def rerank(
        self, query: str, search_results: List[SearchResult], top_k: int = 5
    ) -> List[SearchResult]:
        """Rerank search results using cross-encoder"""
        if not search_results:
            return []

        start_time = time.time()

        try:
            # Use actual cross-encoder model if available
            if self.model:
                # Prepare query-document pairs for cross-encoder
                pairs = [[query, result.text] for result in search_results]

                # Get cross-encoder scores
                cross_scores = self.model.predict(pairs)

                # Apply cross-encoder scores
                for result, score in zip(search_results, cross_scores):
                    result.rerank_score = float(score)

                # Sort by rerank score and return top-k
                final_results = sorted(
                    search_results, key=lambda x: x.rerank_score, reverse=True
                )[:top_k]
            else:
                # Fallback to heuristic reranking
                reranked_results = self._heuristic_rerank(query, search_results)

                # Apply rerank scores
                for result in reranked_results:
                    result.rerank_score = (
                        result.hybrid_score
                        * self._calculate_quality_boost(query, result.text)
                    )

                # Sort by rerank score and return top-k
                final_results = sorted(
                    reranked_results, key=lambda x: x.rerank_score, reverse=True
                )[:top_k]

            rerank_time = time.time() - start_time
            logger.info(f"Cross-encoder reranking completed in {rerank_time:.3f}s")

            return final_results

        except Exception as e:
            logger.error(f"Reranking failed: {e}")

            # Report to Sentry with reranker-specific context
            if SENTRY_AVAILABLE:
                report_reranker_error(
                    error=e,
                    query=query,
                    results_count=len(search_results),
                    rerank_config={"model_name": self.model_name, "top_k": top_k},
                )

            # Fallback: return top results by hybrid score
            return sorted(search_results, key=lambda x: x.hybrid_score, reverse=True)[
                :top_k
            ]

    def _heuristic_rerank(
        self, query: str, results: List[SearchResult]
    ) -> List[SearchResult]:
        """Enhanced heuristic reranking"""
        query_terms = set(query.lower().split())

        for result in results:
            text_terms = set(result.text.lower().split())

            # Calculate additional quality signals
            term_overlap = len(query_terms.intersection(text_terms)) / len(query_terms)
            text_length_penalty = self._calculate_length_penalty(len(result.text))
            diversity_bonus = self._calculate_diversity_bonus(result, results)

            # Combine signals
            quality_multiplier = (
                1.0
                + 0.2 * term_overlap
                + 0.1 * text_length_penalty
                + 0.1 * diversity_bonus
            )

            result.rerank_score = result.hybrid_score * quality_multiplier

        return results

    def _calculate_quality_boost(self, query: str, text: str) -> float:
        """Calculate quality boost based on query-text match"""
        # Position bonus for early matches
        query_lower = query.lower()
        text_lower = text.lower()

        position_bonus = 1.0
        if query_lower in text_lower:
            position = text_lower.find(query_lower)
            position_bonus = 1.2 - (position / len(text_lower)) * 0.2

        # Length appropriateness
        length_score = self._calculate_length_penalty(len(text))

        return position_bonus * (1.0 + length_score * 0.1)

    def _calculate_length_penalty(self, text_length: int) -> float:
        """Calculate penalty/bonus based on text length"""
        if text_length < 50:
            return 0.7  # Too short
        elif text_length > 1000:
            return 0.8  # Too long
        elif 100 <= text_length <= 500:
            return 1.0  # Optimal length
        else:
            return 0.9  # Acceptable length

    def _calculate_diversity_bonus(
        self, result: SearchResult, all_results: List[SearchResult]
    ) -> float:
        """Calculate diversity bonus to avoid redundant results"""
        # Simple diversity based on source and taxonomy
        unique_sources = len(set(r.source_url for r in all_results if r.source_url))
        unique_taxonomies = len(set(str(r.taxonomy_path) for r in all_results))

        # Bonus for results from diverse sources
        diversity_score = min(1.0, (unique_sources + unique_taxonomies) / 10.0)
        return diversity_score


class ResultCache:
    """In-memory cache for search results"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600) -> None:
        self.cache: Dict[str, List[SearchResult]] = {}
        self.access_times: Dict[str, float] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

    def _generate_cache_key(
        self, query: str, filters: Dict[str, Any], top_k: int
    ) -> str:
        """Generate cache key for query"""
        key_data = {"query": query, "filters": filters, "top_k": top_k}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(
        self, query: str, filters: Dict[str, Any], top_k: int
    ) -> Optional[List[SearchResult]]:
        """Get cached results"""
        cache_key = self._generate_cache_key(query, filters, top_k)

        if cache_key in self.cache:
            cached_time = self.access_times[cache_key]
            if time.time() - cached_time < self.ttl_seconds:
                # Update access time
                self.access_times[cache_key] = time.time()
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return self.cache[cache_key]
            else:
                # Expired
                del self.cache[cache_key]
                del self.access_times[cache_key]

        return None

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def put(
        self,
        query: str,
        filters: Dict[str, Any],
        top_k: int,
        results: List[SearchResult],
    ) -> None:
        """Cache search results"""
        cache_key = self._generate_cache_key(query, filters, top_k)

        # Evict old entries if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        self.cache[cache_key] = results
        self.access_times[cache_key] = time.time()
        logger.debug(f"Cached results for query: {query[:50]}...")

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def _evict_oldest(self) -> None:
        """Evict oldest cache entry"""
        if not self.access_times:
            return

        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[oldest_key]
        del self.access_times[oldest_key]

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.access_times.clear()

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": getattr(self, "_hit_count", 0)
            / max(1, getattr(self, "_total_requests", 1)),
        }


class HybridSearchEngine:
    """Main hybrid search engine combining BM25 and vector search"""

    def __init__(
        self,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
        enable_caching: bool = True,
        enable_reranking: bool = True,
        normalization: str = "min_max",
    ):

        self.score_fusion = HybridScoreFusion(
            bm25_weight=bm25_weight,
            vector_weight=vector_weight,
            normalization=normalization,
        )

        self.reranker = CrossEncoderReranker() if enable_reranking else None
        self.cache = ResultCache() if enable_caching else None

        self.config = {
            "bm25_weight": bm25_weight,
            "vector_weight": vector_weight,
            "enable_caching": enable_caching,
            "enable_reranking": enable_reranking,
            "normalization": normalization,
        }

        logger.info(f"Hybrid search engine initialized: {self.config}")

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        bm25_candidates: int = 50,
        vector_candidates: int = 50,
        correlation_id: Optional[str] = None,
    ) -> Tuple[List[SearchResult], SearchMetrics]:
        """Perform hybrid search combining BM25 and vector similarity"""

        start_time = time.time()
        metrics = SearchMetrics()

        # Normalize inputs
        query = query.strip()
        if not query:
            return [], metrics

        filters = filters or {}

        try:
            # Add breadcrumb for search tracking with correlation
            if SENTRY_AVAILABLE:
                add_search_breadcrumb(
                    query=query,
                    search_type="hybrid",
                    top_k=top_k,
                    has_filters=bool(filters),
                    correlation_id=correlation_id,
                )

            # Check cache first
            if self.cache:
                cached_results = self.cache.get(query, filters, top_k)
                if cached_results:
                    metrics.total_time = time.time() - start_time
                    metrics.cache_hit = True
                    metrics.final_results = len(cached_results)
                    _get_search_metrics().record_search("hybrid", metrics.total_time)

                    # Breadcrumb for cache hit
                    if SENTRY_AVAILABLE:
                        add_search_breadcrumb(
                            query=query,
                            search_type="hybrid_cache_hit",
                            results=len(cached_results),
                            response_time_ms=metrics.total_time * 1000,
                            correlation_id=correlation_id,
                        )

                    return cached_results, metrics

            # Generate query embedding
            embedding_start = time.time()
            query_embedding = await embedding_service.generate_embedding(query)
            metrics.embedding_time = time.time() - embedding_start

            # Parallel execution of BM25 and vector search
            bm25_task = self._perform_bm25_search(query, bm25_candidates, filters)
            vector_task = self._perform_vector_search(
                query_embedding, vector_candidates, filters
            )

            bm25_results, vector_results = await asyncio.gather(
                bm25_task, vector_task, return_exceptions=True
            )

            # Handle exceptions
            if isinstance(bm25_results, Exception):
                logger.error(f"BM25 search failed: {bm25_results}")
                bm25_results = []

            if isinstance(vector_results, Exception):
                logger.error(f"Vector search failed: {vector_results}")
                vector_results = []

            metrics.bm25_candidates = len(bm25_results)
            metrics.vector_candidates = len(vector_results)

            # Fuse results
            fusion_start = time.time()
            fused_results = self._fuse_results(query, bm25_results, vector_results)
            metrics.fusion_time = time.time() - fusion_start

            # Apply cross-encoder reranking
            final_results = fused_results
            if self.reranker and fused_results:
                rerank_start = time.time()
                final_results = self.reranker.rerank(query, fused_results, top_k)
                metrics.rerank_time = time.time() - rerank_start
            else:
                # Simple sorting by hybrid score
                final_results = sorted(
                    fused_results, key=lambda x: x.hybrid_score, reverse=True
                )[:top_k]

            metrics.final_results = len(final_results)
            metrics.total_time = time.time() - start_time

            # Cache results
            if self.cache and final_results:
                self.cache.put(query, filters, top_k, final_results)

            # Record metrics
            _get_search_metrics().record_search("hybrid", metrics.total_time)

            logger.info(
                f"Hybrid search completed: {len(final_results)} results in {metrics.total_time:.3f}s"
            )

            return final_results, metrics

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            metrics.total_time = time.time() - start_time
            _get_search_metrics().record_search(
                "hybrid", metrics.total_time, error=True
            )

            # Report to Sentry with comprehensive context
            if SENTRY_AVAILABLE:
                report_search_failure(
                    error=e,
                    query=query,
                    filters=filters,
                    metrics={
                        "total_time": metrics.total_time,
                        "bm25_time": metrics.bm25_time,
                        "vector_time": metrics.vector_time,
                        "embedding_time": metrics.embedding_time,
                        "fusion_time": metrics.fusion_time,
                        "rerank_time": metrics.rerank_time,
                        "bm25_candidates": metrics.bm25_candidates,
                        "vector_candidates": metrics.vector_candidates,
                        "final_results": metrics.final_results,
                        "cache_hit": metrics.cache_hit,
                    },
                    search_type="hybrid",
                    error_boundary="hybrid_search_engine",
                )

            return [], metrics

    async def _perform_bm25_search(
        self, query: str, top_k: int, filters: Dict[str, Any]
    ) -> List[SearchResult]:
        """Perform BM25 keyword search using PostgreSQL FTS"""
        start_time = time.time()

        try:
            db_mgr = _get_db_manager()
            async with db_mgr.async_session() as session:
                # Build filter clause
                filter_clause, filter_params = self._build_filter_clause(filters)

                # Check if PostgreSQL or SQLite
                if "postgresql" in str(db_mgr.engine.url):
                    # PostgreSQL full-text search with BM25-like ranking
                    bm25_query = text(
                        f"""
                        SELECT
                            c.chunk_id,
                            c.text,
                            d.source_url as title,
                            d.source_url,
                            dt.path as taxonomy_path,
                            ts_rank_cd(
                                to_tsvector('english', c.text),
                                plainto_tsquery('english', :query),
                                32 | 1  -- normalization flags for length and term frequency
                            ) as bm25_score
                        FROM chunks c
                        JOIN documents d ON c.doc_id = d.doc_id
                        LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                        WHERE to_tsvector('english', c.text) @@ plainto_tsquery('english', :query)
                        {filter_clause}
                        ORDER BY bm25_score DESC
                        LIMIT :top_k
                    """
                    )
                else:
                    # SQLite FTS fallback
                    bm25_query = text(
                        f"""
                        SELECT
                            c.chunk_id,
                            c.text,
                            d.source_url as title,
                            d.source_url,
                            dt.path as taxonomy_path,
                            bm25(chunks_fts) as bm25_score
                        FROM chunks_fts
                        JOIN chunks c ON chunks_fts.chunk_id = c.chunk_id
                        JOIN documents d ON c.doc_id = d.doc_id
                        LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                        WHERE chunks_fts MATCH :query
                        {filter_clause}
                        ORDER BY bm25_score DESC
                        LIMIT :top_k
                    """
                    )

                query_params = {"query": query, "top_k": top_k, **filter_params}
                result = await session.execute(bm25_query, query_params)
                rows = result.fetchall()

                # Convert to SearchResult objects
                search_results = []
                for row in rows:
                    search_result = SearchResult(
                        chunk_id=str(row[0]),
                        text=row[1],
                        title=row[2],
                        source_url=row[3],
                        taxonomy_path=row[4] if row[4] else [],
                        bm25_score=float(row[5]) if row[5] else 0.0,
                        vector_score=0.0,
                        metadata={
                            "search_type": "bm25",
                            "raw_bm25_score": float(row[5]) if row[5] else 0.0,
                        },
                    )
                    search_results.append(search_result)

                bm25_time = time.time() - start_time
                logger.debug(
                    f"BM25 search: {len(search_results)} results in {bm25_time:.3f}s"
                )

                return search_results

        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []

    async def _perform_vector_search(
        self, query_embedding: List[float], top_k: int, filters: Dict[str, Any]
    ) -> List[SearchResult]:
        """Perform vector similarity search using pgvector"""
        start_time = time.time()

        try:
            db_mgr = _get_db_manager()
            async with db_mgr.async_session() as session:
                # Build filter clause
                filter_clause, filter_params = self._build_filter_clause(filters)

                # Check if PostgreSQL with pgvector or SQLite
                if "postgresql" in str(db_mgr.engine.url):
                    # Convert embedding to PostgreSQL vector format
                    vector_str = "[" + ",".join(map(str, query_embedding)) + "]"

                    # pgvector cosine similarity search
                    # Note: Using string formatting for vector to avoid asyncpg named parameter issues
                    vector_query = text(
                        f"""
                        SELECT
                            c.chunk_id,
                            c.text,
                            d.source_url as title,
                            d.source_url,
                            dt.path as taxonomy_path,
                            1 - (e.vec <=> '{vector_str}'::vector) as cosine_similarity
                        FROM chunks c
                        JOIN documents d ON c.doc_id = d.doc_id
                        LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                        JOIN embeddings e ON c.chunk_id = e.chunk_id
                        WHERE e.vec IS NOT NULL
                        {filter_clause}
                        ORDER BY e.vec <=> '{vector_str}'::vector
                        LIMIT :top_k
                    """
                    )
                    query_params = {"top_k": top_k, **filter_params}
                else:
                    # SQLite vector similarity fallback using JSON
                    vector_query = text(
                        f"""
                        SELECT
                            c.chunk_id,
                            c.text,
                            d.source_url as title,
                            d.source_url,
                            dt.path as taxonomy_path,
                            0.5 as cosine_similarity
                        FROM chunks c
                        JOIN documents d ON c.doc_id = d.doc_id
                        LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                        JOIN embeddings e ON c.chunk_id = e.chunk_id
                        WHERE e.vec IS NOT NULL
                        {filter_clause}
                        ORDER BY c.chunk_id
                        LIMIT :top_k
                    """
                    )
                    query_params = {"top_k": top_k, **filter_params}

                result = await session.execute(vector_query, query_params)
                rows = result.fetchall()

                # Convert to SearchResult objects
                search_results = []
                for row in rows:
                    search_result = SearchResult(
                        chunk_id=str(row[0]),
                        text=row[1],
                        title=row[2],
                        source_url=row[3],
                        taxonomy_path=row[4] if row[4] else [],
                        bm25_score=0.0,
                        vector_score=float(row[5]) if row[5] else 0.0,
                        metadata={
                            "search_type": "vector",
                            "raw_cosine_similarity": float(row[5]) if row[5] else 0.0,
                        },
                    )
                    search_results.append(search_result)

                vector_time = time.time() - start_time
                logger.debug(
                    f"Vector search: {len(search_results)} results in {vector_time:.3f}s"
                )

                return search_results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    def _fuse_results(
        self,
        query: str,
        bm25_results: List[SearchResult],
        vector_results: List[SearchResult],
    ) -> List[SearchResult]:
        """Fuse BM25 and vector search results with score normalization"""

        # Create a map of all unique results
        results_map = {}

        # Add BM25 results
        for result in bm25_results:
            results_map[result.chunk_id] = result

        # Merge vector results
        for result in vector_results:
            if result.chunk_id in results_map:
                # Update existing result with vector score
                results_map[result.chunk_id].vector_score = result.vector_score
                results_map[result.chunk_id].metadata.update(result.metadata)
            else:
                # Add new vector-only result
                results_map[result.chunk_id] = result

        # Get all results and extract scores
        all_results = list(results_map.values())
        bm25_scores = [r.bm25_score for r in all_results]
        vector_scores = [r.vector_score for r in all_results]

        # Analyze query characteristics for adaptive fusion
        query_characteristics = self._analyze_query(query)

        # Perform score fusion
        if len(set(bm25_scores + vector_scores)) > 1:  # Check if we have varied scores
            hybrid_scores = self.score_fusion.adaptive_fusion(
                bm25_scores, vector_scores, query_characteristics
            )
        else:
            # Fallback to simple weighted average
            hybrid_scores = [
                self.score_fusion.bm25_weight * bm25
                + self.score_fusion.vector_weight * vector
                for bm25, vector in zip(bm25_scores, vector_scores)
            ]

        # Update results with hybrid scores
        for result, hybrid_score in zip(all_results, hybrid_scores):
            result.hybrid_score = hybrid_score
            result.metadata["fusion_method"] = "adaptive"
            result.metadata["query_characteristics"] = query_characteristics

        return all_results

    def _analyze_query(self, query: str) -> Dict[str, float]:
        """Analyze query characteristics for adaptive fusion"""
        terms = query.split()

        return {
            "length": len(terms),
            "exact_terms": any(
                term.startswith('"') or term.endswith('"') for term in terms
            ),
            "semantic_complexity": min(
                1.0, len([t for t in terms if len(t) > 6]) / max(1, len(terms))
            ),
            "has_operators": any(
                op in query.lower() for op in ["and", "or", "not", "+", "-"]
            ),
            "avg_term_length": sum(len(term) for term in terms) / max(1, len(terms)),
        }

    def _build_filter_clause(
        self, filters: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Build SQL WHERE clause from filters with parameterized queries"""
        if not filters:
            return "", {}

        conditions = []
        params = {}

        # Taxonomy path filtering (SECURE)
        if "taxonomy_paths" in filters:
            paths = filters["taxonomy_paths"]
            if paths:
                path_conditions = []
                for idx, path in enumerate(paths):
                    if isinstance(path, list):
                        valid_segments = []
                        for segment in path:
                            segment_str = str(segment)
                            if (
                                segment_str.replace("_", "")
                                .replace("-", "")
                                .replace(" ", "")
                                .isalnum()
                            ):
                                valid_segments.append(segment_str)

                        if valid_segments:
                            param_name = f"taxonomy_path_{idx}"
                            path_str = '{{"{0}"}}'.format('","'.join(valid_segments))
                            params[param_name] = path_str
                            path_conditions.append(f"dt.path = :{param_name}::text[]")

                if path_conditions:
                    conditions.append(f"({' OR '.join(path_conditions)})")

        # Content type filtering (SECURE with whitelist)
        if "content_types" in filters:
            types = filters["content_types"]
            if types:
                ALLOWED_CONTENT_TYPES = {
                    "text/plain",
                    "text/html",
                    "text/markdown",
                    "application/pdf",
                    "application/json",
                    "article",
                    "tutorial",
                    "documentation",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "text/csv",
                    "application/xml",
                }

                type_conditions = []
                for idx, ct in enumerate(types):
                    ct_str = str(ct)
                    if ct_str in ALLOWED_CONTENT_TYPES:
                        param_name = f"content_type_{idx}"
                        params[param_name] = ct_str
                        type_conditions.append(f"d.content_type = :{param_name}")

                if type_conditions:
                    conditions.append(f"({' OR '.join(type_conditions)})")

        # Date range filtering (SECURE with validation)
        if "date_range" in filters:
            from datetime import datetime

            date_range = filters["date_range"]

            if "start" in date_range:
                try:
                    date_str = str(date_range["start"]).replace("Z", "+00:00")
                    datetime.fromisoformat(date_str)
                    params["date_start"] = date_range["start"]
                    conditions.append("d.processed_at >= :date_start")
                except (ValueError, AttributeError):
                    pass

            if "end" in date_range:
                try:
                    date_str = str(date_range["end"]).replace("Z", "+00:00")
                    datetime.fromisoformat(date_str)
                    params["date_end"] = date_range["end"]
                    conditions.append("d.processed_at <= :date_end")
                except (ValueError, AttributeError):
                    pass

        if conditions:
            return " AND " + " AND ".join(conditions), params

        return "", {}

    async def keyword_only_search(
        self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[SearchResult], SearchMetrics]:
        """Perform BM25 keyword search only"""
        start_time = time.time()
        metrics = SearchMetrics()

        try:
            results = await self._perform_bm25_search(query, top_k, filters or {})

            # Set hybrid scores equal to BM25 scores
            for result in results:
                result.hybrid_score = result.bm25_score

            metrics.total_time = time.time() - start_time
            metrics.bm25_time = metrics.total_time
            metrics.final_results = len(results)

            _get_search_metrics().record_search("bm25", metrics.total_time)

            return results, metrics

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            metrics.total_time = time.time() - start_time
            _get_search_metrics().record_search("bm25", metrics.total_time, error=True)
            return [], metrics

    async def vector_only_search(
        self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[SearchResult], SearchMetrics]:
        """Perform vector similarity search only"""
        start_time = time.time()
        metrics = SearchMetrics()

        try:
            # Generate query embedding
            embedding_start = time.time()
            query_embedding = await embedding_service.generate_embedding(query)
            metrics.embedding_time = time.time() - embedding_start

            results = await self._perform_vector_search(
                query_embedding, top_k, filters or {}
            )

            # Set hybrid scores equal to vector scores
            for result in results:
                result.hybrid_score = result.vector_score

            metrics.total_time = time.time() - start_time
            metrics.vector_time = metrics.total_time - metrics.embedding_time
            metrics.final_results = len(results)

            _get_search_metrics().record_search("vector", metrics.total_time)

            return results, metrics

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            metrics.total_time = time.time() - start_time
            _get_search_metrics().record_search(
                "vector", metrics.total_time, error=True
            )
            return [], metrics

    def get_config(self) -> Dict[str, Any]:
        """Get current search engine configuration"""
        config = self.config.copy()
        if self.cache:
            config["cache_stats"] = self.cache.get_stats()
        return config

    def update_config(self, **kwargs: Any) -> None:
        """Update search engine configuration"""
        if "bm25_weight" in kwargs or "vector_weight" in kwargs:
            bm25_weight = kwargs.get("bm25_weight", self.config["bm25_weight"])
            vector_weight = kwargs.get("vector_weight", self.config["vector_weight"])

            # Ensure weights sum to 1.0
            total = bm25_weight + vector_weight
            if total > 0:
                bm25_weight = bm25_weight / total
                vector_weight = vector_weight / total

            self.score_fusion.bm25_weight = bm25_weight
            self.score_fusion.vector_weight = vector_weight
            self.config["bm25_weight"] = bm25_weight
            self.config["vector_weight"] = vector_weight

        if "normalization" in kwargs:
            self.score_fusion.normalization = kwargs["normalization"]
            self.config["normalization"] = kwargs["normalization"]

        logger.info(f"Search engine configuration updated: {kwargs}")

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def clear_cache(self) -> None:
        """Clear search result cache"""
        if self.cache:
            self.cache.clear()
            logger.info("Search result cache cleared")


# Global search engine instance
search_engine = HybridSearchEngine()


# Convenience functions for API integration
async def hybrid_search(
    query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None, **kwargs: Any
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Main hybrid search function for API integration"""
    results, metrics = await search_engine.search(query, top_k, filters, **kwargs)

    # Convert to API-compatible format
    api_results = []
    for result in results:
        api_result = {
            "chunk_id": result.chunk_id,
            "text": result.text,
            "title": result.title,
            "source_url": result.source_url,
            "taxonomy_path": result.taxonomy_path,
            "score": (
                result.rerank_score if result.rerank_score > 0 else result.hybrid_score
            ),
            "metadata": {
                **result.metadata,
                "bm25_score": result.bm25_score,
                "vector_score": result.vector_score,
                "hybrid_score": result.hybrid_score,
                "rerank_score": result.rerank_score,
            },
        }
        api_results.append(api_result)

    api_metrics = {
        "total_time": metrics.total_time,
        "bm25_time": metrics.bm25_time,
        "vector_time": metrics.vector_time,
        "embedding_time": metrics.embedding_time,
        "fusion_time": metrics.fusion_time,
        "rerank_time": metrics.rerank_time,
        "candidates_found": {
            "bm25": metrics.bm25_candidates,
            "vector": metrics.vector_candidates,
        },
        "final_results": metrics.final_results,
        "cache_hit": metrics.cache_hit,
    }

    return api_results, api_metrics


async def keyword_search(
    query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """BM25 keyword search only"""
    results, metrics = await search_engine.keyword_only_search(query, top_k, filters)

    # Convert to API format
    api_results = [
        {
            "chunk_id": result.chunk_id,
            "text": result.text,
            "title": result.title,
            "source_url": result.source_url,
            "taxonomy_path": result.taxonomy_path,
            "score": result.bm25_score,
            "metadata": {**result.metadata, "search_type": "bm25_only"},
        }
        for result in results
    ]

    return api_results, {
        "total_time": metrics.total_time,
        "results_count": len(api_results),
    }


async def vector_search(
    query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Vector similarity search only"""
    results, metrics = await search_engine.vector_only_search(query, top_k, filters)

    # Convert to API format
    api_results = [
        {
            "chunk_id": result.chunk_id,
            "text": result.text,
            "title": result.title,
            "source_url": result.source_url,
            "taxonomy_path": result.taxonomy_path,
            "score": result.vector_score,
            "metadata": {**result.metadata, "search_type": "vector_only"},
        }
        for result in results
    ]

    return api_results, {
        "total_time": metrics.total_time,
        "results_count": len(api_results),
    }


def get_search_engine_config() -> Dict[str, Any]:
    """Get search engine configuration"""
    return search_engine.get_config()


def update_search_engine_config(**kwargs: Any) -> None:
    """Update search engine configuration"""
    search_engine.update_config(**kwargs)


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
def clear_search_cache() -> None:
    """Clear search result cache"""
    search_engine.clear_cache()


async def get_search_statistics() -> Dict[str, Any]:
    """Get comprehensive search statistics"""
    try:
        # Get database statistics
        db_mgr = _get_db_manager()
        SearchDAO = _get_search_dao()
        async with db_mgr.async_session() as session:
            db_stats = await SearchDAO.get_search_analytics(session)

        # Get engine statistics
        engine_stats = search_engine.get_config()

        # Get global metrics
        global_metrics = _get_search_metrics().get_metrics()

        return {
            "database_stats": db_stats,
            "engine_config": engine_stats,
            "performance_metrics": global_metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get search statistics: {e}")
        return {"error": str(e)}
