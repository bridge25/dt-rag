"""
Test suite for RAGAS evaluation engine
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'evaluation'))

from core.ragas_engine import (
    RAGASEvaluationEngine,
    RAGResponse,
    EvaluationResult,
    RAGASMetrics
)


class TestRAGASEvaluationEngine:
    """Test cases for RAGAS evaluation engine"""

    @pytest.fixture
    def evaluation_engine(self):
        """Create evaluation engine instance"""
        return RAGASEvaluationEngine()

    @pytest.fixture
    def sample_rag_responses(self):
        """Sample RAG responses for testing"""
        return [
            RAGResponse(
                answer="Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
                retrieved_docs=[
                    {"content": "Machine learning algorithms learn patterns from data", "score": 0.9},
                    {"content": "AI encompasses machine learning as a key component", "score": 0.8}
                ],
                confidence=0.85,
                processing_time=1.2,
                metadata={"query_id": "test_1"}
            ),
            RAGResponse(
                answer="Deep learning uses neural networks with multiple layers to process complex patterns.",
                retrieved_docs=[
                    {"content": "Deep learning is based on artificial neural networks", "score": 0.95},
                    {"content": "Neural networks have multiple hidden layers", "score": 0.87}
                ],
                confidence=0.92,
                processing_time=1.5,
                metadata={"query_id": "test_2"}
            )
        ]

    @pytest.fixture
    def sample_queries(self):
        """Sample test queries"""
        return [
            "What is machine learning?",
            "How does deep learning work?"
        ]

    @pytest.fixture
    def sample_ground_truths(self):
        """Sample ground truth answers"""
        return [
            "Machine learning is a branch of AI that allows computers to learn without explicit programming.",
            "Deep learning is a machine learning technique using neural networks with multiple layers."
        ]

    @pytest.mark.asyncio
    async def test_ragas_evaluation_basic(self, evaluation_engine, sample_queries, sample_rag_responses, sample_ground_truths):
        """Test basic RAGAS evaluation functionality"""

        # Mock RAGAS library calls
        with patch('core.ragas_engine.evaluate') as mock_evaluate:
            mock_evaluate.return_value = {
                'faithfulness': 0.87,
                'answer_relevancy': 0.82,
                'context_precision': 0.78,
                'context_recall': 0.85
            }

            result = await evaluation_engine.evaluate_rag_system(
                test_queries=sample_queries,
                rag_responses=sample_rag_responses,
                ground_truths=sample_ground_truths
            )

            assert isinstance(result, EvaluationResult)
            assert result.metrics['faithfulness'] >= 0.85  # Quality gate
            assert result.quality_gates_passed is True
            assert len(result.analysis['strengths']) > 0
            assert 'overall_score' in result.analysis

    @pytest.mark.asyncio
    async def test_ragas_evaluation_fallback(self, evaluation_engine, sample_queries, sample_rag_responses):
        """Test fallback evaluation when RAGAS is unavailable"""

        # Mock RAGAS import failure
        with patch('core.ragas_engine.evaluate', side_effect=ImportError("RAGAS not available")):
            result = await evaluation_engine.evaluate_rag_system(
                test_queries=sample_queries,
                rag_responses=sample_rag_responses
            )

            assert isinstance(result, EvaluationResult)
            assert 'faithfulness' in result.metrics
            assert 'answer_relevancy' in result.metrics
            assert result.analysis['fallback_used'] is True

    @pytest.mark.asyncio
    async def test_quality_gates_enforcement(self, evaluation_engine, sample_queries, sample_rag_responses):
        """Test quality gates enforcement"""

        # Mock low quality scores
        with patch('core.ragas_engine.evaluate') as mock_evaluate:
            mock_evaluate.return_value = {
                'faithfulness': 0.70,  # Below threshold
                'answer_relevancy': 0.75,  # Below threshold
                'context_precision': 0.82,
                'context_recall': 0.88
            }

            result = await evaluation_engine.evaluate_rag_system(
                test_queries=sample_queries,
                rag_responses=sample_rag_responses
            )

            assert result.quality_gates_passed is False
            assert len(result.analysis['weaknesses']) > 0
            assert any('faithfulness' in weakness['metric'] for weakness in result.analysis['weaknesses'])

    @pytest.mark.asyncio
    async def test_custom_metrics_integration(self, evaluation_engine, sample_queries, sample_rag_responses):
        """Test custom taxonomy-specific metrics"""

        # Add taxonomy-specific responses
        taxonomy_responses = [
            RAGResponse(
                answer="Machine learning is classified under AI > ML > Supervised Learning",
                retrieved_docs=[{"content": "ML taxonomy hierarchy", "score": 0.9}],
                confidence=0.88,
                processing_time=1.0,
                metadata={"taxonomy_path": ["AI", "ML", "Supervised"]}
            )
        ]

        result = await evaluation_engine.evaluate_rag_system(
            test_queries=["What is the taxonomy of machine learning?"],
            rag_responses=taxonomy_responses
        )

        assert 'taxonomy_consistency' in result.metrics
        assert 'classification_accuracy' in result.metrics

    def test_rag_response_validation(self):
        """Test RAG response data validation"""

        # Valid response
        valid_response = RAGResponse(
            answer="Test answer",
            retrieved_docs=[{"content": "test doc", "score": 0.8}],
            confidence=0.85
        )
        assert valid_response.answer == "Test answer"
        assert len(valid_response.retrieved_docs) == 1

        # Test validation of required fields
        with pytest.raises(TypeError):
            RAGResponse()  # Missing required fields

    @pytest.mark.asyncio
    async def test_evaluation_performance(self, evaluation_engine):
        """Test evaluation performance with large dataset"""

        # Create large dataset
        large_queries = [f"Test query {i}" for i in range(100)]
        large_responses = [
            RAGResponse(
                answer=f"Test answer {i}",
                retrieved_docs=[{"content": f"doc {i}", "score": 0.8}],
                confidence=0.85
            ) for i in range(100)
        ]

        with patch('core.ragas_engine.evaluate') as mock_evaluate:
            mock_evaluate.return_value = {
                'faithfulness': 0.87,
                'answer_relevancy': 0.82,
                'context_precision': 0.78,
                'context_recall': 0.85
            }

            import time
            start_time = time.time()

            result = await evaluation_engine.evaluate_rag_system(
                test_queries=large_queries,
                rag_responses=large_responses
            )

            execution_time = time.time() - start_time

            assert execution_time < 10.0  # Should complete within 10 seconds
            assert isinstance(result, EvaluationResult)

    @pytest.mark.asyncio
    async def test_error_handling(self, evaluation_engine, sample_queries):
        """Test error handling in evaluation"""

        # Test with malformed responses
        malformed_responses = [
            RAGResponse(
                answer="",  # Empty answer
                retrieved_docs=[],  # No documents
                confidence=0.0
            )
        ]

        result = await evaluation_engine.evaluate_rag_system(
            test_queries=sample_queries[:1],
            rag_responses=malformed_responses
        )

        # Should handle gracefully and return low scores
        assert result.metrics['faithfulness'] < 0.5
        assert len(result.analysis['weaknesses']) > 0

    @pytest.mark.asyncio
    async def test_metrics_history_tracking(self, evaluation_engine, sample_queries, sample_rag_responses):
        """Test metrics history tracking for trend analysis"""

        with patch('core.ragas_engine.evaluate') as mock_evaluate:
            # First evaluation
            mock_evaluate.return_value = {
                'faithfulness': 0.85,
                'answer_relevancy': 0.80,
                'context_precision': 0.75,
                'context_recall': 0.82
            }

            result1 = await evaluation_engine.evaluate_rag_system(
                test_queries=sample_queries,
                rag_responses=sample_rag_responses
            )

            # Second evaluation with improved scores
            mock_evaluate.return_value = {
                'faithfulness': 0.90,
                'answer_relevancy': 0.85,
                'context_precision': 0.80,
                'context_recall': 0.87
            }

            result2 = await evaluation_engine.evaluate_rag_system(
                test_queries=sample_queries,
                rag_responses=sample_rag_responses
            )

            # Check trending analysis
            assert 'trending' in result2.analysis
            assert result2.analysis['trending']['direction'] == 'improving'

    def test_ragas_metrics_enum(self):
        """Test RAGAS metrics enumeration"""

        assert RAGASMetrics.FAITHFULNESS == 'faithfulness'
        assert RAGASMetrics.ANSWER_RELEVANCY == 'answer_relevancy'
        assert RAGASMetrics.CONTEXT_PRECISION == 'context_precision'
        assert RAGASMetrics.CONTEXT_RECALL == 'context_recall'

        # Test all metrics are covered
        all_metrics = [metric.value for metric in RAGASMetrics]
        assert len(all_metrics) == 4
        assert len(set(all_metrics)) == 4  # No duplicates


if __name__ == "__main__":
    pytest.main([__file__, "-v"])