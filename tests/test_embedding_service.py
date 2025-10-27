"""
Unit tests for EmbeddingService - SPEC-ENV-VALIDATE-001 Phase 3-4

Tests health check expansion and 401 error handling in embedding service.
"""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock


class TestHealthCheckExpansion:
    """Test cases for health_check() expansion - SPEC-ENV-VALIDATE-001 Phase 3"""

    @pytest.mark.unit
    def test_health_check_with_api_key_configured(self):
        """Test health_check() returns api_key_configured=True when OpenAI key is valid"""
        valid_key = "sk-" + "a" * 48

        with patch.dict(os.environ, {"OPENAI_API_KEY": valid_key}):
            with patch("apps.api.embedding_service.AsyncOpenAI"):
                from apps.api.embedding_service import EmbeddingService

                service = EmbeddingService()
                result = service.health_check()

                assert "api_key_configured" in result
                assert result["api_key_configured"] is True
                assert result.get("fallback_mode", False) is False

    @pytest.mark.unit
    def test_health_check_without_api_key(self):
        """Test health_check() returns api_key_configured=False with warning when key is missing"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
            from apps.api.embedding_service import EmbeddingService

            service = EmbeddingService()
            result = service.health_check()

            assert "api_key_configured" in result
            assert result["api_key_configured"] is False
            assert result.get("fallback_mode") is True
            assert "warning" in result
            assert "OPENAI_API_KEY" in result["warning"]

    @pytest.mark.unit
    def test_health_check_with_invalid_api_key(self):
        """Test health_check() detects invalid API key format"""
        invalid_key = "invalid-key-format"

        with patch.dict(os.environ, {"OPENAI_API_KEY": invalid_key}):
            from apps.api.embedding_service import EmbeddingService

            service = EmbeddingService()
            result = service.health_check()

            assert "api_key_configured" in result
            assert "warning" in result
            assert "invalid" in result["warning"].lower() or "format" in result["warning"].lower()

    @pytest.mark.unit
    def test_health_check_degraded_mode(self):
        """Test health_check() returns degraded status when using Sentence Transformers fallback"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
            with patch("apps.api.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE", True):
                from apps.api.embedding_service import EmbeddingService

                service = EmbeddingService()
                service._sentence_transformer = MagicMock()
                result = service.health_check()

                assert result["status"] == "degraded"
                assert result["fallback_mode"] is True

    @pytest.mark.unit
    def test_health_check_response_structure(self):
        """Test health_check() returns all required fields"""
        valid_key = "sk-" + "b" * 48

        with patch.dict(os.environ, {"OPENAI_API_KEY": valid_key}):
            with patch("apps.api.embedding_service.AsyncOpenAI"):
                from apps.api.embedding_service import EmbeddingService

                service = EmbeddingService()
                result = service.health_check()

                required_fields = ["status", "model_name", "target_dimensions", "api_key_configured"]
                for field in required_fields:
                    assert field in result, f"Missing required field: {field}"


class Test401ErrorHandling:
    """Test cases for 401 error explicit logging - SPEC-ENV-VALIDATE-001 Phase 4"""

    @pytest.mark.asyncio
    async def test_401_error_explicit_logging(self):
        """Test that 401 error from OpenAI triggers explicit ERROR level logging"""
        invalid_key = "sk-" + "c" * 48

        with patch.dict(os.environ, {"OPENAI_API_KEY": invalid_key}):
            with patch("apps.api.embedding_service.AsyncOpenAI") as mock_openai:
                mock_client = AsyncMock()
                mock_openai.return_value = mock_client

                from openai import AuthenticationError
                mock_client.embeddings.create.side_effect = AuthenticationError(
                    message="Incorrect API key provided",
                    response=MagicMock(status_code=401),
                    body=None
                )

                with patch("apps.api.embedding_service.logger") as mock_logger:
                    from apps.api.embedding_service import EmbeddingService

                    service = EmbeddingService()
                    result = await service.generate_embedding("test text")

                    mock_logger.error.assert_any_call(
                        "OpenAI API authentication failed (401): Invalid API key. "
                        "Please check OPENAI_API_KEY environment variable."
                    )

                    assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_401_error_fallback_behavior(self):
        """Test that service falls back to dummy embeddings after 401 error"""
        invalid_key = "sk-" + "d" * 48

        with patch.dict(os.environ, {"OPENAI_API_KEY": invalid_key}):
            with patch("apps.api.embedding_service.AsyncOpenAI") as mock_openai:
                mock_client = AsyncMock()
                mock_openai.return_value = mock_client

                from openai import AuthenticationError
                mock_client.embeddings.create.side_effect = AuthenticationError(
                    message="Incorrect API key provided",
                    response=MagicMock(status_code=401),
                    body=None
                )

                from apps.api.embedding_service import EmbeddingService

                service = EmbeddingService()
                result = await service.generate_embedding("test text")

                assert len(result) == 1536
                assert all(isinstance(x, float) for x in result)
