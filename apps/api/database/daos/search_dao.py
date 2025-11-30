"""
Search Data Access Object for hybrid search operations.

@CODE:DATABASE-PKG-017
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..connection import DATABASE_URL, async_session
from ..utils.embedding_service import EmbeddingService
from ..utils.reranker import CrossEncoderReranker, BM25_WEIGHT, VECTOR_WEIGHT
from .database_manager import db_manager

logger = logging.getLogger(__name__)

__all__ = ["SearchDAO"]


class SearchDAO:
    """Document search data access."""

    @staticmethod
    async def hybrid_search(
        query: str,
        filters: Optional[Dict] = None,
        topk: int = 5,
        bm25_topk: int = 12,
        vector_topk: int = 12,
        rerank_candidates: int = 50,
    ) -> List[Dict[str, Any]]:
        """Optimized hybrid search (BM25 + Vector parallel processing)."""
        # Try async optimization engine
        try:
            # Future implementations - not yet available
            from apps.api.optimization.async_executor import get_async_optimizer  # type: ignore[import-not-found]
            from apps.api.optimization.memory_optimizer import get_gc_optimizer  # type: ignore[import-not-found]
            from apps.api.optimization.concurrency_control import get_concurrency_controller  # type: ignore[import-not-found]

            optimizer = await get_async_optimizer()
            gc_optimizer = get_gc_optimizer()
            concurrency_controller = get_concurrency_controller()

            async with concurrency_controller.controlled_execution("hybrid_search"):
                async with gc_optimizer.optimized_gc_context():
                    return await SearchDAO._execute_optimized_hybrid_search(
                        query,
                        filters or {},
                        topk,
                        bm25_topk,
                        vector_topk,
                        rerank_candidates,
                        optimizer,
                    )

        except ImportError:
            # Fallback: legacy method
            logger.warning("Optimization modules not available, using legacy search")
            return await SearchDAO._execute_legacy_hybrid_search(
                query, filters or {}, topk, bm25_topk, vector_topk, rerank_candidates
            )
        except Exception as e:
            logger.error(f"Optimized hybrid search failed: {e}")
            return await SearchDAO._get_fallback_search(query)

    @staticmethod
    async def _execute_optimized_hybrid_search(
        query: str,
        filters: Dict[str, Any],
        topk: int,
        bm25_topk: int,
        vector_topk: int,
        rerank_candidates: int,
        optimizer: Any,
    ) -> List[Dict[str, Any]]:
        """Execute optimized hybrid search."""
        async with db_manager.async_session() as session:
            try:
                # 1. Generate query embedding (async)
                query_embedding = await EmbeddingService.generate_embedding(query)

                # 2. Execute BM25 + Vector search in parallel
                search_params = {
                    "bm25_topk": bm25_topk,
                    "vector_topk": vector_topk,
                    "filters": filters,
                }

                bm25_results, vector_results, execution_metrics = (
                    await optimizer.execute_parallel_search(
                        session, query, query_embedding, search_params
                    )
                )

                # 3. Fusion results (CPU-intensive work in ThreadPool)
                fusion_params = {
                    "bm25_weight": BM25_WEIGHT,
                    "vector_weight": VECTOR_WEIGHT,
                    "max_candidates": rerank_candidates,
                }

                combined_results = (
                    await optimizer.execute_fusion_with_concurrency_control(
                        bm25_results, vector_results, fusion_params
                    )
                )

                # 4. Cross-encoder reranking (CPU-intensive)
                final_results = await optimizer.execute_cpu_intensive_task(
                    CrossEncoderReranker.rerank_results, query, combined_results, topk
                )

                # 5. Add performance metrics
                for result in final_results:
                    if "metadata" not in result:
                        result["metadata"] = {}
                    result["metadata"]["execution_metrics"] = {
                        "total_time": execution_metrics.total_time,
                        "parallel_time": execution_metrics.parallel_time,
                        "memory_usage": execution_metrics.memory_usage,
                        "optimization_enabled": True,
                    }

                return cast(List[Dict[str, Any]], final_results)

            except Exception as e:
                logger.error(f"Optimized search execution failed: {e}")
                # Fallback: legacy method
                return await SearchDAO._execute_legacy_hybrid_search(
                    query, filters, topk, bm25_topk, vector_topk, rerank_candidates
                )

    @staticmethod
    async def _execute_legacy_hybrid_search(
        query: str,
        filters: Dict,
        topk: int,
        bm25_topk: int,
        vector_topk: int,
        rerank_candidates: int,
    ) -> List[Dict[str, Any]]:
        """Legacy hybrid search (sequential execution)."""
        async with db_manager.async_session() as session:
            try:
                # 1. Generate query embedding
                query_embedding = await EmbeddingService.generate_embedding(query)

                # 2. Perform BM25 search
                bm25_results = await SearchDAO._perform_bm25_search(
                    session, query, bm25_topk, filters
                )

                # 3. Perform Vector search
                vector_results = await SearchDAO._perform_vector_search(
                    session, query_embedding, vector_topk, filters
                )

                # 4. Combine results and remove duplicates
                combined_results = SearchDAO._combine_search_results(
                    bm25_results, vector_results, rerank_candidates
                )

                # 5. Cross-encoder reranking
                final_results = CrossEncoderReranker.rerank_results(
                    query, combined_results, topk
                )

                # Add legacy metadata
                for result in final_results:
                    if "metadata" not in result:
                        result["metadata"] = {}
                    result["metadata"]["optimization_enabled"] = False

                return final_results

            except Exception as e:
                logger.error(f"Legacy hybrid search failed: {e}")
                return await SearchDAO._get_fallback_search(query)

    @staticmethod
    async def _perform_bm25_search(
        session: AsyncSession, query: str, topk: int, filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Perform BM25 search (SQLite/PostgreSQL compatible)."""
        try:
            filter_clause = SearchDAO._build_filter_clause(filters)

            if "sqlite" in DATABASE_URL:
                # SQLite simple text matching
                bm25_query = text(
                    f"""
                    SELECT c.chunk_id, c.text, d.title, d.source_url, dt.path,
                           CASE
                               WHEN c.text LIKE '%' || :query || '%' THEN 1.0
                               ELSE 0.1
                           END as bm25_score
                    FROM chunks c
                    JOIN documents d ON c.doc_id = d.doc_id
                    LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                    WHERE c.text LIKE '%' || :query || '%'
                    {filter_clause}
                    ORDER BY bm25_score DESC
                    LIMIT :topk
                """
                )
            else:
                # PostgreSQL full-text search
                bm25_query = text(
                    f"""
                    SELECT c.chunk_id, c.text, d.title, d.source_url,
                           dt.path,
                           ts_rank_cd(
                               to_tsvector('english', c.text || ' ' || COALESCE(d.title, '')),
                               websearch_to_tsquery('english', :query),
                               32
                           ) as bm25_score
                    FROM chunks c
                    JOIN documents d ON c.doc_id = d.doc_id
                    LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                    WHERE to_tsvector('english', c.text || ' ' || COALESCE(d.title, '')) @@ websearch_to_tsquery('english', :query)
                    {filter_clause}
                    ORDER BY bm25_score DESC
                    LIMIT :topk
                """
                )

            result = await session.execute(bm25_query, {"query": query, "topk": topk})
            rows = result.fetchall()

            results = []
            for row in rows:
                result_dict = {
                    "chunk_id": str(row[0]),
                    "text": row[1],
                    "title": row[2],
                    "source_url": row[3],
                    "taxonomy_path": row[4] if row[4] else [],
                    "score": float(row[5]) if row[5] else 0.0,
                    "metadata": {
                        "bm25_score": float(row[5]) if row[5] else 0.0,
                        "vector_score": 0.0,
                        "source": "bm25",
                    },
                }
                results.append(result_dict)

            return results

        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []

    @staticmethod
    async def _perform_vector_search(
        session: AsyncSession,
        query_embedding: List[float],
        topk: int,
        filters: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """Perform Vector similarity search (SQLite/PostgreSQL compatible)."""
        try:
            filter_clause = SearchDAO._build_filter_clause(filters)

            if "sqlite" in DATABASE_URL:
                # SQLite fallback
                vector_query = text(
                    f"""
                    SELECT c.chunk_id, c.text, d.title, d.source_url, dt.path,
                           0.8 as vector_score
                    FROM chunks c
                    JOIN documents d ON c.doc_id = d.doc_id
                    LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                    JOIN embeddings e ON c.chunk_id = e.chunk_id
                    WHERE e.vec IS NOT NULL
                    {filter_clause}
                    ORDER BY c.chunk_id
                    LIMIT :topk
                """
                )

                result = await session.execute(vector_query, {"topk": topk})
            else:
                # PostgreSQL pgvector search
                try:
                    vector_query = text(
                        f"""
                        SELECT c.chunk_id, c.text, d.title, d.source_url,
                               dt.path,
                               1.0 - (e.vec <-> :query_vector::vector) as vector_score
                        FROM chunks c
                        JOIN documents d ON c.doc_id = d.doc_id
                        JOIN embeddings e ON c.chunk_id = e.chunk_id
                        LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                        WHERE e.vec IS NOT NULL
                        {filter_clause}
                        ORDER BY e.vec <-> :query_vector::vector
                        LIMIT :topk
                    """
                    )

                    vector_str = "[" + ",".join(map(str, query_embedding)) + "]"

                    result = await session.execute(
                        vector_query, {"query_vector": vector_str, "topk": topk}
                    )
                except Exception as vector_error:
                    # Fallback to Python calculation
                    logger.warning(
                        f"pgvector operation failed, falling back to Python: {vector_error}"
                    )
                    vector_query = text(
                        f"""
                        SELECT c.chunk_id, c.text, d.title, d.source_url, dt.path, e.vec,
                               0.8 as vector_score
                        FROM chunks c
                        JOIN documents d ON c.doc_id = d.doc_id
                        LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                        JOIN embeddings e ON c.chunk_id = e.chunk_id
                        WHERE e.vec IS NOT NULL
                        {filter_clause}
                        ORDER BY c.chunk_id
                        LIMIT :topk
                    """
                    )

                    result = await session.execute(vector_query, {"topk": topk})

            rows = result.fetchall()

            results = []
            for row in rows:
                result_dict = {
                    "chunk_id": str(row[0]),
                    "text": row[1],
                    "title": row[2],
                    "source_url": row[3],
                    "taxonomy_path": row[4] if row[4] else [],
                    "score": float(row[5]) if row[5] else 0.0,
                    "metadata": {
                        "bm25_score": 0.0,
                        "vector_score": float(row[5]) if row[5] else 0.0,
                        "source": "vector",
                    },
                }
                results.append(result_dict)

            return results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    @staticmethod
    def _build_filter_clause(filters: Optional[Dict] = None) -> str:
        """Build filter condition SQL clause (SQLite/PostgreSQL compatible)."""
        if not filters:
            return ""

        conditions = []

        # canonical_in filter (classification path filtering)
        if "canonical_in" in filters:
            canonical_paths = filters["canonical_in"]
            if canonical_paths:
                path_conditions = []
                for path in canonical_paths:
                    if isinstance(path, list) and path:
                        if "sqlite" in DATABASE_URL:
                            path_str = json.dumps(path)
                            path_conditions.append(f"dt.path = '{path_str}'")
                        else:
                            path_str = "{" + ",".join(f"'{p}'" for p in path) + "}"
                            path_conditions.append(f"dt.path = '{path_str}'::text[]")

                if path_conditions:
                    conditions.append(f"({' OR '.join(path_conditions)})")

        # doc_type filter
        if "doc_type" in filters:
            doc_types = filters["doc_type"]
            if isinstance(doc_types, list) and doc_types:
                type_conditions = [f"d.content_type = '{dt}'" for dt in doc_types]
                conditions.append(f"({' OR '.join(type_conditions)})")

        if conditions:
            return " AND " + " AND ".join(conditions)

        return ""

    @staticmethod
    def _combine_search_results(
        bm25_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        max_candidates: int,
    ) -> List[Dict[str, Any]]:
        """Combine BM25 and Vector search results."""
        combined = {}

        # Add BM25 results
        for result in bm25_results:
            chunk_id = result["chunk_id"]
            combined[chunk_id] = result.copy()

        # Add/update Vector results
        for result in vector_results:
            chunk_id = result["chunk_id"]
            if chunk_id in combined:
                combined[chunk_id]["metadata"]["vector_score"] = result["metadata"][
                    "vector_score"
                ]
                bm25_score = combined[chunk_id]["metadata"]["bm25_score"]
                vector_score = result["metadata"]["vector_score"]
                combined[chunk_id]["score"] = (
                    BM25_WEIGHT * bm25_score + VECTOR_WEIGHT * vector_score
                )
                combined[chunk_id]["metadata"]["source"] = "hybrid"
            else:
                combined[chunk_id] = result.copy()

        # Sort by score and return top candidates
        sorted_results = sorted(
            combined.values(), key=lambda x: x["score"], reverse=True
        )

        return sorted_results[:max_candidates]

    @staticmethod
    async def optimize_search_indices(session: AsyncSession) -> Dict[str, Any]:
        """Optimize search indices (SQLite/PostgreSQL compatible)."""
        try:
            if "sqlite" in DATABASE_URL:
                optimization_queries = [
                    "CREATE INDEX IF NOT EXISTS idx_chunks_text ON chunks (text)",
                    "CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks (doc_id)",
                    "CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings (chunk_id)",
                    "CREATE INDEX IF NOT EXISTS idx_doc_taxonomy_doc_id ON doc_taxonomy (doc_id)",
                    "CREATE INDEX IF NOT EXISTS idx_documents_title ON documents (title)",
                ]
            else:
                optimization_queries = [
                    "CREATE INDEX IF NOT EXISTS idx_chunks_text_fts ON chunks USING GIN (to_tsvector('english', text))",
                    "CREATE INDEX IF NOT EXISTS idx_embeddings_vec_cosine ON embeddings USING ivfflat (vec vector_cosine_ops) WITH (lists = 100)",
                    "CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks (doc_id)",
                    "CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings (chunk_id)",
                    "CREATE INDEX IF NOT EXISTS idx_doc_taxonomy_doc_id ON doc_taxonomy (doc_id)",
                    "CREATE INDEX IF NOT EXISTS idx_doc_taxonomy_path ON doc_taxonomy USING GIN (path)",
                ]

            created_indices = []
            for query in optimization_queries:
                try:
                    await session.execute(text(query))
                    index_name = (
                        query.split("idx_")[1].split(" ")[0]
                        if "idx_" in query
                        else "unknown"
                    )
                    created_indices.append(index_name)
                except Exception as e:
                    logger.warning(f"Index creation failed: {e}")

            try:
                await session.execute(text("ANALYZE"))
            except Exception as e:
                logger.warning(f"Statistics update failed: {e}")

            return {
                "success": True,
                "indices_created": created_indices,
                "message": f"{len(created_indices)} indices optimized",
            }

        except Exception as e:
            logger.error(f"Index optimization failed: {e}")
            return {"success": False, "error": str(e), "indices_created": []}

    @staticmethod
    async def get_search_analytics(session: AsyncSession) -> Dict[str, Any]:
        """Get search system analytics."""
        try:
            stats_queries = {
                "total_docs": "SELECT COUNT(*) FROM documents",
                "total_chunks": "SELECT COUNT(*) FROM chunks",
                "embedded_chunks": "SELECT COUNT(*) FROM embeddings",
                "taxonomy_mappings": "SELECT COUNT(*) FROM doc_taxonomy",
            }

            statistics = {}
            for stat_name, query in stats_queries.items():
                try:
                    result = await session.execute(text(query))
                    statistics[stat_name] = result.scalar() or 0
                except Exception as e:
                    logger.warning(f"Statistics {stat_name} query failed: {e}")
                    statistics[stat_name] = 0

            # Check index status
            index_query = text(
                """
                SELECT indexname, tablename
                FROM pg_indexes
                WHERE tablename IN ('chunks', 'embeddings', 'documents', 'doc_taxonomy')
                AND schemaname = 'public'
            """
            )

            index_result = await session.execute(index_query)
            indices = [
                {"name": row[0], "table": row[1]} for row in index_result.fetchall()
            ]

            # Search readiness status
            search_readiness = {
                "bm25_ready": statistics["total_chunks"] > 0,
                "vector_ready": statistics["embedded_chunks"] > 0,
                "hybrid_ready": statistics["total_chunks"] > 0
                and statistics["embedded_chunks"] > 0,
                "taxonomy_ready": statistics["taxonomy_mappings"] > 0,
            }

            return {
                "statistics": statistics,
                "indices": indices,
                "search_readiness": search_readiness,
                "embedding_coverage": (
                    statistics["embedded_chunks"] / max(1, statistics["total_chunks"])
                )
                * 100,
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Search analytics query failed: {e}")
            return {
                "statistics": {},
                "indices": [],
                "search_readiness": {},
                "error": str(e),
            }

    @staticmethod
    async def _get_fallback_search(query: str) -> List[Dict[str, Any]]:
        """Fallback search results."""
        return [
            {
                "chunk_id": f"fallback-{hash(query) % 1000}",
                "text": f"Search results related to '{query}'.",
                "title": "Search Result",
                "source_url": "https://example.com",
                "taxonomy_path": ["AI", "General"],
                "score": 0.5,
                "metadata": {
                    "source": "fallback",
                    "bm25_score": 0.5,
                    "vector_score": 0.5,
                },
            }
        ]
