"""
Taxonomy Evolution Engine Models

Dataclasses and Pydantic models for ML-powered taxonomy generation,
evolution suggestions, and proposal management.

@CODE:TAXONOMY-EVOLUTION-001
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


# ============================================================================
# Enums
# ============================================================================


class SuggestionType(str, Enum):
    """Types of evolution suggestions"""
    NEW_CATEGORY = "new_category"
    MERGE = "merge"
    SPLIT = "split"
    RELATIONSHIP = "relationship"
    RENAME = "rename"
    MOVE = "move"


class ProposalStatus(str, Enum):
    """Status of a taxonomy proposal"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FAILED = "failed"


class GenerationAlgorithm(str, Enum):
    """Available taxonomy generation algorithms"""
    LDA_TOPIC = "lda_topic_modeling"
    BERT_CLUSTERING = "bert_clustering"
    KMEANS = "kmeans"
    HDBSCAN = "hdbscan"
    HIERARCHICAL = "hierarchical"
    KEYWORD = "keyword_clustering"


class Granularity(str, Enum):
    """Taxonomy granularity levels"""
    COARSE = "coarse"
    MEDIUM = "medium"
    FINE = "fine"


# ============================================================================
# Dataclasses - Core Domain Models
# ============================================================================


@dataclass
class GeneratorConfig:
    """Configuration for taxonomy generation"""
    max_depth: int = 4
    min_documents_per_category: int = 5
    granularity: Granularity = Granularity.MEDIUM
    domain_hints: List[str] = field(default_factory=list)
    use_ontology: bool = False
    language: str = "auto"
    algorithm: GenerationAlgorithm = GenerationAlgorithm.KMEANS
    min_cluster_size: int = 5
    n_clusters: Optional[int] = None  # Auto-detect if None
    similarity_threshold: float = 0.7


@dataclass
class ProposedCategory:
    """A proposed taxonomy category from generation"""
    id: str
    name: str
    description: str
    parent_id: Optional[str]
    confidence_score: float
    document_count: int
    sample_document_ids: List[str]
    keywords: List[str]
    centroid_embedding: Optional[List[float]] = None
    children: List["ProposedCategory"] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            self.id = f"cat_{uuid.uuid4().hex[:8]}"


@dataclass
class TaxonomyProposal:
    """A complete taxonomy proposal from generation"""
    proposal_id: str
    status: ProposalStatus
    categories: List[ProposedCategory]
    config: GeneratorConfig
    total_documents: int
    processing_time_seconds: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.proposal_id:
            self.proposal_id = f"prop_{uuid.uuid4().hex[:12]}"


@dataclass
class EvolutionSuggestion:
    """A suggestion for taxonomy evolution"""
    id: str
    suggestion_type: SuggestionType
    confidence: float
    impact_score: float
    affected_documents: int
    details: Dict[str, Any]
    created_at: datetime
    expires_at: datetime
    status: str = "pending"  # pending, accepted, rejected, expired

    def __post_init__(self):
        if not self.id:
            self.id = f"sug_{uuid.uuid4().hex[:8]}"
        if not self.expires_at:
            self.expires_at = self.created_at + timedelta(days=30)


@dataclass
class MergeSuggestion:
    """Details for a category merge suggestion"""
    source_category_ids: List[str]
    target_name: str
    overlap_score: float
    shared_keywords: List[str]
    total_affected_documents: int


@dataclass
class SplitSuggestion:
    """Details for a category split suggestion"""
    source_category_id: str
    proposed_splits: List[Dict[str, Any]]
    diversity_score: float
    document_distribution: Dict[str, int]


@dataclass
class ClusteringResult:
    """Result from document clustering"""
    cluster_id: int
    document_ids: List[str]
    centroid: List[float]
    keywords: List[str]
    label: str
    confidence: float
    size: int


@dataclass
class EvolutionMetrics:
    """Metrics for tracking taxonomy evolution"""
    taxonomy_id: str
    period_start: datetime
    period_end: datetime
    total_queries: int
    category_hit_rates: Dict[str, float]
    zero_result_queries: List[str]
    suggestion_acceptance_rate: float
    average_search_time_ms: float


# ============================================================================
# Pydantic Models - API Request/Response
# ============================================================================


class GenerateRequest(BaseModel):
    """Request to generate taxonomy from documents"""
    document_ids: Optional[List[str]] = Field(
        None,
        description="Document IDs to use. If None, uses all documents"
    )
    max_depth: int = Field(4, ge=1, le=10, description="Maximum taxonomy depth")
    min_documents_per_category: int = Field(
        5, ge=1, description="Minimum documents per category"
    )
    granularity: Granularity = Field(
        Granularity.MEDIUM, description="Taxonomy granularity level"
    )
    domain_hints: List[str] = Field(
        default_factory=list, description="Domain-specific hints"
    )
    algorithm: GenerationAlgorithm = Field(
        GenerationAlgorithm.KMEANS, description="Clustering algorithm"
    )
    n_clusters: Optional[int] = Field(
        None, ge=2, le=100, description="Number of clusters (auto if None)"
    )


class ProposedCategoryResponse(BaseModel):
    """Response model for a proposed category"""
    id: str
    name: str
    description: str
    parent_id: Optional[str]
    confidence_score: float
    document_count: int
    sample_document_ids: List[str]
    keywords: List[str]
    children: List["ProposedCategoryResponse"] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TaxonomyProposalResponse(BaseModel):
    """Response model for taxonomy proposal"""
    proposal_id: str
    status: ProposalStatus
    categories: List[ProposedCategoryResponse]
    total_documents: int
    processing_time_seconds: float
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    config: Dict[str, Any]

    class Config:
        from_attributes = True


class GenerateStatusResponse(BaseModel):
    """Status response for generation in progress"""
    proposal_id: str
    status: ProposalStatus
    progress: float = Field(ge=0.0, le=1.0, description="Progress 0-1")
    current_step: str
    estimated_remaining_seconds: Optional[int]


class EvolutionSuggestionResponse(BaseModel):
    """Response model for evolution suggestion"""
    id: str
    suggestion_type: SuggestionType
    confidence: float
    impact_score: float
    affected_documents: int
    details: Dict[str, Any]
    created_at: datetime
    expires_at: datetime
    status: str

    class Config:
        from_attributes = True


class SuggestionsListResponse(BaseModel):
    """Response for list of suggestions"""
    suggestions: List[EvolutionSuggestionResponse]
    total_count: int
    pending_count: int
    summary: Dict[str, Any]


class AcceptProposalRequest(BaseModel):
    """Request to accept a taxonomy proposal"""
    modifications: Optional[Dict[str, Any]] = Field(
        None, description="Optional modifications to apply"
    )
    taxonomy_version: Optional[str] = Field(
        None, description="Version string for new taxonomy"
    )


class AcceptSuggestionRequest(BaseModel):
    """Request to accept a suggestion"""
    apply_immediately: bool = Field(
        True, description="Apply changes immediately"
    )


class RejectSuggestionRequest(BaseModel):
    """Request to reject a suggestion"""
    reason: Optional[str] = Field(None, description="Rejection reason")


class AnalyticsResponse(BaseModel):
    """Response for taxonomy analytics"""
    taxonomy_id: str
    period: str
    usage_stats: Dict[str, Any]
    effectiveness_metrics: Dict[str, Any]
    evolution_history: List[Dict[str, Any]]
    suggestions_summary: Dict[str, Any]


# Enable forward references for recursive models
ProposedCategoryResponse.model_rebuild()
