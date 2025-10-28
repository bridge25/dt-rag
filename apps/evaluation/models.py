# @CODE:EVAL-001 | SPEC: .moai/specs/SPEC-EVAL-001/spec.md | TEST: tests/evaluation/
# @CODE:MYPY-CONSOLIDATION-002 | Phase 1: SQLAlchemy Column Type Casting

"""
Database models for RAGAS evaluation system
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pydantic import BaseModel, Field


class Base(DeclarativeBase):
    pass


class SearchLog(Base):
    """Enhanced search log table for RAGAS evaluation"""

    __tablename__ = "search_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(50))
    query: Mapped[str] = mapped_column(Text)
    response: Mapped[Optional[str]] = mapped_column(Text)
    retrieved_docs: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # RAGAS Core Metrics
    context_precision: Mapped[Optional[float]] = mapped_column(Float)
    context_recall: Mapped[Optional[float]] = mapped_column(Float)
    faithfulness: Mapped[Optional[float]] = mapped_column(Float)
    answer_relevancy: Mapped[Optional[float]] = mapped_column(Float)

    # Additional Quality Metrics
    response_time: Mapped[Optional[float]] = mapped_column(Float)
    num_retrieved_docs: Mapped[Optional[int]] = mapped_column(Integer)
    retrieval_score: Mapped[Optional[float]] = mapped_column(Float)
    user_rating: Mapped[Optional[int]] = mapped_column(Integer)
    search_type: Mapped[str] = mapped_column(String(50), default="hybrid")

    # Metadata
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    experiment_id: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Quality flags
    is_valid_evaluation: Mapped[bool] = mapped_column(Boolean, default=True)
    quality_issues: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)


class GoldenDataset(Base):
    """Golden dataset for evaluation benchmarking"""

    __tablename__ = "golden_dataset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[str] = mapped_column(String(100), unique=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0")

    query: Mapped[str] = mapped_column(Text)
    ground_truth_answer: Mapped[str] = mapped_column(Text)
    expected_contexts: Mapped[Dict[str, Any]] = mapped_column(JSON)

    # Quality metadata
    difficulty_level: Mapped[str] = mapped_column(String(20), default="medium")
    category: Mapped[Optional[str]] = mapped_column(String(50))
    tags: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Validation scores
    inter_annotator_agreement: Mapped[Optional[float]] = mapped_column(Float)
    quality_score: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(100))


class ExperimentRun(Base):
    """A/B testing experiment runs"""

    __tablename__ = "experiment_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Experiment configuration
    control_config: Mapped[Dict[str, Any]] = mapped_column(JSON)
    treatment_config: Mapped[Dict[str, Any]] = mapped_column(JSON)

    # Status and timing
    status: Mapped[str] = mapped_column(String(20), default="planning")
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Statistical parameters
    significance_threshold: Mapped[float] = mapped_column(Float, default=0.05)
    minimum_sample_size: Mapped[int] = mapped_column(Integer, default=100)
    power_threshold: Mapped[float] = mapped_column(Float, default=0.8)

    # Results
    results: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    statistical_significance: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(100))


# Pydantic models for API


class EvaluationMetrics(BaseModel):
    """RAGAS evaluation metrics"""

    context_precision: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Precision of retrieved contexts"
    )
    context_recall: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Recall of retrieved contexts"
    )
    faithfulness: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Factual consistency score"
    )
    answer_relevancy: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Answer relevance to query"
    )

    # Additional metrics
    response_time: Optional[float] = Field(
        None, ge=0.0, description="Response time in seconds"
    )
    retrieval_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Average retrieval score"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "context_precision": 0.85,
                "context_recall": 0.78,
                "faithfulness": 0.92,
                "answer_relevancy": 0.88,
                "response_time": 1.2,
                "retrieval_score": 0.76,
            }
        }


class EvaluationRequest(BaseModel):
    """Request for evaluating a RAG response"""

    query: str = Field(..., description="User query")
    response: str = Field(..., description="Generated response")
    retrieved_contexts: List[str] = Field(
        ..., description="List of retrieved context chunks"
    )
    ground_truth: Optional[str] = Field(
        None, description="Expected correct answer (if available)"
    )

    # Optional metadata
    session_id: Optional[str] = None
    experiment_id: Optional[str] = None
    model_version: Optional[str] = Field(
        None, description="Model version used for generation"
    )

    model_config = {"protected_namespaces": ()}


class EvaluationResult(BaseModel):
    """Result of RAGAS evaluation"""

    evaluation_id: str
    query: str
    metrics: EvaluationMetrics
    overall_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Overall evaluation score"
    )
    quality_flags: List[str] = Field(
        default_factory=list, description="Quality issues detected"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Improvement suggestions"
    )
    timestamp: datetime

    # Detailed results
    detailed_analysis: Optional[Dict[str, Any]] = None


class QualityThresholds(BaseModel):
    """Quality thresholds for monitoring"""

    faithfulness_min: float = Field(0.85, ge=0.0, le=1.0)
    context_precision_min: float = Field(0.75, ge=0.0, le=1.0)
    context_recall_min: float = Field(0.70, ge=0.0, le=1.0)
    answer_relevancy_min: float = Field(0.80, ge=0.0, le=1.0)

    # Performance thresholds
    response_time_max: float = Field(5.0, gt=0.0)  # seconds


class QualityAlert(BaseModel):
    """Quality monitoring alert"""

    alert_id: str
    metric_name: str
    current_value: float
    threshold_value: float
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    message: str
    timestamp: datetime
    suggested_actions: List[str] = Field(default_factory=list)


class DatasetEntry(BaseModel):
    """Golden dataset entry"""

    query: str
    ground_truth_answer: str
    expected_contexts: List[str]
    difficulty_level: str = Field("medium", pattern="^(easy|medium|hard)$")
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class ExperimentConfig(BaseModel):
    """A/B testing experiment configuration"""

    experiment_id: str
    name: str
    description: Optional[str] = None

    control_config: Dict[str, Any]
    treatment_config: Dict[str, Any]

    # Statistical parameters
    significance_threshold: float = Field(0.05, gt=0.0, lt=1.0)
    minimum_sample_size: int = Field(100, gt=0)
    power_threshold: float = Field(0.8, gt=0.0, lt=1.0)


class ExperimentResults(BaseModel):
    """A/B testing experiment results"""

    experiment_id: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Sample sizes
    control_samples: int
    treatment_samples: int

    # Metric comparisons
    metric_comparisons: Dict[
        str, Dict[str, Any]
    ]  # metric_name -> {control_mean, treatment_mean, p_value, effect_size}

    # Statistical significance
    is_statistically_significant: bool
    confidence_interval: Dict[str, List[float]]  # metric_name -> [lower, upper]

    # Recommendations
    recommendation: str  # "rollout", "rollback", "continue_testing"
    summary: str
