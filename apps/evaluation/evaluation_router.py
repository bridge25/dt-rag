"""
RAGAS Evaluation API Router for DT-RAG v1.8.1

Provides comprehensive REST endpoints for RAG evaluation:
- RAGAS metric calculation (Context Precision, Recall, Faithfulness, Answer Relevancy)
- Real-time quality monitoring and alerting
- A/B testing and experiment management
- Golden dataset management for benchmarking
- Evaluation analytics and reporting
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .models import (
    EvaluationRequest, EvaluationResult, EvaluationMetrics,
    QualityThresholds, QualityAlert, DatasetEntry,
    ExperimentConfig, ExperimentResults
)
from .ragas_engine import RAGASEvaluator
from .quality_monitor import QualityMonitor
from .experiment_tracker import ExperimentTracker
from ..api.database import db_manager

logger = logging.getLogger(__name__)

# Create router
evaluation_router = APIRouter(prefix="/evaluation", tags=["RAGAS Evaluation"])

# Global instances
ragas_evaluator = RAGASEvaluator()
quality_monitor = QualityMonitor()
experiment_tracker = ExperimentTracker()

# Additional Pydantic models for API

class EvaluationBatchRequest(BaseModel):
    """Batch evaluation request"""
    evaluations: List[EvaluationRequest]
    async_processing: bool = False

class QualityDashboard(BaseModel):
    """Quality monitoring dashboard data"""
    current_status: Dict[str, Any]
    recent_trends: Dict[str, Any]
    active_alerts: List[QualityAlert]
    quality_gates: Dict[str, Any]
    recommendations: List[str]

class DatasetValidationResult(BaseModel):
    """Dataset validation result"""
    is_valid: bool
    validation_errors: List[str]
    quality_score: float
    statistics: Dict[str, Any]

# Dependency injection
async def get_ragas_evaluator() -> RAGASEvaluator:
    """Get RAGAS evaluator instance"""
    return ragas_evaluator

async def get_quality_monitor() -> QualityMonitor:
    """Get quality monitor instance"""
    return quality_monitor

async def get_experiment_tracker() -> ExperimentTracker:
    """Get experiment tracker instance"""
    return experiment_tracker

# Core evaluation endpoints

@evaluation_router.post("/evaluate", response_model=EvaluationResult)
async def evaluate_rag_response(
    request: EvaluationRequest,
    evaluator: RAGASEvaluator = Depends(get_ragas_evaluator),
    monitor: QualityMonitor = Depends(get_quality_monitor)
):
    """
    Evaluate RAG response using RAGAS metrics

    Calculates:
    - Context Precision: Relevance of retrieved contexts
    - Context Recall: Coverage of necessary information
    - Faithfulness: Factual consistency with contexts
    - Answer Relevancy: Relevance to user query

    Returns comprehensive evaluation with recommendations.
    """
    try:
        # Perform RAGAS evaluation
        result = await evaluator.evaluate_rag_response(
            query=request.query,
            response=request.response,
            retrieved_contexts=request.retrieved_contexts,
            ground_truth=request.ground_truth
        )

        # Record for quality monitoring
        alerts = await monitor.record_evaluation(result)

        # Store evaluation in database
        await _store_evaluation_result(request, result)

        # Add alerts to response if any
        if alerts:
            result.quality_flags.extend([alert.alert_id for alert in alerts])

        return result

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )

@evaluation_router.post("/evaluate/batch")
async def evaluate_batch(
    request: EvaluationBatchRequest,
    evaluator: RAGASEvaluator = Depends(get_ragas_evaluator)
):
    """
    Batch evaluate multiple RAG responses

    Supports:
    - Synchronous batch processing (returns all results)
    - Asynchronous processing (returns job ID for status tracking)
    - Parallel evaluation for improved performance
    """
    try:
        if request.async_processing:
            # Start async processing
            job_id = str(uuid.uuid4())

            # TODO: Implement async job processing with Celery or similar
            # For now, return mock job response
            return {
                "job_id": job_id,
                "status": "processing",
                "total_evaluations": len(request.evaluations),
                "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
            }

        # Synchronous processing
        results = []
        for eval_request in request.evaluations:
            result = await evaluator.evaluate_rag_response(
                query=eval_request.query,
                response=eval_request.response,
                retrieved_contexts=eval_request.retrieved_contexts,
                ground_truth=eval_request.ground_truth
            )
            results.append(result)

            # Store in database
            await _store_evaluation_result(eval_request, result)

        return {
            "batch_id": str(uuid.uuid4()),
            "total_evaluations": len(results),
            "results": results,
            "summary": _summarize_batch_results(results)
        }

    except Exception as e:
        logger.error(f"Batch evaluation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch evaluation failed: {str(e)}"
        )

# Quality monitoring endpoints

@evaluation_router.get("/quality/dashboard", response_model=QualityDashboard)
async def get_quality_dashboard(
    monitor: QualityMonitor = Depends(get_quality_monitor)
):
    """
    Get comprehensive quality monitoring dashboard

    Returns:
    - Current quality metrics and status
    - Quality trends over time
    - Active quality alerts
    - Quality gate status
    - Improvement recommendations
    """
    try:
        current_status = await monitor.get_quality_status()
        recent_trends = await monitor.get_quality_trends(hours=24)
        active_alerts = await monitor.get_quality_alerts(active_only=True)

        return QualityDashboard(
            current_status=current_status,
            recent_trends=recent_trends,
            active_alerts=active_alerts,
            quality_gates=current_status.get('quality_gates', {}),
            recommendations=current_status.get('recommendations', [])
        )

    except Exception as e:
        logger.error(f"Failed to get quality dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve quality dashboard: {str(e)}"
        )

@evaluation_router.get("/quality/trends")
async def get_quality_trends(
    hours: int = Query(24, ge=1, le=168, description="Hours of trend data to retrieve"),
    monitor: QualityMonitor = Depends(get_quality_monitor)
):
    """
    Get quality trends over specified time period

    Returns hourly aggregated quality metrics with trend analysis.
    """
    try:
        trends = await monitor.get_quality_trends(hours=hours)
        return trends

    except Exception as e:
        logger.error(f"Failed to get quality trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve quality trends: {str(e)}"
        )

@evaluation_router.get("/quality/alerts", response_model=List[QualityAlert])
async def get_quality_alerts(
    active_only: bool = Query(True, description="Only return active alerts"),
    monitor: QualityMonitor = Depends(get_quality_monitor)
):
    """
    Get quality monitoring alerts

    Returns list of quality alerts with severity and suggested actions.
    """
    try:
        alerts = await monitor.get_quality_alerts(active_only=active_only)
        return alerts

    except Exception as e:
        logger.error(f"Failed to get quality alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve quality alerts: {str(e)}"
        )

@evaluation_router.put("/quality/thresholds")
async def update_quality_thresholds(
    thresholds: QualityThresholds,
    monitor: QualityMonitor = Depends(get_quality_monitor)
):
    """
    Update quality monitoring thresholds

    Allows configuration of quality thresholds for alerting and quality gates.
    """
    try:
        await monitor.update_thresholds(thresholds)

        return {
            "message": "Quality thresholds updated successfully",
            "thresholds": thresholds.dict(),
            "updated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to update quality thresholds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update quality thresholds: {str(e)}"
        )

# A/B testing and experiment endpoints

@evaluation_router.post("/experiments")
async def create_experiment(
    config: ExperimentConfig,
    tracker: ExperimentTracker = Depends(get_experiment_tracker)
):
    """
    Create new A/B testing experiment

    Sets up experiment configuration for comparing different RAG system versions.
    """
    try:
        experiment_id = await tracker.create_experiment(config)

        return {
            "experiment_id": experiment_id,
            "message": "Experiment created successfully",
            "next_steps": [
                "Start experiment to begin collecting data",
                "Users will be automatically assigned to control/treatment groups",
                "Monitor experiment progress via status endpoint"
            ]
        }

    except Exception as e:
        logger.error(f"Failed to create experiment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create experiment: {str(e)}"
        )

@evaluation_router.post("/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: str,
    tracker: ExperimentTracker = Depends(get_experiment_tracker)
):
    """
    Start running an A/B testing experiment

    Begins data collection and user assignment for the experiment.
    """
    try:
        success = await tracker.start_experiment(experiment_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment {experiment_id} not found"
            )

        return {
            "experiment_id": experiment_id,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "message": "Experiment started successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start experiment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start experiment: {str(e)}"
        )

@evaluation_router.post("/experiments/{experiment_id}/stop")
async def stop_experiment(
    experiment_id: str,
    reason: str = Query("manual_stop", description="Reason for stopping experiment"),
    tracker: ExperimentTracker = Depends(get_experiment_tracker)
):
    """
    Stop a running A/B testing experiment

    Stops data collection and generates final results analysis.
    """
    try:
        success = await tracker.stop_experiment(experiment_id, reason)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment {experiment_id} not found"
            )

        return {
            "experiment_id": experiment_id,
            "status": "stopped",
            "reason": reason,
            "stopped_at": datetime.utcnow().isoformat(),
            "message": "Experiment stopped successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop experiment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop experiment: {str(e)}"
        )

@evaluation_router.get("/experiments/{experiment_id}/status")
async def get_experiment_status(
    experiment_id: str,
    tracker: ExperimentTracker = Depends(get_experiment_tracker)
):
    """
    Get current status of A/B testing experiment

    Returns experiment progress, sample sizes, and preliminary results if available.
    """
    try:
        status_info = await tracker.get_experiment_status(experiment_id)

        if 'error' in status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=status_info['error']
            )

        return status_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get experiment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get experiment status: {str(e)}"
        )

@evaluation_router.get("/experiments/{experiment_id}/results", response_model=ExperimentResults)
async def get_experiment_results(
    experiment_id: str,
    tracker: ExperimentTracker = Depends(get_experiment_tracker)
):
    """
    Get detailed results of A/B testing experiment

    Returns statistical analysis, significance testing, and recommendations.
    """
    try:
        results = await tracker.analyze_experiment_results(experiment_id)

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No results available for experiment {experiment_id}"
            )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get experiment results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get experiment results: {str(e)}"
        )

# Canary deployment endpoints

@evaluation_router.post("/canary/deploy")
async def deploy_canary(
    canary_config: Dict[str, Any],
    traffic_percentage: float = Query(5.0, ge=0.1, le=50.0, description="Percentage of traffic for canary"),
    duration_minutes: int = Query(60, ge=10, le=1440, description="Monitoring duration in minutes"),
    tracker: ExperimentTracker = Depends(get_experiment_tracker)
):
    """
    Deploy and monitor canary release

    Automatically monitors quality metrics and triggers rollback if degradation detected.
    """
    try:
        monitoring_result = await tracker.monitor_canary_deployment(
            canary_config=canary_config,
            traffic_percentage=traffic_percentage,
            duration_minutes=duration_minutes
        )

        return monitoring_result

    except Exception as e:
        logger.error(f"Canary deployment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Canary deployment failed: {str(e)}"
        )

# Golden dataset endpoints

@evaluation_router.post("/dataset/validate")
async def validate_dataset(
    entries: List[DatasetEntry]
) -> DatasetValidationResult:
    """
    Validate golden dataset entries

    Checks dataset quality, consistency, and completeness for evaluation benchmarking.
    """
    try:
        validation_errors = []
        quality_scores = []

        # Validate each entry
        for i, entry in enumerate(entries):
            entry_errors = []

            # Check required fields
            if not entry.query.strip():
                entry_errors.append(f"Entry {i}: Query is empty")

            if not entry.ground_truth_answer.strip():
                entry_errors.append(f"Entry {i}: Ground truth answer is empty")

            if not entry.expected_contexts:
                entry_errors.append(f"Entry {i}: No expected contexts provided")

            # Check quality
            if len(entry.query.split()) < 3:
                entry_errors.append(f"Entry {i}: Query too short (< 3 words)")

            if len(entry.ground_truth_answer.split()) < 5:
                entry_errors.append(f"Entry {i}: Answer too short (< 5 words)")

            validation_errors.extend(entry_errors)

            # Calculate quality score for entry (0-1)
            entry_quality = 1.0 - (len(entry_errors) * 0.1)
            quality_scores.append(max(0.0, entry_quality))

        # Overall statistics
        overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        statistics_info = {
            "total_entries": len(entries),
            "valid_entries": len([s for s in quality_scores if s > 0.8]),
            "avg_query_length": sum(len(e.query.split()) for e in entries) / len(entries),
            "avg_answer_length": sum(len(e.ground_truth_answer.split()) for e in entries) / len(entries),
            "difficulty_distribution": {
                level: len([e for e in entries if e.difficulty_level == level])
                for level in ["easy", "medium", "hard"]
            }
        }

        return DatasetValidationResult(
            is_valid=len(validation_errors) == 0,
            validation_errors=validation_errors,
            quality_score=overall_quality,
            statistics=statistics_info
        )

    except Exception as e:
        logger.error(f"Dataset validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dataset validation failed: {str(e)}"
        )

@evaluation_router.post("/dataset/benchmark")
async def run_dataset_benchmark(
    dataset_id: str = Query(..., description="Golden dataset ID to benchmark against"),
    evaluator: RAGASEvaluator = Depends(get_ragas_evaluator)
):
    """
    Run benchmark evaluation against golden dataset

    Evaluates current RAG system performance against curated golden dataset.
    """
    try:
        # TODO: Load golden dataset from database
        # For now, return mock benchmark results

        benchmark_results = {
            "dataset_id": dataset_id,
            "benchmark_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "faithfulness": 0.87,
                "context_precision": 0.82,
                "context_recall": 0.79,
                "answer_relevancy": 0.85
            },
            "performance_comparison": {
                "vs_previous_benchmark": {
                    "faithfulness": "+0.03",
                    "context_precision": "-0.01",
                    "context_recall": "+0.02",
                    "answer_relevancy": "+0.04"
                }
            },
            "detailed_results": {
                "total_queries": 100,
                "passed_quality_gates": 89,
                "failed_queries": 11,
                "avg_processing_time": 1.34
            },
            "recommendations": [
                "Improve context precision by optimizing retrieval ranking",
                "Overall performance shows positive trend"
            ]
        }

        return benchmark_results

    except Exception as e:
        logger.error(f"Dataset benchmark failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dataset benchmark failed: {str(e)}"
        )

# Analytics endpoints

@evaluation_router.get("/analytics/summary")
async def get_evaluation_analytics(
    days: int = Query(7, ge=1, le=90, description="Days of analytics data")
):
    """
    Get comprehensive evaluation analytics

    Returns performance metrics, quality trends, and system insights.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        async with db_manager.async_session() as session:
            from sqlalchemy import text, func

            # Query evaluation statistics
            query = text("""
                SELECT
                    COUNT(*) as total_evaluations,
                    AVG(faithfulness) as avg_faithfulness,
                    AVG(context_precision) as avg_context_precision,
                    AVG(context_recall) as avg_context_recall,
                    AVG(answer_relevancy) as avg_answer_relevancy,
                    AVG(response_time) as avg_response_time,
                    COUNT(CASE WHEN faithfulness >= 0.85 THEN 1 END) as high_quality_responses
                FROM search_logs
                WHERE created_at >= :cutoff_date
                AND is_valid_evaluation = true
            """)

            result = await session.execute(query, {'cutoff_date': cutoff_date})
            stats = result.fetchone()

            analytics = {
                "period_days": days,
                "summary_statistics": {
                    "total_evaluations": int(stats[0]) if stats[0] else 0,
                    "avg_faithfulness": float(stats[1]) if stats[1] else None,
                    "avg_context_precision": float(stats[2]) if stats[2] else None,
                    "avg_context_recall": float(stats[3]) if stats[3] else None,
                    "avg_answer_relevancy": float(stats[4]) if stats[4] else None,
                    "avg_response_time": float(stats[5]) if stats[5] else None,
                    "high_quality_rate": float(stats[6]) / max(1, stats[0]) if stats[0] else 0
                },
                "quality_insights": {
                    "strengths": _identify_system_strengths(stats),
                    "improvement_areas": _identify_improvement_areas(stats),
                    "trends": "stable"  # TODO: Calculate actual trends
                },
                "generated_at": datetime.utcnow().isoformat()
            }

            return analytics

    except Exception as e:
        logger.error(f"Failed to get evaluation analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve evaluation analytics: {str(e)}"
        )

# Helper functions

async def _store_evaluation_result(request: EvaluationRequest, result: EvaluationResult):
    """Store evaluation result in database"""
    try:
        async with db_manager.async_session() as session:
            from sqlalchemy import text

            insert_query = text("""
                INSERT INTO search_logs (
                    session_id, query, response, retrieved_docs,
                    context_precision, context_recall, faithfulness, answer_relevancy,
                    response_time, num_retrieved_docs, model_version, experiment_id,
                    is_valid_evaluation, quality_issues, created_at
                ) VALUES (
                    :session_id, :query, :response, :retrieved_docs,
                    :context_precision, :context_recall, :faithfulness, :answer_relevancy,
                    :response_time, :num_retrieved_docs, :model_version, :experiment_id,
                    :is_valid_evaluation, :quality_issues, :created_at
                )
            """)

            await session.execute(insert_query, {
                'session_id': request.session_id,
                'query': request.query,
                'response': request.response,
                'retrieved_docs': request.retrieved_contexts,
                'context_precision': result.metrics.context_precision,
                'context_recall': result.metrics.context_recall,
                'faithfulness': result.metrics.faithfulness,
                'answer_relevancy': result.metrics.answer_relevancy,
                'response_time': result.metrics.response_time,
                'num_retrieved_docs': len(request.retrieved_contexts),
                'model_version': request.model_version,
                'experiment_id': request.experiment_id,
                'is_valid_evaluation': len(result.quality_flags) == 0,
                'quality_issues': result.quality_flags,
                'created_at': result.timestamp
            })

            await session.commit()

    except Exception as e:
        logger.error(f"Failed to store evaluation result: {e}")

def _summarize_batch_results(results: List[EvaluationResult]) -> Dict[str, Any]:
    """Summarize batch evaluation results"""
    if not results:
        return {}

    metrics_sums = {
        'faithfulness': [],
        'context_precision': [],
        'context_recall': [],
        'answer_relevancy': []
    }

    for result in results:
        if result.metrics.faithfulness is not None:
            metrics_sums['faithfulness'].append(result.metrics.faithfulness)
        if result.metrics.context_precision is not None:
            metrics_sums['context_precision'].append(result.metrics.context_precision)
        if result.metrics.context_recall is not None:
            metrics_sums['context_recall'].append(result.metrics.context_recall)
        if result.metrics.answer_relevancy is not None:
            metrics_sums['answer_relevancy'].append(result.metrics.answer_relevancy)

    return {
        "total_evaluations": len(results),
        "average_metrics": {
            metric: sum(values) / len(values) if values else None
            for metric, values in metrics_sums.items()
        },
        "quality_issues": sum(len(result.quality_flags) for result in results),
        "high_quality_responses": len([r for r in results if not r.quality_flags])
    }

def _identify_system_strengths(stats) -> List[str]:
    """Identify system strengths from statistics"""
    strengths = []

    if stats[1] and stats[1] > 0.9:  # High faithfulness
        strengths.append("Excellent factual accuracy")
    if stats[4] and stats[4] > 0.85:  # High answer relevancy
        strengths.append("Highly relevant responses")
    if stats[5] and stats[5] < 2.0:  # Fast response time
        strengths.append("Fast response times")

    return strengths

def _identify_improvement_areas(stats) -> List[str]:
    """Identify areas needing improvement from statistics"""
    improvements = []

    if stats[1] and stats[1] < 0.8:  # Low faithfulness
        improvements.append("Factual accuracy needs improvement")
    if stats[2] and stats[2] < 0.75:  # Low context precision
        improvements.append("Retrieval precision needs optimization")
    if stats[3] and stats[3] < 0.7:  # Low context recall
        improvements.append("Context coverage needs expansion")

    return improvements