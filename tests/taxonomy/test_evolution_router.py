"""
Tests for Taxonomy Evolution Router API Endpoints

TDD RED phase - tests written before router implementation.

@TEST:TAXONOMY-EVOLUTION-001
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from apps.api.models.evolution_models import (
    GeneratorConfig,
    GenerationAlgorithm,
    Granularity,
    ProposalStatus,
    SuggestionType,
    ProposedCategory,
    TaxonomyProposal,
    EvolutionSuggestion,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_proposal() -> TaxonomyProposal:
    """Sample taxonomy proposal for testing"""
    return TaxonomyProposal(
        proposal_id="prop_test_12345",
        status=ProposalStatus.COMPLETED,
        categories=[
            ProposedCategory(
                id="cat_1",
                name="Machine Learning",
                description="Documents about ML",
                parent_id=None,
                confidence_score=0.85,
                document_count=10,
                sample_document_ids=["doc1", "doc2"],
                keywords=["ml", "neural", "deep learning"],
            ),
            ProposedCategory(
                id="cat_2",
                name="Database Systems",
                description="Documents about databases",
                parent_id=None,
                confidence_score=0.78,
                document_count=5,
                sample_document_ids=["doc3", "doc4"],
                keywords=["sql", "database", "query"],
            ),
        ],
        config=GeneratorConfig(),
        total_documents=15,
        processing_time_seconds=2.5,
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_suggestion() -> EvolutionSuggestion:
    """Sample evolution suggestion for testing"""
    now = datetime.utcnow()
    return EvolutionSuggestion(
        id="sug_test_123",
        suggestion_type=SuggestionType.MERGE,
        confidence=0.9,
        impact_score=0.5,
        affected_documents=25,
        details={
            "source_categories": ["cat_1", "cat_2"],
            "overlap_score": 0.85,
            "shared_keywords": ["data", "analysis"],
        },
        created_at=now,
        expires_at=now,
    )


@pytest.fixture
def mock_evolution_service():
    """Mock evolution service"""
    mock = MagicMock()
    mock.generate_taxonomy = AsyncMock()
    mock.detect_merge_opportunities = AsyncMock()
    return mock


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service"""
    mock = MagicMock()
    mock.batch_generate_embeddings = AsyncMock()
    return mock


@pytest.fixture
async def test_client(mock_evolution_service, mock_embedding_service):
    """Create test client with mocked services"""
    from apps.api.main import app

    # Mock the services
    with patch("apps.api.routers.evolution_router.get_evolution_service", return_value=mock_evolution_service):
        with patch("apps.api.routers.evolution_router.embedding_service", mock_embedding_service):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                yield client


# ============================================================================
# Test: POST /api/v1/taxonomy/generate
# ============================================================================


class TestGenerateEndpoint:
    """Tests for taxonomy generation endpoint"""

    @pytest.mark.asyncio
    async def test_generate_taxonomy_success(
        self,
        test_client,
        sample_proposal,
        mock_evolution_service,
    ):
        """Should successfully generate taxonomy"""
        mock_evolution_service.generate_taxonomy.return_value = sample_proposal

        response = await test_client.post(
            "/api/v1/taxonomy/evolution/generate",
            json={
                "max_depth": 3,
                "granularity": "medium",
                "algorithm": "kmeans",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["proposal_id"] == sample_proposal.proposal_id
        assert data["status"] == "completed"
        assert len(data["categories"]) == 2

    @pytest.mark.asyncio
    async def test_generate_with_document_ids(
        self,
        test_client,
        sample_proposal,
        mock_evolution_service,
    ):
        """Should accept specific document IDs"""
        mock_evolution_service.generate_taxonomy.return_value = sample_proposal

        response = await test_client.post(
            "/api/v1/taxonomy/evolution/generate",
            json={
                "document_ids": ["doc1", "doc2", "doc3"],
                "granularity": "fine",
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_generate_with_custom_clusters(
        self,
        test_client,
        sample_proposal,
        mock_evolution_service,
    ):
        """Should accept custom cluster count"""
        mock_evolution_service.generate_taxonomy.return_value = sample_proposal

        response = await test_client.post(
            "/api/v1/taxonomy/evolution/generate",
            json={
                "n_clusters": 5,
                "algorithm": "hierarchical",
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_generate_validates_n_clusters(
        self,
        test_client,
    ):
        """Should validate n_clusters range"""
        response = await test_client.post(
            "/api/v1/taxonomy/evolution/generate",
            json={
                "n_clusters": 200,  # Too many
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_generate_handles_failure(
        self,
        test_client,
        mock_evolution_service,
    ):
        """Should handle generation failure gracefully"""
        failed_proposal = TaxonomyProposal(
            proposal_id="prop_failed",
            status=ProposalStatus.FAILED,
            categories=[],
            config=GeneratorConfig(),
            total_documents=0,
            processing_time_seconds=0.5,
            created_at=datetime.utcnow(),
            error_message="No documents found",
        )
        mock_evolution_service.generate_taxonomy.return_value = failed_proposal

        response = await test_client.post(
            "/api/v1/taxonomy/evolution/generate",
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] is not None


# ============================================================================
# Test: GET /api/v1/taxonomy/generate/{proposal_id}
# ============================================================================


class TestGetProposalEndpoint:
    """Tests for getting proposal status/details"""

    @pytest.mark.asyncio
    async def test_get_proposal_success(
        self,
        test_client,
        sample_proposal,
    ):
        """Should return proposal details"""
        with patch(
            "apps.api.routers.evolution_router.get_proposal_by_id",
            return_value=sample_proposal,
        ):
            response = await test_client.get(
                "/api/v1/taxonomy/evolution/generate/prop_test_12345"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["proposal_id"] == "prop_test_12345"

    @pytest.mark.asyncio
    async def test_get_proposal_not_found(
        self,
        test_client,
    ):
        """Should return 404 for non-existent proposal"""
        with patch(
            "apps.api.routers.evolution_router.get_proposal_by_id",
            return_value=None,
        ):
            response = await test_client.get(
                "/api/v1/taxonomy/evolution/generate/prop_nonexistent"
            )

            assert response.status_code == 404


# ============================================================================
# Test: POST /api/v1/taxonomy/generate/{proposal_id}/accept
# ============================================================================


class TestAcceptProposalEndpoint:
    """Tests for accepting a proposal"""

    @pytest.mark.asyncio
    async def test_accept_proposal_success(
        self,
        test_client,
        sample_proposal,
    ):
        """Should accept and apply proposal"""
        with patch(
            "apps.api.routers.evolution_router.get_proposal_by_id",
            return_value=sample_proposal,
        ):
            with patch(
                "apps.api.routers.evolution_router.apply_proposal",
                return_value={"taxonomy_id": "tax_new_123", "success": True},
            ):
                response = await test_client.post(
                    "/api/v1/taxonomy/evolution/generate/prop_test_12345/accept",
                    json={"taxonomy_version": "1.0.0"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["taxonomy_id"] == "tax_new_123"

    @pytest.mark.asyncio
    async def test_accept_proposal_with_modifications(
        self,
        test_client,
        sample_proposal,
    ):
        """Should accept with modifications"""
        with patch(
            "apps.api.routers.evolution_router.get_proposal_by_id",
            return_value=sample_proposal,
        ):
            with patch(
                "apps.api.routers.evolution_router.apply_proposal",
                return_value={"taxonomy_id": "tax_modified", "success": True},
            ):
                response = await test_client.post(
                    "/api/v1/taxonomy/evolution/generate/prop_test_12345/accept",
                    json={
                        "modifications": {
                            "rename": {"cat_1": "Artificial Intelligence"}
                        }
                    },
                )

                assert response.status_code == 200


# ============================================================================
# Test: GET /api/v1/taxonomy/{id}/suggestions
# ============================================================================


class TestSuggestionsEndpoint:
    """Tests for evolution suggestions endpoint"""

    @pytest.mark.asyncio
    async def test_list_suggestions_success(
        self,
        test_client,
        sample_suggestion,
    ):
        """Should return list of suggestions"""
        with patch(
            "apps.api.routers.evolution_router.get_suggestions_for_taxonomy",
            return_value=[sample_suggestion],
        ):
            response = await test_client.get(
                "/api/v1/taxonomy/evolution/tax_123/suggestions"
            )

            assert response.status_code == 200
            data = response.json()
            assert "suggestions" in data
            assert len(data["suggestions"]) == 1
            assert data["suggestions"][0]["suggestion_type"] == "merge"

    @pytest.mark.asyncio
    async def test_list_suggestions_empty(
        self,
        test_client,
    ):
        """Should return empty list when no suggestions"""
        with patch(
            "apps.api.routers.evolution_router.get_suggestions_for_taxonomy",
            return_value=[],
        ):
            response = await test_client.get(
                "/api/v1/taxonomy/evolution/tax_123/suggestions"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["suggestions"] == []
            assert data["total_count"] == 0


# ============================================================================
# Test: POST /api/v1/taxonomy/{id}/suggestions/{suggestion_id}/accept
# ============================================================================


class TestAcceptSuggestionEndpoint:
    """Tests for accepting a suggestion"""

    @pytest.mark.asyncio
    async def test_accept_suggestion_success(
        self,
        test_client,
        sample_suggestion,
    ):
        """Should accept and apply suggestion"""
        with patch(
            "apps.api.routers.evolution_router.get_suggestion_by_id",
            return_value=sample_suggestion,
        ):
            with patch(
                "apps.api.routers.evolution_router.apply_suggestion",
                return_value={"applied": True, "affected_documents": 25},
            ):
                response = await test_client.post(
                    "/api/v1/taxonomy/evolution/tax_123/suggestions/sug_test_123/accept",
                    json={"apply_immediately": True},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["applied"] is True
                assert data["affected_documents"] == 25

    @pytest.mark.asyncio
    async def test_accept_suggestion_not_found(
        self,
        test_client,
    ):
        """Should return 404 for non-existent suggestion"""
        with patch(
            "apps.api.routers.evolution_router.get_suggestion_by_id",
            return_value=None,
        ):
            response = await test_client.post(
                "/api/v1/taxonomy/evolution/tax_123/suggestions/sug_nonexistent/accept",
                json={},
            )

            assert response.status_code == 404


# ============================================================================
# Test: POST /api/v1/taxonomy/{id}/suggestions/{suggestion_id}/reject
# ============================================================================


class TestRejectSuggestionEndpoint:
    """Tests for rejecting a suggestion"""

    @pytest.mark.asyncio
    async def test_reject_suggestion_success(
        self,
        test_client,
        sample_suggestion,
    ):
        """Should reject suggestion with reason"""
        with patch(
            "apps.api.routers.evolution_router.get_suggestion_by_id",
            return_value=sample_suggestion,
        ):
            with patch(
                "apps.api.routers.evolution_router.reject_suggestion",
                return_value={"acknowledged": True},
            ):
                response = await test_client.post(
                    "/api/v1/taxonomy/evolution/tax_123/suggestions/sug_test_123/reject",
                    json={"reason": "Categories should remain separate"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["acknowledged"] is True


# ============================================================================
# Test: GET /api/v1/taxonomy/{id}/analytics
# ============================================================================


class TestAnalyticsEndpoint:
    """Tests for taxonomy analytics endpoint"""

    @pytest.mark.asyncio
    async def test_get_analytics_success(
        self,
        test_client,
    ):
        """Should return analytics data"""
        mock_analytics = {
            "taxonomy_id": "tax_123",
            "period": "week",
            "usage_stats": {
                "total_queries": 150,
                "category_hits": {"cat_1": 80, "cat_2": 70},
            },
            "effectiveness_metrics": {
                "hit_rate": 0.85,
                "avg_results": 5.2,
            },
            "evolution_history": [],
            "suggestions_summary": {"pending": 2, "accepted": 5, "rejected": 1},
        }

        with patch(
            "apps.api.routers.evolution_router.get_taxonomy_analytics",
            return_value=mock_analytics,
        ):
            response = await test_client.get(
                "/api/v1/taxonomy/evolution/tax_123/analytics?period=week"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["taxonomy_id"] == "tax_123"
            assert data["usage_stats"]["total_queries"] == 150

    @pytest.mark.asyncio
    async def test_get_analytics_invalid_period(
        self,
        test_client,
    ):
        """Should validate period parameter"""
        response = await test_client.get(
            "/api/v1/taxonomy/evolution/tax_123/analytics?period=invalid"
        )

        # Should either return 422 or default to valid period
        assert response.status_code in [200, 422]
