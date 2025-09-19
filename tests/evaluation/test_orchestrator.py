"""
Test suite for evaluation orchestrator
"""
import pytest
import asyncio
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'evaluation'))

from orchestrator.evaluation_orchestrator import (
    EvaluationOrchestrator,
    EvaluationJob,
    EvaluationTrigger,
    JobStatus,
    QualityGate,
    AlertRule
)


class TestEvaluationOrchestrator:
    """Test cases for evaluation orchestrator"""

    @pytest.fixture
    def orchestrator(self):
        """Create evaluation orchestrator instance"""
        return EvaluationOrchestrator()

    @pytest.fixture
    def sample_quality_gates(self):
        """Sample quality gates"""
        return [
            QualityGate(
                name="Faithfulness Gate",
                metric_name="faithfulness",
                threshold=0.85,
                operator="gte",
                severity="critical"
            ),
            QualityGate(
                name="Answer Relevancy Gate",
                metric_name="answer_relevancy",
                threshold=0.80,
                operator="gte",
                severity="warning"
            )
        ]

    @pytest.fixture
    def sample_alert_rules(self):
        """Sample alert rules"""
        return [
            AlertRule(
                name="Quality Degradation",
                condition="metrics.get('faithfulness', 1.0) < 0.8",
                severity="critical",
                channels=["email", "slack"]
            ),
            AlertRule(
                name="High Failure Rate",
                condition="failed_jobs / max(total_jobs, 1) > 0.2",
                severity="warning",
                channels=["slack"]
            )
        ]

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization"""

        await orchestrator.initialize()

        assert orchestrator.is_initialized is True
        assert orchestrator.scheduler is not None
        assert orchestrator.job_queue is not None

    @pytest.mark.asyncio
    async def test_schedule_evaluation(self, orchestrator, sample_quality_gates):
        """Test evaluation scheduling"""

        orchestrator.quality_gates = sample_quality_gates
        await orchestrator.initialize()

        job_id = await orchestrator.schedule_evaluation(
            name="Test Evaluation",
            description="Test evaluation scheduling",
            golden_dataset_id="test_dataset_001",
            trigger=EvaluationTrigger.MANUAL
        )

        assert job_id is not None
        assert len(job_id) > 0

        # Verify job was created
        job_status = await orchestrator.get_job_status(job_id)
        assert job_status["status"] == JobStatus.PENDING
        assert job_status["name"] == "Test Evaluation"

    @pytest.mark.asyncio
    async def test_run_evaluation_now(self, orchestrator, sample_quality_gates):
        """Test immediate evaluation execution"""

        orchestrator.quality_gates = sample_quality_gates

        # Mock RAG system callable
        async def mock_rag_system(query: str):
            from core.ragas_engine import RAGResponse
            return RAGResponse(
                answer=f"Mock answer for: {query}",
                retrieved_docs=[{"content": "mock context", "score": 0.8}],
                confidence=0.85,
                processing_time=0.5
            )

        with patch('orchestrator.evaluation_orchestrator.EvaluationOrchestrator._load_golden_dataset') as mock_load:
            # Mock golden dataset
            mock_load.return_value = Mock(
                data_points=[
                    Mock(query="What is AI?", expected_answer="AI is..."),
                    Mock(query="How does ML work?", expected_answer="ML works by...")
                ]
            )

            with patch('core.ragas_engine.RAGASEvaluationEngine.evaluate_rag_system') as mock_evaluate:
                # Mock evaluation result
                mock_evaluate.return_value = Mock(
                    metrics={"faithfulness": 0.87, "answer_relevancy": 0.83},
                    quality_gates_passed=True,
                    analysis={"overall_score": 0.85}
                )

                result = await orchestrator.run_evaluation_now(
                    name="Immediate Test",
                    description="Test immediate execution",
                    golden_dataset_id="test_dataset_001",
                    rag_system_callable=mock_rag_system
                )

                assert result is not None
                assert result.metrics["faithfulness"] >= 0.85
                assert result.quality_gates_passed is True

    @pytest.mark.asyncio
    async def test_quality_gates_enforcement(self, orchestrator, sample_quality_gates):
        """Test quality gates enforcement"""

        orchestrator.quality_gates = sample_quality_gates

        # Test passing quality gates
        passing_metrics = {
            "faithfulness": 0.90,
            "answer_relevancy": 0.85,
            "context_precision": 0.80
        }

        gates_result = await orchestrator.check_quality_gates(passing_metrics)
        assert gates_result.passed is True
        assert len(gates_result.failed_gates) == 0

        # Test failing quality gates
        failing_metrics = {
            "faithfulness": 0.75,  # Below threshold
            "answer_relevancy": 0.82,
            "context_precision": 0.70
        }

        gates_result = await orchestrator.check_quality_gates(failing_metrics)
        assert gates_result.passed is False
        assert len(gates_result.failed_gates) > 0
        assert any(gate.metric_name == "faithfulness" for gate in gates_result.failed_gates)

    @pytest.mark.asyncio
    async def test_continuous_evaluation_setup(self, orchestrator):
        """Test continuous evaluation setup"""

        schedule_id = await orchestrator.setup_continuous_evaluation(
            golden_dataset_id="continuous_dataset",
            schedule_interval_hours=24,
            performance_thresholds={
                "faithfulness": 0.85,
                "answer_relevancy": 0.80
            }
        )

        assert schedule_id is not None

        # Verify schedule was created
        schedules = await orchestrator.list_continuous_evaluations()
        assert len(schedules) > 0
        assert any(schedule["id"] == schedule_id for schedule in schedules)

    @pytest.mark.asyncio
    async def test_job_retry_mechanism(self, orchestrator):
        """Test job retry mechanism for failed evaluations"""

        # Mock a failing evaluation
        async def failing_rag_system(query: str):
            raise Exception("Simulated failure")

        with patch('orchestrator.evaluation_orchestrator.EvaluationOrchestrator._load_golden_dataset') as mock_load:
            mock_load.return_value = Mock(
                data_points=[Mock(query="Test query", expected_answer="Test answer")]
            )

            job_id = await orchestrator.schedule_evaluation(
                name="Retry Test",
                description="Test retry mechanism",
                golden_dataset_id="test_dataset_001"
            )

            # Manually trigger job execution with failing system
            job = await orchestrator._get_job(job_id)
            job.rag_system_callable = failing_rag_system

            # Execute job (should fail and retry)
            await orchestrator._execute_job(job)

            # Check that retries were attempted
            final_status = await orchestrator.get_job_status(job_id)
            assert final_status["retry_count"] > 0

    @pytest.mark.asyncio
    async def test_alert_system(self, orchestrator, sample_alert_rules):
        """Test alert system functionality"""

        orchestrator.alert_rules = sample_alert_rules

        # Test quality degradation alert
        metrics = {"faithfulness": 0.75}  # Below threshold
        job_stats = {"failed_jobs": 1, "total_jobs": 10}

        alerts = await orchestrator.check_alert_conditions(metrics, job_stats)

        assert len(alerts) > 0
        assert any(alert.rule_name == "Quality Degradation" for alert in alerts)

        # Test high failure rate alert
        high_failure_stats = {"failed_jobs": 3, "total_jobs": 10}
        alerts = await orchestrator.check_alert_conditions({}, high_failure_stats)

        assert any(alert.rule_name == "High Failure Rate" for alert in alerts)

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, orchestrator):
        """Test performance monitoring and metrics collection"""

        await orchestrator.initialize()

        # Simulate some job history
        for i in range(5):
            job_id = await orchestrator.schedule_evaluation(
                name=f"Perf Test {i}",
                description="Performance monitoring test",
                golden_dataset_id="perf_dataset"
            )

            # Mock job completion
            job = await orchestrator._get_job(job_id)
            job.status = JobStatus.COMPLETED
            job.execution_time = 30.0 + i * 5  # Varying execution times
            job.end_time = datetime.utcnow()

        # Get performance metrics
        metrics = await orchestrator.get_performance_metrics()

        assert "success_rate" in metrics
        assert "average_execution_time" in metrics
        assert "jobs_per_hour" in metrics
        assert "queue_length" in metrics

        assert 0 <= metrics["success_rate"] <= 1.0
        assert metrics["average_execution_time"] > 0

    @pytest.mark.asyncio
    async def test_scheduler_management(self, orchestrator):
        """Test scheduler start/stop functionality"""

        await orchestrator.start_scheduler()
        assert orchestrator.scheduler_running is True

        await orchestrator.stop_scheduler()
        assert orchestrator.scheduler_running is False

    @pytest.mark.asyncio
    async def test_job_cleanup(self, orchestrator):
        """Test automatic cleanup of completed jobs"""

        await orchestrator.initialize()

        # Create old completed jobs
        old_job_id = await orchestrator.schedule_evaluation(
            name="Old Job",
            description="Job for cleanup testing",
            golden_dataset_id="cleanup_dataset"
        )

        # Mock job as old and completed
        job = await orchestrator._get_job(old_job_id)
        job.status = JobStatus.COMPLETED
        job.end_time = datetime.utcnow() - timedelta(hours=25)  # 25 hours ago

        # Run cleanup
        cleaned_count = await orchestrator.cleanup_completed_jobs(max_age_hours=24)

        assert cleaned_count > 0

        # Verify job was cleaned up
        with pytest.raises(Exception):
            await orchestrator.get_job_status(old_job_id)

    @pytest.mark.asyncio
    async def test_evaluation_reports(self, orchestrator):
        """Test evaluation report generation"""

        # Mock some evaluation history
        evaluation_results = [
            {
                "timestamp": datetime.utcnow() - timedelta(days=1),
                "metrics": {"faithfulness": 0.85, "answer_relevancy": 0.80},
                "quality_gates_passed": True
            },
            {
                "timestamp": datetime.utcnow() - timedelta(hours=12),
                "metrics": {"faithfulness": 0.87, "answer_relevancy": 0.82},
                "quality_gates_passed": True
            },
            {
                "timestamp": datetime.utcnow(),
                "metrics": {"faithfulness": 0.89, "answer_relevancy": 0.85},
                "quality_gates_passed": True
            }
        ]

        report = await orchestrator.generate_evaluation_report(
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
            evaluation_results=evaluation_results
        )

        assert "summary" in report
        assert "trends" in report
        assert "quality_gates_summary" in report
        assert "recommendations" in report

        # Check trend analysis
        assert report["trends"]["faithfulness"]["direction"] in ["improving", "stable", "declining"]

    @pytest.mark.asyncio
    async def test_concurrent_job_execution(self, orchestrator):
        """Test concurrent job execution limits"""

        orchestrator.max_concurrent_jobs = 2
        await orchestrator.initialize()

        # Schedule multiple jobs
        job_ids = []
        for i in range(5):
            job_id = await orchestrator.schedule_evaluation(
                name=f"Concurrent Test {i}",
                description="Test concurrent execution",
                golden_dataset_id="concurrent_dataset"
            )
            job_ids.append(job_id)

        # Check that only max_concurrent_jobs are running
        running_jobs = await orchestrator.get_running_jobs()
        assert len(running_jobs) <= orchestrator.max_concurrent_jobs

    @pytest.mark.asyncio
    async def test_integration_with_dt_rag_pipeline(self, orchestrator):
        """Test integration with existing dt-rag pipeline"""

        # Mock LangGraph pipeline integration
        with patch('apps.orchestration.src.langgraph_pipeline.get_pipeline') as mock_get_pipeline:
            mock_pipeline = Mock()
            mock_pipeline.execute = AsyncMock(return_value=Mock(
                answer="Mock pipeline answer",
                sources=[{"content": "mock source", "score": 0.8}],
                confidence=0.85
            ))
            mock_get_pipeline.return_value = mock_pipeline

            # Test pipeline integration
            pipeline_callable = await orchestrator.create_pipeline_callable()

            from core.ragas_engine import RAGResponse
            response = await pipeline_callable("Test query")

            assert isinstance(response, RAGResponse)
            assert response.answer == "Mock pipeline answer"
            assert len(response.retrieved_docs) > 0

    def test_job_status_enum(self):
        """Test job status enumeration"""

        assert JobStatus.PENDING == "pending"
        assert JobStatus.RUNNING == "running"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.FAILED == "failed"
        assert JobStatus.CANCELLED == "cancelled"

    def test_evaluation_trigger_enum(self):
        """Test evaluation trigger enumeration"""

        assert EvaluationTrigger.MANUAL == "manual"
        assert EvaluationTrigger.SCHEDULED == "scheduled"
        assert EvaluationTrigger.WEBHOOK == "webhook"
        assert EvaluationTrigger.PERFORMANCE_DEGRADATION == "performance_degradation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])