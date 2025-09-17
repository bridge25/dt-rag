"""
Integration tests for the complete evaluation framework
"""
import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'evaluation'))

from core.ragas_engine import RAGASEvaluationEngine, RAGResponse
from core.golden_dataset import GoldenDatasetManager
from core.ab_testing import ABTestingFramework, ExperimentMetric, ExperimentVariant, MetricType
from orchestrator.evaluation_orchestrator import EvaluationOrchestrator


class TestEvaluationFrameworkIntegration:
    """Integration tests for the complete evaluation framework"""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def sample_evaluation_data(self):
        """Sample data for integration testing"""
        return [
            {
                "query": "What is retrieval-augmented generation?",
                "expected_answer": "RAG combines information retrieval with text generation to provide more accurate and contextual responses.",
                "expected_contexts": [
                    "RAG is a technique that retrieves relevant information from a knowledge base",
                    "The retrieved information is then used to augment the generation process"
                ],
                "taxonomy_path": ["AI", "NLP", "RAG"],
                "difficulty_level": "intermediate",
                "domain": "ai_technology"
            },
            {
                "query": "How does vector search work in RAG systems?",
                "expected_answer": "Vector search converts text into embeddings and finds semantically similar content using similarity metrics.",
                "expected_contexts": [
                    "Vector embeddings represent text in high-dimensional space",
                    "Similarity search uses cosine similarity or dot product"
                ],
                "taxonomy_path": ["AI", "NLP", "RAG", "Vector Search"],
                "difficulty_level": "advanced",
                "domain": "ai_technology"
            },
            {
                "query": "What are the benefits of using RAG over traditional language models?",
                "expected_answer": "RAG provides up-to-date information, reduces hallucination, and allows for domain-specific knowledge integration.",
                "expected_contexts": [
                    "RAG can access external knowledge sources",
                    "Traditional LMs are limited to training data"
                ],
                "taxonomy_path": ["AI", "NLP", "RAG"],
                "difficulty_level": "intermediate",
                "domain": "ai_technology"
            }
        ]

    @pytest.mark.asyncio
    async def test_end_to_end_evaluation_workflow(self, temp_storage, sample_evaluation_data):
        """Test complete end-to-end evaluation workflow"""

        # Initialize components
        dataset_manager = GoldenDatasetManager()
        dataset_manager.storage_path = temp_storage

        evaluation_engine = RAGASEvaluationEngine()
        orchestrator = EvaluationOrchestrator()
        orchestrator.storage_path = temp_storage

        # 1. Create golden dataset
        dataset = await dataset_manager.create_golden_dataset(
            name="Integration Test Dataset",
            description="Dataset for integration testing",
            raw_data=sample_evaluation_data,
            version="1.0"
        )

        assert dataset.quality_score >= 0.8
        assert len(dataset.data_points) == 3

        # 2. Store dataset
        await dataset_manager.store_dataset(dataset)

        # 3. Create mock RAG system
        async def mock_rag_system(query: str) -> RAGResponse:
            if "retrieval-augmented" in query.lower():
                return RAGResponse(
                    answer="RAG combines retrieval and generation for better responses.",
                    retrieved_docs=[
                        {"content": "RAG retrieves relevant documents", "score": 0.9},
                        {"content": "Generation is enhanced with retrieved context", "score": 0.8}
                    ],
                    confidence=0.87,
                    processing_time=1.2
                )
            elif "vector search" in query.lower():
                return RAGResponse(
                    answer="Vector search uses embeddings to find similar content.",
                    retrieved_docs=[
                        {"content": "Embeddings represent text numerically", "score": 0.85},
                        {"content": "Similarity metrics compare vectors", "score": 0.82}
                    ],
                    confidence=0.84,
                    processing_time=1.5
                )
            else:
                return RAGResponse(
                    answer="RAG offers advantages over traditional models.",
                    retrieved_docs=[
                        {"content": "RAG accesses external knowledge", "score": 0.88},
                        {"content": "Reduces model hallucination", "score": 0.86}
                    ],
                    confidence=0.89,
                    processing_time=1.1
                )

        # 4. Run evaluation through orchestrator
        with patch('core.ragas_engine.evaluate') as mock_ragas:
            mock_ragas.return_value = {
                'faithfulness': 0.87,
                'answer_relevancy': 0.84,
                'context_precision': 0.81,
                'context_recall': 0.86
            }

            result = await orchestrator.run_evaluation_now(
                name="Integration Test Evaluation",
                description="End-to-end integration test",
                golden_dataset_id=dataset.id,
                rag_system_callable=mock_rag_system
            )

            # 5. Verify results
            assert result.metrics['faithfulness'] >= 0.85
            assert result.quality_gates_passed is True
            assert 'overall_score' in result.analysis
            assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_ab_testing_integration(self, temp_storage, sample_evaluation_data):
        """Test A/B testing integration with evaluation framework"""

        # Initialize components
        dataset_manager = GoldenDatasetManager()
        ab_framework = ABTestingFramework()
        orchestrator = EvaluationOrchestrator()

        # Create dataset
        dataset = await dataset_manager.create_golden_dataset(
            name="A/B Test Dataset",
            description="Dataset for A/B testing",
            raw_data=sample_evaluation_data
        )

        # Define experiment
        primary_metric = ExperimentMetric(
            name="faithfulness",
            type=MetricType.CONTINUOUS,
            description="RAGAS faithfulness score",
            minimum_detectable_effect=0.05,
            baseline_value=0.80
        )

        variants = [
            ExperimentVariant(
                id="control",
                name="Current RAG System",
                description="Existing implementation",
                traffic_allocation=0.5,
                configuration={"model": "current"}
            ),
            ExperimentVariant(
                id="treatment",
                name="Enhanced RAG System",
                description="Improved implementation",
                traffic_allocation=0.5,
                configuration={"model": "enhanced"}
            )
        ]

        # Design experiment
        experiment = await ab_framework.design_experiment(
            name="RAG System A/B Test",
            description="Compare RAG system variants",
            primary_metric=primary_metric,
            variants=variants
        )

        # Simulate experiment data collection
        import numpy as np
        np.random.seed(42)

        # Control group data (lower performance)
        for i in range(100):
            await ab_framework.record_observation(
                experiment_id=experiment.experiment_id,
                variant_id="control",
                randomization_unit_id=f"user_{i}",
                metric_values={"faithfulness": np.random.normal(0.78, 0.08)}
            )

        # Treatment group data (higher performance)
        for i in range(100):
            await ab_framework.record_observation(
                experiment_id=experiment.experiment_id,
                variant_id="treatment",
                randomization_unit_id=f"user_{i+100}",
                metric_values={"faithfulness": np.random.normal(0.84, 0.08)}
            )

        # Analyze experiment
        analysis_result = await ab_framework.analyze_experiment(experiment.experiment_id)

        assert analysis_result.primary_metric_result.is_significant
        assert analysis_result.winning_variant == "treatment"
        assert "recommend" in analysis_result.recommendation.lower()

    @pytest.mark.asyncio
    async def test_continuous_monitoring_integration(self, temp_storage, sample_evaluation_data):
        """Test continuous monitoring and alerting integration"""

        # Initialize components
        dataset_manager = GoldenDatasetManager()
        orchestrator = EvaluationOrchestrator()
        orchestrator.storage_path = temp_storage

        # Create dataset
        dataset = await dataset_manager.create_golden_dataset(
            name="Monitoring Dataset",
            description="Dataset for continuous monitoring",
            raw_data=sample_evaluation_data
        )

        await dataset_manager.store_dataset(dataset)

        # Set up quality gates
        from orchestrator.evaluation_orchestrator import QualityGate
        quality_gates = [
            QualityGate(
                name="Critical Faithfulness",
                metric_name="faithfulness",
                threshold=0.85,
                operator="gte",
                severity="critical"
            ),
            QualityGate(
                name="Answer Relevancy Check",
                metric_name="answer_relevancy",
                threshold=0.80,
                operator="gte",
                severity="warning"
            )
        ]

        orchestrator.quality_gates = quality_gates

        # Set up alert rules
        from orchestrator.evaluation_orchestrator import AlertRule
        alert_rules = [
            AlertRule(
                name="Performance Degradation",
                condition="metrics.get('faithfulness', 1.0) < 0.8",
                severity="critical",
                channels=["email"]
            )
        ]

        orchestrator.alert_rules = alert_rules

        # Simulate quality degradation
        degraded_metrics = {
            "faithfulness": 0.75,  # Below threshold
            "answer_relevancy": 0.82,
            "context_precision": 0.79
        }

        # Check quality gates
        gates_result = await orchestrator.check_quality_gates(degraded_metrics)
        assert gates_result.passed is False
        assert len(gates_result.failed_gates) > 0

        # Check alerts
        alerts = await orchestrator.check_alert_conditions(degraded_metrics, {"failed_jobs": 0, "total_jobs": 1})
        assert len(alerts) > 0
        assert any(alert.severity == "critical" for alert in alerts)

    @pytest.mark.asyncio
    async def test_performance_benchmarking(self, temp_storage, sample_evaluation_data):
        """Test performance benchmarking functionality"""

        # Initialize components
        dataset_manager = GoldenDatasetManager()
        evaluation_engine = RAGASEvaluationEngine()

        # Create larger dataset for benchmarking
        benchmark_data = sample_evaluation_data * 10  # 30 data points

        dataset = await dataset_manager.create_golden_dataset(
            name="Benchmark Dataset",
            description="Large dataset for performance testing",
            raw_data=benchmark_data
        )

        # Create mock RAG responses
        rag_responses = []
        for data_point in dataset.data_points:
            response = RAGResponse(
                answer=f"Mock answer for: {data_point.query[:50]}...",
                retrieved_docs=[
                    {"content": "Mock context 1", "score": 0.85},
                    {"content": "Mock context 2", "score": 0.80}
                ],
                confidence=0.85,
                processing_time=1.0
            )
            rag_responses.append(response)

        # Run benchmark evaluation
        import time
        start_time = time.time()

        with patch('core.ragas_engine.evaluate') as mock_ragas:
            mock_ragas.return_value = {
                'faithfulness': 0.86,
                'answer_relevancy': 0.83,
                'context_precision': 0.80,
                'context_recall': 0.84
            }

            queries = [dp.query for dp in dataset.data_points]
            ground_truths = [dp.expected_answer for dp in dataset.data_points]

            result = await evaluation_engine.evaluate_rag_system(
                test_queries=queries,
                rag_responses=rag_responses,
                ground_truths=ground_truths
            )

        execution_time = time.time() - start_time

        # Verify performance
        assert execution_time < 30.0  # Should complete within 30 seconds
        assert result.metrics['faithfulness'] > 0.8
        assert len(result.analysis['strengths']) > 0

    @pytest.mark.asyncio
    async def test_dataset_evolution_workflow(self, temp_storage, sample_evaluation_data):
        """Test dataset evolution and versioning workflow"""

        dataset_manager = GoldenDatasetManager()
        dataset_manager.storage_path = temp_storage

        # Create initial dataset
        dataset_v1 = await dataset_manager.create_golden_dataset(
            name="Evolving Dataset",
            description="Dataset that evolves over time",
            raw_data=sample_evaluation_data,
            version="1.0"
        )

        await dataset_manager.store_dataset(dataset_v1)

        # Simulate feedback and improvements
        additional_data = [
            {
                "query": "What is semantic search in RAG?",
                "expected_answer": "Semantic search finds relevant content based on meaning rather than keywords.",
                "expected_contexts": [
                    "Semantic search uses embeddings to understand meaning",
                    "It goes beyond keyword matching"
                ],
                "taxonomy_path": ["AI", "NLP", "RAG", "Semantic Search"],
                "difficulty_level": "advanced",
                "domain": "ai_technology"
            }
        ]

        # Create evolved dataset
        evolved_data = sample_evaluation_data + additional_data

        dataset_v2 = await dataset_manager.create_golden_dataset(
            name="Evolving Dataset",
            description="Updated dataset with additional examples",
            raw_data=evolved_data,
            version="2.0"
        )

        await dataset_manager.store_dataset(dataset_v2)

        # Verify evolution
        assert len(dataset_v2.data_points) > len(dataset_v1.data_points)
        assert dataset_v2.version == "2.0"
        assert dataset_v2.quality_score >= dataset_v1.quality_score

        # Test dataset comparison
        comparison = await dataset_manager.compare_datasets(dataset_v1, dataset_v2)
        assert "added_points" in comparison
        assert comparison["version_change"] == "1.0 -> 2.0"

    @pytest.mark.asyncio
    async def test_multi_domain_evaluation(self, temp_storage):
        """Test evaluation across multiple domains"""

        # Create multi-domain dataset
        multi_domain_data = [
            {
                "query": "What is machine learning?",
                "expected_answer": "ML enables systems to learn from data.",
                "expected_contexts": ["ML algorithms", "Data learning"],
                "taxonomy_path": ["AI", "ML"],
                "difficulty_level": "beginner",
                "domain": "technology"
            },
            {
                "query": "How do you calculate ROI?",
                "expected_answer": "ROI = (Gain - Cost) / Cost * 100%",
                "expected_contexts": ["Return on investment formula", "Financial metrics"],
                "taxonomy_path": ["Finance", "Metrics"],
                "difficulty_level": "intermediate",
                "domain": "finance"
            },
            {
                "query": "What causes climate change?",
                "expected_answer": "Greenhouse gas emissions from human activities.",
                "expected_contexts": ["Carbon emissions", "Global warming"],
                "taxonomy_path": ["Science", "Climate"],
                "difficulty_level": "intermediate",
                "domain": "science"
            }
        ]

        dataset_manager = GoldenDatasetManager()
        evaluation_engine = RAGASEvaluationEngine()

        dataset = await dataset_manager.create_golden_dataset(
            name="Multi-Domain Dataset",
            description="Cross-domain evaluation dataset",
            raw_data=multi_domain_data
        )

        # Evaluate by domain
        domains = set(dp.domain for dp in dataset.data_points)
        domain_results = {}

        for domain in domains:
            domain_points = [dp for dp in dataset.data_points if dp.domain == domain]
            domain_responses = [
                RAGResponse(
                    answer=f"Domain-specific answer for {dp.query}",
                    retrieved_docs=[{"content": f"{domain} context", "score": 0.8}],
                    confidence=0.85
                ) for dp in domain_points
            ]

            with patch('core.ragas_engine.evaluate') as mock_ragas:
                # Simulate domain-specific performance
                domain_scores = {
                    "technology": 0.88,
                    "finance": 0.82,
                    "science": 0.85
                }

                mock_ragas.return_value = {
                    'faithfulness': domain_scores.get(domain, 0.85),
                    'answer_relevancy': domain_scores.get(domain, 0.80) - 0.02,
                    'context_precision': 0.80,
                    'context_recall': 0.83
                }

                result = await evaluation_engine.evaluate_rag_system(
                    test_queries=[dp.query for dp in domain_points],
                    rag_responses=domain_responses
                )

                domain_results[domain] = result

        # Verify domain-specific results
        assert len(domain_results) == 3
        assert all(result.metrics['faithfulness'] > 0.8 for result in domain_results.values())

        # Technology domain should perform best
        assert domain_results["technology"].metrics['faithfulness'] >= domain_results["finance"].metrics['faithfulness']

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, temp_storage, sample_evaluation_data):
        """Test error handling and recovery mechanisms"""

        orchestrator = EvaluationOrchestrator()
        orchestrator.storage_path = temp_storage

        # Test evaluation with failing RAG system
        async def failing_rag_system(query: str):
            if "vector search" in query.lower():
                raise Exception("Simulated vector search failure")
            return RAGResponse(
                answer="Successful response",
                retrieved_docs=[{"content": "context", "score": 0.8}],
                confidence=0.85
            )

        dataset_manager = GoldenDatasetManager()
        dataset = await dataset_manager.create_golden_dataset(
            name="Error Test Dataset",
            description="Dataset for error testing",
            raw_data=sample_evaluation_data
        )

        await dataset_manager.store_dataset(dataset)

        # Run evaluation with partial failures
        with patch('core.ragas_engine.evaluate') as mock_ragas:
            mock_ragas.return_value = {
                'faithfulness': 0.85,
                'answer_relevancy': 0.80,
                'context_precision': 0.78,
                'context_recall': 0.82
            }

            result = await orchestrator.run_evaluation_now(
                name="Error Recovery Test",
                description="Test error handling",
                golden_dataset_id=dataset.id,
                rag_system_callable=failing_rag_system
            )

            # Should handle errors gracefully
            assert result is not None
            assert 'error_count' in result.analysis
            assert result.analysis['error_count'] > 0

    def test_configuration_loading(self, temp_storage):
        """Test configuration loading and validation"""

        # Create test configuration
        config = {
            "ragas_engine": {
                "metrics": {
                    "faithfulness": {"threshold": 0.85, "weight": 0.3},
                    "answer_relevancy": {"threshold": 0.80, "weight": 0.25}
                }
            },
            "golden_dataset": {
                "quality_thresholds": {
                    "min_completeness": 0.95,
                    "min_consistency": 0.90
                }
            },
            "orchestrator": {
                "max_concurrent_jobs": 3,
                "quality_gate_enforcement": True
            }
        }

        config_path = Path(temp_storage) / "test_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)

        # Test configuration loading
        from orchestrator.evaluation_orchestrator import load_config
        loaded_config = load_config(str(config_path))

        assert loaded_config["ragas_engine"]["metrics"]["faithfulness"]["threshold"] == 0.85
        assert loaded_config["orchestrator"]["max_concurrent_jobs"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])