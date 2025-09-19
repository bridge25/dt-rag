"""
Test suite for golden dataset management
"""
import pytest
import asyncio
import tempfile
import json
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from typing import List, Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'apps', 'evaluation'))

from core.golden_dataset import (
    GoldenDatasetManager,
    GoldenDataPoint,
    GoldenDataset,
    DatasetValidationResult,
    DatasetSplit
)


class TestGoldenDatasetManager:
    """Test cases for golden dataset management"""

    @pytest.fixture
    def dataset_manager(self):
        """Create dataset manager instance"""
        return GoldenDatasetManager()

    @pytest.fixture
    def sample_raw_data(self):
        """Sample raw data for creating datasets"""
        return [
            {
                "query": "What is machine learning?",
                "expected_answer": "Machine learning is a subset of AI that enables systems to learn from data without explicit programming.",
                "expected_contexts": [
                    "Machine learning algorithms learn patterns from training data",
                    "ML is a branch of artificial intelligence"
                ],
                "taxonomy_path": ["AI", "Machine Learning"],
                "difficulty_level": "beginner",
                "domain": "technology",
                "metadata": {"source": "textbook", "verified": True}
            },
            {
                "query": "How does deep learning differ from traditional ML?",
                "expected_answer": "Deep learning uses neural networks with multiple layers, while traditional ML uses simpler algorithms.",
                "expected_contexts": [
                    "Deep learning is based on artificial neural networks",
                    "Traditional ML includes algorithms like decision trees and SVM"
                ],
                "taxonomy_path": ["AI", "Machine Learning", "Deep Learning"],
                "difficulty_level": "intermediate",
                "domain": "technology",
                "metadata": {"source": "research_paper", "verified": True}
            },
            {
                "query": "What are the applications of NLP?",
                "expected_answer": "NLP applications include chatbots, translation, sentiment analysis, and text summarization.",
                "expected_contexts": [
                    "NLP enables computers to understand human language",
                    "Common NLP tasks include translation and sentiment analysis"
                ],
                "taxonomy_path": ["AI", "NLP"],
                "difficulty_level": "intermediate",
                "domain": "technology",
                "metadata": {"source": "documentation", "verified": True}
            }
        ]

    @pytest.fixture
    def sample_dataset(self, sample_raw_data):
        """Create a sample golden dataset"""
        data_points = [
            GoldenDataPoint(
                query=item["query"],
                expected_answer=item["expected_answer"],
                expected_contexts=item["expected_contexts"],
                taxonomy_path=item["taxonomy_path"],
                difficulty_level=item["difficulty_level"],
                domain=item["domain"],
                metadata=item["metadata"]
            ) for item in sample_raw_data
        ]

        return GoldenDataset(
            id="test_dataset_001",
            name="Test Dataset",
            description="Sample dataset for testing",
            version="1.0",
            data_points=data_points,
            metadata={"created_by": "test_user"},
            quality_score=0.95
        )

    @pytest.mark.asyncio
    async def test_create_golden_dataset(self, dataset_manager, sample_raw_data):
        """Test creating a golden dataset"""

        dataset = await dataset_manager.create_golden_dataset(
            name="Test Dataset",
            description="A test dataset for evaluation",
            raw_data=sample_raw_data,
            version="1.0"
        )

        assert isinstance(dataset, GoldenDataset)
        assert dataset.name == "Test Dataset"
        assert len(dataset.data_points) == 3
        assert dataset.quality_score >= 0.8  # Minimum quality threshold

        # Verify data point structure
        first_point = dataset.data_points[0]
        assert first_point.query == "What is machine learning?"
        assert len(first_point.expected_contexts) == 2
        assert first_point.difficulty_level == "beginner"

    @pytest.mark.asyncio
    async def test_dataset_validation(self, dataset_manager, sample_raw_data):
        """Test dataset validation functionality"""

        # Test valid dataset
        valid_result = await dataset_manager.validate_dataset_quality(sample_raw_data)
        assert isinstance(valid_result, DatasetValidationResult)
        assert valid_result.is_valid is True
        assert valid_result.quality_score >= 0.8
        assert len(valid_result.issues) == 0

        # Test invalid dataset with empty fields
        invalid_data = [
            {
                "query": "",  # Empty query
                "expected_answer": "Test answer",
                "expected_contexts": [],  # Empty contexts
                "taxonomy_path": ["AI"],
                "difficulty_level": "beginner",
                "domain": "technology"
            }
        ]

        invalid_result = await dataset_manager.validate_dataset_quality(invalid_data)
        assert invalid_result.is_valid is False
        assert len(invalid_result.issues) > 0
        assert any("empty query" in issue.lower() for issue in invalid_result.issues)

    @pytest.mark.asyncio
    async def test_dataset_completeness_validation(self, dataset_manager):
        """Test dataset completeness validation"""

        # Dataset with missing required fields
        incomplete_data = [
            {
                "query": "Test query",
                # Missing expected_answer
                "expected_contexts": ["context1"],
                "taxonomy_path": ["AI"]
            }
        ]

        result = await dataset_manager.validate_dataset_quality(incomplete_data)
        assert result.is_valid is False
        assert any("missing" in issue.lower() for issue in result.issues)

    @pytest.mark.asyncio
    async def test_dataset_consistency_validation(self, dataset_manager):
        """Test dataset consistency validation"""

        # Dataset with inconsistent data types
        inconsistent_data = [
            {
                "query": "Test query 1",
                "expected_answer": "Answer 1",
                "expected_contexts": ["context1"],
                "taxonomy_path": ["AI"],
                "difficulty_level": "beginner"
            },
            {
                "query": "Test query 2",
                "expected_answer": "Answer 2",
                "expected_contexts": "context2",  # Should be list, not string
                "taxonomy_path": ["AI"],
                "difficulty_level": "invalid_level"  # Invalid difficulty
            }
        ]

        result = await dataset_manager.validate_dataset_quality(inconsistent_data)
        assert result.is_valid is False
        assert len(result.issues) >= 2

    @pytest.mark.asyncio
    async def test_dataset_diversity_validation(self, dataset_manager):
        """Test dataset diversity validation"""

        # Dataset with too many similar queries
        similar_data = [
            {
                "query": "What is machine learning?",
                "expected_answer": "ML is AI subset",
                "expected_contexts": ["ML context"],
                "taxonomy_path": ["AI"]
            },
            {
                "query": "What is machine learning exactly?",  # Very similar
                "expected_answer": "ML is AI subset",
                "expected_contexts": ["ML context"],
                "taxonomy_path": ["AI"]
            },
            {
                "query": "Can you explain machine learning?",  # Very similar
                "expected_answer": "ML is AI subset",
                "expected_contexts": ["ML context"],
                "taxonomy_path": ["AI"]
            }
        ]

        with patch('sklearn.feature_extraction.text.TfidfVectorizer') as mock_vectorizer:
            # Mock high similarity between queries
            mock_vectorizer.return_value.fit_transform.return_value = [[1, 0], [0.9, 0.1], [0.85, 0.15]]

            result = await dataset_manager.validate_dataset_quality(similar_data)
            # Should detect low diversity
            assert result.quality_score < 0.9

    @pytest.mark.asyncio
    async def test_dataset_splitting(self, dataset_manager, sample_dataset):
        """Test dataset splitting functionality"""

        split_result = await dataset_manager.split_dataset(
            dataset=sample_dataset,
            train_ratio=0.6,
            val_ratio=0.2,
            test_ratio=0.2,
            stratify_by="difficulty_level"
        )

        assert isinstance(split_result, DatasetSplit)
        assert len(split_result.train_data) >= 1
        assert len(split_result.val_data) >= 0
        assert len(split_result.test_data) >= 0

        # Verify total count matches original
        total_split = len(split_result.train_data) + len(split_result.val_data) + len(split_result.test_data)
        assert total_split == len(sample_dataset.data_points)

        # Verify stratification
        train_levels = [dp.difficulty_level for dp in split_result.train_data]
        assert len(set(train_levels)) <= len(set([dp.difficulty_level for dp in sample_dataset.data_points]))

    @pytest.mark.asyncio
    async def test_dataset_augmentation(self, dataset_manager, sample_dataset):
        """Test dataset augmentation functionality"""

        # Test paraphrase augmentation
        augmented_dataset = await dataset_manager.augment_dataset(
            dataset=sample_dataset,
            augmentation_methods=["paraphrase"],
            target_size=6  # Double the size
        )

        assert len(augmented_dataset.data_points) > len(sample_dataset.data_points)
        assert augmented_dataset.version != sample_dataset.version

        # Verify augmented data maintains structure
        for data_point in augmented_dataset.data_points:
            assert hasattr(data_point, 'query')
            assert hasattr(data_point, 'expected_answer')
            assert hasattr(data_point, 'expected_contexts')

    @pytest.mark.asyncio
    async def test_dataset_storage_and_retrieval(self, dataset_manager, sample_dataset):
        """Test dataset storage and retrieval"""

        with tempfile.TemporaryDirectory() as temp_dir:
            # Store dataset
            dataset_manager.storage_path = temp_dir
            await dataset_manager.store_dataset(sample_dataset)

            # Verify file was created
            dataset_file = Path(temp_dir) / f"{sample_dataset.id}.json"
            assert dataset_file.exists()

            # Retrieve dataset
            retrieved_dataset = await dataset_manager.load_dataset(sample_dataset.id)
            assert retrieved_dataset.id == sample_dataset.id
            assert retrieved_dataset.name == sample_dataset.name
            assert len(retrieved_dataset.data_points) == len(sample_dataset.data_points)

    @pytest.mark.asyncio
    async def test_dataset_version_management(self, dataset_manager, sample_raw_data):
        """Test dataset version management"""

        # Create initial version
        dataset_v1 = await dataset_manager.create_golden_dataset(
            name="Versioned Dataset",
            description="Test versioning",
            raw_data=sample_raw_data,
            version="1.0"
        )

        # Create updated version
        updated_data = sample_raw_data + [{
            "query": "What is computer vision?",
            "expected_answer": "Computer vision enables machines to interpret visual information.",
            "expected_contexts": ["CV processes images and videos"],
            "taxonomy_path": ["AI", "Computer Vision"],
            "difficulty_level": "intermediate",
            "domain": "technology"
        }]

        dataset_v2 = await dataset_manager.create_golden_dataset(
            name="Versioned Dataset",
            description="Updated version with more data",
            raw_data=updated_data,
            version="2.0"
        )

        assert dataset_v2.version == "2.0"
        assert len(dataset_v2.data_points) > len(dataset_v1.data_points)

    @pytest.mark.asyncio
    async def test_inter_annotator_agreement(self, dataset_manager):
        """Test inter-annotator agreement calculation"""

        # Mock annotations from multiple annotators
        annotations = {
            "annotator_1": [
                {"query": "What is AI?", "label": "correct", "quality": 5},
                {"query": "How does ML work?", "label": "correct", "quality": 4}
            ],
            "annotator_2": [
                {"query": "What is AI?", "label": "correct", "quality": 5},
                {"query": "How does ML work?", "label": "partially_correct", "quality": 3}
            ],
            "annotator_3": [
                {"query": "What is AI?", "label": "correct", "quality": 4},
                {"query": "How does ML work?", "label": "correct", "quality": 4}
            ]
        }

        agreement_score = await dataset_manager.calculate_inter_annotator_agreement(annotations)
        assert 0.0 <= agreement_score <= 1.0
        assert agreement_score > 0.5  # Reasonable agreement

    @pytest.mark.asyncio
    async def test_dataset_quality_monitoring(self, dataset_manager, sample_dataset):
        """Test ongoing dataset quality monitoring"""

        # Simulate usage feedback
        usage_feedback = [
            {"data_point_id": "dp_001", "rating": 5, "feedback": "Excellent example"},
            {"data_point_id": "dp_002", "rating": 3, "feedback": "Answer could be clearer"},
            {"data_point_id": "dp_003", "rating": 4, "feedback": "Good overall"}
        ]

        quality_report = await dataset_manager.monitor_dataset_quality(
            dataset=sample_dataset,
            usage_feedback=usage_feedback
        )

        assert "average_rating" in quality_report
        assert "quality_trends" in quality_report
        assert "improvement_suggestions" in quality_report
        assert quality_report["average_rating"] >= 1.0

    def test_golden_data_point_validation(self):
        """Test golden data point validation"""

        # Valid data point
        valid_point = GoldenDataPoint(
            query="Test query",
            expected_answer="Test answer",
            expected_contexts=["context1", "context2"],
            taxonomy_path=["AI", "ML"],
            difficulty_level="beginner",
            domain="technology"
        )

        assert valid_point.query == "Test query"
        assert len(valid_point.expected_contexts) == 2

        # Test required field validation
        with pytest.raises(TypeError):
            GoldenDataPoint()  # Missing required fields


if __name__ == "__main__":
    pytest.main([__file__, "-v"])