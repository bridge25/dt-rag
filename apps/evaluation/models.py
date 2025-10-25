"""
Database models for RAGAS evaluation system
"""
# @CODE:MYPY-001:PHASE2:BATCH5

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase
    Base = DeclarativeBase
else:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()


class SearchLog(Base):
    """Enhanced search log table for RAGAS evaluation"""

    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), nullable=True)  # For tracking user sessions
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    retrieved_docs = Column(JSON, nullable=True)  # List of retrieved document chunks

    # RAGAS Core Metrics
    context_precision = Column(Float, nullable=True)  # Precision of retrieved context
    context_recall = Column(Float, nullable=True)  # Recall of retrieved context
    faithfulness = Column(Float, nullable=True)  # Factual consistency of response
    answer_relevancy = Column(Float, nullable=True)  # Relevance of answer to query

    # Additional Quality Metrics
    response_time = Column(Float, nullable=True)  # Response latency in seconds
    num_retrieved_docs = Column(Integer, nullable=True)
    retrieval_score = Column(Float, nullable=True)  # Average retrieval score
    user_rating = Column(Integer, nullable=True)  # User satisfaction (1-5)
    search_type = Column(String(50), default="hybrid")

    # Metadata
    model_version = Column(String(50), nullable=True)
    experiment_id = Column(String(100), nullable=True)  # For A/B testing
    created_at = Column(DateTime, default=datetime.utcnow)

    # Quality flags
    is_valid_evaluation = Column(Boolean, default=True)
    quality_issues = Column(JSON, nullable=True)  # List of detected issues


class GoldenDataset(Base):
    """Golden dataset for evaluation benchmarking"""

    __tablename__ = "golden_dataset"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(String(100), nullable=False, unique=True)
    version = Column(String(20), nullable=False, default="1.0")

    query = Column(Text, nullable=False)
    ground_truth_answer = Column(Text, nullable=False)
    expected_contexts = Column(JSON, nullable=False)  # List of expected context chunks

    # Quality metadata
    difficulty_level = Column(String(20), default="medium")  # easy, medium, hard
    category = Column(String(50), nullable=True)
    tags = Column(JSON, nullable=True)

    # Validation scores
    inter_annotator_agreement = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)


class ExperimentRun(Base):
    """A/B testing experiment runs"""

    __tablename__ = "experiment_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Experiment configuration
    control_config = Column(JSON, nullable=False)  # Control system configuration
    treatment_config = Column(JSON, nullable=False)  # Treatment system configuration

    # Status and timing
    status = Column(
        String(20), default="planning"
    )  # planning, running, completed, stopped
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    # Statistical parameters
    significance_threshold = Column(Float, default=0.05)
    minimum_sample_size = Column(Integer, default=100)
    power_threshold = Column(Float, default=0.8)

    # Results
    results = Column(JSON, nullable=True)
    statistical_significance = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), nullable=True)


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
    model_version_: Optional[str] = Field(None, alias="model_version")


class EvaluationResult(BaseModel):
    """Result of RAGAS evaluation"""

    evaluation_id: str
    query: str
    metrics: EvaluationMetrics
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
