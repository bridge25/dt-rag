"""
Search Repository Implementation

Implementation of ISearchRepository interface using existing search infrastructure.

@CODE:CLEAN-ARCHITECTURE-SEARCH-REPOSITORY-IMPL
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities.search import (
    SearchResult,
    SearchMetadata,
    RetrievalSource,
)
from ...domain.repositories.search_repository import (
    ISearchRepository,
    SearchParams,
    EmbeddingParams,
    IndexOptimizationResult,
    SearchAnalytics,
)
# Import existing search infrastructure
from ...database import (
    SearchDAO,
    EmbeddingService,
    ClassifyDAO,
    CrossEncoderReranker,
)

logger = logging.getLogger(__name__)


class SearchRepositoryImpl(ISearchRepository):
    """
    Search Repository Implementation

    Wraps existing SearchDAO and related services to provide
    a clean interface for search operations.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    # Core Search Operations

    async def hybrid_search(self, params: SearchParams) -> List[SearchResult]:
        """Perform hybrid search (BM25 + Vector)"""
        try:
            raw_results = await SearchDAO.hybrid_search(
                query=params.query,
                filters=params.filters,
                topk=params.top_k,
                bm25_topk=params.bm25_topk,
                vector_topk=params.vector_topk,
                rerank_candidates=params.rerank_candidates,
            )

            # Apply reranking if enabled
            if params.enable_reranking and raw_results:
                raw_results = CrossEncoderReranker.rerank_results(
                    params.query, raw_results, params.top_k
                )

            return self._convert_to_search_results(raw_results, params.include_metadata)
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    async def bm25_search(self, params: SearchParams) -> List[SearchResult]:
        """Perform BM25 lexical search only"""
        try:
            raw_results = await SearchDAO._perform_bm25_search(
                self._session,
                params.query,
                params.top_k,
                params.filters,
            )

            return self._convert_to_search_results(raw_results, params.include_metadata)
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []

    async def vector_search(self, params: SearchParams) -> List[SearchResult]:
        """Perform vector similarity search only"""
        try:
            # Generate query embedding
            query_embedding = await EmbeddingService.generate_embedding(params.query)

            raw_results = await SearchDAO._perform_vector_search(
                self._session,
                query_embedding,
                params.top_k,
                params.filters,
            )

            return self._convert_to_search_results(raw_results, params.include_metadata)
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def rerank_results(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 5
    ) -> List[SearchResult]:
        """Apply cross-encoder reranking to results"""
        try:
            # Convert to raw format for reranker
            raw_results = [
                {
                    "chunk_id": str(r.chunk_id),
                    "text": r.text,
                    "title": r.title,
                    "source_url": r.source_url,
                    "taxonomy_path": r.taxonomy_path,
                    "score": r.score,
                    "metadata": {
                        "bm25_score": r.metadata.bm25_score,
                        "vector_score": r.metadata.vector_score,
                    },
                }
                for r in results
            ]

            reranked = CrossEncoderReranker.rerank_results(query, raw_results, top_k)

            return self._convert_to_search_results(reranked, include_metadata=True)
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results[:top_k]

    # Embedding Operations

    async def generate_embedding(self, params: EmbeddingParams) -> List[float]:
        """Generate embedding for text"""
        try:
            return await EmbeddingService.generate_embedding(
                params.text,
                model="openai" if "ada" in params.model else "dummy"
            )
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    async def generate_batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            return await EmbeddingService.generate_batch_embeddings(texts, batch_size)
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise

    # Index Operations

    async def optimize_indices(self) -> IndexOptimizationResult:
        """Optimize search indices for better performance"""
        import time
        start = time.time()

        try:
            result = await SearchDAO.optimize_search_indices(self._session)

            return IndexOptimizationResult(
                success=result.get("success", False),
                indices_created=result.get("indices_created", []),
                indices_updated=[],
                message=result.get("message", "Optimization complete"),
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error(f"Index optimization failed: {e}")
            return IndexOptimizationResult(
                success=False,
                indices_created=[],
                indices_updated=[],
                message=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    async def rebuild_bm25_index(self) -> bool:
        """Rebuild BM25 full-text search index"""
        try:
            result = await self.optimize_indices()
            return result.success
        except Exception:
            return False

    async def rebuild_vector_index(self) -> bool:
        """Rebuild vector similarity index"""
        try:
            result = await self.optimize_indices()
            return result.success
        except Exception:
            return False

    # Analytics

    async def get_analytics(self) -> SearchAnalytics:
        """Get search system analytics"""
        try:
            analytics = await SearchDAO.get_search_analytics(self._session)
            stats = analytics.get("statistics", {})
            readiness = analytics.get("search_readiness", {})

            return SearchAnalytics(
                total_documents=stats.get("total_docs", 0),
                total_chunks=stats.get("total_chunks", 0),
                embedded_chunks=stats.get("embedded_chunks", 0),
                taxonomy_mappings=stats.get("taxonomy_mappings", 0),
                embedding_coverage=analytics.get("embedding_coverage", 0.0),
                bm25_ready=readiness.get("bm25_ready", False),
                vector_ready=readiness.get("vector_ready", False),
                hybrid_ready=readiness.get("hybrid_ready", False),
                last_updated=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return SearchAnalytics(
                total_documents=0,
                total_chunks=0,
                embedded_chunks=0,
                taxonomy_mappings=0,
                embedding_coverage=0.0,
                bm25_ready=False,
                vector_ready=False,
                hybrid_ready=False,
                last_updated=datetime.utcnow(),
            )

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get search performance metrics"""
        from ...database import search_metrics

        return search_metrics.get_metrics()

    # CaseBank Operations

    async def search_casebank(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search CaseBank for similar past queries"""
        # This would need CaseBank repository implementation
        return []

    async def add_to_casebank(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        category_path: Optional[List[str]] = None,
        quality: float = 1.0
    ) -> UUID:
        """Add a query-answer pair to CaseBank"""
        # This would need CaseBank repository implementation
        return uuid4()

    # Classification

    async def classify_text(
        self,
        text: str,
        hint_paths: Optional[List[List[str]]] = None
    ) -> Dict[str, Any]:
        """Classify text into taxonomy categories"""
        try:
            return await ClassifyDAO.classify_text(text, hint_paths)
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return {
                "canonical": ["AI", "General"],
                "label": "General",
                "confidence": 0.5,
                "reasoning": [f"Classification error: {e}"],
            }

    # Helper Methods

    def _convert_to_search_results(
        self,
        raw_results: List[Dict[str, Any]],
        include_metadata: bool = True
    ) -> List[SearchResult]:
        """Convert raw search results to SearchResult entities"""
        results = []

        for raw in raw_results:
            try:
                # Determine source from metadata
                source = RetrievalSource.HYBRID
                meta = raw.get("metadata", {})
                if meta.get("source") == "bm25":
                    source = RetrievalSource.BM25
                elif meta.get("source") == "vector":
                    source = RetrievalSource.VECTOR
                elif meta.get("source") == "fallback":
                    source = RetrievalSource.FALLBACK

                # Parse chunk_id
                chunk_id_str = raw.get("chunk_id", "00000000-0000-0000-0000-000000000000")
                try:
                    chunk_id = UUID(chunk_id_str)
                except ValueError:
                    chunk_id = uuid4()

                # Build metadata
                metadata = SearchMetadata(
                    source=source,
                    bm25_score=meta.get("bm25_score", 0.0),
                    vector_score=meta.get("vector_score", 0.0),
                    hybrid_score=raw.get("score", 0.0),
                    rerank_score=meta.get("rerank_score"),
                    latency_ms=meta.get("latency_ms", 0.0),
                ) if include_metadata else SearchMetadata()

                # Normalize score to 0-1
                score = raw.get("score", 0.0)
                if score > 1.0:
                    score = min(1.0, score / 10.0)  # Normalize if needed

                results.append(SearchResult(
                    chunk_id=chunk_id,
                    doc_id=chunk_id,  # Using same for now
                    text=raw.get("text", ""),
                    score=score,
                    title=raw.get("title"),
                    source_url=raw.get("source_url"),
                    taxonomy_path=raw.get("taxonomy_path", []),
                    metadata=metadata,
                ))
            except Exception as e:
                logger.warning(f"Failed to convert search result: {e}")
                continue

        return results
