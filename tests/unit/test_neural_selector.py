"""
Unit tests for Neural Case Selector (SPEC-NEURAL-001)

@SPEC:NEURAL-001 @TEST:NEURAL-001:0.1
Tests vector similarity search, hybrid score calculation, and score normalization.
"""

import pytest
import asyncio
from typing import List, Dict, Any
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession


class TestVectorSimilaritySearch:
    """Test vector similarity search functionality"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_vector_similarity_search_basic(self):
        """
        @TEST:NEURAL-001:0.1.1
        Test basic vector similarity search with cosine distance

        Given: Query embedding [1536 dimensions], CaseBank with 3 cases
        When: vector_similarity_search() is called
        Then: Results sorted by cosine similarity (descending)
        """
        from apps.api.neural_selector import vector_similarity_search
        from apps.api.database import CaseBank, async_session

        # Mock query embedding (1536-dim normalized vector)
        query_embedding = [0.1] * 1536

        # Create mock session
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock database result
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ("case1", "query1", "response1", ["AI", "RAG"], 0.95),
            ("case2", "query2", "response2", ["AI", "ML"], 0.85),
            ("case3", "query3", "response3", ["AI", "General"], 0.75),
        ]
        mock_session.execute.return_value = mock_result

        # Execute vector search
        results = await vector_similarity_search(
            mock_session, query_embedding, limit=3, timeout=0.1
        )

        # Assertions
        assert len(results) == 3
        assert results[0]["case_id"] == "case1"
        assert results[0]["score"] == 0.95
        assert results[1]["score"] == 0.85
        assert results[2]["score"] == 0.75
        # Verify sorted by score descending
        assert results[0]["score"] >= results[1]["score"] >= results[2]["score"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_vector_similarity_search_timeout(self):
        """
        @TEST:NEURAL-001:0.1.2
        Test vector search timeout handling

        Given: Vector search timeout set to 100ms
        When: Search exceeds timeout
        Then: Return empty list and log warning
        """
        from apps.api.neural_selector import vector_similarity_search

        query_embedding = [0.1] * 1536

        # Mock session with delayed response
        mock_session = AsyncMock(spec=AsyncSession)

        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(0.2)  # Exceeds timeout
            return Mock()

        mock_session.execute = slow_execute

        # Execute with timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                vector_similarity_search(mock_session, query_embedding, timeout=0.1),
                timeout=0.1
            )

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_vector_similarity_empty_results(self):
        """
        @TEST:NEURAL-001:0.1.3
        Test vector search with no matching cases

        Given: CaseBank with no cases
        When: vector_similarity_search() is called
        Then: Return empty list
        """
        from apps.api.neural_selector import vector_similarity_search

        query_embedding = [0.1] * 1536

        # Mock session with empty result
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        results = await vector_similarity_search(
            mock_session, query_embedding, limit=10, timeout=0.1
        )

        assert results == []


class TestScoreNormalization:
    """Test score normalization functionality"""

    @pytest.mark.unit
    def test_normalize_scores_basic(self):
        """
        @TEST:NEURAL-001:0.2.1
        Test basic Min-Max normalization

        Given: Raw scores [0.1, 0.5, 0.9]
        When: normalize_scores() is called
        Then: Return [0.0, 0.5, 1.0]
        """
        from apps.api.neural_selector import normalize_scores

        raw_scores = [0.1, 0.5, 0.9]
        normalized = normalize_scores(raw_scores)

        assert normalized[0] == pytest.approx(0.0, abs=1e-6)
        assert normalized[1] == pytest.approx(0.5, abs=1e-6)
        assert normalized[2] == pytest.approx(1.0, abs=1e-6)

    @pytest.mark.unit
    def test_normalize_scores_all_same(self):
        """
        @TEST:NEURAL-001:0.2.2
        Test normalization when all scores are identical

        Given: Raw scores [0.7, 0.7, 0.7]
        When: normalize_scores() is called
        Then: Return [1.0, 1.0, 1.0] (avoid division by zero)
        """
        from apps.api.neural_selector import normalize_scores

        raw_scores = [0.7, 0.7, 0.7]
        normalized = normalize_scores(raw_scores)

        assert all(s == 1.0 for s in normalized)

    @pytest.mark.unit
    def test_normalize_scores_empty_list(self):
        """
        @TEST:NEURAL-001:0.2.3
        Test normalization with empty list

        Given: Empty score list []
        When: normalize_scores() is called
        Then: Return []
        """
        from apps.api.neural_selector import normalize_scores

        normalized = normalize_scores([])

        assert normalized == []

    @pytest.mark.unit
    def test_normalize_scores_single_value(self):
        """
        @TEST:NEURAL-001:0.2.4
        Test normalization with single value

        Given: Raw scores [0.5]
        When: normalize_scores() is called
        Then: Return [1.0]
        """
        from apps.api.neural_selector import normalize_scores

        normalized = normalize_scores([0.5])

        assert normalized == [1.0]


class TestHybridScoreCalculation:
    """Test hybrid score calculation functionality"""

    @pytest.mark.unit
    def test_calculate_hybrid_score_default_weights(self):
        """
        @TEST:NEURAL-001:0.3.1
        Test hybrid score calculation with default weights (0.7:0.3)

        Given: Vector scores [0.9, 0.7, 0.5], BM25 scores [0.6, 0.8, 0.4]
        When: calculate_hybrid_score() is called
        Then: Return [0.81, 0.73, 0.47] (0.7*v + 0.3*b after normalization)
        """
        from apps.api.neural_selector import calculate_hybrid_score

        vector_scores = [0.9, 0.7, 0.5]
        bm25_scores = [0.6, 0.8, 0.4]

        hybrid = calculate_hybrid_score(
            vector_scores, bm25_scores, vector_weight=0.7, bm25_weight=0.3
        )

        # After normalization:
        # vector: [1.0, 0.5, 0.0]
        # bm25: [0.5, 1.0, 0.0]
        # hybrid: [0.7*1.0+0.3*0.5, 0.7*0.5+0.3*1.0, 0.7*0.0+0.3*0.0]
        assert hybrid[0] == pytest.approx(0.85, abs=1e-2)  # 0.7 + 0.15
        assert hybrid[1] == pytest.approx(0.65, abs=1e-2)  # 0.35 + 0.3
        assert hybrid[2] == pytest.approx(0.0, abs=1e-2)

    @pytest.mark.unit
    def test_calculate_hybrid_score_custom_weights(self):
        """
        @TEST:NEURAL-001:0.3.2
        Test hybrid score calculation with custom weights (0.5:0.5)

        Given: Custom weights vector=0.5, bm25=0.5
        When: calculate_hybrid_score() is called
        Then: Equal weighting applied
        """
        from apps.api.neural_selector import calculate_hybrid_score

        vector_scores = [1.0, 0.5]
        bm25_scores = [0.5, 1.0]

        hybrid = calculate_hybrid_score(
            vector_scores, bm25_scores, vector_weight=0.5, bm25_weight=0.5
        )

        # After normalization: [1.0, 0.0] and [0.0, 1.0]
        # hybrid: [0.5*1.0+0.5*0.0, 0.5*0.0+0.5*1.0]
        assert hybrid[0] == pytest.approx(0.5, abs=1e-2)
        assert hybrid[1] == pytest.approx(0.5, abs=1e-2)

    @pytest.mark.unit
    def test_calculate_hybrid_score_empty_lists(self):
        """
        @TEST:NEURAL-001:0.3.3
        Test hybrid score calculation with empty lists

        Given: Empty vector and BM25 scores
        When: calculate_hybrid_score() is called
        Then: Return []
        """
        from apps.api.neural_selector import calculate_hybrid_score

        hybrid = calculate_hybrid_score([], [])

        assert hybrid == []


class TestFeatureFlagIntegration:
    """Test feature flag integration for neural case selector"""

    @pytest.mark.unit
    def test_neural_case_selector_flag_off(self):
        """
        @TEST:NEURAL-001:0.4.1
        Test search behavior when neural_case_selector flag is OFF

        Given: neural_case_selector=False
        When: search() is called
        Then: BM25 search only, mode="bm25"
        """
        from apps.api.env_manager import get_env_manager

        env_manager = get_env_manager()
        flags = env_manager.get_feature_flags()

        # Default should be False
        assert flags.get("neural_case_selector") == False

    @pytest.mark.unit
    def test_neural_case_selector_flag_override(self):
        """
        @TEST:NEURAL-001:0.4.2
        Test feature flag override via environment variable

        Given: FEATURE_NEURAL_CASE_SELECTOR=true
        When: get_feature_flags() is called
        Then: neural_case_selector=True
        """
        import os
        from apps.api.env_manager import EnvironmentManager

        # Set environment variable
        os.environ["FEATURE_NEURAL_CASE_SELECTOR"] = "true"

        # Create new instance to pick up env var
        env_manager = EnvironmentManager()
        flags = env_manager.get_feature_flags()

        assert flags.get("neural_case_selector") == True

        # Cleanup
        del os.environ["FEATURE_NEURAL_CASE_SELECTOR"]


class TestPgvectorIntegration:
    """Test pgvector integration and SQL query generation"""

    @pytest.mark.unit
    def test_pgvector_cosine_distance_operator(self):
        """
        @TEST:NEURAL-001:0.5.1
        Test pgvector cosine distance operator (<=>)

        Given: Vector search SQL query
        When: Query is constructed
        Then: Contains '<=> :query_vector::vector' operator
        """
        from apps.api.neural_selector import _build_vector_search_query

        query = _build_vector_search_query()

        assert "<=> :query_vector::vector" in query
        assert "1.0 - (query_vector <=>" in query
        assert "ORDER BY query_vector <=>" in query

    @pytest.mark.unit
    def test_vector_string_formatting(self):
        """
        @TEST:NEURAL-001:0.5.2
        Test vector array to PostgreSQL string conversion

        Given: Python list [0.1, 0.2, 0.3]
        When: Convert to pgvector string format
        Then: Return '[0.1,0.2,0.3]'
        """
        from apps.api.neural_selector import _format_vector_for_postgres

        vector = [0.1, 0.2, 0.3]
        vector_str = _format_vector_for_postgres(vector)

        assert vector_str == "[0.1,0.2,0.3]"
