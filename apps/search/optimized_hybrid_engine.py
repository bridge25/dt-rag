"""
Optimized Hybrid Search Engine
High-performance BM25 + Vector similarity search with advanced fusion
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from .optimized_vector_engine import OptimizedVectorEngine, VectorSearchConfig
from .hybrid_fusion import HybridScoreFusion, AdaptiveFusion, FusionMethod, NormalizationMethod
from .optimization import SearchCache, QueryOptimizer, get_cache

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchConfig:
    """Hybrid search configuration"""
    # Search parameters
    bm25_top_k: int = 50
    vector_top_k: int = 50
    final_top_k: int = 10

    # Fusion configuration
    bm25_weight: float = 0.5
    vector_weight: float = 0.5
    fusion_method: FusionMethod = FusionMethod.RRF
    normalization_method: NormalizationMethod = NormalizationMethod.MIN_MAX

    # Performance parameters
    max_parallel_searches: int = 4
    enable_adaptive_fusion: bool = True
    enable_query_expansion: bool = False

    # Cache settings
    cache_ttl: int = 1800  # 30 minutes
    enable_result_caching: bool = True

    # Vector search config
    vector_config: VectorSearchConfig = None

    def __post_init__(self):
        if self.vector_config is None:
            self.vector_config = VectorSearchConfig()


class OptimizedHybridEngine:
    """High-performance hybrid search engine"""

    def __init__(self, config: HybridSearchConfig = None):
        self.config = config or HybridSearchConfig()
        self.vector_engine: Optional[OptimizedVectorEngine] = None
        self.cache: Optional[SearchCache] = None
        self.adaptive_fusion = AdaptiveFusion()

        # Thread pool for CPU-intensive operations
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Performance tracking
        self._stats = {
            'total_searches': 0,
            'cache_hits': 0,
            'avg_latency': 0.0,
            'bm25_avg_time': 0.0,
            'vector_avg_time': 0.0,
            'fusion_avg_time': 0.0
        }

    async def initialize(self):
        """Initialize hybrid search engine"""
        # Initialize vector engine
        self.vector_engine = OptimizedVectorEngine(self.config.vector_config)
        await self.vector_engine.initialize()

        # Initialize cache
        self.cache = await get_cache()

        logger.info("Optimized hybrid search engine initialized")

    async def search(
        self,
        session: AsyncSession,
        query: str,
        filters: Dict[str, Any] = None,
        top_k: int = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        High-performance hybrid search

        Args:
            session: Database session
            query: Search query
            filters: Optional filters
            top_k: Number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of search results with hybrid scores
        """
        start_time = time.time()

        try:
            # Use provided top_k or default
            final_k = top_k or self.config.final_top_k

            # Optimize query
            optimized_query = QueryOptimizer.optimize_query(query)

            # Check cache
            cache_key = self._generate_cache_key(optimized_query, filters, final_k)
            if self.cache and self.config.enable_result_caching:
                cached_result = await self.cache.get_search_results(cache_key, "hybrid")
                if cached_result:
                    self._stats['cache_hits'] += 1
                    return cached_result

            # Perform parallel searches
            bm25_results, vector_results = await self._parallel_search(
                session, optimized_query, filters
            )

            # Apply hybrid fusion
            fusion_start = time.time()
            fused_results = await self._apply_fusion(
                optimized_query, bm25_results, vector_results, final_k
            )
            fusion_time = time.time() - fusion_start

            # Convert to final format
            final_results = self._format_results(fused_results)[:final_k]

            # Cache results
            if self.cache and self.config.enable_result_caching and final_results:
                await self.cache.set_search_results(
                    cache_key, final_results, "hybrid", self.config.cache_ttl
                )

            # Update statistics
            total_time = time.time() - start_time
            self._update_stats(total_time, fusion_time)

            return final_results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    async def batch_search(
        self,
        session: AsyncSession,
        queries: List[str],
        filters: Dict[str, Any] = None,
        top_k: int = None
    ) -> List[List[Dict[str, Any]]]:
        """Batch hybrid search for multiple queries"""
        if not queries:
            return []

        # Process queries in batches to manage resources
        batch_size = min(self.config.max_parallel_searches, len(queries))
        results = []

        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]

            # Execute batch searches concurrently
            tasks = [
                self.search(session, query, filters, top_k)
                for query in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch search query failed: {result}")
                    results.append([])
                else:
                    results.append(result)

        return results

    async def _parallel_search(
        self,
        session: AsyncSession,
        query: str,
        filters: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Execute BM25 and vector searches in parallel"""

        # Create tasks for parallel execution
        bm25_task = self._bm25_search(session, query, filters)
        vector_task = self._vector_search(session, query, filters)

        # Execute in parallel
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

        return bm25_results, vector_results

    async def _bm25_search(
        self,
        session: AsyncSession,
        query: str,
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Optimized BM25 search"""
        start_time = time.time()

        try:
            # Build filter conditions
            filter_clause, filter_params = self._build_filter_clause(filters)

            # Use PostgreSQL full-text search or SQLite fallback
            if "postgresql" in str(session.bind.url).lower():
                search_query = text(f"""
                    WITH bm25_search AS (
                        SELECT
                            c.chunk_id,
                            c.text,
                            d.title,
                            d.source_url,
                            dt.path as taxonomy_path,
                            ts_rank_cd(
                                to_tsvector('english', c.text),
                                websearch_to_tsquery('english', :query),
                                32
                            ) as bm25_score,
                            c.chunk_metadata
                        FROM chunks c
                        JOIN documents d ON c.doc_id = d.doc_id
                        LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                        WHERE to_tsvector('english', c.text) @@ websearch_to_tsquery('english', :query)
                        {filter_clause}
                        ORDER BY bm25_score DESC
                        LIMIT :top_k
                    )
                    SELECT * FROM bm25_search WHERE bm25_score > 0.01
                """)
            else:
                # SQLite fallback
                search_query = text(f"""
                    SELECT
                        c.chunk_id,
                        c.text,
                        d.title,
                        d.source_url,
                        dt.path as taxonomy_path,
                        CASE
                            WHEN c.text LIKE '%' || :query || '%' THEN 1.0
                            ELSE 0.1
                        END as bm25_score,
                        c.chunk_metadata
                    FROM chunks c
                    JOIN documents d ON c.doc_id = d.doc_id
                    LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                    WHERE c.text LIKE '%' || :query || '%'
                    {filter_clause}
                    ORDER BY bm25_score DESC
                    LIMIT :top_k
                """)

            # Execute query
            result = await session.execute(search_query, {
                "query": query,
                "top_k": self.config.bm25_top_k,
                **filter_params
            })

            rows = result.fetchall()

            # Format results
            results = []
            for row in rows:
                result_dict = {
                    "chunk_id": str(row.chunk_id),
                    "text": row.text,
                    "title": row.title,
                    "source_url": row.source_url,
                    "taxonomy_path": row.taxonomy_path or [],
                    "bm25_score": float(row.bm25_score),
                    "metadata": {
                        "chunk_metadata": row.chunk_metadata or {},
                        "search_type": "bm25"
                    }
                }
                results.append(result_dict)

            # Update timing stats
            elapsed = time.time() - start_time
            self._stats['bm25_avg_time'] = (
                self._stats['bm25_avg_time'] + elapsed
            ) / 2

            return results

        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []

    async def _vector_search(
        self,
        session: AsyncSession,
        query: str,
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Optimized vector search using vector engine"""
        start_time = time.time()

        try:
            # Generate query embedding
            from ..api.database import EmbeddingService
            query_embedding = await EmbeddingService.generate_embedding(query)

            if not isinstance(query_embedding, list):
                query_embedding = query_embedding.tolist()

            # Use optimized vector engine
            results = await self.vector_engine.search_similar(
                session=session,
                query_vector=np.array(query_embedding),
                top_k=self.config.vector_top_k,
                filters=filters
            )

            # Update timing stats
            elapsed = time.time() - start_time
            self._stats['vector_avg_time'] = (
                self._stats['vector_avg_time'] + elapsed
            ) / 2

            return results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def _apply_fusion(
        self,
        query: str,
        bm25_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Apply hybrid fusion with adaptive weights"""

        try:
            if self.config.enable_adaptive_fusion:
                # Use adaptive fusion
                fused_candidates = self.adaptive_fusion.adaptive_fuse(
                    query, bm25_results, vector_results
                )
            else:
                # Use configured fusion method
                fusion_engine = HybridScoreFusion(
                    fusion_method=self.config.fusion_method,
                    normalization_method=self.config.normalization_method,
                    bm25_weight=self.config.bm25_weight,
                    vector_weight=self.config.vector_weight
                )
                fused_candidates = fusion_engine.fuse_results(
                    bm25_results, vector_results, top_k * 2
                )

            return fused_candidates[:top_k]

        except Exception as e:
            logger.error(f"Fusion failed: {e}")
            # Fallback: simple weighted combination
            return self._simple_fusion(bm25_results, vector_results, top_k)

    def _simple_fusion(
        self,
        bm25_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Simple fallback fusion"""
        combined = {}

        # Add BM25 results
        for result in bm25_results:
            chunk_id = result['chunk_id']
            combined[chunk_id] = result.copy()
            combined[chunk_id]['final_score'] = result.get('bm25_score', 0) * self.config.bm25_weight

        # Add vector results
        for result in vector_results:
            chunk_id = result['chunk_id']
            if chunk_id in combined:
                combined[chunk_id]['final_score'] += result.get('similarity', 0) * self.config.vector_weight
                combined[chunk_id]['metadata']['search_type'] = 'hybrid'
            else:
                combined[chunk_id] = result.copy()
                combined[chunk_id]['final_score'] = result.get('similarity', 0) * self.config.vector_weight

        # Sort by final score
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x.get('final_score', 0),
            reverse=True
        )

        return sorted_results[:top_k]

    def _build_filter_clause(self, filters: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Build SQL filter clause from filters dictionary"""
        if not filters:
            return "", {}

        conditions = []
        params = {}

        # Taxonomy path filter
        if "canonical_in" in filters:
            paths = filters["canonical_in"]
            if paths:
                path_conditions = []
                for i, path in enumerate(paths):
                    param_name = f"path_{i}"
                    path_conditions.append(f"dt.path = :{param_name}")
                    params[param_name] = path

                if path_conditions:
                    conditions.append(f"({' OR '.join(path_conditions)})")

        # Document type filter
        if "doc_type" in filters:
            doc_types = filters["doc_type"]
            if isinstance(doc_types, list) and doc_types:
                type_conditions = []
                for i, doc_type in enumerate(doc_types):
                    param_name = f"doc_type_{i}"
                    type_conditions.append(f"d.content_type = :{param_name}")
                    params[param_name] = doc_type

                if type_conditions:
                    conditions.append(f"({' OR '.join(type_conditions)})")

        filter_clause = ""
        if conditions:
            filter_clause = " AND " + " AND ".join(conditions)

        return filter_clause, params

    def _format_results(self, fused_results) -> List[Dict[str, Any]]:
        """Format fused results to standard output format"""
        formatted_results = []

        for candidate in fused_results:
            if hasattr(candidate, 'chunk_id'):
                # SearchCandidate object
                result = {
                    "chunk_id": candidate.chunk_id,
                    "text": candidate.text,
                    "score": candidate.final_score or 0.0,
                    "metadata": {
                        **candidate.metadata,
                        "bm25_score": candidate.bm25_score,
                        "vector_score": candidate.vector_score,
                        "sources": candidate.sources,
                        "search_type": "hybrid"
                    }
                }
            else:
                # Dictionary format
                result = candidate.copy()
                if 'final_score' in result:
                    result['score'] = result.pop('final_score')

            formatted_results.append(result)

        return formatted_results

    def _generate_cache_key(
        self,
        query: str,
        filters: Dict[str, Any],
        top_k: int
    ) -> str:
        """Generate cache key for hybrid search"""
        return QueryOptimizer.generate_query_hash(
            query, filters, {
                "top_k": top_k,
                "bm25_weight": self.config.bm25_weight,
                "vector_weight": self.config.vector_weight,
                "fusion_method": self.config.fusion_method.value
            }
        )

    def _update_stats(self, total_time: float, fusion_time: float):
        """Update search statistics"""
        self._stats['total_searches'] += 1
        self._stats['avg_latency'] = (
            self._stats['avg_latency'] + total_time
        ) / 2
        self._stats['fusion_avg_time'] = (
            self._stats['fusion_avg_time'] + fusion_time
        ) / 2

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        cache_stats = self.cache.get_cache_stats() if self.cache else {}
        vector_stats = self.vector_engine.get_stats() if self.vector_engine else {}

        return {
            "hybrid_engine": self._stats,
            "cache": cache_stats,
            "vector_engine": vector_stats,
            "config": {
                "bm25_weight": self.config.bm25_weight,
                "vector_weight": self.config.vector_weight,
                "fusion_method": self.config.fusion_method.value,
                "adaptive_fusion": self.config.enable_adaptive_fusion
            }
        }

    async def optimize_performance(self, session: AsyncSession):
        """Optimize engine performance"""
        try:
            # Optimize vector engine
            if self.vector_engine:
                await self.vector_engine.optimize_index(session)

            # Clear old cache entries
            if self.cache:
                await self.cache.clear_cache("search:hybrid:*")

            # Update database statistics
            await session.execute(text("ANALYZE chunks, documents, embeddings"))

            logger.info("Hybrid engine performance optimization completed")

        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")


# Global instance
_hybrid_engine_instance = None

async def get_hybrid_engine(config: HybridSearchConfig = None) -> OptimizedHybridEngine:
    """Get global hybrid engine instance"""
    global _hybrid_engine_instance
    if _hybrid_engine_instance is None:
        _hybrid_engine_instance = OptimizedHybridEngine(config)
        await _hybrid_engine_instance.initialize()
    return _hybrid_engine_instance


# Import numpy for vector operations
import numpy as np