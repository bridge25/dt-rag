"""
Optimized Vector Search Engine for PostgreSQL + pgvector
High-performance vector similarity search with caching and batching
"""

import asyncio
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from .optimization import SearchCache, QueryOptimizer, get_cache

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchConfig:
    """Vector search configuration"""
    # HNSW parameters
    ef_search: int = 80  # Runtime search parameter

    # Search parameters
    similarity_threshold: float = 0.7  # Minimum similarity score
    max_results: int = 1000  # Maximum results before filtering

    # Performance parameters
    batch_size: int = 100  # Batch size for multiple queries
    cache_ttl: int = 3600  # Cache TTL in seconds
    enable_prefiltering: bool = True  # Enable metadata prefiltering

    # Memory optimization
    enable_result_streaming: bool = True  # Stream large result sets
    max_memory_mb: int = 512  # Maximum memory usage


class OptimizedVectorEngine:
    """High-performance vector search engine"""

    def __init__(self, config: VectorSearchConfig = None):
        self.config = config or VectorSearchConfig()
        self.cache: Optional[SearchCache] = None
        self._stats = {
            'searches': 0,
            'cache_hits': 0,
            'avg_latency': 0.0,
            'total_time': 0.0
        }

    async def initialize(self):
        """Initialize the vector engine"""
        self.cache = await get_cache()
        logger.info("Optimized vector engine initialized")

    async def search_similar(
        self,
        session: AsyncSession,
        query_vector: np.ndarray,
        top_k: int = 10,
        filters: Dict[str, Any] = None,
        similarity_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """
        High-performance vector similarity search

        Args:
            session: Database session
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: Optional metadata filters
            similarity_threshold: Minimum similarity score

        Returns:
            List of similar documents with scores
        """
        start_time = time.time()

        try:
            # Use configured threshold if not provided
            threshold = similarity_threshold or self.config.similarity_threshold

            # Check cache first
            cache_key = self._generate_cache_key(query_vector, top_k, filters, threshold)
            if self.cache:
                cached_result = await self.cache.get_search_results(cache_key, "vector")
                if cached_result:
                    self._stats['cache_hits'] += 1
                    return cached_result

            # Optimize query parameters
            await self._optimize_session_parameters(session)

            # Build and execute optimized query
            results = await self._execute_vector_query(
                session, query_vector, top_k, filters, threshold
            )

            # Cache results
            if self.cache and results:
                await self.cache.set_search_results(
                    cache_key, results, "vector", self.config.cache_ttl
                )

            # Update statistics
            elapsed = time.time() - start_time
            self._update_stats(elapsed)

            return results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def batch_search(
        self,
        session: AsyncSession,
        query_vectors: List[np.ndarray],
        top_k: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Batch vector similarity search for multiple queries

        Args:
            session: Database session
            query_vectors: List of query embedding vectors
            top_k: Number of results per query
            filters: Optional metadata filters

        Returns:
            List of result lists for each query
        """
        if not query_vectors:
            return []

        # Process in batches to manage memory
        batch_size = self.config.batch_size
        all_results = []

        for i in range(0, len(query_vectors), batch_size):
            batch = query_vectors[i:i + batch_size]

            # Execute batch queries concurrently
            tasks = [
                self.search_similar(session, vector, top_k, filters)
                for vector in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            processed_results = []
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch query failed: {result}")
                    processed_results.append([])
                else:
                    processed_results.append(result)

            all_results.extend(processed_results)

        return all_results

    async def find_nearest_neighbors(
        self,
        session: AsyncSession,
        query_vector: np.ndarray,
        k: int = 50,
        distance_metric: str = "cosine"
    ) -> List[Tuple[str, float]]:
        """
        Find k nearest neighbors with distances

        Args:
            session: Database session
            query_vector: Query vector
            k: Number of neighbors
            distance_metric: Distance metric (cosine, l2, inner_product)

        Returns:
            List of (chunk_id, distance) tuples
        """
        try:
            # Map distance metric to pgvector operator
            operator_map = {
                "cosine": "<->",
                "l2": "<->",
                "inner_product": "<#>"
            }

            operator = operator_map.get(distance_metric, "<->")

            # Execute optimized KNN query
            query = text(f"""
                SELECT
                    chunk_id,
                    vec {operator} :query_vector as distance
                FROM embeddings
                WHERE vec IS NOT NULL
                ORDER BY vec {operator} :query_vector
                LIMIT :k
            """)

            result = await session.execute(query, {
                "query_vector": query_vector.tolist(),
                "k": k
            })

            return [(str(row[0]), float(row[1])) for row in result.fetchall()]

        except Exception as e:
            logger.error(f"KNN search failed: {e}")
            return []

    async def _execute_vector_query(
        self,
        session: AsyncSession,
        query_vector: np.ndarray,
        top_k: int,
        filters: Dict[str, Any],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Execute optimized vector similarity query"""

        # Build filter conditions
        filter_clause, filter_params = self._build_filter_conditions(filters)

        # Choose query strategy based on filters
        if filters and self.config.enable_prefiltering:
            # Use materialized view for filtered searches if available
            query = self._build_filtered_vector_query(filter_clause, threshold)
        else:
            # Use direct table query for unfiltered searches
            query = self._build_direct_vector_query(filter_clause, threshold)

        # Execute query with parameters
        query_params = {
            "query_vector": query_vector.tolist(),
            "top_k": min(top_k, self.config.max_results),
            "threshold": threshold,
            **filter_params
        }

        result = await session.execute(query, query_params)
        rows = result.fetchall()

        # Convert to result format
        results = []
        for row in rows:
            similarity = 1.0 - row.distance if hasattr(row, 'distance') else row.similarity

            result_dict = {
                "chunk_id": str(row.chunk_id),
                "text": row.text,
                "title": row.title,
                "source_url": row.source_url,
                "taxonomy_path": row.taxonomy_path or [],
                "similarity": float(similarity),
                "metadata": {
                    "model_name": getattr(row, 'model_name', 'unknown'),
                    "created_at": getattr(row, 'created_at', None),
                    "chunk_metadata": getattr(row, 'chunk_metadata', {}),
                    "search_type": "vector"
                }
            }
            results.append(result_dict)

        return results

    def _build_direct_vector_query(self, filter_clause: str, threshold: float) -> text:
        """Build direct vector query"""
        return text(f"""
            WITH vector_search AS (
                SELECT
                    e.chunk_id,
                    1.0 - (e.vec <-> :query_vector) as similarity,
                    e.model_name,
                    e.created_at
                FROM embeddings e
                WHERE e.vec IS NOT NULL
                  AND (1.0 - (e.vec <-> :query_vector)) >= :threshold
                ORDER BY e.vec <-> :query_vector
                LIMIT :top_k
            )
            SELECT
                vs.chunk_id,
                vs.similarity,
                c.text,
                d.title,
                d.source_url,
                dt.path as taxonomy_path,
                vs.model_name,
                vs.created_at,
                c.chunk_metadata
            FROM vector_search vs
            JOIN chunks c ON vs.chunk_id = c.chunk_id
            JOIN documents d ON c.doc_id = d.doc_id
            LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
            {filter_clause}
            ORDER BY vs.similarity DESC
        """)

    def _build_filtered_vector_query(self, filter_clause: str, threshold: float) -> text:
        """Build filtered vector query using materialized view if available"""
        return text(f"""
            SELECT
                chunk_id,
                1.0 - (vec <-> :query_vector) as similarity,
                text,
                title,
                source_url,
                taxonomy_path,
                'optimized' as model_name,
                NOW() as created_at,
                chunk_metadata
            FROM mv_hot_search_paths
            WHERE vec IS NOT NULL
              AND (1.0 - (vec <-> :query_vector)) >= :threshold
              {filter_clause}
            ORDER BY vec <-> :query_vector
            LIMIT :top_k
        """)

    def _build_filter_conditions(self, filters: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Build SQL filter conditions from filter dictionary"""
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

        # Date range filter
        if "date_range" in filters:
            date_range = filters["date_range"]
            if date_range.get("start"):
                conditions.append("d.processed_at >= :start_date")
                params["start_date"] = date_range["start"]
            if date_range.get("end"):
                conditions.append("d.processed_at <= :end_date")
                params["end_date"] = date_range["end"]

        filter_clause = ""
        if conditions:
            filter_clause = " AND " + " AND ".join(conditions)

        return filter_clause, params

    async def _optimize_session_parameters(self, session: AsyncSession):
        """Optimize session parameters for vector operations"""
        try:
            # Set HNSW search parameter
            await session.execute(text(f"SET hnsw.ef_search = {self.config.ef_search}"))

            # Optimize for vector workloads
            await session.execute(text("SET work_mem = '256MB'"))
            await session.execute(text("SET enable_seqscan = off"))

        except Exception as e:
            logger.warning(f"Failed to optimize session parameters: {e}")

    def _generate_cache_key(
        self,
        query_vector: np.ndarray,
        top_k: int,
        filters: Dict[str, Any],
        threshold: float
    ) -> str:
        """Generate cache key for vector search"""
        import hashlib
        import json

        # Create a hash from vector and parameters
        vector_hash = hashlib.md5(query_vector.tobytes()).hexdigest()[:8]

        params = {
            "vector_hash": vector_hash,
            "top_k": top_k,
            "filters": filters or {},
            "threshold": threshold
        }

        param_string = json.dumps(params, sort_keys=True)
        return hashlib.md5(param_string.encode()).hexdigest()

    def _update_stats(self, elapsed_time: float):
        """Update search statistics"""
        self._stats['searches'] += 1
        self._stats['total_time'] += elapsed_time
        self._stats['avg_latency'] = self._stats['total_time'] / self._stats['searches']

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        cache_stats = self.cache.get_cache_stats() if self.cache else {}

        return {
            **self._stats,
            "cache_hit_rate": self._stats['cache_hits'] / max(1, self._stats['searches']),
            "cache_stats": cache_stats,
            "config": {
                "ef_search": self.config.ef_search,
                "similarity_threshold": self.config.similarity_threshold,
                "batch_size": self.config.batch_size
            }
        }

    async def optimize_index(self, session: AsyncSession):
        """Optimize vector index performance"""
        try:
            # Update statistics for query planner
            await session.execute(text("ANALYZE embeddings"))

            # Refresh materialized view if it exists
            try:
                await session.execute(text("REFRESH MATERIALIZED VIEW mv_hot_search_paths"))
                logger.info("Refreshed materialized view for hot search paths")
            except Exception:
                pass  # View might not exist

            logger.info("Vector index optimization completed")

        except Exception as e:
            logger.error(f"Index optimization failed: {e}")


# Global instance
_vector_engine_instance = None

async def get_vector_engine(config: VectorSearchConfig = None) -> OptimizedVectorEngine:
    """Get global vector engine instance"""
    global _vector_engine_instance
    if _vector_engine_instance is None:
        _vector_engine_instance = OptimizedVectorEngine(config)
        await _vector_engine_instance.initialize()
    return _vector_engine_instance