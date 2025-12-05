"""
Unit tests for EmbeddingService - SPEC-ENV-VALIDATE-001 Phase 3-4

Tests health check expansion and error handling in embedding service.
Provider-agnostic tests supporting Gemini, OpenAI, and Sentence Transformers.

@TEST:EMBED-001
"""

import pytest
import os
from unittest.mock import patch, MagicMock


class TestHealthCheckExpansion:
    """Test cases for health_check() expansion - SPEC-ENV-VALIDATE-001 Phase 3"""

    @pytest.mark.unit
    def test_health_check_with_gemini_api_key_configured(self):
        """Test health_check() returns healthy when Gemini key is configured"""
        valid_key = "AIza" + "a" * 35  # Gemini key format

        with patch.dict(os.environ, {"GEMINI_API_KEY": valid_key, "OPENAI_API_KEY": ""}, clear=True):
            with patch("apps.api.embedding_service.GEMINI_AVAILABLE", True):
                with patch("apps.api.embedding_service.genai") as mock_genai:
                    from importlib import reload
                    import apps.api.embedding_service as embed_module
                    reload(embed_module)

                    service = embed_module.EmbeddingService()
                    result = service.health_check()

                    assert "api_key_configured" in result
                    assert result["api_key_configured"] is True
                    assert result.get("fallback_mode", False) is False

    @pytest.mark.unit
    def test_health_check_without_any_api_key(self):
        """Test health_check() returns fallback mode when no API keys configured"""
        # Clear all API keys to simulate no-key scenario
        with patch.dict(os.environ, {"OPENAI_API_KEY": "", "GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=True):
            with patch("apps.api.embedding_service.GEMINI_AVAILABLE", False):
                with patch("apps.api.embedding_service.OPENAI_AVAILABLE", False):
                    from importlib import reload
                    import apps.api.embedding_service as embed_module
                    reload(embed_module)

                    service = embed_module.EmbeddingService()
                    result = service.health_check()

                    assert "api_key_configured" in result
                    # When no API keys, should be in fallback/degraded mode
                    # api_key_configured should be False
                    assert result["api_key_configured"] is False

    @pytest.mark.unit
    def test_health_check_returns_status_field(self):
        """Test health_check() always returns status field"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "", "GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=True):
            with patch("apps.api.embedding_service.GEMINI_AVAILABLE", False):
                with patch("apps.api.embedding_service.OPENAI_AVAILABLE", False):
                    from importlib import reload
                    import apps.api.embedding_service as embed_module
                    reload(embed_module)

                    service = embed_module.EmbeddingService()
                    result = service.health_check()

                    # Status should always be present
                    assert "status" in result
                    assert result["status"] in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.unit
    def test_health_check_response_structure_minimal(self):
        """Test health_check() returns minimal required fields"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "", "GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=True):
            with patch("apps.api.embedding_service.GEMINI_AVAILABLE", False):
                with patch("apps.api.embedding_service.OPENAI_AVAILABLE", False):
                    from importlib import reload
                    import apps.api.embedding_service as embed_module
                    reload(embed_module)

                    service = embed_module.EmbeddingService()
                    result = service.health_check()

                    # Essential fields should always be present
                    required_fields = ["status", "api_key_configured"]
                    for field in required_fields:
                        assert field in result, f"Missing required field: {field}"


class TestEmbeddingServiceFallback:
    """Test cases for fallback behavior"""

    @pytest.mark.unit
    def test_fallback_to_sentence_transformers(self):
        """Test that service falls back to Sentence Transformers when no API keys"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "", "GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=True):
            with patch("apps.api.embedding_service.GEMINI_AVAILABLE", False):
                with patch("apps.api.embedding_service.OPENAI_AVAILABLE", False):
                    from importlib import reload
                    import apps.api.embedding_service as embed_module
                    reload(embed_module)

                    service = embed_module.EmbeddingService()

                    # Should be using sentence transformers fallback model
                    assert service.model_name == "all-mpnet-base-v2"
                    assert service.model_config["provider"] == "local"

    @pytest.mark.unit
    def test_target_dimensions_constant(self):
        """Test that TARGET_DIMENSIONS is always 1536"""
        from apps.api.embedding_service import EmbeddingService

        assert EmbeddingService.TARGET_DIMENSIONS == 1536

    @pytest.mark.asyncio
    async def test_generate_dummy_embedding_returns_correct_dimensions(self):
        """Test that dummy embedding returns correct dimensions"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "", "GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=True):
            with patch("apps.api.embedding_service.GEMINI_AVAILABLE", False):
                with patch("apps.api.embedding_service.OPENAI_AVAILABLE", False):
                    from importlib import reload
                    import apps.api.embedding_service as embed_module
                    reload(embed_module)

                    service = embed_module.EmbeddingService()
                    result = await service._generate_dummy_embedding("test text")

                    assert isinstance(result, list)
                    assert len(result) == 1536
                    assert all(isinstance(x, float) for x in result)


class TestSimilarityCalculation:
    """Test cases for similarity calculation"""

    @pytest.mark.unit
    def test_calculate_similarity_identical_vectors(self):
        """Test similarity calculation for identical vectors"""
        from apps.api.embedding_service import EmbeddingService

        service = EmbeddingService()
        vec = [1.0, 0.0, 0.0]

        similarity = service.calculate_similarity(vec, vec)

        assert similarity == pytest.approx(1.0, abs=0.01)

    @pytest.mark.unit
    def test_calculate_similarity_orthogonal_vectors(self):
        """Test similarity calculation for orthogonal vectors"""
        from apps.api.embedding_service import EmbeddingService

        service = EmbeddingService()
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]

        similarity = service.calculate_similarity(vec1, vec2)

        assert similarity == pytest.approx(0.0, abs=0.01)

    @pytest.mark.unit
    def test_calculate_similarity_empty_vector(self):
        """Test similarity calculation handles zero vectors gracefully"""
        from apps.api.embedding_service import EmbeddingService

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
        from apps.api.embedding_service import EmbeddingService

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
        from apps.api.embedding_service import EmbeddingService

        service = EmbeddingService()
        text = "test text for caching"

        key1 = service._get_cache_key(text)
        key2 = service._get_cache_key(text)

        assert key1 == key2

    @pytest.mark.unit
    def test_get_cache_key_different_for_different_text(self):
        """Test that different text produces different cache keys"""
        from apps.api.embedding_service import EmbeddingService

        service = EmbeddingService()

        key1 = service._get_cache_key("text one")
        key2 = service._get_cache_key("text two")

        assert key1 != key2
