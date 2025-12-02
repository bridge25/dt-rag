"""
Search Application Service

Orchestrates search-related use cases and handles cross-cutting concerns.

@CODE:CLEAN-ARCHITECTURE-SEARCH-SERVICE
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
import time

from ..domain.entities.search import SearchResult, SearchResponse
from ..domain.repositories.search_repository import (
    ISearchRepository,
    SearchParams,
    EmbeddingParams,
)
from ..domain.usecases.search import (
    HybridSearchUseCase,
    ClassifyTextUseCase,
)

# Import ReflectionEngine for mentor memory learning loop (optional)
try:
    from ..orchestration.reflection_engine import ReflectionEngine
    HAS_REFLECTION_ENGINE = True
except ImportError:
    ReflectionEngine = None  # type: ignore
    HAS_REFLECTION_ENGINE = False

import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class SearchService:
    """
    Search Application Service

    Provides a high-level interface for search operations,
    orchestrating use cases and managing search configurations.

    Responsibilities:
    - Coordinate search use cases
    - Handle search result transformation
    - Manage search caching and optimization
    - Provide unified search interface
    """

    def __init__(self, search_repository: ISearchRepository):
        """
        Initialize search service with dependencies.

        Args:
            search_repository: Repository for search operations
        """
        self._search_repository = search_repository

        # Initialize use cases
        self._hybrid_search = HybridSearchUseCase(search_repository)
        self._classify_text = ClassifyTextUseCase(search_repository)

    # Search Operations

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        enable_reranking: bool = True,
        bm25_topk: int = 50,
        vector_topk: int = 50,
        rerank_candidates: int = 100,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform hybrid search (BM25 + Vector).

        Args:
            query: Search query string
            top_k: Number of final results
            filters: Optional filters (taxonomy_path, doc_ids, etc.)
            enable_reranking: Whether to apply cross-encoder reranking
            bm25_topk: BM25 candidates to retrieve
            vector_topk: Vector candidates to retrieve
            rerank_candidates: Total candidates for reranking
            include_metadata: Whether to include detailed metadata

        Returns:
            Search response dictionary
        """
        start_time = time.time()

        try:
            result = await self._hybrid_search.execute(
                query=query,
                top_k=top_k,
                filters=filters,
                enable_reranking=enable_reranking,
                bm25_topk=bm25_topk,
                vector_topk=vector_topk,
                rerank_candidates=rerank_candidates,
            )

            latency_ms = (time.time() - start_time) * 1000

            return {
                "query": query,
                "results": [
                    self._result_to_dict(r, include_metadata)
                    for r in result.results
                ],
                "total_found": result.total_found,
                "latency_ms": round(latency_ms, 2),
                "search_type": "hybrid",
                "bm25_count": result.bm25_count,
                "vector_count": result.vector_count,
                "reranked": enable_reranking,
            }
        except Exception as e:
            logger.error(f"Hybrid search failed for '{query}': {e}")
            raise

    async def bm25_search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform BM25 lexical search only.

        Args:
            query: Search query string
            top_k: Number of results
            filters: Optional filters

        Returns:
            Search response dictionary
        """
        start_time = time.time()

        try:
            params = SearchParams(
                query=query,
                top_k=top_k,
                filters=filters or {},
            )

            results = await self._search_repository.bm25_search(params)
            latency_ms = (time.time() - start_time) * 1000

            return {
                "query": query,
                "results": [self._result_to_dict(r) for r in results],
                "total_found": len(results),
                "latency_ms": round(latency_ms, 2),
                "search_type": "bm25",
            }
        except Exception as e:
            logger.error(f"BM25 search failed for '{query}': {e}")
            raise

    async def vector_search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform vector similarity search only.

        Args:
            query: Search query string
            top_k: Number of results
            filters: Optional filters

        Returns:
            Search response dictionary
        """
        start_time = time.time()

        try:
            params = SearchParams(
                query=query,
                top_k=top_k,
                filters=filters or {},
            )

            results = await self._search_repository.vector_search(params)
            latency_ms = (time.time() - start_time) * 1000

            return {
                "query": query,
                "results": [self._result_to_dict(r) for r in results],
                "total_found": len(results),
                "latency_ms": round(latency_ms, 2),
                "search_type": "vector",
            }
        except Exception as e:
            logger.error(f"Vector search failed for '{query}': {e}")
            raise

    # Classification Operations

    async def classify_text(
        self,
        text: str,
        hint_paths: Optional[List[List[str]]] = None,
        threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Classify text into taxonomy categories.

        Args:
            text: Text to classify
            hint_paths: Optional hint paths for classification
            threshold: Confidence threshold

        Returns:
            Classification result dictionary
        """
        try:
            result = await self._classify_text.execute(
                text=text,
                hint_paths=hint_paths,
                threshold=threshold,
            )

            return {
                "text": text[:100] + "..." if len(text) > 100 else text,
                "canonical_path": result.canonical_path,
                "label": result.label,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "alternative_paths": result.alternative_paths,
            }
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            raise

    # Embedding Operations

    async def generate_embedding(
        self,
        text: str,
        model: str = "text-embedding-ada-002",
    ) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed
            model: Embedding model name

        Returns:
            Embedding vector
        """
        try:
            params = EmbeddingParams(text=text, model=model)
            return await self._search_repository.generate_embedding(params)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    async def generate_batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        try:
            return await self._search_repository.generate_batch_embeddings(
                texts, batch_size
            )
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise

    # Index Operations

    async def optimize_indices(self) -> Dict[str, Any]:
        """
        Optimize search indices for better performance.

        Returns:
            Optimization result dictionary
        """
        try:
            result = await self._search_repository.optimize_indices()
            return {
                "success": result.success,
                "indices_created": result.indices_created,
                "indices_updated": result.indices_updated,
                "message": result.message,
                "duration_ms": result.duration_ms,
            }
        except Exception as e:
            logger.error(f"Index optimization failed: {e}")
            raise

    async def rebuild_indices(self) -> Dict[str, Any]:
        """
        Rebuild all search indices.

        Returns:
            Rebuild result dictionary
        """
        try:
            bm25_success = await self._search_repository.rebuild_bm25_index()
            vector_success = await self._search_repository.rebuild_vector_index()

            return {
                "bm25_rebuild": bm25_success,
                "vector_rebuild": vector_success,
                "success": bm25_success and vector_success,
            }
        except Exception as e:
            logger.error(f"Index rebuild failed: {e}")
            raise

    # Analytics

    async def get_analytics(self) -> Dict[str, Any]:
        """
        Get search system analytics.

        Returns:
            Analytics dictionary
        """
        try:
            analytics = await self._search_repository.get_analytics()
            return {
                "total_documents": analytics.total_documents,
                "total_chunks": analytics.total_chunks,
                "embedded_chunks": analytics.embedded_chunks,
                "taxonomy_mappings": analytics.taxonomy_mappings,
                "embedding_coverage": analytics.embedding_coverage,
                "search_readiness": {
                    "bm25_ready": analytics.bm25_ready,
                    "vector_ready": analytics.vector_ready,
                    "hybrid_ready": analytics.hybrid_ready,
                },
                "last_updated": analytics.last_updated.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            raise

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get search performance metrics.

        Returns:
            Performance metrics dictionary
        """
        try:
            return await self._search_repository.get_performance_metrics()
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            raise

    # CaseBank Operations

    async def search_casebank(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search CaseBank for similar past queries.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of CaseBank matches
        """
        try:
            return await self._search_repository.search_casebank(query, top_k)
        except Exception as e:
            logger.error(f"CaseBank search failed: {e}")
            raise

    async def add_to_casebank(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        category_path: Optional[List[str]] = None,
        quality: float = 1.0,
    ) -> str:
        """
        Add a query-answer pair to CaseBank.

        Args:
            query: User query
            answer: Generated answer
            sources: Source documents
            category_path: Taxonomy category path
            quality: Quality score

        Returns:
            CaseBank entry ID
        """
        try:
            entry_id = await self._search_repository.add_to_casebank(
                query=query,
                answer=answer,
                sources=sources,
                category_path=category_path,
                quality=quality,
            )

            # 🧠 MENTOR MEMORY: Trigger ReflectionEngine for learning
            await self._trigger_learning_cycle()

            return str(entry_id)
        except Exception as e:
            logger.error(f"Failed to add to CaseBank: {e}")
            raise

    async def _trigger_learning_cycle(self):
        """
        Trigger ReflectionEngine to analyze and learn from stored cases.
        This runs in the background to avoid blocking search operations.
        """
        try:
            # Run ReflectionEngine in background to avoid blocking
            asyncio.create_task(self._run_reflection_batch())
            logger.debug("🧠 ReflectionEngine batch cycle triggered")
        except Exception as e:
            logger.warning(f"⚠️ Failed to trigger reflection cycle: {e}")

    async def _run_reflection_batch(self):
        """
        Run ReflectionEngine batch processing for learning and improvement.
        """
        try:
            reflection_engine = ReflectionEngine()

            # Run batch reflection on all stored cases
            result = await reflection_engine.run_reflection_batch()

            if result.success:
                logger.info(f"✅ ReflectionEngine batch completed: {result.summary}")
            else:
                logger.warning(f"⚠️ ReflectionEngine batch issues: {result.issues}")

        except Exception as e:
            logger.error(f"❌ ReflectionEngine batch failed: {e}")

    # Helper Methods

    def _result_to_dict(
        self,
        result: SearchResult,
        include_metadata: bool = True,
    ) -> Dict[str, Any]:
        """Convert search result entity to dictionary."""
        data = {
            "chunk_id": str(result.chunk_id),
            "doc_id": str(result.doc_id),
            "text": result.text,
            "score": result.score,
            "title": result.title,
            "source_url": result.source_url,
            "taxonomy_path": result.taxonomy_path,
        }

        if include_metadata:
            data["metadata"] = {
                "source": result.metadata.source.value,
                "bm25_score": result.metadata.bm25_score,
                "vector_score": result.metadata.vector_score,
                "hybrid_score": result.metadata.hybrid_score,
                "rerank_score": result.metadata.rerank_score,
                "latency_ms": result.metadata.latency_ms,
            }

        return data
