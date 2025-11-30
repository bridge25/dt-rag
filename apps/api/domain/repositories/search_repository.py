"""
Search Repository Interface

Defines the contract for Search data access operations.

@CODE:CLEAN-ARCHITECTURE-SEARCH-REPOSITORY
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from ..entities.search import (
    SearchResult,
    SearchResponse,
    SearchQuery,
    SearchStrategy,
)


@dataclass
class SearchParams:
    """Parameters for search operations"""
    query: str
    top_k: int = 5
    strategy: SearchStrategy = SearchStrategy.HYBRID
    bm25_weight: float = 0.5
    vector_weight: float = 0.5
    bm25_topk: int = 12
    vector_topk: int = 12
    rerank_candidates: int = 50
    enable_reranking: bool = True
    filters: Dict[str, Any] = field(default_factory=dict)
    include_metadata: bool = True


@dataclass
class EmbeddingParams:
    """Parameters for embedding generation"""
    text: str
    model: str = "text-embedding-ada-002"
    dimensions: int = 1536


@dataclass
class IndexOptimizationResult:
    """Result of index optimization"""
    success: bool
    indices_created: List[str]
    indices_updated: List[str]
    message: str
    duration_ms: float


@dataclass
class SearchAnalytics:
    """Search system analytics"""
    total_documents: int
    total_chunks: int
    embedded_chunks: int
    taxonomy_mappings: int
    embedding_coverage: float
    bm25_ready: bool
    vector_ready: bool
    hybrid_ready: bool
    last_updated: datetime


class ISearchRepository(ABC):
    """
    Search Repository Interface

    Defines all data access operations for Search functionality.
    """

    # Core Search Operations

    @abstractmethod
    async def hybrid_search(self, params: SearchParams) -> List[SearchResult]:
        """
        Perform hybrid search (BM25 + Vector).

        Args:
            params: Search parameters

        Returns:
            List of search results ranked by relevance
        """
        pass

    @abstractmethod
    async def bm25_search(self, params: SearchParams) -> List[SearchResult]:
        """
        Perform BM25 lexical search only.

        Args:
            params: Search parameters

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    async def vector_search(self, params: SearchParams) -> List[SearchResult]:
        """
        Perform vector similarity search only.

        Args:
            params: Search parameters

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    async def rerank_results(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        Apply cross-encoder reranking to results.

        Args:
            query: Original query
            results: Results to rerank
            top_k: Number of results to return

        Returns:
            Reranked results
        """
        pass

    # Embedding Operations

    @abstractmethod
    async def generate_embedding(self, params: EmbeddingParams) -> List[float]:
        """
        Generate embedding for text.

        Args:
            params: Embedding parameters

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    async def generate_batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts
            batch_size: Batch size for API calls

        Returns:
            List of embedding vectors
        """
        pass

    # Index Operations

    @abstractmethod
    async def optimize_indices(self) -> IndexOptimizationResult:
        """
        Optimize search indices for better performance.

        Returns:
            Optimization result with created/updated indices
        """
        pass

    @abstractmethod
    async def rebuild_bm25_index(self) -> bool:
        """Rebuild BM25 full-text search index"""
        pass

    @abstractmethod
    async def rebuild_vector_index(self) -> bool:
        """Rebuild vector similarity index"""
        pass

    # Analytics

    @abstractmethod
    async def get_analytics(self) -> SearchAnalytics:
        """
        Get search system analytics.

        Returns:
            Analytics data including readiness and coverage
        """
        pass

    @abstractmethod
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get search performance metrics.

        Returns dict with:
        - avg_latency_ms: float
        - p95_latency_ms: float
        - total_searches: int
        - error_rate: float
        - cache_hit_rate: float
        """
        pass

    # CaseBank Operations (Optional)

    @abstractmethod
    async def search_casebank(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search CaseBank for similar past queries.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of matching cases
        """
        pass

    @abstractmethod
    async def add_to_casebank(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        category_path: Optional[List[str]] = None,
        quality: float = 1.0
    ) -> UUID:
        """
        Add a query-answer pair to CaseBank.

        Args:
            query: Original query
            answer: Generated answer
            sources: Source documents used
            category_path: Taxonomy classification
            quality: Quality score (0-1)

        Returns:
            Case ID
        """
        pass

    # Classification

    @abstractmethod
    async def classify_text(
        self,
        text: str,
        hint_paths: Optional[List[List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Classify text into taxonomy categories.

        Args:
            text: Text to classify
            hint_paths: Optional hint paths

        Returns:
            Classification result with canonical path and confidence
        """
        pass
