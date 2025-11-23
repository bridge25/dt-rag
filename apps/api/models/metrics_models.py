"""
Taxonomy Usage Metrics Models

Models for tracking taxonomy usage, search patterns, and user interactions.
Designed for time-series analysis and evolution decision support.

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


class EventType(str, Enum):
    """Types of trackable events"""
    SEARCH_QUERY = "search_query"
    CATEGORY_VIEW = "category_view"
    CATEGORY_SELECT = "category_select"
    DOCUMENT_VIEW = "document_view"
    SEARCH_RESULT_CLICK = "search_result_click"
    SUGGESTION_VIEW = "suggestion_view"
    SUGGESTION_ACCEPT = "suggestion_accept"
    SUGGESTION_REJECT = "suggestion_reject"
    TAXONOMY_NAVIGATE = "taxonomy_navigate"
    FEEDBACK_POSITIVE = "feedback_positive"
    FEEDBACK_NEGATIVE = "feedback_negative"
    ZERO_RESULTS = "zero_results"


class AggregationPeriod(str, Enum):
    """Time periods for metrics aggregation"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


# ============================================================================
# Dataclasses - Core Domain Models
# ============================================================================


@dataclass
class UsageEvent:
    """A single usage event for tracking"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    taxonomy_id: str
    category_id: Optional[str] = None
    document_id: Optional[str] = None
    query_text: Optional[str] = None
    user_id: Optional[str] = None  # Anonymous tracking
    session_id: Optional[str] = None
    result_count: Optional[int] = None
    response_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"evt_{uuid.uuid4().hex[:12]}"


@dataclass
class CategoryMetrics:
    """Aggregated metrics for a single category"""
    category_id: str
    taxonomy_id: str
    period_start: datetime
    period_end: datetime
    period_type: AggregationPeriod

    # View metrics
    total_views: int = 0
    unique_views: int = 0

    # Search metrics
    search_hits: int = 0  # Times appeared in search results
    search_clicks: int = 0  # Times clicked from search results
    click_through_rate: float = 0.0

    # Navigation metrics
    navigation_entries: int = 0  # Direct navigation to category
    navigation_exits: int = 0  # Left category for another

    # Document metrics
    documents_viewed: int = 0
    avg_documents_per_session: float = 0.0

    # Effectiveness
    bounce_rate: float = 0.0  # Users who left immediately
    avg_time_spent_seconds: float = 0.0


@dataclass
class QueryMetrics:
    """Metrics for search queries"""
    query_text: str
    taxonomy_id: str
    period_start: datetime
    period_end: datetime

    total_searches: int = 0
    zero_result_count: int = 0
    avg_result_count: float = 0.0
    avg_response_time_ms: float = 0.0

    # Click metrics
    total_clicks: int = 0
    click_through_rate: float = 0.0

    # Category distribution
    category_distribution: Dict[str, int] = field(default_factory=dict)

    # Potential for new category
    is_potential_category: bool = False
    similarity_to_existing: float = 0.0


@dataclass
class TaxonomyHealthMetrics:
    """Overall health metrics for a taxonomy"""
    taxonomy_id: str
    calculated_at: datetime
    period_type: AggregationPeriod

    # Coverage metrics
    total_categories: int = 0
    active_categories: int = 0  # Had activity in period
    orphan_categories: int = 0  # No activity

    # Search effectiveness
    overall_hit_rate: float = 0.0
    zero_result_rate: float = 0.0
    avg_search_time_ms: float = 0.0

    # Category balance
    category_utilization_variance: float = 0.0  # How evenly distributed
    overloaded_categories: List[str] = field(default_factory=list)  # >2x avg
    underutilized_categories: List[str] = field(default_factory=list)  # <0.5x avg

    # Evolution metrics
    pending_suggestions: int = 0
    suggestion_acceptance_rate: float = 0.0
    last_evolution_date: Optional[datetime] = None


@dataclass
class ZeroResultQuery:
    """A query that returned no results - potential new category"""
    query_text: str
    taxonomy_id: str
    first_seen: datetime
    last_seen: datetime
    occurrence_count: int = 1
    similar_queries: List[str] = field(default_factory=list)
    potential_category_name: Optional[str] = None
    confidence_score: float = 0.0


# ============================================================================
# Pydantic Models - API Request/Response
# ============================================================================


class RecordEventRequest(BaseModel):
    """Request to record a usage event"""
    event_type: EventType
    taxonomy_id: str
    category_id: Optional[str] = None
    document_id: Optional[str] = None
    query_text: Optional[str] = None
    session_id: Optional[str] = None
    result_count: Optional[int] = None
    response_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CategoryMetricsResponse(BaseModel):
    """Response model for category metrics"""
    category_id: str
    taxonomy_id: str
    period_start: datetime
    period_end: datetime
    total_views: int
    unique_views: int
    search_hits: int
    search_clicks: int
    click_through_rate: float
    bounce_rate: float
    avg_time_spent_seconds: float

    class Config:
        from_attributes = True


class QueryMetricsResponse(BaseModel):
    """Response model for query metrics"""
    query_text: str
    total_searches: int
    zero_result_count: int
    avg_result_count: float
    click_through_rate: float
    is_potential_category: bool

    class Config:
        from_attributes = True


class TaxonomyHealthResponse(BaseModel):
    """Response model for taxonomy health"""
    taxonomy_id: str
    calculated_at: datetime
    total_categories: int
    active_categories: int
    orphan_categories: int
    overall_hit_rate: float
    zero_result_rate: float
    overloaded_categories: List[str]
    underutilized_categories: List[str]
    suggestion_acceptance_rate: float

    class Config:
        from_attributes = True


class MetricsSummaryResponse(BaseModel):
    """Summary response for dashboard"""
    taxonomy_id: str
    period: AggregationPeriod
    period_start: datetime
    period_end: datetime

    # Key metrics
    total_events: int
    total_searches: int
    total_category_views: int
    unique_users: int

    # Performance
    avg_response_time_ms: float
    zero_result_rate: float
    overall_ctr: float

    # Top performers
    top_categories: List[Dict[str, Any]]
    top_queries: List[Dict[str, Any]]

    # Alerts
    potential_new_categories: List[str]
    underperforming_categories: List[str]


class ZeroResultQueryResponse(BaseModel):
    """Response for zero result queries"""
    queries: List[Dict[str, Any]]
    total_count: int
    potential_categories: List[Dict[str, Any]]


class EventBatchRequest(BaseModel):
    """Batch request for recording multiple events"""
    events: List[RecordEventRequest]
