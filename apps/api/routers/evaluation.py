"""
Evaluation API Router

Provides REST API endpoints for RAGAS evaluation and quality assessment:
- Single query evaluation
- Batch evaluation
- Golden dataset management
- Quality gate monitoring
- Performance analytics
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from apps.evaluation.core.ragas_engine import RAGASEvaluationEngine, RAGResponse, EvaluationResult
from apps.evaluation.core.golden_dataset import GoldenDatasetManager, GoldenDataPoint
from apps.search.core.search_dao import SearchDAO
from apps.monitoring.core.metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)

# Initialize components
ragas_engine = RAGASEvaluationEngine()
golden_dataset_manager = GoldenDatasetManager()
search_dao = SearchDAO()
metrics_collector = MetricsCollector()

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

# Request/Response Models
class QueryEvaluationRequest(BaseModel):
    query: str = Field(..., description="Query to evaluate")
    expected_answer: Optional[str] = Field(None, description="Expected answer for comparison")
    expected_contexts: Optional[List[str]] = Field(None, description="Expected relevant contexts")
    use_golden_dataset: bool = Field(False, description="Whether to use golden dataset for comparison")

class BatchEvaluationRequest(BaseModel):
    queries: List[str] = Field(..., description="List of queries to evaluate")
    golden_dataset_name: Optional[str] = Field(None, description="Golden dataset to use for evaluation")
    sample_size: Optional[int] = Field(None, description="Number of queries to sample (if not all)")
    random_seed: Optional[int] = Field(42, description="Random seed for reproducible sampling")

class RAGResponseModel(BaseModel):
    answer: str
    retrieved_docs: List[Dict[str, Any]]
    confidence: float = 0.0
    metadata: Dict[str, Any] = {}

class EvaluationResponse(BaseModel):
    evaluation_id: str
    query: str
    metrics: Dict[str, float]
    quality_gates_passed: bool
    recommendations: List[str]
    timestamp: datetime

class BatchEvaluationResponse(BaseModel):
    batch_id: str
    total_queries: int
    completed_queries: int
    status: str  # "running", "completed", "failed"
    overall_metrics: Dict[str, float]
    quality_gates_passed: bool
    started_at: datetime
    completed_at: Optional[datetime] = None

class GoldenDataPointModel(BaseModel):
    query: str
    expected_answer: str
    expected_contexts: List[str]
    taxonomy_path: List[str]
    difficulty_level: str = Field(..., regex="^(easy|medium|hard)$")
    domain: str
    metadata: Dict[str, Any] = {}

# In-memory batch tracking (in production, use Redis or database)
batch_evaluations = {}

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_query(request: QueryEvaluationRequest):
    """
    Evaluate a single query using RAGAS metrics
    """
    try:
        logger.info(f"Starting evaluation for query: {request.query[:100]}...")

        # Execute search to get RAG response
        search_results = await search_dao.hybrid_search(
            query=request.query,
            limit=10,
            hybrid_alpha=0.7
        )

        # Convert search results to RAG response format
        rag_response = RAGResponse(
            answer=search_results.get('generated_answer', 'No answer generated'),
            retrieved_docs=[
                {
                    'text': doc.get('content', ''),
                    'title': doc.get('title', ''),
                    'taxonomy_path': doc.get('taxonomy_path', []),
                    'score': doc.get('score', 0.0)
                }
                for doc in search_results.get('documents', [])
            ],
            confidence=search_results.get('confidence', 0.0),
            metadata={
                'search_type': 'hybrid',
                'total_results': len(search_results.get('documents', [])),
                'search_time': search_results.get('search_time', 0.0)
            }
        )

        # Prepare evaluation data
        ground_truths = [request.expected_answer] if request.expected_answer else None
        expected_contexts = [request.expected_contexts] if request.expected_contexts else None

        # Run RAGAS evaluation
        evaluation_result = await ragas_engine.evaluate_rag_system(
            test_queries=[request.query],
            rag_responses=[rag_response],
            ground_truths=ground_truths,
            expected_contexts=expected_contexts
        )

        # Generate evaluation ID
        evaluation_id = f"eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(request.query) % 10000}"

        # Record metrics
        await metrics_collector.record_evaluation_metrics(evaluation_result.metrics)

        logger.info(f"Evaluation completed. Quality gates passed: {evaluation_result.quality_gates_passed}")

        return EvaluationResponse(
            evaluation_id=evaluation_id,
            query=request.query,
            metrics=evaluation_result.metrics,
            quality_gates_passed=evaluation_result.quality_gates_passed,
            recommendations=evaluation_result.recommendations,
            timestamp=evaluation_result.timestamp
        )

    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@router.post("/evaluate/batch", response_model=BatchEvaluationResponse)
async def start_batch_evaluation(request: BatchEvaluationRequest, background_tasks: BackgroundTasks):
    """
    Start a batch evaluation process
    """
    try:
        batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(request.queries)}"

        # Initialize batch tracking
        batch_evaluations[batch_id] = {
            "status": "running",
            "total_queries": len(request.queries),
            "completed_queries": 0,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "results": [],
            "overall_metrics": {},
            "quality_gates_passed": False
        }

        # Start background evaluation
        background_tasks.add_task(
            run_batch_evaluation,
            batch_id,
            request.queries,
            request.golden_dataset_name,
            request.sample_size,
            request.random_seed
        )

        logger.info(f"Started batch evaluation {batch_id} for {len(request.queries)} queries")

        return BatchEvaluationResponse(
            batch_id=batch_id,
            total_queries=len(request.queries),
            completed_queries=0,
            status="running",
            overall_metrics={},
            quality_gates_passed=False,
            started_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Batch evaluation start failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch evaluation failed: {str(e)}")

@router.get("/evaluate/batch/{batch_id}", response_model=BatchEvaluationResponse)
async def get_batch_evaluation_status(batch_id: str):
    """
    Get status of a batch evaluation
    """
    if batch_id not in batch_evaluations:
        raise HTTPException(status_code=404, detail="Batch evaluation not found")

    batch_data = batch_evaluations[batch_id]

    return BatchEvaluationResponse(
        batch_id=batch_id,
        total_queries=batch_data["total_queries"],
        completed_queries=batch_data["completed_queries"],
        status=batch_data["status"],
        overall_metrics=batch_data["overall_metrics"],
        quality_gates_passed=batch_data["quality_gates_passed"],
        started_at=batch_data["started_at"],
        completed_at=batch_data["completed_at"]
    )

@router.get("/metrics/summary")
async def get_evaluation_metrics_summary():
    """
    Get summary of recent evaluation metrics
    """
    try:
        summary = ragas_engine.get_evaluation_summary()
        return JSONResponse(content=summary)
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics summary: {str(e)}")

@router.get("/golden-dataset")
async def list_golden_datasets():
    """
    List available golden datasets
    """
    try:
        datasets = await golden_dataset_manager.list_datasets()
        return JSONResponse(content={"datasets": datasets})
    except Exception as e:
        logger.error(f"Failed to list golden datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list datasets: {str(e)}")

@router.post("/golden-dataset/{dataset_name}")
async def create_golden_dataset(dataset_name: str, data_points: List[GoldenDataPointModel]):
    """
    Create a new golden dataset
    """
    try:
        # Convert Pydantic models to GoldenDataPoint objects
        golden_points = []
        for point in data_points:
            golden_point = GoldenDataPoint(
                id=f"dp_{len(golden_points)}_{hash(point.query) % 10000}",
                query=point.query,
                expected_answer=point.expected_answer,
                expected_contexts=point.expected_contexts,
                taxonomy_path=point.taxonomy_path,
                difficulty_level=point.difficulty_level,
                domain=point.domain,
                metadata=point.metadata
            )
            golden_points.append(golden_point)

        # Create dataset
        dataset = await golden_dataset_manager.create_dataset(
            name=dataset_name,
            data_points=golden_points,
            description=f"Golden dataset with {len(golden_points)} data points"
        )

        logger.info(f"Created golden dataset '{dataset_name}' with {len(golden_points)} data points")

        return JSONResponse(content={
            "message": f"Golden dataset '{dataset_name}' created successfully",
            "dataset_id": dataset.id,
            "data_points_count": len(golden_points)
        })

    except Exception as e:
        logger.error(f"Failed to create golden dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create dataset: {str(e)}")

@router.get("/golden-dataset/{dataset_name}")
async def get_golden_dataset(dataset_name: str):
    """
    Get golden dataset details
    """
    try:
        dataset = await golden_dataset_manager.load_dataset(dataset_name)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        return JSONResponse(content={
            "dataset_id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "data_points_count": len(dataset.data_points),
            "created_at": dataset.created_at.isoformat(),
            "quality_score": dataset.quality_score,
            "domains": list(set(point.domain for point in dataset.data_points)),
            "difficulty_distribution": {
                level: sum(1 for point in dataset.data_points if point.difficulty_level == level)
                for level in ["easy", "medium", "hard"]
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get golden dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get dataset: {str(e)}")

@router.get("/quality-gates/status")
async def get_quality_gates_status():
    """
    Get current quality gates status and thresholds
    """
    try:
        thresholds = {
            **ragas_engine.metrics_config,
            **{k: {"threshold": v} for k, v in ragas_engine.taxonomy_thresholds.items()}
        }

        # Get recent evaluation results
        summary = ragas_engine.get_evaluation_summary()
        recent_metrics = summary.get("average_metrics", {})

        # Check which gates are passing
        gates_status = {}
        for metric_name, config in thresholds.items():
            threshold = config.get("threshold", 0.8)
            current_value = recent_metrics.get(metric_name, 0.0)

            gates_status[metric_name] = {
                "threshold": threshold,
                "current_value": current_value,
                "status": "passing" if current_value >= threshold else "failing",
                "gap": threshold - current_value if current_value < threshold else 0.0
            }

        overall_status = all(gate["status"] == "passing" for gate in gates_status.values())

        return JSONResponse(content={
            "overall_status": "passing" if overall_status else "failing",
            "gates": gates_status,
            "last_evaluation": summary.get("latest_evaluation"),
            "success_rate": summary.get("success_rate", 0.0)
        })

    except Exception as e:
        logger.error(f"Failed to get quality gates status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get quality gates status: {str(e)}")

@router.get("/performance/trends")
async def get_performance_trends(
    days: int = Query(7, description="Number of days to analyze", ge=1, le=30)
):
    """
    Get performance trends over time
    """
    try:
        # This would typically query a time-series database
        # For now, we'll use the in-memory evaluation history

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Filter evaluations within date range
        relevant_evaluations = [
            eval_rec for eval_rec in ragas_engine.evaluation_history
            if start_date <= eval_rec["timestamp"] <= end_date
        ]

        if not relevant_evaluations:
            return JSONResponse(content={
                "message": f"No evaluations found in the last {days} days",
                "trends": {}
            })

        # Calculate daily averages
        daily_metrics = {}
        for eval_rec in relevant_evaluations:
            date_key = eval_rec["timestamp"].date().isoformat()
            if date_key not in daily_metrics:
                daily_metrics[date_key] = []
            daily_metrics[date_key].append(eval_rec["metrics"])

        # Calculate trends
        trends = {}
        for date, metrics_list in daily_metrics.items():
            daily_avg = {}
            for metric_name in ragas_engine.metrics_config.keys():
                values = [m.get(metric_name, 0) for m in metrics_list if metric_name in m]
                daily_avg[metric_name] = sum(values) / len(values) if values else 0.0
            trends[date] = daily_avg

        return JSONResponse(content={
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "evaluations_count": len(relevant_evaluations),
            "trends": trends
        })

    except Exception as e:
        logger.error(f"Failed to get performance trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance trends: {str(e)}")

# Background task functions
async def run_batch_evaluation(
    batch_id: str,
    queries: List[str],
    golden_dataset_name: Optional[str] = None,
    sample_size: Optional[int] = None,
    random_seed: int = 42
):
    """
    Run batch evaluation in background
    """
    try:
        batch_data = batch_evaluations[batch_id]

        # Sample queries if needed
        if sample_size and sample_size < len(queries):
            import random
            random.seed(random_seed)
            queries = random.sample(queries, sample_size)
            batch_data["total_queries"] = len(queries)

        # Load golden dataset if specified
        expected_answers = None
        expected_contexts_list = None

        if golden_dataset_name:
            try:
                golden_dataset = await golden_dataset_manager.load_dataset(golden_dataset_name)
                if golden_dataset:
                    # Match queries with golden dataset
                    golden_map = {point.query: point for point in golden_dataset.data_points}
                    expected_answers = []
                    expected_contexts_list = []

                    for query in queries:
                        if query in golden_map:
                            expected_answers.append(golden_map[query].expected_answer)
                            expected_contexts_list.append(golden_map[query].expected_contexts)
                        else:
                            expected_answers.append(None)
                            expected_contexts_list.append(None)

            except Exception as e:
                logger.warning(f"Failed to load golden dataset '{golden_dataset_name}': {str(e)}")

        # Process queries in batches
        rag_responses = []
        batch_size = 5  # Process 5 queries at a time

        for i in range(0, len(queries), batch_size):
            batch_queries = queries[i:i + batch_size]

            # Execute searches for this batch
            batch_responses = []
            for query in batch_queries:
                try:
                    search_results = await search_dao.hybrid_search(
                        query=query,
                        limit=10,
                        hybrid_alpha=0.7
                    )

                    rag_response = RAGResponse(
                        answer=search_results.get('generated_answer', 'No answer generated'),
                        retrieved_docs=[
                            {
                                'text': doc.get('content', ''),
                                'title': doc.get('title', ''),
                                'taxonomy_path': doc.get('taxonomy_path', []),
                                'score': doc.get('score', 0.0)
                            }
                            for doc in search_results.get('documents', [])
                        ],
                        confidence=search_results.get('confidence', 0.0),
                        metadata={'search_type': 'hybrid'}
                    )

                    batch_responses.append(rag_response)
                    batch_data["completed_queries"] += 1

                except Exception as e:
                    logger.error(f"Search failed for query '{query}': {str(e)}")
                    # Add empty response for failed queries
                    batch_responses.append(RAGResponse(answer="", retrieved_docs=[]))
                    batch_data["completed_queries"] += 1

            rag_responses.extend(batch_responses)

            # Small delay between batches
            await asyncio.sleep(0.1)

        # Run comprehensive evaluation
        evaluation_result = await ragas_engine.evaluate_rag_system(
            test_queries=queries,
            rag_responses=rag_responses,
            ground_truths=expected_answers,
            expected_contexts=expected_contexts_list
        )

        # Update batch status
        batch_data.update({
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "overall_metrics": evaluation_result.metrics,
            "quality_gates_passed": evaluation_result.quality_gates_passed,
            "results": [
                {
                    "query": q,
                    "answer": r.answer,
                    "confidence": r.confidence
                }
                for q, r in zip(queries, rag_responses)
            ]
        })

        # Record metrics
        await metrics_collector.record_evaluation_metrics(evaluation_result.metrics)

        logger.info(f"Batch evaluation {batch_id} completed successfully")

    except Exception as e:
        logger.error(f"Batch evaluation {batch_id} failed: {str(e)}")
        batch_evaluations[batch_id].update({
            "status": "failed",
            "completed_at": datetime.utcnow(),
            "error": str(e)
        })