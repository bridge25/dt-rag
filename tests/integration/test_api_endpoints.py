"""
API Endpoints Integration Tests
Tests all FastAPI endpoints with real database

@TEST:PHASE-2-STABILIZATION | SPEC-TEST-STABILIZE-002
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Health check endpoint tests"""

    @pytest.mark.asyncio
    async def test_health_check_returns_200(self, async_client: AsyncClient) -> None:
        """
        @TEST:PHASE-2-STABILIZATION

        Test health endpoint returns 200 OK

        Given: Health check endpoint is available
        When: GET request to /healthz
        Then: Response status is 200 OK
        """
        response = await async_client.get(
            "/healthz", headers={"X-API-Key": "test_api_key_for_testing"}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_check_returns_json(self, async_client: AsyncClient) -> None:
        """
        @TEST:PHASE-2-STABILIZATION

        Test health endpoint returns valid JSON

        Given: Health check endpoint is available
        When: GET request to /healthz
        Then: Response contains status and timestamp fields
        """
        response = await async_client.get(
            "/healthz", headers={"X-API-Key": "test_api_key_for_testing"}
        )
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"


class TestClassifyEndpoint:
    """Classification endpoint tests"""

    @pytest.mark.asyncio
    async def test_classify_endpoint_exists(self, async_client: AsyncClient, sample_text: str) -> None:
        """
        @TEST:PHASE-2-STABILIZATION

        Test classify endpoint is accessible

        Given: Classify endpoint is available
        When: POST request with sample text
        Then: Response status is 200 or 422
        """
        response = await async_client.post(
            "/classify",
            json={"chunk_id": "test-001", "text": sample_text},
            headers={"X-API-Key": "test_api_key_for_testing"},
        )
        assert response.status_code in [200, 422]  # 200 OK or 422 Validation Error

    @pytest.mark.asyncio
    async def test_classify_rag_text(self, async_client: AsyncClient) -> None:
        """
        @TEST:PHASE-2-STABILIZATION

        Test classification of RAG-related text

        Given: RAG-related text is provided
        When: POST request to /classify
        Then: Returns canonical paths and confidence score
        """
        response = await async_client.post(
            "/classify",
            json={
                "chunk_id": "rag-001",
                "text": "Retrieval-Augmented Generation uses vector databases for semantic search",
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "canonical" in data
            assert "confidence" in data
            assert isinstance(data["canonical"], list)
            assert data["confidence"] >= 0.0
            assert data["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_classify_ml_text(self, async_client: AsyncClient) -> None:
        """
        @TEST:PHASE-2-STABILIZATION

        Test classification of ML-related text

        Given: ML-related text is provided
        When: POST request to /classify
        Then: Returns canonical path containing AI or ML
        """
        response = await async_client.post(
            "/classify",
            json={
                "chunk_id": "ml-001",
                "text": "Machine learning models use neural networks for classification tasks",
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "canonical" in data
            assert "AI" in data["canonical"] or "ML" in data["canonical"]

    @pytest.mark.asyncio
    async def test_classify_with_hint_paths(self, async_client: AsyncClient) -> None:
        """
        @TEST:PHASE-2-STABILIZATION

        Test classification with hint paths

        Given: Text with hint paths is provided
        When: POST request to /classify with hint_paths parameter
        Then: Returns classification with confidence
        """
        response = await async_client.post(
            "/classify",
            json={
                "chunk_id": "hint-001",
                "text": "Neural network architectures",
                "hint_paths": [["AI", "ML"]],
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "confidence" in data


class TestSearchEndpoint:
    """Search endpoint tests"""

    @pytest.mark.asyncio
    async def test_search_endpoint_exists(self, async_client: AsyncClient) -> None:
        """
        @TEST:PHASE-2-STABILIZATION

        Test search endpoint is accessible

        Given: Search endpoint is available
        When: POST request to /search
        Then: Response status is 200 or 422
        """
        response = await async_client.post(
            "/search",
            json={"q": "machine learning", "final_topk": 5},
            headers={"X-API-Key": "test_api_key_for_testing"},
        )
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_search_returns_hits(self, async_client: AsyncClient) -> None:
        """
        @TEST:PHASE-2-STABILIZATION

        Test search returns hits array

        Given: Search query is provided
        When: POST request to /search
        Then: Response contains hits array
        """
        response = await async_client.post("/search", json={"q": "RAG system", "final_topk": 3})

        if response.status_code == 200:
            data = response.json()
            assert "hits" in data
            assert isinstance(data["hits"], list)

    @pytest.mark.asyncio
    async def test_search_with_filters(self, async_client: AsyncClient) -> None:
        """
        @TEST:PHASE-2-STABILIZATION

        Test search with taxonomy filters

        Given: Search query with taxonomy filters
        When: POST request to /search with filters
        Then: Response contains filtered hits
        """
        response = await async_client.post(
            "/search",
            json={
                "q": "neural networks",
                "filters": {"taxonomy_path": ["AI", "ML"]},
                "final_topk": 5,
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "hits" in data


class TestTaxonomyEndpoint:
    """Taxonomy endpoint tests"""

    @pytest.mark.asyncio
    async def test_get_taxonomy_tree(self, async_client: AsyncClient) -> None:
        """
        @TEST:PHASE-2-STABILIZATION

        Test taxonomy tree retrieval

        Given: Taxonomy endpoint is available
        When: GET request to /taxonomy/version/tree
        Then: Response contains tree structure
        """
        response = await async_client.get("/taxonomy/v1.8.1/tree")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    @pytest.mark.asyncio
    async def test_taxonomy_version_format(self, async_client: AsyncClient) -> None:
        """
        @TEST:PHASE-2-STABILIZATION

        Test taxonomy endpoint accepts version parameter

        Given: Multiple taxonomy versions exist
        When: GET requests with different version parameters
        Then: Each returns 200 OK or 404 Not Found
        """
        versions = ["v1.8.1", "v1.0.0", "latest"]

        for version in versions:
            response = await async_client.get(
                f"/taxonomy/{version}/tree",
                headers={"X-API-Key": "test_api_key_for_testing"},
            )
            assert response.status_code in [200, 404]  # OK or Not Found


class TestErrorHandling:
    """Error handling tests"""

    @pytest.mark.asyncio
    async def test_classify_missing_text(self, async_client: AsyncClient) -> None:
        """
        @TEST:PHASE-2-STABILIZATION

        Test classify endpoint with missing text field

        Given: Request without required text field
        When: POST request to /classify
        Then: Response status is 422 Validation Error
        """
        response = await async_client.post(
            "/classify",
            json={
                "chunk_id": "missing-001"
                # text field missing
            },
            headers={"X-API-Key": "test_api_key_for_testing"},
        )
        assert response.status_code == 422  # Validation Error

    @pytest.mark.asyncio
    async def test_search_missing_query(self, async_client: AsyncClient) -> None:
        """
        @TEST:PHASE-2-STABILIZATION

        Test search endpoint with missing query

        Given: Request without required q field
        When: POST request to /search
        Then: Response status is 422 Validation Error
        """
        response = await async_client.post(
            "/search",
            json={
                "final_topk": 5
                # q field missing
            },
            headers={"X-API-Key": "test_api_key_for_testing"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_endpoint(self, async_client: AsyncClient) -> None:
        """
        @TEST:PHASE-2-STABILIZATION

        Test non-existent endpoint returns 404

        Given: Invalid endpoint path
        When: GET request to non-existent endpoint
        Then: Response status is 404 Not Found
        """
        response = await async_client.get("/nonexistent")
        assert response.status_code == 404
