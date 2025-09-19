"""
RAGAS Evaluation System Tests

Comprehensive test suite for RAGAS evaluation framework:
- RAGAS engine functionality
- Golden dataset management
- Evaluation API endpoints
- Quality gate monitoring
- Performance analytics
"""

import asyncio
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

from apps.evaluation.core.ragas_engine import (
    RAGASEvaluationEngine,
    RAGResponse,
    EvaluationResult,
    RAGASMetrics
)
from apps.evaluation.core.golden_dataset import (
    GoldenDatasetManager,
    GoldenDataPoint,
    GoldenDataset
)

class TestRAGASEvaluationEngine:
    """Test RAGAS evaluation engine functionality"""

    @pytest.fixture
    def ragas_engine(self):
        """Create RAGAS engine for testing"""
        return RAGASEvaluationEngine(use_openai=False)  # Use fallback for testing

    @pytest.fixture
    def sample_queries(self):
        """Sample test queries"""
        return [
            "What is Retrieval-Augmented Generation?",
            "How does vector search work?",
            "What are the benefits of hybrid search?"
        ]

    @pytest.fixture
    def sample_rag_responses(self):
        """Sample RAG responses for testing"""
        return [
            RAGResponse(
                answer="RAG combines retrieval and generation to provide accurate answers using external knowledge.",
                retrieved_docs=[
                    {
                        'text': "RAG is a framework that retrieves relevant documents and uses them for generation.",
                        'title': "RAG Overview",
                        'taxonomy_path': ["AI", "NLP", "RAG"],
                        'score': 0.9
                    }
                ],
                confidence=0.85,
                metadata={'search_type': 'hybrid'}
            ),
            RAGResponse(
                answer="Vector search uses embeddings to find semantically similar documents in high-dimensional space.",
                retrieved_docs=[
                    {
                        'text': "Vector search converts text to embeddings and uses similarity measures like cosine similarity.",
                        'title': "Vector Search",
                        'taxonomy_path': ["AI", "Information Retrieval", "Vector Search"],
                        'score': 0.88
                    }
                ],
                confidence=0.90,
                metadata={'search_type': 'vector'}
            ),
            RAGResponse(
                answer="Hybrid search combines keyword and semantic search for better retrieval performance.",
                retrieved_docs=[
                    {
                        'text': "Hybrid search systems combine BM25 and vector search using fusion techniques.",
                        'title': "Hybrid Search",
                        'taxonomy_path': ["AI", "Information Retrieval", "Hybrid"],
                        'score': 0.85
                    }
                ],
                confidence=0.80,
                metadata={'search_type': 'hybrid'}
            )
        ]

    @pytest.fixture
    def sample_ground_truths(self):
        """Sample ground truth answers"""
        return [
            "RAG is a framework that combines information retrieval with text generation for accurate responses.",
            "Vector search uses neural embeddings to find semantically similar content in high-dimensional space.",
            "Hybrid search combines lexical and semantic search methods for comprehensive retrieval."
        ]

    @pytest.mark.asyncio
    async def test_basic_rag_evaluation(self, ragas_engine, sample_queries, sample_rag_responses, sample_ground_truths):
        """Test basic RAGAS evaluation functionality"""

        result = await ragas_engine.evaluate_rag_system(
            test_queries=sample_queries,
            rag_responses=sample_rag_responses,
            ground_truths=sample_ground_truths
        )

        # Verify result structure
        assert isinstance(result, EvaluationResult)
        assert isinstance(result.metrics, dict)
        assert isinstance(result.analysis, dict)
        assert isinstance(result.quality_gates_passed, bool)
        assert isinstance(result.recommendations, list)

        # Check that key metrics are present
        expected_metrics = ['faithfulness', 'answer_relevancy']
        for metric in expected_metrics:
            assert metric in result.metrics
            assert 0.0 <= result.metrics[metric] <= 1.0

    @pytest.mark.asyncio
    async def test_faithfulness_calculation(self, ragas_engine):
        """Test faithfulness score calculation"""

        # High faithfulness case
        answer = "RAG combines retrieval and generation using neural networks."
        contexts = ["RAG frameworks use neural networks to combine retrieval with generation capabilities."]

        score = ragas_engine._calculate_faithfulness_score(answer, contexts)
        assert 0.0 <= score <= 1.0
        assert score > 0.3  # Should have reasonable similarity

        # Low faithfulness case
        answer = "Cats are fluffy animals that meow."
        contexts = ["RAG frameworks use neural networks for text generation."]

        score = ragas_engine._calculate_faithfulness_score(answer, contexts)
        assert 0.0 <= score <= 1.0
        assert score < 0.5  # Should have low similarity

    @pytest.mark.asyncio
    async def test_answer_relevancy_calculation(self, ragas_engine):
        """Test answer relevancy score calculation"""

        # High relevancy case
        question = "What is RAG?"
        answer = "RAG is Retrieval-Augmented Generation, a framework for AI."

        score = ragas_engine._calculate_relevancy_score(question, answer)
        assert 0.0 <= score <= 1.0
        assert score > 0.3

        # Low relevancy case
        question = "What is RAG?"
        answer = "The weather is nice today and birds are singing."

        score = ragas_engine._calculate_relevancy_score(question, answer)
        assert 0.0 <= score <= 1.0
        assert score < 0.3

    @pytest.mark.asyncio
    async def test_context_precision_calculation(self, ragas_engine):
        """Test context precision calculation"""

        question = "What is machine learning?"
        contexts = [
            "Machine learning is a subset of AI that learns from data.",
            "The weather forecast shows rain tomorrow.",
            "Neural networks are used in machine learning applications."
        ]
        ground_truth = "Machine learning is an AI technique that learns patterns from data."

        score = ragas_engine._calculate_context_precision(question, contexts, ground_truth)
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_context_recall_calculation(self, ragas_engine):
        """Test context recall calculation"""

        retrieved_contexts = [
            "Machine learning uses algorithms to learn from data.",
            "Deep learning is a subset of machine learning."
        ]
        expected_contexts = [
            "Machine learning algorithms learn patterns from training data.",
            "Deep learning networks have multiple layers.",
            "Supervised learning uses labeled training examples."
        ]

        score = ragas_engine._calculate_context_recall(retrieved_contexts, expected_contexts)
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_taxonomy_performance_evaluation(self, ragas_engine, sample_rag_responses):
        """Test taxonomy-specific performance evaluation"""

        queries = ["What is AI?", "How does classification work?"]

        taxonomy_metrics = await ragas_engine._evaluate_taxonomy_performance(queries, sample_rag_responses[:2])

        # Check expected taxonomy metrics
        expected_taxonomy_metrics = [
            'classification_accuracy',
            'taxonomy_consistency',
            'path_precision',
            'hierarchical_coherence'
        ]

        for metric in expected_taxonomy_metrics:
            assert metric in taxonomy_metrics
            assert 0.0 <= taxonomy_metrics[metric] <= 1.0

    @pytest.mark.asyncio
    async def test_quality_gates_checking(self, ragas_engine):
        """Test quality gates validation"""

        # Test passing metrics
        passing_metrics = {
            'faithfulness': 0.90,
            'answer_relevancy': 0.85,
            'context_precision': 0.80,
            'context_recall': 0.85
        }

        assert ragas_engine._check_quality_gates(passing_metrics) == True

        # Test failing metrics
        failing_metrics = {
            'faithfulness': 0.70,  # Below 0.85 threshold
            'answer_relevancy': 0.85,
            'context_precision': 0.80,
            'context_recall': 0.85
        }

        assert ragas_engine._check_quality_gates(failing_metrics) == False

    @pytest.mark.asyncio
    async def test_recommendations_generation(self, ragas_engine):
        """Test recommendation generation based on metrics"""

        # Metrics with weaknesses
        metrics = {
            'faithfulness': 0.70,  # Below threshold
            'answer_relevancy': 0.90,
            'context_precision': 0.60,  # Below threshold
            'context_recall': 0.85
        }

        analysis = ragas_engine._analyze_results(metrics, [])
        recommendations = ragas_engine._generate_recommendations(metrics, analysis)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Check that recommendations address specific weaknesses
        rec_text = " ".join(recommendations).lower()
        assert "faithfulness" in rec_text
        assert "precision" in rec_text

    def test_evaluation_history_tracking(self, ragas_engine):
        """Test evaluation history tracking"""

        # Record some evaluations
        metrics1 = {'faithfulness': 0.8, 'answer_relevancy': 0.7}
        metrics2 = {'faithfulness': 0.85, 'answer_relevancy': 0.75}

        ragas_engine._record_evaluation(metrics1, 1.5)
        ragas_engine._record_evaluation(metrics2, 1.2)

        assert len(ragas_engine.evaluation_history) == 2

        # Test summary generation
        summary = ragas_engine.get_evaluation_summary()
        assert 'recent_evaluations_count' in summary
        assert 'average_metrics' in summary
        assert 'success_rate' in summary

class TestGoldenDatasetManager:
    """Test golden dataset management functionality"""

    @pytest.fixture
    def dataset_manager(self):
        """Create dataset manager for testing"""
        return GoldenDatasetManager()

    @pytest.fixture
    def sample_data_points(self):
        """Sample golden data points"""
        return [
            GoldenDataPoint(
                id="test_001",
                query="What is RAG?",
                expected_answer="RAG is Retrieval-Augmented Generation.",
                expected_contexts=["RAG combines retrieval with generation."],
                taxonomy_path=["AI", "NLP", "RAG"],
                difficulty_level="easy",
                domain="AI/RAG"
            ),
            GoldenDataPoint(
                id="test_002",
                query="How does vector search work?",
                expected_answer="Vector search uses embeddings and similarity measures.",
                expected_contexts=["Vector search converts text to embeddings."],
                taxonomy_path=["AI", "Information Retrieval", "Vector Search"],
                difficulty_level="medium",
                domain="AI/RAG"
            )
        ]

    @pytest.mark.asyncio
    async def test_dataset_creation(self, dataset_manager, sample_data_points):
        """Test golden dataset creation"""

        dataset = await dataset_manager.create_dataset(
            name="test_dataset",
            data_points=sample_data_points,
            description="Test dataset for RAGAS evaluation"
        )

        assert isinstance(dataset, GoldenDataset)
        assert dataset.name == "test_dataset"
        assert len(dataset.data_points) == 2
        assert dataset.quality_score > 0.0

    @pytest.mark.asyncio
    async def test_dataset_validation(self, dataset_manager, sample_data_points):
        """Test dataset validation functionality"""

        # Test valid dataset
        validation_result = await dataset_manager.validate_dataset(sample_data_points)
        assert validation_result.is_valid == True
        assert validation_result.quality_score > 0.0

        # Test dataset with issues
        invalid_data_points = [
            GoldenDataPoint(
                id="invalid_001",
                query="",  # Empty query
                expected_answer="Some answer",
                expected_contexts=[],  # Empty contexts
                taxonomy_path=[],  # Empty path
                difficulty_level="easy",
                domain="Test"
            )
        ]

        validation_result = await dataset_manager.validate_dataset(invalid_data_points)
        assert validation_result.is_valid == False
        assert len(validation_result.errors) > 0

    @pytest.mark.asyncio
    async def test_dataset_sampling(self, dataset_manager, sample_data_points):
        """Test dataset sampling strategies"""

        # Create dataset with more points
        extended_data_points = sample_data_points * 5  # 10 points total
        for i, point in enumerate(extended_data_points):
            point.id = f"test_{i:03d}"

        dataset = await dataset_manager.create_dataset(
            name="extended_test",
            data_points=extended_data_points
        )

        # Test random sampling
        sample = dataset_manager.sample_dataset(dataset, sample_size=5, strategy="random")
        assert len(sample) == 5

        # Test stratified sampling
        sample = dataset_manager.sample_dataset(dataset, sample_size=6, strategy="stratified")
        assert len(sample) == 6

    def test_dataset_quality_scoring(self, dataset_manager, sample_data_points):
        """Test dataset quality scoring"""

        quality_score = dataset_manager._calculate_dataset_quality(sample_data_points)
        assert 0.0 <= quality_score <= 1.0

    @pytest.mark.asyncio
    async def test_dataset_persistence(self, dataset_manager, sample_data_points):
        """Test dataset saving and loading"""

        with tempfile.TemporaryDirectory() as temp_dir:
            # Override the datasets directory for testing
            dataset_manager.datasets_dir = Path(temp_dir)

            # Create and save dataset
            dataset = await dataset_manager.create_dataset(
                name="persistence_test",
                data_points=sample_data_points
            )

            await dataset_manager.save_dataset(dataset)

            # Load dataset
            loaded_dataset = await dataset_manager.load_dataset("persistence_test")

            assert loaded_dataset is not None
            assert loaded_dataset.name == dataset.name
            assert len(loaded_dataset.data_points) == len(dataset.data_points)

class TestEvaluationIntegration:
    """Integration tests for complete evaluation pipeline"""

    @pytest.mark.asyncio
    async def test_end_to_end_evaluation_pipeline(self):
        """Test complete evaluation pipeline from queries to results"""

        # Setup components
        ragas_engine = RAGASEvaluationEngine(use_openai=False)
        dataset_manager = GoldenDatasetManager()

        # Create test dataset
        test_queries = [
            "What is machine learning?",
            "How does natural language processing work?"
        ]

        test_responses = [
            RAGResponse(
                answer="Machine learning is a subset of AI that learns from data.",
                retrieved_docs=[{
                    'text': "Machine learning algorithms learn patterns from training data.",
                    'title': "ML Overview",
                    'taxonomy_path': ["AI", "Machine Learning"],
                    'score': 0.9
                }],
                confidence=0.85
            ),
            RAGResponse(
                answer="NLP processes and understands human language using computational methods.",
                retrieved_docs=[{
                    'text': "Natural language processing uses algorithms to understand text and speech.",
                    'title': "NLP Basics",
                    'taxonomy_path': ["AI", "NLP"],
                    'score': 0.88
                }],
                confidence=0.80
            )
        ]

        # Run evaluation
        result = await ragas_engine.evaluate_rag_system(
            test_queries=test_queries,
            rag_responses=test_responses
        )

        # Verify comprehensive results
        assert isinstance(result, EvaluationResult)
        assert len(result.metrics) > 0
        assert 'faithfulness' in result.metrics
        assert 'answer_relevancy' in result.metrics

        # Check analysis quality
        assert 'overall_score' in result.analysis
        assert 'strengths' in result.analysis
        assert 'weaknesses' in result.analysis

        # Verify recommendations are actionable
        assert isinstance(result.recommendations, list)

    @pytest.mark.asyncio
    async def test_performance_benchmarking(self):
        """Test performance characteristics of evaluation system"""

        ragas_engine = RAGASEvaluationEngine(use_openai=False)

        # Generate larger test set
        num_queries = 20
        test_queries = [f"Test query number {i}" for i in range(num_queries)]
        test_responses = [
            RAGResponse(
                answer=f"This is test answer {i}",
                retrieved_docs=[{
                    'text': f"Test document content {i}",
                    'title': f"Doc {i}",
                    'taxonomy_path': ["Test", f"Category{i%3}"],
                    'score': 0.8
                }],
                confidence=0.8
            )
            for i in range(num_queries)
        ]

        # Measure evaluation time
        start_time = datetime.utcnow()

        result = await ragas_engine.evaluate_rag_system(
            test_queries=test_queries,
            rag_responses=test_responses
        )

        end_time = datetime.utcnow()
        evaluation_duration = (end_time - start_time).total_seconds()

        # Performance assertions
        assert evaluation_duration < 30.0  # Should complete within 30 seconds
        assert len(result.metrics) > 0
        assert result.analysis['overall_score'] >= 0.0

    @pytest.mark.asyncio
    async def test_golden_dataset_loading_from_files(self):
        """Test loading golden datasets from JSON files"""

        dataset_manager = GoldenDatasetManager()

        # Test loading AI/RAG dataset
        try:
            # This would load from the actual golden dataset files
            ai_rag_path = Path("data/golden_datasets/ai_rag_qa.json")
            if ai_rag_path.exists():
                with open(ai_rag_path, 'r') as f:
                    dataset_data = json.load(f)

                # Verify dataset structure
                assert 'dataset_name' in dataset_data
                assert 'data_points' in dataset_data
                assert len(dataset_data['data_points']) > 0

                # Verify data point structure
                point = dataset_data['data_points'][0]
                required_fields = ['id', 'query', 'expected_answer', 'expected_contexts', 'taxonomy_path']
                for field in required_fields:
                    assert field in point

        except FileNotFoundError:
            pytest.skip("Golden dataset files not found - this is expected in test environment")

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])