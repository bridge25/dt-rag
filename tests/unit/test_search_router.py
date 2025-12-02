"""
Unit tests for search router module (apps.api.routers.search_router)

This test module provides comprehensive coverage for search API endpoints
including request validation, response formatting, and error handling.

@TEST:SEARCH-001
"""

import pytest
import uuid
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, status
from datetime import datetime

# Import the modules under test
from apps.api.routers.search_router import (
    search_router,
    ProductionSearchHandler,
    SearchAnalytics,
    SearchConfig,
    ReindexRequest,
    get_search_handler,
)
# Alias for backward compatibility with test naming
SearchService = ProductionSearchHandler
get_search_service = get_search_handler

# Import common schemas
import sys
from pathlib import Path as PathLib

# Add packages directory to Python path
project_root = PathLib(__file__).parent.parent.parent
packages_path = project_root / "packages"
if str(packages_path) not in sys.path:
    sys.path.insert(0, str(packages_path))

try:
    # Try importing from packages directory in sys.path
    from common_schemas.common_schemas.models import (
        SearchRequest,
        SearchResponse,
        SearchHit,
        SourceMeta,
    )
except ImportError:
    try:
        # Try with direct packages path
        sys.path.insert(0, str(project_root / "packages"))
        from common_schemas.common_schemas.models import (  # type: ignore[import-not-found]
            SearchRequest,
            SearchResponse,
            SearchHit,
            SourceMeta,
        )
    except ImportError:
        # Final fallback: direct path import
        sys.path.insert(0, str(project_root))
        from packages.common_schemas.common_schemas.models import (
            SearchRequest,
            SearchResponse,
            SearchHit,
            SourceMeta,
        )


class TestSearchService:
    """Test cases for SearchService class"""

    @pytest.fixture
    def search_service(self):
        """Create SearchService instance for testing"""
        return SearchService()

    @pytest.mark.unit
    async def test_search_basic(self, search_service):
        """Test basic search functionality"""
        request = SearchRequest(
            q="machine learning", max_results=10, canonical_in=[["Technology", "AI"]]
        )

        response = await search_service.search(request)

        assert isinstance(response, SearchResponse)
        assert len(response.hits) > 0
        assert response.latency > 0
        assert response.request_id is not None
        assert response.total_candidates > 0
        assert response.taxonomy_version == "1.8.1"

        # Check that hits have required fields
        for hit in response.hits:
            assert isinstance(hit, SearchHit)
            assert hit.chunk_id is not None
            assert hit.score > 0
            assert hit.text is not None
            assert isinstance(hit.source, SourceMeta)
            assert isinstance(hit.taxonomy_path, list)

    @pytest.mark.unit
    async def test_search_hit_structure(self, search_service):
        """Test search hit structure and content"""
        request = SearchRequest(q="test query")
        response = await search_service.search(request)

        hit = response.hits[0]
        assert hit.chunk_id == "doc123_chunk456"
        assert hit.score == 0.89
        assert "Machine learning algorithms" in hit.text
        assert hit.source.url == "https://example.com/ml-guide"
        assert hit.source.title == "Machine Learning Guide"
        assert hit.source.date == "2024-01-15"
        assert hit.taxonomy_path == ["Technology", "AI", "Machine Learning"]

    @pytest.mark.unit
    async def test_get_analytics(self, search_service):
        """Test getting search analytics"""
        analytics = await search_service.get_analytics()

        assert isinstance(analytics, SearchAnalytics)
        assert analytics.total_searches == 15420
        assert analytics.avg_latency_ms == 45.2
        assert analytics.avg_results_count == 8.3
        assert len(analytics.top_queries) == 3
        assert analytics.top_queries[0]["query"] == "machine learning algorithms"
        assert analytics.top_queries[0]["count"] == 234
        assert "Technology" in analytics.search_patterns
        assert analytics.search_patterns["Technology"] == 45

    @pytest.mark.unit
    async def test_get_config(self, search_service):
        """Test getting search configuration"""
        config = await search_service.get_config()

        assert isinstance(config, SearchConfig)
        assert config.bm25_weight == 0.5
        assert config.vector_weight == 0.5
        assert config.rerank_threshold == 0.7
        assert config.max_candidates == 100
        assert config.embedding_model == "text-embedding-ada-002"

    @pytest.mark.unit
    async def test_update_config(self, search_service):
        """Test updating search configuration"""
        new_config = SearchConfig(
            bm25_weight=0.6,
            vector_weight=0.4,
            rerank_threshold=0.8,
            max_candidates=150,
            embedding_model="text-embedding-3-small",
        )

        updated_config = await search_service.update_config(new_config)

        assert updated_config == new_config
        assert updated_config.bm25_weight == 0.6
        assert updated_config.vector_weight == 0.4
        assert updated_config.embedding_model == "text-embedding-3-small"

    @pytest.mark.unit
    async def test_reindex_incremental(self, search_service):
        """Test incremental reindex operation"""
        request = ReindexRequest(
            taxonomy_version="1.8.1", incremental=True, force=False
        )

        result = await search_service.reindex(request)

        assert "job_id" in result
        assert result["status"] == "started"
        assert result["estimated_duration_minutes"] == 15
        assert result["incremental"] is True
        # Verify job_id is a valid UUID
        uuid.UUID(result["job_id"])  # Will raise if invalid

    @pytest.mark.unit
    async def test_reindex_full(self, search_service):
        """Test full reindex operation"""
        request = ReindexRequest(incremental=False, force=True)

        result = await search_service.reindex(request)

        assert "job_id" in result
        assert result["status"] == "started"
        assert result["incremental"] is False

    @pytest.mark.unit
    async def test_reindex_default_params(self, search_service):
        """Test reindex with default parameters"""
        request = ReindexRequest()

        result = await search_service.reindex(request)

        assert result["incremental"] is False  # Default value
        assert "job_id" in result


class TestSearchConfig:
    """Test cases for SearchConfig model"""

    @pytest.mark.unit
    def test_search_config_defaults(self):
        """Test SearchConfig default values"""
        config = SearchConfig()

        assert config.bm25_weight == 0.5
        assert config.vector_weight == 0.5
        assert config.rerank_threshold == 0.7
        assert config.max_candidates == 100
        assert config.embedding_model == "text-embedding-ada-002"

    @pytest.mark.unit
    def test_search_config_validation_valid(self):
        """Test SearchConfig validation with valid values"""
        config = SearchConfig(
            bm25_weight=0.3, vector_weight=0.7, rerank_threshold=0.9, max_candidates=200
        )

        assert config.bm25_weight == 0.3
        assert config.vector_weight == 0.7
        assert config.rerank_threshold == 0.9
        assert config.max_candidates == 200

    @pytest.mark.unit
    def test_search_config_validation_invalid_weight(self):
        """Test SearchConfig validation with invalid weight values"""
        with pytest.raises(ValueError):
            SearchConfig(bm25_weight=-0.1)

        with pytest.raises(ValueError):
            SearchConfig(bm25_weight=1.1)

        with pytest.raises(ValueError):
            SearchConfig(vector_weight=-0.5)

        with pytest.raises(ValueError):
            SearchConfig(vector_weight=1.5)

    @pytest.mark.unit
    def test_search_config_validation_invalid_threshold(self):
        """Test SearchConfig validation with invalid threshold values"""
        with pytest.raises(ValueError):
            SearchConfig(rerank_threshold=-0.1)

        with pytest.raises(ValueError):
            SearchConfig(rerank_threshold=1.1)

    @pytest.mark.unit
    def test_search_config_validation_invalid_candidates(self):
        """Test SearchConfig validation with invalid candidate values"""
        with pytest.raises(ValueError):
            SearchConfig(max_candidates=5)  # Below minimum

        with pytest.raises(ValueError):
            SearchConfig(max_candidates=600)  # Above maximum


class TestReindexRequest:
    """Test cases for ReindexRequest model"""

    @pytest.mark.unit
    def test_reindex_request_defaults(self):
        """Test ReindexRequest default values"""
        request = ReindexRequest()

        assert request.taxonomy_version is None
        assert request.incremental is False
        assert request.force is False

    @pytest.mark.unit
    def test_reindex_request_with_values(self):
        """Test ReindexRequest with explicit values"""
        request = ReindexRequest(taxonomy_version="1.8.2", incremental=True, force=True)

        assert request.taxonomy_version == "1.8.2"
        assert request.incremental is True
        assert request.force is True


class TestSearchRouterEndpoints:
    """Test cases for search router API endpoints"""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with search router for testing"""
        app = FastAPI()
        app.include_router(search_router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_search_service(self):
        """Create mock search service"""
        service = AsyncMock(spec=SearchService)
        return service

    @pytest.mark.unit
    def test_search_documents_success(self, client):
        """Test successful search request"""
        request_data = {
            "q": "machine learning algorithms",
            "max_results": 10,
            "canonical_in": [["Technology", "AI"]],
        }

        response = client.post("/search/", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "hits" in data
        assert "latency" in data
        assert "request_id" in data
        assert len(data["hits"]) > 0

        # Check response headers
        assert "X-Search-Latency" in response.headers
        assert "X-Request-ID" in response.headers
        assert "X-Total-Candidates" in response.headers

    @pytest.mark.unit
    def test_search_documents_empty_query(self, client):
        """Test search with empty query"""
        request_data = {"q": "", "max_results": 10}

        response = client.post("/search/", json=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Search query cannot be empty" in response.json()["detail"]

    @pytest.mark.unit
    def test_search_documents_whitespace_query(self, client):
        """Test search with whitespace-only query"""
        request_data = {"q": "   ", "max_results": 10}

        response = client.post("/search/", json=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Search query cannot be empty" in response.json()["detail"]

    @pytest.mark.unit
    def test_search_documents_max_results_exceeded(self, client):
        """Test search with max results exceeded"""
        request_data = {"q": "test query", "max_results": 150}  # Exceeds limit of 100

        response = client.post("/search/", json=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Maximum results limit is 100" in response.json()["detail"]

    @pytest.mark.unit
    def test_search_documents_minimal_request(self, client):
        """Test search with minimal valid request"""
        request_data = {"q": "test"}

        response = client.post("/search/", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "hits" in data
        assert "latency" in data

    @pytest.mark.unit
    def test_search_documents_with_all_parameters(self, client):
        """Test search with all available parameters"""
        request_data = {
            "q": "machine learning deep neural networks",
            "max_results": 20,
            "canonical_in": [
                ["Technology", "AI", "Machine Learning"],
                ["Science", "Computer Science"],
            ],
        }

        response = client.post("/search/", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["hits"]) > 0

    @pytest.mark.unit
    def test_get_search_analytics_success(self, client):
        """Test getting search analytics successfully"""
        response = client.get("/search/analytics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_searches" in data
        assert "avg_latency_ms" in data
        assert "avg_results_count" in data
        assert "top_queries" in data
        assert "search_patterns" in data
        assert data["total_searches"] == 15420
        assert len(data["top_queries"]) == 3

    @pytest.mark.unit
    def test_get_search_config_success(self, client):
        """Test getting search configuration successfully"""
        response = client.get("/search/config")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "bm25_weight" in data
        assert "vector_weight" in data
        assert "rerank_threshold" in data
        assert "max_candidates" in data
        assert "embedding_model" in data
        assert data["bm25_weight"] == 0.5
        assert data["vector_weight"] == 0.5

    @pytest.mark.unit
    def test_update_search_config_success(self, client):
        """Test updating search configuration successfully"""
        config_data = {
            "bm25_weight": 0.6,
            "vector_weight": 0.4,
            "rerank_threshold": 0.8,
            "max_candidates": 150,
            "embedding_model": "text-embedding-3-large",
        }

        response = client.put("/search/config", json=config_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["bm25_weight"] == 0.6
        assert data["vector_weight"] == 0.4
        assert data["rerank_threshold"] == 0.8
        assert data["embedding_model"] == "text-embedding-3-large"

    @pytest.mark.unit
    def test_update_search_config_invalid_weights(self, client):
        """Test updating search configuration with invalid weights"""
        config_data = {"bm25_weight": 1.5, "vector_weight": 0.4}  # Invalid: > 1.0

        response = client.put("/search/config", json=config_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.unit
    def test_trigger_reindex_incremental(self, client):
        """Test triggering incremental reindex"""
        request_data = {
            "taxonomy_version": "1.8.2",
            "incremental": True,
            "force": False,
        }

        response = client.post("/search/reindex", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "started"
        assert data["incremental"] is True
        assert isinstance(data["estimated_duration_minutes"], int)

    @pytest.mark.unit
    def test_trigger_reindex_full(self, client):
        """Test triggering full reindex"""
        request_data = {"incremental": False, "force": True}

        response = client.post("/search/reindex", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["incremental"] is False
        uuid.UUID(data["job_id"])  # Validate UUID format

    @pytest.mark.unit
    def test_trigger_reindex_default_params(self, client):
        """Test triggering reindex with default parameters"""
        response = client.post("/search/reindex", json={})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["incremental"] is False  # Default value


class TestSearchRouterWithMocks:
    """Test search router endpoints with mocked dependencies"""

    @pytest.fixture
    def app_with_mock_service(self, mock_search_service):
        """Create FastAPI app with mocked search service"""
        app = FastAPI()

        async def get_mock_search_service():
            return mock_search_service

        # Override dependency
        app.dependency_overrides[get_search_service] = get_mock_search_service
        app.include_router(search_router)
        return app

    @pytest.fixture
    def client_with_mock(self, app_with_mock_service):
        """Create test client with mocked service"""
        return TestClient(app_with_mock_service)

    @pytest.fixture
    def mock_search_service(self):
        """Create mock search service with predefined responses"""
        service = AsyncMock(spec=SearchService)

        # Mock search response
        mock_response = SearchResponse(
            hits=[
                SearchHit(
                    chunk_id="test_chunk_1",
                    score=0.95,
                    text="Test search result",
                    source=SourceMeta(
                        url="https://test.com", title="Test Document", date="2024-01-01"
                    ),
                    taxonomy_path=["Test", "Category"],
                )
            ],
            latency=0.025,
            request_id="test-request-id",
            total_candidates=25,
            sources_count=5,
            taxonomy_version="test-version",
        )
        service.search.return_value = mock_response

        # Mock analytics response
        mock_analytics = SearchAnalytics(
            total_searches=1000,
            avg_latency_ms=30.0,
            avg_results_count=7.5,
            top_queries=[{"query": "test", "count": 100}],
            search_patterns={"Test": 50},
        )
        service.get_analytics.return_value = mock_analytics

        # Mock config responses
        mock_config = SearchConfig(bm25_weight=0.7, vector_weight=0.3)
        service.get_config.return_value = mock_config
        service.update_config.return_value = mock_config

        # Mock reindex response
        mock_reindex = {
            "job_id": "test-job-id",
            "status": "started",
            "estimated_duration_minutes": 5,
            "incremental": False,
        }
        service.reindex.return_value = mock_reindex

        return service

    @pytest.mark.unit
    def test_search_with_mock_service(self, client_with_mock, mock_search_service):
        """Test search endpoint with mocked service"""
        request_data = {"q": "test query", "max_results": 5}

        response = client_with_mock.post("/search/", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["hits"][0]["chunk_id"] == "test_chunk_1"
        assert data["request_id"] == "test-request-id"

        # Verify mock was called correctly
        mock_search_service.search.assert_called_once()
        call_args = mock_search_service.search.call_args[0][0]
        assert call_args.q == "test query"
        assert call_args.max_results == 5

    @pytest.mark.unit
    def test_search_service_error_handling(self, client_with_mock, mock_search_service):
        """Test search endpoint error handling with mocked service"""
        # Configure mock to raise exception
        mock_search_service.search.side_effect = Exception("Database connection failed")

        request_data = {"q": "test query"}

        response = client_with_mock.post("/search/", json=request_data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Search operation failed" in response.json()["detail"]

    @pytest.mark.unit
    def test_analytics_with_mock_service(self, client_with_mock, mock_search_service):
        """Test analytics endpoint with mocked service"""
        response = client_with_mock.get("/search/analytics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_searches"] == 1000
        assert data["avg_latency_ms"] == 30.0
        mock_search_service.get_analytics.assert_called_once()

    @pytest.mark.unit
    def test_config_endpoints_with_mock_service(
        self, client_with_mock, mock_search_service
    ):
        """Test config endpoints with mocked service"""
        # Test GET config
        response = client_with_mock.get("/search/config")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["bm25_weight"] == 0.7

        # Test PUT config
        new_config = {"bm25_weight": 0.8, "vector_weight": 0.2}
        response = client_with_mock.put("/search/config", json=new_config)
        assert response.status_code == status.HTTP_200_OK

        # Verify mock calls
        mock_search_service.get_config.assert_called_once()
        mock_search_service.update_config.assert_called_once()

    @pytest.mark.unit
    def test_reindex_with_mock_service(self, client_with_mock, mock_search_service):
        """Test reindex endpoint with mocked service"""
        request_data = {"incremental": True}

        response = client_with_mock.post("/search/reindex", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == "test-job-id"
        assert data["status"] == "started"

        mock_search_service.reindex.assert_called_once()
        call_args = mock_search_service.reindex.call_args[0][0]
        assert call_args.incremental is True


class TestGetSearchService:
    """Test cases for dependency injection function"""

    @pytest.mark.unit
    async def test_get_search_service_returns_instance(self):
        """Test get_search_service returns SearchService instance"""
        service = await get_search_service()

        assert isinstance(service, SearchService)

    @pytest.mark.unit
    async def test_get_search_service_multiple_calls(self):
        """Test multiple calls to get_search_service return separate instances"""
        service1 = await get_search_service()
        service2 = await get_search_service()

        # Should be different instances (not singleton)
        assert service1 is not service2
        assert isinstance(service1, SearchService)
        assert isinstance(service2, SearchService)
