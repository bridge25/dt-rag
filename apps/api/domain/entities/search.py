"""
Search Entity - Core Business Model

Represents search results and metadata for RAG operations.

Business Rules:
- Score must be between 0 and 1
- Results should include source attribution
- Metadata tracks search strategy used

@CODE:CLEAN-ARCHITECTURE-SEARCH-ENTITY
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum


class SearchStrategy(str, Enum):
    """Search strategy type"""
    BM25 = "bm25"
    VECTOR = "vector"
    HYBRID = "hybrid"


class RetrievalSource(str, Enum):
    """Source of retrieval result"""
    BM25 = "bm25"
    VECTOR = "vector"
    CASEBANK = "casebank"
    HYBRID = "hybrid"
    FALLBACK = "fallback"


@dataclass(frozen=True)
class SearchMetadata:
    """
    Search Result Metadata

    Tracks how a result was retrieved and scored.

    Attributes:
        source: Which retrieval method found this result
        bm25_score: BM25 lexical matching score
        vector_score: Vector similarity score
        hybrid_score: Combined weighted score
        rerank_score: Optional cross-encoder reranking score
        latency_ms: Time to retrieve this result
    """
    source: RetrievalSource = RetrievalSource.HYBRID
    bm25_score: float = 0.0
    vector_score: float = 0.0
    hybrid_score: float = 0.0
    rerank_score: Optional[float] = None
    latency_ms: float = 0.0

    @property
    def final_score(self) -> float:
        """Get the final score used for ranking"""
        if self.rerank_score is not None:
            return self.rerank_score
        return self.hybrid_score


@dataclass(frozen=True)
class SearchResult:
    """
    Search Result Entity

    A single search result with content and scoring.

    Attributes:
        chunk_id: Source chunk identifier
        doc_id: Source document identifier
        text: Retrieved text content
        score: Final relevance score (0-1)
        title: Optional document title
        source_url: Optional source URL
        taxonomy_path: Classification path
        metadata: Search metadata
    """
    chunk_id: UUID
    doc_id: UUID
    text: str
    score: float
    title: Optional[str] = None
    source_url: Optional[str] = None
    taxonomy_path: List[str] = field(default_factory=list)
    metadata: SearchMetadata = field(default_factory=SearchMetadata)

    def __post_init__(self) -> None:
        """Validate business rules"""
        if not 0 <= self.score <= 1:
            raise ValueError("Score must be between 0 and 1")

    @property
    def has_source_attribution(self) -> bool:
        """Check if result has proper source attribution"""
        return bool(self.source_url or self.title)

    @property
    def summary(self) -> str:
        """Get a brief summary of the result"""
        max_length = 200
        if len(self.text) <= max_length:
            return self.text
        return self.text[:max_length] + "..."


@dataclass(frozen=True)
class SearchQuery:
    """
    Search Query Entity

    Represents a user search query with configuration.

    Attributes:
        query_text: The search query string
        top_k: Maximum results to return
        strategy: Search strategy to use
        filters: Taxonomy/metadata filters
        include_metadata: Whether to include detailed metadata
        rerank: Whether to apply cross-encoder reranking
    """
    query_text: str
    top_k: int = 5
    strategy: SearchStrategy = SearchStrategy.HYBRID
    filters: Dict[str, Any] = field(default_factory=dict)
    include_metadata: bool = True
    rerank: bool = True

    def __post_init__(self) -> None:
        """Validate business rules"""
        if not self.query_text or not self.query_text.strip():
            raise ValueError("Query text cannot be empty")
        if self.top_k < 1 or self.top_k > 100:
            raise ValueError("top_k must be between 1 and 100")


@dataclass(frozen=True)
class SearchResponse:
    """
    Search Response Entity

    Complete search response with results and metrics.

    Attributes:
        query: Original query
        results: List of search results
        total_results: Total results found
        query_time_ms: Total query execution time
        strategy_used: Actual strategy used
        execution_metrics: Detailed execution metrics
    """
    query: str
    results: List[SearchResult]
    total_results: int
    query_time_ms: float
    strategy_used: SearchStrategy = SearchStrategy.HYBRID
    execution_metrics: Dict[str, Any] = field(default_factory=dict)
    executed_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def has_results(self) -> bool:
        """Check if search returned any results"""
        return len(self.results) > 0

    @property
    def top_result(self) -> Optional[SearchResult]:
        """Get the highest scoring result"""
        if not self.results:
            return None
        return max(self.results, key=lambda r: r.score)

    @property
    def avg_score(self) -> float:
        """Calculate average result score"""
        if not self.results:
            return 0.0
        return sum(r.score for r in self.results) / len(self.results)


# Business Logic Functions

def calculate_hybrid_score(
    bm25_score: float,
    vector_score: float,
    bm25_weight: float = 0.5,
    vector_weight: float = 0.5
) -> float:
    """
    Calculate hybrid search score.

    Business Rules:
    - Weights must sum to 1.0
    - Both scores should be normalized (0-1)
    """
    if abs(bm25_weight + vector_weight - 1.0) > 0.01:
        raise ValueError("Weights must sum to 1.0")
    return bm25_score * bm25_weight + vector_score * vector_weight


def should_apply_reranking(
    results: List[SearchResult],
    min_results: int = 3,
    score_variance_threshold: float = 0.1
) -> bool:
    """
    Determine if reranking would be beneficial.

    Business Rules:
    - Need at least min_results for meaningful reranking
    - High score variance suggests reranking could help
    """
    if len(results) < min_results:
        return False

    scores = [r.score for r in results]
    avg = sum(scores) / len(scores)
    variance = sum((s - avg) ** 2 for s in scores) / len(scores)

    return variance < score_variance_threshold


def filter_results_by_taxonomy(
    results: List[SearchResult],
    allowed_paths: List[List[str]]
) -> List[SearchResult]:
    """Filter results to only include those matching taxonomy paths"""
    if not allowed_paths:
        return results

    allowed_set = {tuple(path) for path in allowed_paths}
    return [
        r for r in results
        if tuple(r.taxonomy_path) in allowed_set or
        any(tuple(r.taxonomy_path[:len(path)]) == tuple(path) for path in allowed_paths)
    ]


def calculate_result_diversity(results: List[SearchResult]) -> float:
    """
    Calculate diversity score based on taxonomy coverage.

    Returns value between 0 (all same taxonomy) and 1 (all different).
    """
    if len(results) <= 1:
        return 1.0

    unique_paths = {tuple(r.taxonomy_path) for r in results if r.taxonomy_path}
    return len(unique_paths) / len(results)
