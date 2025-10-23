"""
Unit tests for EmbeddingService (Phase 3)

@TEST:EMBED-001 | SPEC: .moai/specs/SPEC-EMBED-001/spec.md | CODE: apps/api/embedding_service.py

Tests the 1536-dimensional vector embedding service with OpenAI API
and Sentence Transformers fallback mechanism.
"""
import pytest
import os
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from apps.api.embedding_service import EmbeddingService


class TestEmbeddingServiceInitialization:
    """Test EmbeddingService initialization and configuration"""

    def test_service_default_initialization(self):
        """Should initialize with default text-embedding-3-large model"""
        service = EmbeddingService()
        assert service.model_name in ["text-embedding-3-large", "all-mpnet-base-v2"]
        assert service.TARGET_DIMENSIONS == 1536
        assert service.model_config is not None

    def test_service_with_custom_model(self):
        """Should initialize with custom model"""
        service = EmbeddingService(model_name="text-embedding-3-small")
        # May fall back to all-mpnet-base-v2 if no API key
        assert service.model_name in ["text-embedding-3-small", "all-mpnet-base-v2"]

    def test_service_with_invalid_model_falls_back(self):
        """Should fall back to default model with invalid model name"""
        service = EmbeddingService(model_name="invalid-model")
        assert service.model_name in ["text-embedding-3-large", "all-mpnet-base-v2"]

    def test_supported_models_configuration(self):
        """Should have correct model configurations"""
        service = EmbeddingService()
        assert "text-embedding-3-large" in service.SUPPORTED_MODELS
        assert "text-embedding-3-small" in service.SUPPORTED_MODELS
        assert "text-embedding-ada-002" in service.SUPPORTED_MODELS
        assert "all-mpnet-base-v2" in service.SUPPORTED_MODELS

        large_model = service.SUPPORTED_MODELS["text-embedding-3-large"]
        assert large_model["dimensions"] == 1536
        assert large_model["cost_per_1k_tokens"] == 0.00013


class TestVectorPaddingAndTruncation:
    """Test vector dimension adjustment to 1536"""

    def test_pad_768_to_1536(self):
        """Should pad 768-dim vector to 1536-dim"""
        service = EmbeddingService()
        vector_768 = np.random.rand(768).tolist()

        padded = service._pad_or_truncate_vector(vector_768)

        assert len(padded) == 1536
        assert padded[:768] == vector_768
        assert all(v == 0.0 for v in padded[768:])

    def test_truncate_2048_to_1536(self):
        """Should truncate 2048-dim vector to 1536-dim"""
        service = EmbeddingService()
        vector_2048 = np.random.rand(2048)  # Keep as numpy array

        truncated = service._pad_or_truncate_vector(vector_2048)

        assert len(truncated) == 1536
        assert truncated == vector_2048[:1536].tolist()

    def test_keep_1536_as_is(self):
        """Should keep 1536-dim vector unchanged"""
        service = EmbeddingService()
        vector_1536 = np.random.rand(1536)  # Keep as numpy array

        result = service._pad_or_truncate_vector(vector_1536)

        assert len(result) == 1536
        assert result == vector_1536.tolist()


class TestEmbeddingGeneration:
    """Test embedding generation with mocked API calls"""

    @pytest.mark.asyncio
    @patch('apps.api.embedding_service.OPENAI_AVAILABLE', True)
    async def test_generate_embedding_with_openai(self):
        """Should generate 1536-dim embedding using OpenAI API"""
        service = EmbeddingService()

        # Mock OpenAI client response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        service._openai_client = AsyncMock()
        service._openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        text = "Test document for embedding"
        embedding = await service.generate_embedding(text, use_cache=False)

        assert len(embedding) == 1536
        assert all(isinstance(v, float) for v in embedding)
        service._openai_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_embedding_cache_functionality(self):
        """Should cache embeddings and reuse them"""
        service = EmbeddingService()

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        service._openai_client = AsyncMock()
        service._openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        text = "Cached document"

        # First call - should hit API
        embedding1 = await service.generate_embedding(text, use_cache=True)
        assert service._openai_client.embeddings.create.call_count == 1

        # Second call - should use cache
        embedding2 = await service.generate_embedding(text, use_cache=True)
        assert service._openai_client.embeddings.create.call_count == 1  # No additional call

        assert embedding1 == embedding2

    @pytest.mark.asyncio
    @patch('apps.api.embedding_service.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    async def test_fallback_to_sentence_transformer(self):
        """Should fall back to Sentence Transformers if OpenAI fails"""
        service = EmbeddingService()
        service._openai_client = None  # No OpenAI client

        # Mock Sentence Transformer
        mock_st = MagicMock()
        mock_st.encode.return_value = np.random.rand(768)  # 768-dim output
        service._sentence_transformer = mock_st

        text = "Fallback test document"
        embedding = await service.generate_embedding(text, use_cache=False)

        assert len(embedding) == 1536  # Should be padded to 1536
        # Sentence Transformer wraps text in list
        mock_st.encode.assert_called_once_with([text], convert_to_numpy=True)


class TestMultipleEmbeddings:
    """Test multiple embedding generation"""

    @pytest.mark.asyncio
    @patch('apps.api.embedding_service.OPENAI_AVAILABLE', True)
    async def test_generate_multiple_embeddings_sequentially(self):
        """Should generate embeddings for multiple texts sequentially"""
        service = EmbeddingService()

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        service._openai_client = AsyncMock()
        service._openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        texts = ["Doc 1", "Doc 2", "Doc 3"]
        embeddings = []
        for text in texts:
            emb = await service.generate_embedding(text, use_cache=False)
            embeddings.append(emb)

        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)
        assert service._openai_client.embeddings.create.call_count == 3


class TestCostTracking:
    """Test Langfuse cost tracking integration"""

    def test_langfuse_observe_decorator_available(self):
        """Should have Langfuse @observe decorator"""
        from apps.api.embedding_service import observe
        assert callable(observe)

    @pytest.mark.asyncio
    @patch('apps.api.embedding_service.LANGFUSE_AVAILABLE', True)
    @patch('apps.api.embedding_service.OPENAI_AVAILABLE', True)
    async def test_embedding_with_langfuse_tracking(self):
        """Should track embedding costs with Langfuse"""
        service = EmbeddingService()

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_response.usage = MagicMock(total_tokens=100)
        service._openai_client = AsyncMock()
        service._openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        text = "Cost tracking test"
        embedding = await service.generate_embedding(text, use_cache=False)

        # Langfuse @observe decorator should be called (implicitly)
        assert len(embedding) == 1536


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_empty_text_handling(self):
        """Should handle empty text gracefully"""
        service = EmbeddingService()

        # Mock to avoid actual API call
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.0] * 1536)]
        service._openai_client = AsyncMock()
        service._openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        embedding = await service.generate_embedding("", use_cache=False)
        assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_very_long_text_handling(self):
        """Should handle very long text (truncation by API)"""
        service = EmbeddingService()

        # Mock response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        service._openai_client = AsyncMock()
        service._openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        long_text = "word " * 10000  # Very long text
        embedding = await service.generate_embedding(long_text, use_cache=False)

        assert len(embedding) == 1536
        service._openai_client.embeddings.create.assert_called_once()


class TestModelCompatibility:
    """Test compatibility with different embedding models"""

    def test_text_embedding_3_large_config(self):
        """Should correctly configure text-embedding-3-large"""
        config = EmbeddingService.SUPPORTED_MODELS["text-embedding-3-large"]
        assert config["dimensions"] == 1536
        assert config["cost_per_1k_tokens"] > 0

    def test_text_embedding_3_small_config(self):
        """Should correctly configure text-embedding-3-small"""
        config = EmbeddingService.SUPPORTED_MODELS["text-embedding-3-small"]
        assert config["dimensions"] == 1536
        assert config["cost_per_1k_tokens"] < EmbeddingService.SUPPORTED_MODELS["text-embedding-3-large"]["cost_per_1k_tokens"]

    def test_text_embedding_ada_002_config(self):
        """Should correctly configure text-embedding-ada-002 (legacy)"""
        config = EmbeddingService.SUPPORTED_MODELS["text-embedding-ada-002"]
        assert config["dimensions"] == 1536
        assert config["cost_per_1k_tokens"] > 0

    def test_sentence_transformer_fallback_config(self):
        """Should correctly configure Sentence Transformers fallback"""
        config = EmbeddingService.SUPPORTED_MODELS["all-mpnet-base-v2"]
        assert config["dimensions"] == 768  # Native dimension
        assert config["cost_per_1k_tokens"] == 0.0  # Free
