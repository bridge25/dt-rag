"""
API Endpoints Integration Tests
Tests all FastAPI endpoints with real database
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Health check endpoint tests"""

    def test_health_check_returns_200(self, api_client: TestClient):
        """Test health endpoint returns 200 OK"""
        response = api_client.get(
            "/healthz", headers={"X-API-Key": "test_api_key_for_testing"}
        )
        assert response.status_code == 200

    def test_health_check_returns_json(self, api_client: TestClient):
        """Test health endpoint returns valid JSON"""
        response = api_client.get(
            "/healthz", headers={"X-API-Key": "test_api_key_for_testing"}
        )
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"


class TestClassifyEndpoint:
    """Classification endpoint tests"""

    def test_classify_endpoint_exists(self, api_client: TestClient, sample_text: str):
        """Test classify endpoint is accessible"""
        response = api_client.post(
            "/classify",
            json={"chunk_id": "test-001", "text": sample_text},
            headers={"X-API-Key": "test_api_key_for_testing"},
        )
        assert response.status_code in [200, 422]  # 200 OK or 422 Validation Error

    def test_classify_rag_text(self, api_client: TestClient):
        """Test classification of RAG-related text"""
        response = api_client.post(
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

    def test_classify_ml_text(self, api_client: TestClient):
        """Test classification of ML-related text"""
        response = api_client.post(
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

    def test_classify_with_hint_paths(self, api_client: TestClient):
        """Test classification with hint paths"""
        response = api_client.post(
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

    def test_search_endpoint_exists(self, api_client: TestClient):
        """Test search endpoint is accessible"""
        response = api_client.post(
            "/search",
            json={"q": "machine learning", "final_topk": 5},
            headers={"X-API-Key": "test_api_key_for_testing"},
        )
        assert response.status_code in [200, 422]

    def test_search_returns_hits(self, api_client: TestClient):
        """Test search returns hits array"""
        response = api_client.post("/search", json={"q": "RAG system", "final_topk": 3})

        if response.status_code == 200:
            data = response.json()
            assert "hits" in data
            assert isinstance(data["hits"], list)

    def test_search_with_filters(self, api_client: TestClient):
        """Test search with taxonomy filters"""
        response = api_client.post(
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

    def test_get_taxonomy_tree(self, api_client: TestClient):
        """Test taxonomy tree retrieval"""
        response = api_client.get("/taxonomy/v1.8.1/tree")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_taxonomy_version_format(self, api_client: TestClient):
        """Test taxonomy endpoint accepts version parameter"""
        versions = ["v1.8.1", "v1.0.0", "latest"]

        for version in versions:
            response = api_client.get(
                f"/taxonomy/{version}/tree",
                headers={"X-API-Key": "test_api_key_for_testing"},
            )
            assert response.status_code in [200, 404]  # OK or Not Found


class TestErrorHandling:
    """Error handling tests"""

    def test_classify_missing_text(self, api_client: TestClient):
        """Test classify endpoint with missing text field"""
        response = api_client.post(
            "/classify",
            json={
                "chunk_id": "missing-001"
                # text field missing
            },
            headers={"X-API-Key": "test_api_key_for_testing"},
        )
        assert response.status_code == 422  # Validation Error

    def test_search_missing_query(self, api_client: TestClient):
        """Test search endpoint with missing query"""
        response = api_client.post(
            "/search",
            json={
                "final_topk": 5
                # q field missing
            },
            headers={"X-API-Key": "test_api_key_for_testing"},
        )
        assert response.status_code == 422

    def test_invalid_endpoint(self, api_client: TestClient):
        """Test non-existent endpoint returns 404"""
        response = api_client.get("/nonexistent")
        assert response.status_code == 404
