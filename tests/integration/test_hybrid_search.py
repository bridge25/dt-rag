"""
Integration tests for Hybrid Search (SPEC-NEURAL-001)

@SPEC:NEURAL-001 @TEST:NEURAL-001:0.2
Tests end-to-end hybrid search flow, feature flag integration, and fallback behavior.
"""

import pytest
import time
from typing import List, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import text


class TestHybridSearchE2E:
    """End-to-end hybrid search integration tests"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_hybrid_search_full_flow(self):
        """
        @TEST:NEURAL-001:0.2.1
        Test complete hybrid search workflow

        Given: CaseBank with 10 cases, neural_case_selector=True
        When: POST /search with use_neural=true
        Then: Hybrid scores (0.7*vector + 0.3*bm25), mode="hybrid"
        """
        from apps.api.database import async_session, CaseBank
        from apps.api.routers.search_router import search_router
        from fastapi import FastAPI

        # Setup test data
        async with async_session() as session:
            # Create test cases in CaseBank
            test_cases = [
                CaseBank(
                    case_id=f"test_case_{i}",
                    query=f"Test query {i}",
                    answer=f"Test response {i}",  # Fixed: response_text → answer
                    category_path=["AI", "Test"],
                    query_vector=[0.1 * i] * 1536,
                    quality_score=0.8,
                    usage_count=10,
                    success_rate=0.9,
                )
                for i in range(1, 11)
            ]

            for case in test_cases:
                session.add(case)

            await session.commit()

        # Setup test client
        app = FastAPI()
        app.include_router(search_router)
        client = TestClient(app)

        # Execute hybrid search
        response = client.post(
            "/search",
            json={
                "q": "test query neural search",
                "max_results": 5,
                "use_neural": True,
            },
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["mode"] == "hybrid"
        assert len(data["results"]) <= 5
        assert data["latency"] < 0.2  # 200ms total

        # Verify hybrid scores
        for result in data["results"]:
            assert "score" in result
            assert "metadata" in result
            assert result["metadata"].get("mode") == "hybrid"

        # Cleanup
        async with async_session() as session:
            await session.execute(
                text("DELETE FROM case_bank WHERE case_id LIKE 'test_case_%'")
            )
            await session.commit()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_vector_search_timeout_fallback(self):
        """
        @TEST:NEURAL-001:0.2.2
        Test vector search timeout with BM25 fallback

        Given: Vector search configured with 100ms timeout
        When: Vector search exceeds timeout
        Then: Fallback to BM25, mode="bm25_fallback", warning logged
        """
        from apps.api.routers.search_router import search_router
        from fastapi import FastAPI
        from unittest.mock import patch, AsyncMock
        import asyncio

        app = FastAPI()
        app.include_router(search_router)
        client = TestClient(app)

        # Mock vector search to timeout
        async def timeout_vector_search(*args, **kwargs):
            await asyncio.sleep(0.15)  # Exceeds 100ms
            raise asyncio.TimeoutError("Vector search timeout")

        with patch(
            "apps.api.neural_selector.vector_similarity_search",
            side_effect=timeout_vector_search,
        ):
            response = client.post(
                "/search",
                json={"q": "test query", "max_results": 5, "use_neural": True},
            )

            # Should fallback to BM25
            assert response.status_code == 200
            data = response.json()

            assert data["mode"] == "bm25_fallback"
            assert len(data["results"]) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_embedding_generation_failure_fallback(self):
        """
        @TEST:NEURAL-001:0.2.3
        Test embedding generation failure with BM25 fallback

        Given: OpenAI API fails or returns error
        When: Embedding generation raises exception
        Then: Fallback to BM25, mode="bm25_fallback", warning logged
        """
        from apps.api.routers.search_router import search_router
        from fastapi import FastAPI
        from unittest.mock import patch

        app = FastAPI()
        app.include_router(search_router)
        client = TestClient(app)

        # Mock embedding generation to fail
        with patch(
            "apps.api.database.EmbeddingService.generate_embedding",
            side_effect=Exception("API Error"),
        ):
            response = client.post(
                "/search",
                json={"q": "test query", "max_results": 5, "use_neural": True},
            )

            # Should fallback to BM25
            assert response.status_code == 200
            data = response.json()

            assert data["mode"] == "bm25_fallback"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_feature_flag_off_bm25_only(self):
        """
        @TEST:NEURAL-001:0.2.4
        Test search behavior when feature flag is OFF

        Given: neural_case_selector=False
        When: POST /search
        Then: BM25 search only, mode="bm25"
        """
        from apps.api.routers.search_router import search_router
        from fastapi import FastAPI
        import os

        # Ensure flag is OFF
        if "FEATURE_NEURAL_CASE_SELECTOR" in os.environ:
            del os.environ["FEATURE_NEURAL_CASE_SELECTOR"]

        app = FastAPI()
        app.include_router(search_router)
        client = TestClient(app)

        response = client.post(
            "/search",
            json={
                "q": "test query",
                "max_results": 5,
                "use_neural": False,  # Explicit BM25 request
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["mode"] == "bm25"

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_performance_vector_search_latency(self):
        """
        @TEST:NEURAL-001:0.2.5
        Test vector search performance meets < 100ms requirement

        Given: CaseBank with 1000 cases
        When: Vector search is executed
        Then: Latency < 100ms
        """
        from apps.api.neural_selector import vector_similarity_search
        from apps.api.database import async_session

        query_embedding = [0.1] * 1536

        start_time = time.time()

        async with async_session() as session:
            results = await vector_similarity_search(
                session, query_embedding, limit=10, timeout=0.1
            )

        latency = time.time() - start_time

        # Verify performance requirement
        assert latency < 0.1  # 100ms

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_hybrid_score_ranking(self):
        """
        @TEST:NEURAL-001:0.2.6
        Test hybrid score ranking order

        Given: Cases with varying vector and BM25 scores
        When: Hybrid search is executed
        Then: Results sorted by hybrid score (descending)
        """
        from apps.api.routers.search_router import search_router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(search_router)
        client = TestClient(app)

        response = client.post(
            "/search",
            json={
                "q": "machine learning neural networks",
                "max_results": 10,
                "use_neural": True,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify descending score order
        scores = [result["score"] for result in data["results"]]
        assert scores == sorted(scores, reverse=True)


class TestSearchRequestModel:
    """Test SearchRequest model extension for Neural search"""

    @pytest.mark.integration
    def test_search_request_use_neural_field(self):
        """
        @TEST:NEURAL-001:0.2.7
        Test SearchRequest model has use_neural field

        Given: SearchRequest model
        When: Initialize with use_neural=True
        Then: Field is set correctly
        """
        from packages.common_schemas.common_schemas.models import SearchRequest

        request = SearchRequest(q="test query", max_results=10, use_neural=True)

        assert hasattr(request, "use_neural")
        assert request.use_neural == True

    @pytest.mark.integration
    def test_search_request_use_neural_default(self):
        """
        @TEST:NEURAL-001:0.2.8
        Test SearchRequest use_neural defaults to False

        Given: SearchRequest without use_neural
        When: Initialize request
        Then: use_neural defaults to False
        """
        from packages.common_schemas.common_schemas.models import SearchRequest

        request = SearchRequest(q="test query", max_results=10)

        # Should default to False (BM25 only)
        assert request.use_neural == False


class TestSearchResponseModel:
    """Test SearchResponse model extension for mode field"""

    @pytest.mark.integration
    def test_search_response_mode_field(self):
        """
        @TEST:NEURAL-001:0.2.9
        Test SearchResponse includes mode field

        Given: SearchResponse model
        When: Response is created
        Then: mode field indicates search type (neural/bm25/hybrid)
        """
        from packages.common_schemas.common_schemas.models import SearchResponse

        response = SearchResponse(
            hits=[],
            latency=0.05,
            request_id="test-id",
            total_candidates=100,
            sources_count=10,
            taxonomy_version="1.8.1",
            mode="hybrid",
        )

        assert hasattr(response, "mode")
        assert response.mode == "hybrid"
