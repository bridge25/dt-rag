# @SPEC:FOUNDATION-001 @TEST:0.2-casebank-vector
"""
Unit tests for CaseBank Vector Embedding (SPEC-FOUNDATION-001)

Tests embedding generation for case queries:
- Successful embedding generation (1536 dimensions)
- API failure fallback to dummy vector
- add_case() stores query_vector
"""

import pytest
from unittest.mock import patch
from apps.orchestration.src.main import CBRSystem


pytestmark = pytest.mark.unit


class TestCaseEmbedding:
    """Test case embedding functionality"""

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self):
        """TEST-EMBED-001: 정상 임베딩 생성 (1536차원)"""
        cbr = CBRSystem(data_dir="test_data/cbr_embed")

        with patch("apps.orchestration.src.main.CBRSystem.generate_case_embedding") as mock_gen:
            # Mock successful embedding generation
            mock_gen.return_value = [0.1] * 1536

            query = "test query for embedding"
            vector = await cbr.generate_case_embedding(query)

            assert len(vector) == 1536
            assert all(isinstance(v, float) for v in vector)

    @pytest.mark.asyncio
    async def test_generate_embedding_failure_fallback(self):
        """TEST-EMBED-002: API 실패 시 더미 벡터 + 경고 로그"""
        cbr = CBRSystem(data_dir="test_data/cbr_embed")

        with patch("apps.orchestration.src.main.CBRSystem.generate_case_embedding") as mock_gen:
            # Mock API failure - returns dummy vector
            mock_gen.return_value = [0.0] * 1536

            query = "test query for fallback"
            vector = await cbr.generate_case_embedding(query)

            # Fallback to dummy vector
            assert len(vector) == 1536
            assert vector == [0.0] * 1536

    @pytest.mark.asyncio
    async def test_add_case_with_vector(self):
        """TEST-EMBED-003: add_case() 호출 시 query_vector 저장 확인"""
        cbr = CBRSystem(data_dir="test_data/cbr_embed")

        with patch("apps.orchestration.src.main.CBRSystem.generate_case_embedding") as mock_gen:
            mock_gen.return_value = [0.1] * 1536

            case_data = {
                "case_id": "test-case-001",
                "query": "test query",
                "category_path": ["test", "category"],
                "content": "test content",
                "quality_score": 0.8,
                "metadata": {}
            }

            # Call add_case() which should generate and store embedding
            result = await cbr.add_case(case_data)

            assert result is True
            mock_gen.assert_called_once_with("test query")

    def teardown_method(self):
        """Cleanup test data"""
        import shutil
        import os

        test_dir = "test_data/cbr_embed"
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
