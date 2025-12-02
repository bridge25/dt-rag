"""
Hybrid Search Use Case

Business logic for performing hybrid search.

@CODE:CLEAN-ARCHITECTURE-HYBRID-SEARCH
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

from ...entities.search import (
    SearchResult,
    SearchResponse,
    SearchStrategy,
    filter_results_by_taxonomy,
    calculate_result_diversity,
)
from ...repositories.search_repository import ISearchRepository, SearchParams


@dataclass
class HybridSearchInput:
    """Input for HybridSearchUseCase"""
    query: str
    top_k: int = 5
    bm25_weight: float = 0.5
    vector_weight: float = 0.5
    enable_reranking: bool = True
    taxonomy_filters: Optional[List[List[str]]] = None
    doc_type_filters: Optional[List[str]] = None
    include_metadata: bool = True


class HybridSearchUseCase:
    """
    Hybrid Search Use Case

    Performs hybrid search combining BM25 and vector similarity.

    Business Logic:
    - Combine BM25 and vector scores with configurable weights
    - Apply taxonomy and document type filters
    - Optionally rerank with cross-encoder
    - Track search metrics
    """

    def __init__(self, search_repository: ISearchRepository):
        self._search_repository = search_repository

    async def execute(self, input_data: HybridSearchInput) -> SearchResponse:
        """
        Execute the use case.

        Args:
            input_data: Search parameters

        Returns:
            SearchResponse with results and metrics

        Raises:
            ValueError: If query is empty
        """
        # Validate input
        if not input_data.query or not input_data.query.strip():
            raise ValueError("Search query cannot be empty")

        if input_data.top_k < 1 or input_data.top_k > 100:
            raise ValueError("top_k must be between 1 and 100")

        if abs(input_data.bm25_weight + input_data.vector_weight - 1.0) > 0.01:
            raise ValueError("bm25_weight + vector_weight must equal 1.0")

        # Build filters
        filters: Dict[str, Any] = {}
        if input_data.taxonomy_filters:
            filters["canonical_in"] = input_data.taxonomy_filters
        if input_data.doc_type_filters:
            filters["doc_type"] = input_data.doc_type_filters

        # Build search params
        params = SearchParams(
            query=input_data.query.strip(),
            top_k=input_data.top_k,
            strategy=SearchStrategy.HYBRID,
            bm25_weight=input_data.bm25_weight,
            vector_weight=input_data.vector_weight,
            enable_reranking=input_data.enable_reranking,
            filters=filters,
            include_metadata=input_data.include_metadata,
        )

        # Execute search
        import time
        start_time = time.time()

        results = await self._search_repository.hybrid_search(params)

        query_time_ms = (time.time() - start_time) * 1000

        # Calculate diversity metric
        diversity = calculate_result_diversity(results)

        return SearchResponse(
            query=input_data.query,
            results=results,
            total_results=len(results),
            query_time_ms=query_time_ms,
            strategy_used=SearchStrategy.HYBRID,
            execution_metrics={
                "bm25_weight": input_data.bm25_weight,
                "vector_weight": input_data.vector_weight,
                "reranking_applied": input_data.enable_reranking,
                "result_diversity": diversity,
            },
            executed_at=datetime.utcnow(),
        )
