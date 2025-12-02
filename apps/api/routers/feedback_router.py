"""
Feedback API Router for DT-RAG Mentor Memory System

Provides REST endpoints for collecting and processing user feedback
to improve the AI mentor's performance.

@CODE:FEEDBACK-API-001
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import API Key authentication
from ..deps import verify_api_key
from ..security.api_key_storage import APIKeyInfo

# Import database and models
from ..database.daos.casebank_dao import CaseBankDAO
from ..database.daos.search_dao import SearchDAO
from ..database.connection import get_async_session
from ..database.models.casebank import ExecutionLog

# Import metrics tracking
from ..monitoring.metrics import get_metrics_collector

logger = logging.getLogger(__name__)

feedback_router = APIRouter(prefix="/feedback", tags=["feedback"])

# Pydantic models for request/response
class FeedbackRequest(BaseModel):
    """User feedback request model."""
    search_result_id: str = Field(..., description="ID of the search result")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    helpful: bool = Field(..., description="Whether the result was helpful")
    comment: Optional[str] = Field(None, description="Optional feedback comment")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class FeedbackResponse(BaseModel):
    """Feedback submission response model."""
    feedback_id: str = Field(..., description="Unique feedback ID")
    success: bool = Field(..., description="Whether submission was successful")
    message: str = Field(..., description="Response message")
    timestamp: str = Field(..., description="Submission timestamp")

@feedback_router.post("/", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    api_key: APIKeyInfo = Depends(verify_api_key),
):
    """
    Submit user feedback for a search result.

    This endpoint allows users to provide feedback on search results,
    which is used to improve the AI mentor's performance.
    """
    try:
        feedback_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # Get metrics collector
        metrics_collector = get_metrics_collector()

        # Validate search_result_id
        try:
            result_uuid = uuid.UUID(request.search_result_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid search_result_id format"
            )

        # Process feedback in database session
        async with get_async_session() as session:
            # Initialize DAOs
            casebank_dao = CaseBankDAO(session)

            # Record feedback as an execution log entry
            feedback_log = await casebank_dao.create_execution_log(
                case_id=result_uuid,
                success=request.helpful,
                execution_time_ms=0,
                error_type=None if request.helpful else "user_unhelpful",
                metadata={
                    "feedback_id": feedback_id,
                    "rating": request.rating,
                    "helpful": request.helpful,
                    "comment": request.comment,
                    "api_key_id": api_key.key_id,
                    "timestamp": timestamp,
                    "feedback_type": "user_rating",
                    **request.metadata
                }
            )

            # Update CaseBank success rate based on feedback
            if request.helpful:
                # Increase success rate for helpful feedback
                current_case = await casebank_dao.get_casebank_by_id(result_uuid)
                if current_case:
                    # Calculate new success rate: weighted average
                    new_success_rate = (
                        (current_case.success_rate * current_case.usage_count + request.rating) /
                        (current_case.usage_count + 1)
                    )
                    await casebank_dao.update_success_rate(
                        result_uuid,
                        min(new_success_rate, 1.0)  # Cap at 1.0
                    )

            # Record metrics
            metrics_collector.increment_counter(
                "feedback_submissions",
                {"helpful": str(request.helpful), "rating": str(request.rating)}
            )

            logger.info(
                f"✅ Feedback submitted: {feedback_id} "
                f"(rating: {request.rating}, helpful: {request.helpful}) "
                f"for result: {request.search_result_id}"
            )

            return FeedbackResponse(
                feedback_id=feedback_id,
                success=True,
                message="Feedback submitted successfully",
                timestamp=timestamp
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Feedback submission failed: {e}")
        metrics_collector.increment_counter("feedback_errors")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process feedback submission"
        )

@feedback_router.get("/stats")
async def get_feedback_stats(
    api_key: APIKeyInfo = Depends(verify_api_key),
) -> Dict[str, Any]:
    """
    Get feedback statistics and CaseBank metrics.

    Returns overall statistics about user feedback and CaseBank performance.
    """
    try:
        metrics_collector = get_metrics_collector()

        # Get CaseBank statistics
        async with get_async_session() as session:
            casebank_dao = CaseBankDAO(session)
            casebank_stats = await casebank_dao.get_casebank_stats()

        # Get feedback-specific metrics from metrics collector
        feedback_metrics = metrics_collector.get_counter("feedback_submissions")

        response_data = {
            "casebank_stats": casebank_stats,
            "feedback_metrics": feedback_metrics,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }

        logger.info("✅ Feedback stats retrieved successfully")

        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"❌ Failed to get feedback stats: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback statistics"
        )

@feedback_router.get("/health")
async def feedback_health_check():
    """Health check endpoint for feedback service."""
    return {
        "status": "healthy",
        "service": "feedback_api",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }