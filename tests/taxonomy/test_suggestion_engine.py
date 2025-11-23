"""
Tests for Taxonomy Suggestion Engine

Tests for overlap detection, merge/split suggestions, and ranking.
TDD RED phase - tests written before implementation.

@TEST:TAXONOMY-EVOLUTION-001
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from apps.api.models.evolution_models import (
    SuggestionType,
    EvolutionSuggestion,
    ProposedCategory,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_categories() -> List[Dict[str, Any]]:
    """Sample categories for testing"""
    np.random.seed(42)
    return [
        {
            "id": "cat_ml",
            "name": "Machine Learning",
            "keywords": ["machine", "learning", "neural", "model", "training"],
            "embedding": np.random.normal(0, 1, 1536).tolist(),
            "document_count": 50,
            "document_ids": [f"doc_{i}" for i in range(50)],
        },
        {
            "id": "cat_dl",
            "name": "Deep Learning",
            "keywords": ["deep", "learning", "neural", "network", "training"],
            "embedding": (np.random.normal(0, 1, 1536) * 0.1 + np.random.normal(0, 1, 1536)).tolist(),
            "document_count": 45,
            "document_ids": [f"doc_{i}" for i in range(45, 90)],
        },
        {
            "id": "cat_db",
            "name": "Database Systems",
            "keywords": ["database", "sql", "query", "index", "storage"],
            "embedding": np.random.normal(5, 1, 1536).tolist(),
            "document_count": 30,
            "document_ids": [f"doc_{i}" for i in range(90, 120)],
        },
        {
            "id": "cat_finance",
            "name": "Financial Analysis",
            "keywords": ["finance", "market", "trading", "stock", "investment"],
            "embedding": np.random.normal(-5, 1, 1536).tolist(),
            "document_count": 200,  # Large category
            "document_ids": [f"doc_{i}" for i in range(120, 320)],
        },
    ]


@pytest.fixture
def sample_zero_result_queries() -> List[Dict[str, Any]]:
    """Sample zero result queries"""
    return [
        {"query": "quantum computing", "count": 25, "first_seen": datetime.utcnow() - timedelta(days=10)},
        {"query": "quantum algorithms", "count": 15, "first_seen": datetime.utcnow() - timedelta(days=8)},
        {"query": "blockchain", "count": 12, "first_seen": datetime.utcnow() - timedelta(days=5)},
        {"query": "kubernetes", "count": 8, "first_seen": datetime.utcnow() - timedelta(days=3)},
    ]


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service"""
    mock = MagicMock()
    mock.calculate_similarity = MagicMock()
    mock.generate_embedding = AsyncMock()
    return mock


@pytest.fixture
def mock_metrics_service():
    """Mock metrics service"""
    mock = MagicMock()
    mock.get_zero_result_patterns = AsyncMock()
    mock.get_category_metrics = AsyncMock()
    return mock


# ============================================================================
# Test: Overlap Detection
# ============================================================================


class TestOverlapDetection:
    """Tests for category overlap detection"""

    @pytest.mark.asyncio
    async def test_detect_high_overlap_categories(
        self,
        sample_categories,
        mock_embedding_service,
    ):
        """Should detect categories with high semantic overlap"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        # ML and DL have similar embeddings
        mock_embedding_service.calculate_similarity.side_effect = [
            0.92,  # ML vs DL - high overlap
            0.15,  # ML vs DB - low overlap
            0.10,  # ML vs Finance - low overlap
            0.20,  # DL vs DB - low overlap
            0.12,  # DL vs Finance - low overlap
            0.08,  # DB vs Finance - low overlap
        ]

        engine = SuggestionEngine(
            embedding_service=mock_embedding_service,
            metrics_service=None,
        )

        overlaps = await engine.detect_overlapping_categories(
            categories=sample_categories,
            threshold=0.8,
        )

        assert len(overlaps) > 0
        assert any(
            ("cat_ml" in o["categories"] and "cat_dl" in o["categories"])
            for o in overlaps
        )

    @pytest.mark.asyncio
    async def test_no_overlap_below_threshold(
        self,
        sample_categories,
        mock_embedding_service,
    ):
        """Should not detect overlap below threshold"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        # All similarities below threshold
        mock_embedding_service.calculate_similarity.return_value = 0.5

        engine = SuggestionEngine(
            embedding_service=mock_embedding_service,
            metrics_service=None,
        )

        overlaps = await engine.detect_overlapping_categories(
            categories=sample_categories,
            threshold=0.8,
        )

        assert len(overlaps) == 0

    @pytest.mark.asyncio
    async def test_overlap_includes_shared_keywords(
        self,
        sample_categories,
        mock_embedding_service,
    ):
        """Should include shared keywords in overlap result"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        mock_embedding_service.calculate_similarity.side_effect = [
            0.9, 0.1, 0.1, 0.1, 0.1, 0.1
        ]

        engine = SuggestionEngine(
            embedding_service=mock_embedding_service,
            metrics_service=None,
        )

        overlaps = await engine.detect_overlapping_categories(
            categories=sample_categories,
            threshold=0.8,
        )

        assert len(overlaps) > 0
        assert "shared_keywords" in overlaps[0]
        # ML and DL share "learning", "neural", "training"
        assert len(overlaps[0]["shared_keywords"]) >= 2


# ============================================================================
# Test: Merge Suggestions
# ============================================================================


class TestMergeSuggestions:
    """Tests for merge suggestion generation"""

    @pytest.mark.asyncio
    async def test_create_merge_suggestion(
        self,
        sample_categories,
        mock_embedding_service,
    ):
        """Should create merge suggestion for overlapping categories"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        mock_embedding_service.calculate_similarity.side_effect = [
            0.9, 0.1, 0.1, 0.1, 0.1, 0.1
        ]

        engine = SuggestionEngine(
            embedding_service=mock_embedding_service,
            metrics_service=None,
        )

        suggestions = await engine.generate_merge_suggestions(
            categories=sample_categories,
            overlap_threshold=0.8,
        )

        assert len(suggestions) > 0
        merge_sug = suggestions[0]
        assert merge_sug.suggestion_type == SuggestionType.MERGE
        assert merge_sug.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_merge_suggestion_includes_impact(
        self,
        sample_categories,
        mock_embedding_service,
    ):
        """Should calculate impact of merge"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        mock_embedding_service.calculate_similarity.side_effect = [
            0.9, 0.1, 0.1, 0.1, 0.1, 0.1
        ]

        engine = SuggestionEngine(
            embedding_service=mock_embedding_service,
            metrics_service=None,
        )

        suggestions = await engine.generate_merge_suggestions(
            categories=sample_categories,
            overlap_threshold=0.8,
        )

        assert len(suggestions) > 0
        merge_sug = suggestions[0]
        # ML (50) + DL (45) = 95 documents affected
        assert merge_sug.affected_documents == 95

    @pytest.mark.asyncio
    async def test_merge_suggests_best_name(
        self,
        sample_categories,
        mock_embedding_service,
    ):
        """Should suggest best name for merged category"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        mock_embedding_service.calculate_similarity.side_effect = [
            0.9, 0.1, 0.1, 0.1, 0.1, 0.1
        ]

        engine = SuggestionEngine(
            embedding_service=mock_embedding_service,
            metrics_service=None,
        )

        suggestions = await engine.generate_merge_suggestions(
            categories=sample_categories,
            overlap_threshold=0.8,
        )

        assert len(suggestions) > 0
        assert "suggested_name" in suggestions[0].details


# ============================================================================
# Test: Split Suggestions
# ============================================================================


class TestSplitSuggestions:
    """Tests for split suggestion generation"""

    @pytest.mark.asyncio
    async def test_suggest_split_for_large_category(
        self,
        sample_categories,
        mock_embedding_service,
    ):
        """Should suggest splitting categories with many documents"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        engine = SuggestionEngine(
            embedding_service=mock_embedding_service,
            metrics_service=None,
        )

        suggestions = await engine.generate_split_suggestions(
            categories=sample_categories,
            max_documents_threshold=100,  # Finance has 200
        )

        assert len(suggestions) > 0
        split_sug = suggestions[0]
        assert split_sug.suggestion_type == SuggestionType.SPLIT
        assert split_sug.details["source_category"] == "cat_finance"

    @pytest.mark.asyncio
    async def test_split_proposes_subcategories(
        self,
        sample_categories,
        mock_embedding_service,
    ):
        """Should propose specific subcategories"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        # Mock embedding generation for subcategory detection
        mock_embedding_service.generate_embedding.return_value = [0.1] * 1536

        engine = SuggestionEngine(
            embedding_service=mock_embedding_service,
            metrics_service=None,
        )

        suggestions = await engine.generate_split_suggestions(
            categories=sample_categories,
            max_documents_threshold=100,
        )

        assert len(suggestions) > 0
        assert "proposed_splits" in suggestions[0].details
        assert len(suggestions[0].details["proposed_splits"]) >= 2

    @pytest.mark.asyncio
    async def test_no_split_for_small_categories(
        self,
        sample_categories,
        mock_embedding_service,
    ):
        """Should not suggest splitting small categories"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        engine = SuggestionEngine(
            embedding_service=mock_embedding_service,
            metrics_service=None,
        )

        suggestions = await engine.generate_split_suggestions(
            categories=sample_categories,
            max_documents_threshold=500,  # All categories below this
        )

        assert len(suggestions) == 0


# ============================================================================
# Test: New Category Suggestions
# ============================================================================


class TestNewCategorySuggestions:
    """Tests for new category suggestion from zero-result queries"""

    @pytest.mark.asyncio
    async def test_suggest_new_category_from_queries(
        self,
        sample_zero_result_queries,
        mock_embedding_service,
        mock_metrics_service,
    ):
        """Should suggest new category from recurring queries"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        mock_metrics_service.get_zero_result_patterns.return_value = [
            MagicMock(
                query_text="quantum computing",
                occurrence_count=25,
                first_seen=datetime.utcnow() - timedelta(days=10),
                last_seen=datetime.utcnow(),
            )
        ]

        engine = SuggestionEngine(
            embedding_service=mock_embedding_service,
            metrics_service=mock_metrics_service,
        )

        suggestions = await engine.generate_new_category_suggestions(
            taxonomy_id="tax_1",
            min_query_count=10,
            min_days_observed=5,
        )

        assert len(suggestions) > 0
        new_cat = suggestions[0]
        assert new_cat.suggestion_type == SuggestionType.NEW_CATEGORY

    @pytest.mark.asyncio
    async def test_group_similar_queries_for_suggestion(
        self,
        mock_embedding_service,
        mock_metrics_service,
    ):
        """Should group similar queries into single suggestion"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        mock_metrics_service.get_zero_result_patterns.return_value = [
            MagicMock(
                query_text="quantum computing",
                occurrence_count=25,
                first_seen=datetime.utcnow() - timedelta(days=10),
                last_seen=datetime.utcnow(),
            ),
            MagicMock(
                query_text="quantum algorithms",
                occurrence_count=15,
                first_seen=datetime.utcnow() - timedelta(days=8),
                last_seen=datetime.utcnow(),
            ),
        ]

        engine = SuggestionEngine(
            embedding_service=mock_embedding_service,
            metrics_service=mock_metrics_service,
        )

        suggestions = await engine.generate_new_category_suggestions(
            taxonomy_id="tax_1",
            min_query_count=5,
            min_days_observed=3,
        )

        # Should create one suggestion for "quantum" related queries
        quantum_suggestions = [
            s for s in suggestions
            if "quantum" in s.details.get("suggested_name", "").lower()
        ]
        assert len(quantum_suggestions) >= 1


# ============================================================================
# Test: Suggestion Ranking
# ============================================================================


class TestSuggestionRanking:
    """Tests for suggestion ranking and prioritization"""

    @pytest.mark.asyncio
    async def test_rank_suggestions_by_impact(self):
        """Should rank suggestions by impact score"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        suggestions = [
            EvolutionSuggestion(
                id="sug_1",
                suggestion_type=SuggestionType.MERGE,
                confidence=0.9,
                impact_score=0.3,
                affected_documents=30,
                details={},
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
            ),
            EvolutionSuggestion(
                id="sug_2",
                suggestion_type=SuggestionType.SPLIT,
                confidence=0.8,
                impact_score=0.7,
                affected_documents=200,
                details={},
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
            ),
            EvolutionSuggestion(
                id="sug_3",
                suggestion_type=SuggestionType.NEW_CATEGORY,
                confidence=0.95,
                impact_score=0.5,
                affected_documents=0,
                details={},
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
            ),
        ]

        engine = SuggestionEngine(embedding_service=None, metrics_service=None)
        ranked = engine.rank_suggestions(suggestions, strategy="impact")

        # Higher impact first
        assert ranked[0].id == "sug_2"

    @pytest.mark.asyncio
    async def test_rank_suggestions_by_confidence(self):
        """Should rank suggestions by confidence"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        suggestions = [
            EvolutionSuggestion(
                id="sug_1",
                suggestion_type=SuggestionType.MERGE,
                confidence=0.7,
                impact_score=0.9,
                affected_documents=100,
                details={},
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
            ),
            EvolutionSuggestion(
                id="sug_2",
                suggestion_type=SuggestionType.NEW_CATEGORY,
                confidence=0.95,
                impact_score=0.3,
                affected_documents=0,
                details={},
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
            ),
        ]

        engine = SuggestionEngine(embedding_service=None, metrics_service=None)
        ranked = engine.rank_suggestions(suggestions, strategy="confidence")

        # Higher confidence first
        assert ranked[0].id == "sug_2"

    @pytest.mark.asyncio
    async def test_rank_combined_score(self):
        """Should rank by combined confidence and impact"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        suggestions = [
            EvolutionSuggestion(
                id="sug_1",
                suggestion_type=SuggestionType.MERGE,
                confidence=0.8,
                impact_score=0.8,  # Combined: 0.8
                affected_documents=50,
                details={},
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
            ),
            EvolutionSuggestion(
                id="sug_2",
                suggestion_type=SuggestionType.SPLIT,
                confidence=0.6,
                impact_score=0.6,  # Combined: 0.6
                affected_documents=30,
                details={},
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
            ),
        ]

        engine = SuggestionEngine(embedding_service=None, metrics_service=None)
        ranked = engine.rank_suggestions(suggestions, strategy="combined")

        assert ranked[0].id == "sug_1"


# ============================================================================
# Test: Full Suggestion Pipeline
# ============================================================================


class TestSuggestionPipeline:
    """Tests for full suggestion generation pipeline"""

    @pytest.mark.asyncio
    async def test_generate_all_suggestions(
        self,
        sample_categories,
        mock_embedding_service,
        mock_metrics_service,
    ):
        """Should generate all types of suggestions"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        mock_embedding_service.calculate_similarity.return_value = 0.5
        mock_metrics_service.get_zero_result_patterns.return_value = []

        engine = SuggestionEngine(
            embedding_service=mock_embedding_service,
            metrics_service=mock_metrics_service,
        )

        all_suggestions = await engine.generate_all_suggestions(
            taxonomy_id="tax_1",
            categories=sample_categories,
        )

        assert isinstance(all_suggestions, list)

    @pytest.mark.asyncio
    async def test_filter_expired_suggestions(self):
        """Should filter out expired suggestions"""
        from apps.api.services.suggestion_engine import SuggestionEngine

        suggestions = [
            EvolutionSuggestion(
                id="sug_valid",
                suggestion_type=SuggestionType.MERGE,
                confidence=0.9,
                impact_score=0.5,
                affected_documents=50,
                details={},
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
            ),
            EvolutionSuggestion(
                id="sug_expired",
                suggestion_type=SuggestionType.SPLIT,
                confidence=0.8,
                impact_score=0.5,
                affected_documents=50,
                details={},
                created_at=datetime.utcnow() - timedelta(days=60),
                expires_at=datetime.utcnow() - timedelta(days=30),
            ),
        ]

        engine = SuggestionEngine(embedding_service=None, metrics_service=None)
        valid = engine.filter_expired(suggestions)

        assert len(valid) == 1
        assert valid[0].id == "sug_valid"
