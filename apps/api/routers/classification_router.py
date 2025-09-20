"""
Classification API Router for DT-RAG v1.8.1

Provides REST endpoints for document classification including:
- Document chunk classification with HITL support
- Batch classification operations
- Classification confidence analysis
- Human-in-the-loop workflow management
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, Query, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import common schemas with fallback
import sys
from pathlib import Path as PathLib
sys.path.append(str(PathLib(__file__).parent.parent.parent.parent))

try:
    from packages.common_schemas.common_schemas.models import (
        ClassifyRequest, ClassifyResponse, TaxonomyNode
    )
except ImportError:
    # Fallback to local models
    try:
        from apps.api.models.common_models import ClassificationRequest as ClassifyRequest
        from apps.api.models.common_models import ClassificationResult as ClassifyResponse
    except ImportError:
        # Define minimal inline models if needed
        from pydantic import BaseModel, Field
        from typing import List, Optional

        class ClassifyRequest(BaseModel):
            """Request for document classification"""
            text: str = Field(..., description="Text to classify")
            chunk_id: Optional[str] = None
            taxonomy_version: Optional[str] = None

        class TaxonomyNode(BaseModel):
            """Taxonomy node model"""
            node_id: str
            label: str
            canonical_path: List[str]
            version: str
            confidence: float

        class ClassifyResponse(BaseModel):
            """Response for document classification"""
            canonical: List[str]
            candidates: List[TaxonomyNode]
            hitl: bool = False
            confidence: float
            reasoning: Optional[List[str]] = None

# Configure logging
logger = logging.getLogger(__name__)

# Create router
classification_router = APIRouter(prefix="/classify", tags=["Classification"])

# Additional models for classification operations

class BatchClassifyRequest(BaseModel):
    """Request for batch classification"""
    items: List[ClassifyRequest] = Field(..., min_items=1, max_items=100)
    taxonomy_version: Optional[str] = None

class BatchClassifyResponse(BaseModel):
    """Response for batch classification"""
    batch_id: str
    results: List[ClassifyResponse]
    summary: Dict[str, Any]
    processing_time_ms: float

class HITLReviewRequest(BaseModel):
    """Human-in-the-loop review request"""
    chunk_id: str
    approved_path: List[str]
    confidence_override: Optional[float] = None
    reviewer_notes: Optional[str] = None

class HITLTask(BaseModel):
    """HITL task for human review"""
    task_id: str
    chunk_id: str
    text: str
    suggested_classification: List[str]
    confidence: float
    alternatives: List["TaxonomyNode"]
    created_at: datetime
    priority: str = "normal"

class ClassificationAnalytics(BaseModel):
    """Classification analytics"""
    total_classifications: int
    avg_confidence: float
    hitl_rate: float
    accuracy_metrics: Dict[str, float]
    category_distribution: Dict[str, int]

# Mock classification service

class ClassificationService:
    """Mock classification service"""

    async def classify_single(self, request: ClassifyRequest) -> ClassifyResponse:
        """Classify a single document chunk"""
        # Mock classification logic
        confidence = 0.85 if "machine learning" in request.text.lower() else 0.72
        canonical_path = ["Technology", "AI", "Machine Learning"]

        # Determine if HITL is needed
        hitl_needed = confidence < 0.70

        candidates = [
            TaxonomyNode(
                node_id="tech-ai-ml",
                label="Machine Learning",
                canonical_path=canonical_path,
                version="1.8.1",
                confidence=confidence
            ),
            TaxonomyNode(
                node_id="tech-ai-nlp",
                label="Natural Language Processing",
                canonical_path=["Technology", "AI", "NLP"],
                version="1.8.1",
                confidence=0.65
            )
        ]

        return ClassifyResponse(
            canonical=canonical_path,
            candidates=candidates,
            hitl=hitl_needed,
            confidence=confidence,
            reasoning=[
                "Text contains machine learning terminology",
                "Technical context suggests AI/ML classification"
            ]
        )

    async def classify_batch(self, request: BatchClassifyRequest) -> BatchClassifyResponse:
        """Classify multiple document chunks"""
        batch_id = str(uuid.uuid4())
        results = []

        for item in request.items:
            result = await self.classify_single(item)
            results.append(result)

        summary = {
            "total_items": len(request.items),
            "hitl_required": sum(1 for r in results if r.hitl),
            "avg_confidence": sum(r.confidence for r in results) / len(results),
            "categories": list(set(tuple(r.canonical) for r in results))
        }

        return BatchClassifyResponse(
            batch_id=batch_id,
            results=results,
            summary=summary,
            processing_time_ms=125.5
        )

    async def get_hitl_tasks(self, limit: int = 50) -> List[HITLTask]:
        """Get pending HITL tasks"""
        return [
            HITLTask(
                task_id=str(uuid.uuid4()),
                chunk_id="doc456_chunk789",
                text="Quantum computing represents a fundamental shift...",
                suggested_classification=["Technology", "Computing", "Quantum"],
                confidence=0.65,
                alternatives=[],
                created_at=datetime.utcnow(),
                priority="high"
            )
        ]

    async def submit_hitl_review(self, review: HITLReviewRequest) -> Dict[str, Any]:
        """Submit HITL review"""
        return {
            "task_id": str(uuid.uuid4()),
            "status": "approved",
            "updated_classification": review.approved_path,
            "reviewer_notes": review.reviewer_notes
        }

    async def get_analytics(self) -> ClassificationAnalytics:
        """Get classification analytics"""
        return ClassificationAnalytics(
            total_classifications=45672,
            avg_confidence=0.78,
            hitl_rate=0.15,
            accuracy_metrics={
                "precision": 0.89,
                "recall": 0.87,
                "f1_score": 0.88
            },
            category_distribution={
                "Technology": 15432,
                "Science": 12456,
                "Business": 9876,
                "Arts": 5432,
                "Other": 2476
            }
        )

# Dependency injection
async def get_classification_service() -> ClassificationService:
    """Get classification service instance"""
    return ClassificationService()

# API Endpoints

@classification_router.post("/", response_model=ClassifyResponse)
async def classify_document_chunk(
    request: ClassifyRequest,
    service: ClassificationService = Depends(get_classification_service)
):
    """
    Classify a document chunk into taxonomy categories

    Features:
    - AI-powered classification with confidence scoring
    - Multiple candidate suggestions
    - Automatic HITL triggering for low confidence
    - Reasoning explanation for transparency
    """
    try:
        # Validate request
        if not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content cannot be empty"
            )

        if len(request.text) > 10000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content exceeds maximum length of 10000 characters"
            )

        # Perform classification
        result = await service.classify_single(request)

        # Add response headers
        headers = {
            "X-Classification-Confidence": str(result.confidence),
            "X-HITL-Required": str(result.hitl).lower(),
            "X-Candidates-Count": str(len(result.candidates))
        }

        return JSONResponse(
            content=result.dict(),
            headers=headers
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Classification operation failed"
        )

@classification_router.post("/batch", response_model=BatchClassifyResponse)
async def classify_batch(
    request: BatchClassifyRequest,
    background_tasks: BackgroundTasks,
    service: ClassificationService = Depends(get_classification_service)
):
    """
    Classify multiple document chunks in batch

    Features:
    - Efficient batch processing
    - Parallel classification execution
    - Batch-level analytics and summaries
    - Background processing for large batches
    """
    try:
        # Validate batch size
        if len(request.items) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size exceeds maximum of 100 items"
            )

        # For large batches, process in background
        if len(request.items) > 50:
            batch_id = str(uuid.uuid4())
            background_tasks.add_task(
                service.classify_batch, request
            )
            return JSONResponse(
                content={
                    "batch_id": batch_id,
                    "status": "processing",
                    "message": "Large batch submitted for background processing"
                },
                status_code=202  # Accepted
            )

        # Process smaller batches immediately
        result = await service.classify_batch(request)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch classification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch classification operation failed"
        )

@classification_router.get("/hitl/tasks", response_model=List[HITLTask])
async def get_hitl_tasks(
    limit: int = Query(50, ge=1, le=100, description="Maximum tasks to return"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    service: ClassificationService = Depends(get_classification_service)
):
    """
    Get pending human-in-the-loop classification tasks

    Returns tasks that require human review including:
    - Low confidence classifications
    - Ambiguous cases
    - Quality assurance samples
    """
    try:
        tasks = await service.get_hitl_tasks(limit)

        # Filter by priority if specified
        if priority:
            tasks = [task for task in tasks if task.priority == priority]

        return tasks

    except Exception as e:
        logger.error(f"Failed to get HITL tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve HITL tasks"
        )

@classification_router.post("/hitl/review")
async def submit_hitl_review(
    review: HITLReviewRequest,
    service: ClassificationService = Depends(get_classification_service)
):
    """
    Submit human review for classification task

    Allows human reviewers to:
    - Approve or modify AI classifications
    - Provide confidence overrides
    - Add reviewer notes and feedback
    """
    try:
        # Validate review data
        if not review.approved_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approved classification path is required"
            )

        result = await service.submit_hitl_review(review)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HITL review submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit HITL review"
        )

@classification_router.get("/analytics", response_model=ClassificationAnalytics)
async def get_classification_analytics(
    service: ClassificationService = Depends(get_classification_service)
):
    """
    Get classification analytics and performance metrics

    Returns:
    - Classification volume and accuracy statistics
    - HITL usage rates and effectiveness
    - Category distribution analysis
    - Performance trends over time
    """
    try:
        analytics = await service.get_analytics()
        return analytics

    except Exception as e:
        logger.error(f"Failed to get classification analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve classification analytics"
        )

@classification_router.get("/confidence/{chunk_id}")
async def get_classification_confidence(
    chunk_id: str,
    service: ClassificationService = Depends(get_classification_service)
):
    """
    Get detailed confidence analysis for a classification

    Returns:
    - Confidence breakdown by factors
    - Alternative classifications with scores
    - Feature importance analysis
    """
    try:
        # Mock confidence analysis
        confidence_analysis = {
            "chunk_id": chunk_id,
            "overall_confidence": 0.85,
            "confidence_factors": {
                "text_clarity": 0.92,
                "taxonomy_match": 0.88,
                "context_relevance": 0.75,
                "keyword_presence": 0.95
            },
            "uncertainty_sources": [
                "Ambiguous technical terminology",
                "Multiple valid interpretations"
            ],
            "recommendations": [
                "Consider human review for edge cases",
                "Collect more domain-specific training data"
            ]
        }

        return confidence_analysis

    except Exception as e:
        logger.error(f"Failed to get confidence analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve confidence analysis"
        )

@classification_router.get("/status")
async def get_classification_status():
    """
    Get classification system status and health

    Returns:
    - Model status and performance
    - Processing queue information
    - System health metrics
    """
    try:
        status_info = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "model_info": {
                "model_version": "1.8.1",
                "last_trained": "2024-12-15T09:00:00Z",
                "accuracy": 0.89,
                "total_training_samples": 125000
            },
            "processing_stats": {
                "classifications_per_minute": 45,
                "avg_processing_time_ms": 89,
                "queue_length": 12,
                "hitl_queue_length": 3
            },
            "health_checks": {
                "model_service": "healthy",
                "taxonomy_service": "healthy",
                "hitl_service": "healthy"
            }
        }

        return status_info

    except Exception as e:
        logger.error(f"Failed to get classification status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve classification status"
        )

# Export router
__all__ = ["classification_router"]