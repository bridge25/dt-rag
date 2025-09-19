"""
RAG Evaluation API

FastAPI-based REST API for RAG evaluation framework:
- RAGAS evaluation endpoints
- Golden dataset management
- A/B testing coordination
- Evaluation orchestration
- Real-time monitoring and reporting
- Integration with existing dt-rag system
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
import uvicorn

# Import evaluation components
from ..core.ragas_engine import RAGASEvaluationEngine, RAGResponse, EvaluationResult
from ..core.golden_dataset import GoldenDatasetManager, GoldenDataPoint, ValidationResult
from ..core.ab_testing import (
    ABTestingFramework, ExperimentDesign, ExperimentMetric,
    ExperimentVariant, MetricType, ExperimentType
)
from ..orchestrator.evaluation_orchestrator import (
    EvaluationOrchestrator, EvaluationTrigger, QualityGate, AlertRule
)

# Import existing dt-rag components
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

try:
    from apps.orchestration.src.langgraph_pipeline import get_pipeline, PipelineRequest
    from apps.api.database import db_manager
    RAG_PIPELINE_AVAILABLE = True
except ImportError:
    RAG_PIPELINE_AVAILABLE = False
    logging.warning("RAG pipeline not available for evaluation")

logger = logging.getLogger(__name__)

# Pydantic models for API
class EvaluationRequest(BaseModel):
    name: str = Field(..., description="Evaluation name")
    description: str = Field(..., description="Evaluation description")
    golden_dataset_id: str = Field(..., description="Golden dataset ID")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Additional configuration")

class GoldenDatasetCreateRequest(BaseModel):
    name: str = Field(..., description="Dataset name")
    description: str = Field(..., description="Dataset description")
    data_points: List[Dict[str, Any]] = Field(..., description="Raw data points")
    version: str = Field(default="1.0", description="Dataset version")

class ABTestRequest(BaseModel):
    name: str = Field(..., description="Experiment name")
    description: str = Field(..., description="Experiment description")
    primary_metric: Dict[str, Any] = Field(..., description="Primary metric configuration")
    variants: List[Dict[str, Any]] = Field(..., description="Experiment variants")
    secondary_metrics: Optional[List[Dict[str, Any]]] = Field(default=None, description="Secondary metrics")
    significance_level: float = Field(default=0.05, description="Statistical significance level")
    statistical_power: float = Field(default=0.8, description="Desired statistical power")

class ObservationRequest(BaseModel):
    experiment_id: str = Field(..., description="Experiment ID")
    variant_id: str = Field(..., description="Variant ID")
    user_id: str = Field(..., description="User/randomization unit ID")
    metric_values: Dict[str, Any] = Field(..., description="Metric values")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

# Initialize evaluation framework
ragas_engine = RAGASEvaluationEngine()
golden_dataset_manager = GoldenDatasetManager()
ab_testing_framework = ABTestingFramework()
evaluation_orchestrator = EvaluationOrchestrator(
    ragas_engine=ragas_engine,
    golden_dataset_manager=golden_dataset_manager,
    ab_testing_framework=ab_testing_framework
)

# FastAPI app
app = FastAPI(
    title="RAG Evaluation API",
    description="Comprehensive evaluation framework for RAG systems",
    version="1.8.1"
)

# RAG System Integration
async def get_rag_response(query: str) -> RAGResponse:
    """Get response from the dt-rag system"""

    if not RAG_PIPELINE_AVAILABLE:
        # Return mock response for testing
        return RAGResponse(
            answer=f"Mock answer for: {query}",
            retrieved_docs=[
                {
                    "chunk_id": "mock_chunk_1",
                    "text": f"Mock retrieved content for query: {query}",
                    "score": 0.8,
                    "source": {"title": "Mock Document", "url": "https://example.com"}
                }
            ],
            confidence=0.75,
            metadata={"mock": True}
        )

    try:
        # Use actual dt-rag pipeline
        pipeline = get_pipeline()
        request = PipelineRequest(query=query)
        response = await pipeline.execute(request)

        # Convert pipeline response to RAGResponse
        retrieved_docs = []
        for source in response.sources:
            retrieved_docs.append({
                "chunk_id": source.get("chunk_id", "unknown"),
                "text": source.get("text_snippet", ""),
                "score": source.get("relevance_score", 0.0),
                "source": {
                    "title": source.get("title", "Unknown"),
                    "url": source.get("url", "")
                }
            })

        return RAGResponse(
            answer=response.answer,
            retrieved_docs=retrieved_docs,
            confidence=response.confidence,
            metadata={
                "taxonomy_version": response.taxonomy_version,
                "cost": response.cost,
                "latency": response.latency,
                "intent": response.intent
            }
        )

    except Exception as e:
        logger.error(f"RAG pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG system error: {str(e)}")

# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize evaluation framework on startup"""
    logger.info("Starting RAG Evaluation API...")

    # Start evaluation orchestrator
    await evaluation_orchestrator.start_scheduler()

    # Initialize database if available
    if RAG_PIPELINE_AVAILABLE:
        try:
            await db_manager.test_connection()
            logger.info("Database connection verified")
        except Exception as e:
            logger.warning(f"Database connection failed: {str(e)}")

    logger.info("RAG Evaluation API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down RAG Evaluation API...")
    await evaluation_orchestrator.stop_scheduler()
    logger.info("RAG Evaluation API shutdown complete")

# Health and Status Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.8.1",
        "rag_pipeline_available": RAG_PIPELINE_AVAILABLE
    }

@app.get("/status")
async def get_status():
    """Get comprehensive system status"""

    # Get orchestrator metrics
    orchestrator_metrics = evaluation_orchestrator.get_metrics()

    # Get RAGAS engine summary
    ragas_summary = ragas_engine.get_evaluation_summary()

    # Get AB testing summary
    ab_testing_summary = ab_testing_framework.get_experiment_summary()

    # Get golden dataset info
    datasets = await golden_dataset_manager.list_datasets()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "orchestrator": orchestrator_metrics,
        "ragas_engine": ragas_summary,
        "ab_testing": ab_testing_summary,
        "golden_datasets": {
            "total_datasets": len(datasets),
            "datasets": datasets[:5]  # Show first 5
        },
        "rag_pipeline_available": RAG_PIPELINE_AVAILABLE
    }

# RAGAS Evaluation Endpoints

@app.post("/evaluate")
async def run_evaluation(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks
):
    """Run RAGAS evaluation on golden dataset"""

    try:
        # Schedule evaluation
        job_id = await evaluation_orchestrator.schedule_evaluation(
            name=request.name,
            description=request.description,
            golden_dataset_id=request.golden_dataset_id,
            trigger=EvaluationTrigger.MANUAL,
            evaluation_config=request.config
        )

        return {
            "job_id": job_id,
            "message": "Evaluation scheduled successfully",
            "status": "pending"
        }

    except Exception as e:
        logger.error(f"Evaluation scheduling failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate/immediate")
async def run_immediate_evaluation(request: EvaluationRequest):
    """Run immediate RAGAS evaluation and return results"""

    try:
        result = await evaluation_orchestrator.run_evaluation_now(
            name=request.name,
            description=request.description,
            golden_dataset_id=request.golden_dataset_id,
            rag_system_callable=get_rag_response,
            evaluation_config=request.config
        )

        return {
            "metrics": result.metrics,
            "analysis": result.analysis,
            "quality_gates_passed": result.quality_gates_passed,
            "recommendations": result.recommendations,
            "timestamp": result.timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Immediate evaluation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/evaluate/{job_id}")
async def get_evaluation_result(job_id: str):
    """Get evaluation job status and results"""

    try:
        status = await evaluation_orchestrator.get_job_status(job_id)
        return status

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get evaluation status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/evaluate")
async def list_evaluations(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of results")
):
    """List evaluation jobs"""

    try:
        # Convert status string to enum if provided
        status_filter = None
        if status:
            from ..orchestrator.evaluation_orchestrator import EvaluationStatus
            try:
                status_filter = EvaluationStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        jobs = await evaluation_orchestrator.list_jobs(status_filter, limit)
        return {"jobs": jobs}

    except Exception as e:
        logger.error(f"Failed to list evaluations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Golden Dataset Endpoints

@app.post("/datasets")
async def create_golden_dataset(request: GoldenDatasetCreateRequest):
    """Create a new golden dataset"""

    try:
        dataset = await golden_dataset_manager.create_golden_dataset(
            name=request.name,
            description=request.description,
            raw_data=request.data_points,
            version=request.version
        )

        # Get statistics
        stats = golden_dataset_manager.get_dataset_statistics(dataset)

        return {
            "dataset_id": dataset.id,
            "name": dataset.name,
            "version": dataset.version,
            "data_points": len(dataset.data_points),
            "quality_metrics": dataset.quality_metrics,
            "statistics": {
                "total_size": stats.total_size,
                "validated_count": stats.validated_count,
                "domain_distribution": stats.domain_distribution,
                "difficulty_distribution": stats.difficulty_distribution,
                "avg_query_length": stats.avg_query_length,
                "avg_answer_length": stats.avg_answer_length
            }
        }

    except Exception as e:
        logger.error(f"Dataset creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/datasets")
async def list_golden_datasets():
    """List all golden datasets"""

    try:
        datasets = await golden_dataset_manager.list_datasets()
        return {"datasets": datasets}

    except Exception as e:
        logger.error(f"Failed to list datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/datasets/{dataset_id}")
async def get_golden_dataset(dataset_id: str):
    """Get golden dataset details"""

    try:
        dataset = await golden_dataset_manager.load_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        stats = golden_dataset_manager.get_dataset_statistics(dataset)

        return {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "version": dataset.version,
            "created_at": dataset.created_at.isoformat(),
            "data_points_count": len(dataset.data_points),
            "quality_metrics": dataset.quality_metrics,
            "statistics": {
                "total_size": stats.total_size,
                "validated_count": stats.validated_count,
                "domain_distribution": stats.domain_distribution,
                "difficulty_distribution": stats.difficulty_distribution,
                "taxonomy_distribution": stats.taxonomy_distribution,
                "quality_distribution": stats.quality_distribution,
                "avg_query_length": stats.avg_query_length,
                "avg_answer_length": stats.avg_answer_length
            }
        }

    except Exception as e:
        logger.error(f"Failed to get dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/datasets/{dataset_id}/validate")
async def validate_golden_dataset(dataset_id: str):
    """Validate a golden dataset"""

    try:
        dataset = await golden_dataset_manager.load_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        validation_result = await golden_dataset_manager.validate_dataset(dataset)

        return {
            "dataset_id": dataset_id,
            "is_valid": validation_result.is_valid,
            "quality_score": validation_result.quality_score,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
            "recommendations": validation_result.recommendations
        }

    except Exception as e:
        logger.error(f"Dataset validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/datasets/{dataset_id}/split")
async def split_golden_dataset(
    dataset_id: str,
    train_ratio: float = Query(0.7, description="Training set ratio"),
    val_ratio: float = Query(0.15, description="Validation set ratio"),
    test_ratio: float = Query(0.15, description="Test set ratio")
):
    """Split golden dataset into train/validation/test sets"""

    try:
        dataset = await golden_dataset_manager.load_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        train_dataset, val_dataset, test_dataset = golden_dataset_manager.split_dataset(
            dataset, train_ratio, val_ratio, test_ratio
        )

        # Save split datasets
        await golden_dataset_manager.save_dataset(train_dataset)
        await golden_dataset_manager.save_dataset(val_dataset)
        await golden_dataset_manager.save_dataset(test_dataset)

        return {
            "original_dataset_id": dataset_id,
            "splits": {
                "train": {
                    "dataset_id": train_dataset.id,
                    "size": len(train_dataset.data_points)
                },
                "validation": {
                    "dataset_id": val_dataset.id,
                    "size": len(val_dataset.data_points)
                },
                "test": {
                    "dataset_id": test_dataset.id,
                    "size": len(test_dataset.data_points)
                }
            }
        }

    except Exception as e:
        logger.error(f"Dataset splitting failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# A/B Testing Endpoints

@app.post("/experiments")
async def create_ab_test(request: ABTestRequest):
    """Create a new A/B test experiment"""

    try:
        # Convert request to internal format
        primary_metric = ExperimentMetric(
            name=request.primary_metric["name"],
            type=MetricType(request.primary_metric["type"]),
            description=request.primary_metric["description"],
            higher_is_better=request.primary_metric.get("higher_is_better", True),
            minimum_detectable_effect=request.primary_metric.get("minimum_detectable_effect", 0.05),
            baseline_value=request.primary_metric.get("baseline_value")
        )

        variants = []
        for variant_data in request.variants:
            variant = ExperimentVariant(
                id=variant_data["id"],
                name=variant_data["name"],
                description=variant_data["description"],
                traffic_allocation=variant_data["traffic_allocation"],
                config=variant_data.get("config", {}),
                metadata=variant_data.get("metadata", {})
            )
            variants.append(variant)

        secondary_metrics = []
        if request.secondary_metrics:
            for metric_data in request.secondary_metrics:
                metric = ExperimentMetric(
                    name=metric_data["name"],
                    type=MetricType(metric_data["type"]),
                    description=metric_data["description"],
                    higher_is_better=metric_data.get("higher_is_better", True),
                    minimum_detectable_effect=metric_data.get("minimum_detectable_effect", 0.05)
                )
                secondary_metrics.append(metric)

        # Design experiment
        design = await ab_testing_framework.design_experiment(
            name=request.name,
            description=request.description,
            primary_metric=primary_metric,
            variants=variants,
            secondary_metrics=secondary_metrics,
            significance_level=request.significance_level,
            statistical_power=request.statistical_power
        )

        return {
            "experiment_id": design.experiment_id,
            "name": design.name,
            "target_sample_size": design.target_sample_size,
            "expected_duration_days": design.expected_duration_days,
            "variants": [
                {
                    "id": v.id,
                    "name": v.name,
                    "traffic_allocation": v.traffic_allocation
                } for v in design.variants
            ]
        }

    except Exception as e:
        logger.error(f"A/B test creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/experiments/{experiment_id}/observations")
async def record_observation(experiment_id: str, request: ObservationRequest):
    """Record an observation for an A/B test"""

    try:
        await ab_testing_framework.record_observation(
            experiment_id=experiment_id,
            variant_id=request.variant_id,
            randomization_unit_id=request.user_id,
            metric_values=request.metric_values,
            metadata=request.metadata
        )

        return {"message": "Observation recorded successfully"}

    except Exception as e:
        logger.error(f"Observation recording failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/experiments/{experiment_id}/analyze")
async def analyze_ab_test(experiment_id: str, interim: bool = Query(False, description="Interim analysis")):
    """Analyze A/B test results"""

    try:
        result = await ab_testing_framework.analyze_experiment(experiment_id, interim_analysis=interim)

        return {
            "experiment_id": result.experiment_id,
            "overall_recommendation": result.overall_recommendation,
            "winning_variant": result.winning_variant,
            "confidence_level": result.confidence_level,
            "sample_sizes": result.sample_sizes,
            "effect_sizes": result.effect_sizes,
            "business_impact": result.business_impact,
            "variant_comparisons": {
                comparison_key: {
                    "primary_metric": {
                        "test_name": results["primary"].test_name,
                        "p_value": results["primary"].p_value,
                        "effect_size": results["primary"].effect_size,
                        "is_significant": results["primary"].is_significant,
                        "interpretation": results["primary"].interpretation
                    },
                    "secondary_metrics": {
                        metric_name: {
                            "test_name": metric_result.test_name,
                            "p_value": metric_result.p_value,
                            "effect_size": metric_result.effect_size,
                            "is_significant": metric_result.is_significant
                        }
                        for metric_name, metric_result in results["secondary"].items()
                    }
                }
                for comparison_key, results in result.variant_comparisons.items()
            },
            "timestamp": result.timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"A/B test analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/experiments/{experiment_id}/status")
async def get_ab_test_status(experiment_id: str):
    """Get A/B test experiment status"""

    try:
        status = await ab_testing_framework.get_experiment_status(experiment_id)
        return status

    except Exception as e:
        logger.error(f"Failed to get experiment status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/experiments")
async def list_ab_tests():
    """List all A/B test experiments"""

    try:
        summary = ab_testing_framework.get_experiment_summary()
        return summary

    except Exception as e:
        logger.error(f"Failed to list experiments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Reporting Endpoints

@app.get("/reports/evaluation/{job_id}")
async def get_evaluation_report(
    job_id: str,
    format: str = Query("json", description="Report format: json, markdown, html")
):
    """Get detailed evaluation report"""

    try:
        if format == "json":
            status = await evaluation_orchestrator.get_job_status(job_id)
            return status
        else:
            report_content = await evaluation_orchestrator.create_evaluation_report([job_id], format)
            if format == "markdown":
                return PlainTextResponse(content=report_content, media_type="text/markdown")
            elif format == "html":
                return PlainTextResponse(content=report_content, media_type="text/html")
            else:
                raise HTTPException(status_code=400, detail="Unsupported format")

    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reports/multi-evaluation")
async def create_multi_evaluation_report(
    job_ids: List[str],
    format: str = Query("markdown", description="Report format")
):
    """Create report comparing multiple evaluations"""

    try:
        report_content = await evaluation_orchestrator.create_evaluation_report(job_ids, format)

        if format == "markdown":
            return PlainTextResponse(content=report_content, media_type="text/markdown")
        elif format == "html":
            return PlainTextResponse(content=report_content, media_type="text/html")
        elif format == "json":
            return JSONResponse(content={"report": report_content})
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")

    except Exception as e:
        logger.error(f"Multi-evaluation report failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration Endpoints

@app.get("/config/quality-gates")
async def get_quality_gates():
    """Get current quality gate configuration"""

    gates = [
        {
            "name": gate.name,
            "metric_name": gate.metric_name,
            "threshold": gate.threshold,
            "operator": gate.operator,
            "severity": gate.severity,
            "enabled": gate.enabled
        }
        for gate in evaluation_orchestrator.quality_gates
    ]

    return {"quality_gates": gates}

@app.post("/config/quality-gates")
async def update_quality_gates(gates: List[Dict[str, Any]]):
    """Update quality gate configuration"""

    try:
        new_gates = []
        for gate_data in gates:
            gate = QualityGate(
                name=gate_data["name"],
                metric_name=gate_data["metric_name"],
                threshold=gate_data["threshold"],
                operator=gate_data["operator"],
                severity=gate_data["severity"],
                enabled=gate_data.get("enabled", True)
            )
            new_gates.append(gate)

        evaluation_orchestrator.quality_gates = new_gates

        return {"message": "Quality gates updated successfully"}

    except Exception as e:
        logger.error(f"Quality gate update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Testing and Debug Endpoints

@app.post("/test/rag-response")
async def test_rag_response(query: str):
    """Test RAG system response (for debugging)"""

    try:
        response = await get_rag_response(query)

        return {
            "query": query,
            "answer": response.answer,
            "retrieved_docs_count": len(response.retrieved_docs),
            "confidence": response.confidence,
            "metadata": response.metadata,
            "retrieved_docs": response.retrieved_docs
        }

    except Exception as e:
        logger.error(f"RAG response test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test/sample-evaluation")
async def run_sample_evaluation():
    """Run a sample evaluation with mock data (for testing)"""

    try:
        # Create sample golden dataset
        sample_data = [
            {
                "query": "What is RAG?",
                "expected_answer": "RAG stands for Retrieval-Augmented Generation, a technique that combines information retrieval with language generation.",
                "expected_contexts": ["RAG combines retrieval and generation"],
                "taxonomy_path": ["AI", "RAG"],
                "difficulty_level": "easy",
                "domain": "ai_technology"
            },
            {
                "query": "How does vector search work?",
                "expected_answer": "Vector search works by converting text into numerical vectors and finding similar vectors using distance metrics.",
                "expected_contexts": ["Vector search uses embeddings"],
                "taxonomy_path": ["AI", "Vector Search"],
                "difficulty_level": "medium",
                "domain": "ai_technology"
            }
        ]

        # Create dataset
        dataset = await golden_dataset_manager.create_golden_dataset(
            name="Sample Test Dataset",
            description="Test dataset for API validation",
            raw_data=sample_data,
            version="test-1.0"
        )

        # Run evaluation
        result = await evaluation_orchestrator.run_evaluation_now(
            name="Sample Evaluation Test",
            description="Test evaluation using sample data",
            golden_dataset_id=dataset.id,
            rag_system_callable=get_rag_response
        )

        return {
            "dataset_id": dataset.id,
            "evaluation_result": {
                "metrics": result.metrics,
                "quality_gates_passed": result.quality_gates_passed,
                "overall_score": result.analysis.get("overall_score", 0.0),
                "recommendations": result.recommendations
            }
        }

    except Exception as e:
        logger.error(f"Sample evaluation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Run the API server
if __name__ == "__main__":
    uvicorn.run(
        "evaluation_api:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )