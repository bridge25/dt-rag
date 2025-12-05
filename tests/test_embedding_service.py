"""
Unit tests for EmbeddingService - SPEC-ENV-VALIDATE-001 Phase 3-4

Tests health check expansion and error handling in embedding service.
These tests work regardless of which embedding provider is available in CI/CD.

@TEST:EMBED-001
"""

import pytest
from apps.api.embedding_service import EmbeddingService


class TestHealthCheckExpansion:
    """Test cases for health_check() expansion - SPEC-ENV-VALIDATE-001 Phase 3"""

    @pytest.mark.unit
    def test_health_check_returns_required_fields(self):
        """Test health_check() returns all required fields"""
        service = EmbeddingService()
        result = service.health_check()

        # Essential fields should always be present
        assert "status" in result
        assert "api_key_configured" in result
        assert result["status"] in ["healthy", "degraded", "unhealthy"]
        assert isinstance(result["api_key_configured"], bool)

    @pytest.mark.unit
    def test_health_check_returns_model_info(self):
        """Test health_check() returns model information when healthy"""
        service = EmbeddingService()
        result = service.health_check()

        # In healthy/degraded state, model info is present
        # In unhealthy state (no API keys), these fields may be absent
        if result["status"] in ["healthy", "degraded"]:
            assert "model_name" in result
            assert "target_dimensions" in result
            assert result["target_dimensions"] == 1536
        else:
            # Unhealthy state - just verify status is reported
            assert result["status"] == "unhealthy"

    @pytest.mark.unit
    def test_health_check_returns_provider_status(self):
        """Test health_check() returns provider availability when healthy"""
        service = EmbeddingService()
        result = service.health_check()

        # In healthy/degraded state, provider info is present
        # In unhealthy state (no API keys), these fields may be absent
        if result["status"] in ["healthy", "degraded"]:
            assert "gemini_available" in result or "provider" in result
            if "gemini_available" in result:
                assert isinstance(result["gemini_available"], bool)
        else:
            # Unhealthy state - verify error/warning is present
            assert "error" in result or "warning" in result

    @pytest.mark.unit
    def test_health_check_fallback_mode_indicator(self):
        """Test health_check() indicates fallback mode correctly"""
        service = EmbeddingService()
        result = service.health_check()

        # Fallback mode should be boolean
        assert "fallback_mode" in result
        assert isinstance(result["fallback_mode"], bool)


class TestEmbeddingServiceCore:
    """Test cases for core EmbeddingService functionality"""

    @pytest.mark.unit
    def test_target_dimensions_constant(self):
        """Test that TARGET_DIMENSIONS is always 1536"""
        assert EmbeddingService.TARGET_DIMENSIONS == 1536

    @pytest.mark.unit
    def test_service_initialization(self):
        """Test service initializes without error"""
        service = EmbeddingService()
        assert service is not None
        assert hasattr(service, 'model_name')
        assert hasattr(service, 'model_config')

    @pytest.mark.asyncio
    async def test_generate_dummy_embedding_returns_correct_dimensions(self):
        """Test that dummy embedding returns correct dimensions"""
        service = EmbeddingService()
        result = await service._generate_dummy_embedding("test text")

        assert isinstance(result, list)
        assert len(result) == 1536
        assert all(isinstance(x, float) for x in result)


class TestSimilarityCalculation:
    """Test cases for similarity calculation"""

    @pytest.mark.unit
    def test_calculate_similarity_identical_vectors(self):
        """Test similarity calculation for identical vectors"""
        service = EmbeddingService()
        vec = [1.0, 0.0, 0.0]

        similarity = service.calculate_similarity(vec, vec)

        assert similarity == pytest.approx(1.0, abs=0.01)

    @pytest.mark.unit
    def test_calculate_similarity_orthogonal_vectors(self):
        """Test similarity calculation for orthogonal vectors"""
        service = EmbeddingService()
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]

        similarity = service.calculate_similarity(vec1, vec2)

        assert similarity == pytest.approx(0.0, abs=0.01)

    @pytest.mark.unit
    def test_calculate_similarity_empty_vector(self):
        """Test similarity calculation handles zero vectors gracefully"""
        service = EmbeddingService()
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]

        similarity = service.calculate_similarity(vec1, vec2)

        assert similarity == 0.0


class TestCacheManagement:
    """Test cases for embedding cache"""

    @pytest.mark.unit
    def test_clear_cache_returns_count(self):
        """Test that clear_cache returns the number of cleared items"""
        service = EmbeddingService()
        # Add some items to cache
        service.embedding_cache["key1"] = [0.1] * 1536
        service.embedding_cache["key2"] = [0.2] * 1536

        cleared = service.clear_cache()

        assert cleared == 2
        assert len(service.embedding_cache) == 0

    @pytest.mark.unit
    def test_get_cache_key_deterministic(self):
        """Test that cache key generation is deterministic"""
        service = EmbeddingService()
        text = "test text for caching"

        key1 = service._get_cache_key(text)
        key2 = service._get_cache_key(text)

        assert key1 == key2

    @pytest.mark.unit
    def test_get_cache_key_different_for_different_text(self):
        """Test that different text produces different cache keys"""
        service = EmbeddingService()

        key1 = service._get_cache_key("text one")
        key2 = service._get_cache_key("text two")

        assert key1 != key2
