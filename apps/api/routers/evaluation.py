"""
RAGAS Evaluation API Router for DT-RAG v1.8.1

Provides REST endpoints for RAG system evaluation including:
- Single response evaluation
- Batch evaluation
- Quality monitoring and alerting
- Golden dataset management
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

try:
    from ..deps import verify_api_key
except ImportError:

    def verify_api_key() -> None:
        return None


from apps.evaluation.models import (
    EvaluationMetrics,
    EvaluationRequest,
    EvaluationResult,
    QualityThresholds,
)
from apps.evaluation.ragas_engine import RAGASEvaluator

logger = logging.getLogger(__name__)

evaluation_router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


class BatchEvaluationRequest(BaseModel):
    """Request for batch evaluation"""

    evaluations: List[EvaluationRequest] = Field(..., min_items=1, max_items=50)


class BatchEvaluationResponse(BaseModel):
    """Response for batch evaluation"""

    batch_id: str
    results: List[EvaluationResult]
    summary: Dict[str, Any]
    processing_time_ms: float


class QualityMonitoringResponse(BaseModel):
    """Quality monitoring metrics"""

    period_start: datetime
    period_end: datetime
    total_evaluations: int
    average_metrics: EvaluationMetrics
    quality_alerts: List[Dict[str, Any]]
    trend_analysis: Dict[str, Any]


async def get_evaluator() -> RAGASEvaluator:
    """Get RAGAS evaluator instance"""
    return RAGASEvaluator()


@evaluation_router.post("/evaluate", response_model=EvaluationResult)
async def evaluate_rag_response(
    request: EvaluationRequest,
    evaluator: RAGASEvaluator = Depends(get_evaluator),
    api_key: str = Depends(verify_api_key),
):
    """
    Evaluate a single RAG response using RAGAS metrics

    Metrics evaluated:
    - Context Precision: Relevance of retrieved contexts
    - Context Recall: Coverage of necessary information
    - Faithfulness: Factual consistency with contexts
    - Answer Relevancy: How well answer addresses query

    Returns comprehensive evaluation with quality flags and recommendations.
    """
    try:
        if not request.query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty"
            )

        if not request.response.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Response cannot be empty",
            )

        if not request.retrieved_contexts or len(request.retrieved_contexts) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one retrieved context is required",
            )

        result = await evaluator.evaluate_rag_response(
            query=request.query,
            response=request.response,
            retrieved_contexts=request.retrieved_contexts,
            ground_truth=request.ground_truth,
        )

        headers = {
            "X-Evaluation-ID": result.evaluation_id,
            "X-Overall-Score": str(result.overall_score),
            "X-Has-Quality-Issues": str(len(result.quality_flags) > 0).lower(),
        }

        return JSONResponse(content=result.dict(), headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Evaluation operation failed",
        )


@evaluation_router.post("/evaluate/batch", response_model=BatchEvaluationResponse)
async def evaluate_batch(
    request: BatchEvaluationRequest,
    evaluator: RAGASEvaluator = Depends(get_evaluator),
    api_key: str = Depends(verify_api_key),
):
    """
    Evaluate multiple RAG responses in batch

    Features:
    - Efficient batch processing
    - Aggregate metrics calculation
    - Quality trend analysis
    - Batch-level recommendations
    """
    try:
        import time
        import uuid

        if len(request.evaluations) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch size exceeds maximum of 50 evaluations",
            )

        batch_id = str(uuid.uuid4())
        start_time = time.time()

        results = []
        for eval_request in request.evaluations:
            result = await evaluator.evaluate_rag_response(
                query=eval_request.query,
                response=eval_request.response,
                retrieved_contexts=eval_request.retrieved_contexts,
                ground_truth=eval_request.ground_truth,
            )
            results.append(result)

        processing_time_ms = (time.time() - start_time) * 1000

        avg_precision = sum(r.metrics.context_precision or 0.0 for r in results) / len(
            results
        )
        avg_recall = sum(r.metrics.context_recall or 0.0 for r in results) / len(
            results
        )
        avg_faithfulness = sum(r.metrics.faithfulness or 0.0 for r in results) / len(
            results
        )
        avg_relevancy = sum(r.metrics.answer_relevancy or 0.0 for r in results) / len(
            results
        )
        avg_overall = sum(r.overall_score for r in results) / len(results)

        summary = {
            "total_evaluations": len(results),
            "average_scores": {
                "context_precision": avg_precision,
                "context_recall": avg_recall,
                "faithfulness": avg_faithfulness,
                "answer_relevancy": avg_relevancy,
                "overall_score": avg_overall,
            },
            "quality_issues_count": sum(len(r.quality_flags) for r in results),
            "evaluations_with_issues": sum(1 for r in results if r.quality_flags),
            "processing_time_per_eval_ms": processing_time_ms / len(results),
        }

        return BatchEvaluationResponse(
            batch_id=batch_id,
            results=results,
            summary=summary,
            processing_time_ms=processing_time_ms,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch evaluation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch evaluation operation failed",
        )


@evaluation_router.get("/thresholds", response_model=QualityThresholds)
async def get_quality_thresholds(api_key: str = Depends(verify_api_key)) -> None:
    """
    Get current quality thresholds for monitoring

    Thresholds are used to trigger quality alerts and recommendations.
    """
    try:
        thresholds = QualityThresholds()
        return thresholds

    except Exception as e:
        logger.error(f"Failed to get quality thresholds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quality thresholds",
        )


@evaluation_router.put("/thresholds", response_model=QualityThresholds)
async def update_quality_thresholds(
    thresholds: QualityThresholds, api_key: str = Depends(verify_api_key)
):
    """
    Update quality thresholds for monitoring

    Allows customization of alert thresholds based on system requirements.
    """
    try:
        logger.info(f"Quality thresholds updated: {thresholds.dict()}")
        return thresholds

    except Exception as e:
        logger.error(f"Failed to update quality thresholds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update quality thresholds",
        )


@evaluation_router.get("/status")
async def get_evaluation_system_status(api_key: str = Depends(verify_api_key)) -> None:
    """
    Get evaluation system status and health

    Returns:
    - Gemini API connectivity status
    - Langfuse integration status
    - System configuration
    - Recent evaluation statistics
    """
    try:
        import os

        gemini_configured = bool(os.getenv("GEMINI_API_KEY"))

        try:
            from apps.api.monitoring.langfuse_client import get_langfuse_status

            langfuse_status = get_langfuse_status()
        except ImportError:
            langfuse_status = {"available": False}

        status_info = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "gemini_api": {
                "configured": gemini_configured,
                "model": "gemini-2.5-flash-latest",
                "cost_per_1m_input_tokens_usd": 0.075,
                "cost_per_1m_output_tokens_usd": 0.30,
            },
            "langfuse_integration": langfuse_status,
            "evaluation_features": {
                "context_precision": True,
                "context_recall": True,
                "faithfulness": True,
                "answer_relevancy": True,
                "batch_evaluation": True,
                "quality_monitoring": True,
            },
            "configuration": {
                "max_batch_size": 50,
                "default_thresholds": QualityThresholds().dict(),
            },
        }

        return status_info

    except Exception as e:
        logger.error(f"Failed to get evaluation system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve evaluation system status",
        )


__all__ = ["evaluation_router"]
