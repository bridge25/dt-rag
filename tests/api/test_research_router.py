# @TEST:RESEARCH-BACKEND-001:ROUTER
"""
Tests for Research Router - REST API Endpoints

Tests the research API endpoints including:
- POST /api/v1/research - Start research
- GET /api/v1/research/{id} - Get session status
- POST /api/v1/research/{id}/import - Import documents
- DELETE /api/v1/research/{id} - Cancel research
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.schemas.research_schemas import (
    ResearchSession,
    ResearchStage,
)
from apps.api.deps import verify_api_key
from apps.api.security.api_key_storage import APIKeyInfo


@pytest.fixture
def mock_research_service():
    """Mock ResearchService"""
    service = Mock()
    service.start_research = AsyncMock()
    service.get_session = AsyncMock()
    service.import_documents = AsyncMock()
    service.cancel_research = AsyncMock()
    return service


@pytest.fixture
def mock_api_key():
    """Mock APIKeyInfo"""
    return APIKeyInfo(
        key_id="test_key_001",
        name="Test Key",
        description="Test API Key",
        scope="write",
        permissions=["*"],
        allowed_ips=None,
        rate_limit=1000,
        is_active=True,
        expires_at=None,
        created_at=None,
        last_used_at=None,
        total_requests=0,
        failed_requests=0,
    )


def create_test_app(router, api_key):
    """Helper to create FastAPI test app with mocked dependencies"""
    app = FastAPI()

    async def mock_verify_api_key_fn():
        return api_key

    app.dependency_overrides[verify_api_key] = mock_verify_api_key_fn
    app.include_router(router)
    return TestClient(app)


class TestStartResearchEndpoint:
    """Test POST /api/v1/research endpoint"""

    @pytest.mark.asyncio
    async def test_start_research_returns_201(self, mock_research_service, mock_api_key):
        """Test successful research session creation returns 201"""
        from apps.api.routers.research_router import create_research_router

        mock_research_service.start_research.return_value = ("session_123", 30)
        router = create_research_router(mock_research_service)
        client = create_test_app(router, mock_api_key)

        request_data = {
            "query": "test research query",
            "config": {"maxDocuments": 50, "qualityThreshold": 0.7},
        }

        response = client.post(
            "/api/v1/research",
            json=request_data,
            headers={"X-API-Key": "test_key"},
        )

        assert response.status_code == 201
        data = response.json()
        assert "sessionId" in data
        assert "estimatedDuration" in data

    @pytest.mark.asyncio
    async def test_start_research_validates_query(
        self, mock_research_service, mock_api_key
    ):
        """Test that empty query is rejected"""
        from apps.api.routers.research_router import create_research_router

        router = create_research_router(mock_research_service)
        client = create_test_app(router, mock_api_key)

        request_data = {"query": "", "config": None}

        response = client.post(
            "/api/v1/research",
            json=request_data,
            headers={"X-API-Key": "test_key"},
        )

        # Pydantic validation returns 422, endpoint validation returns 400
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_start_research_rejects_short_query(
        self, mock_research_service, mock_api_key
    ):
        """Test that query shorter than MIN_QUERY_LENGTH is rejected"""
        from apps.api.routers.research_router import create_research_router

        router = create_research_router(mock_research_service)
        client = create_test_app(router, mock_api_key)

        request_data = {"query": "ab", "config": None}  # 2 chars, min is 3

        response = client.post(
            "/api/v1/research",
            json=request_data,
            headers={"X-API-Key": "test_key"},
        )

        assert response.status_code == 400
        assert "too short" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_start_research_rejects_long_query(
        self, mock_research_service, mock_api_key
    ):
        """Test that query longer than MAX_QUERY_LENGTH is rejected"""
        from apps.api.routers.research_router import create_research_router

        router = create_research_router(mock_research_service)
        client = create_test_app(router, mock_api_key)

        # Create a query that exceeds MAX_QUERY_LENGTH (2000 chars)
        long_query = "a" * 2001

        request_data = {"query": long_query, "config": None}

        response = client.post(
            "/api/v1/research",
            json=request_data,
            headers={"X-API-Key": "test_key"},
        )

        # Either 400 (endpoint validation) or 422 (Pydantic validation)
        assert response.status_code in [400, 422]


class TestGetSessionEndpoint:
    """Test GET /api/v1/research/{id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_session_returns_200(self, mock_research_service, mock_api_key):
        """Test getting a session returns 200 with session data"""
        from apps.api.routers.research_router import create_research_router

        session_id = "session_123"
        mock_session = ResearchSession(
            id=session_id,
            query="test query",
            stage=ResearchStage.ANALYZING,
            progress=0.5,
        )

        mock_research_service.get_session.return_value = mock_session
        router = create_research_router(mock_research_service)
        client = create_test_app(router, mock_api_key)

        response = client.get(
            f"/api/v1/research/{session_id}",
            headers={"X-API-Key": "test_key"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "session" in data
        assert data["session"]["id"] == session_id

    @pytest.mark.asyncio
    async def test_get_session_returns_404_if_not_found(
        self, mock_research_service, mock_api_key
    ):
        """Test that getting non-existent session returns 404"""
        from apps.api.routers.research_router import create_research_router

        mock_research_service.get_session.return_value = None
        router = create_research_router(mock_research_service)
        client = create_test_app(router, mock_api_key)

        response = client.get(
            "/api/v1/research/nonexistent",
            headers={"X-API-Key": "test_key"},
        )

        assert response.status_code == 404


class TestImportDocumentsEndpoint:
    """Test POST /api/v1/research/{id}/import endpoint"""

    @pytest.mark.asyncio
    async def test_import_documents_returns_200(
        self, mock_research_service, mock_api_key
    ):
        """Test successful document import returns 200"""
        from apps.api.routers.research_router import create_research_router

        session_id = "session_123"
        mock_research_service.import_documents.return_value = {
            "success": True,
            "documentsImported": 2,
            "taxonomyUpdated": False,
        }

        router = create_research_router(mock_research_service)
        client = create_test_app(router, mock_api_key)

        request_data = {
            "selectedDocumentIds": ["doc_1", "doc_2"],
            "taxonomyId": None,
        }

        response = client.post(
            f"/api/v1/research/{session_id}/import",
            json=request_data,
            headers={"X-API-Key": "test_key"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["documentsImported"] == 2

    @pytest.mark.asyncio
    async def test_import_documents_returns_404_if_not_found(
        self, mock_research_service, mock_api_key
    ):
        """Test that importing to non-existent session returns 404"""
        from apps.api.routers.research_router import create_research_router

        mock_research_service.import_documents.side_effect = ValueError(
            "Session not found"
        )

        router = create_research_router(mock_research_service)
        client = create_test_app(router, mock_api_key)

        request_data = {
            "selectedDocumentIds": ["doc_1"],
            "taxonomyId": None,
        }

        response = client.post(
            "/api/v1/research/nonexistent/import",
            json=request_data,
            headers={"X-API-Key": "test_key"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_import_documents_returns_409_if_invalid_stage(
        self, mock_research_service, mock_api_key
    ):
        """Test that importing with invalid stage returns 409"""
        from apps.api.routers.research_router import create_research_router

        mock_research_service.import_documents.side_effect = ValueError(
            "Session must be in CONFIRMING stage"
        )

        router = create_research_router(mock_research_service)
        client = create_test_app(router, mock_api_key)

        request_data = {
            "selectedDocumentIds": ["doc_1"],
            "taxonomyId": None,
        }

        response = client.post(
            "/api/v1/research/session_123/import",
            json=request_data,
            headers={"X-API-Key": "test_key"},
        )

        assert response.status_code == 409


class TestCancelResearchEndpoint:
    """Test DELETE /api/v1/research/{id} endpoint"""

    @pytest.mark.asyncio
    async def test_cancel_research_returns_204(
        self, mock_research_service, mock_api_key
    ):
        """Test successful cancellation returns 204"""
        from apps.api.routers.research_router import create_research_router

        session_id = "session_123"
        mock_research_service.cancel_research.return_value = True

        router = create_research_router(mock_research_service)
        client = create_test_app(router, mock_api_key)

        response = client.delete(
            f"/api/v1/research/{session_id}",
            headers={"X-API-Key": "test_key"},
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_cancel_research_returns_404_if_not_found(
        self, mock_research_service, mock_api_key
    ):
        """Test that cancelling non-existent session returns 404"""
        from apps.api.routers.research_router import create_research_router

        mock_research_service.cancel_research.return_value = False

        router = create_research_router(mock_research_service)
        client = create_test_app(router, mock_api_key)

        response = client.delete(
            "/api/v1/research/nonexistent",
            headers={"X-API-Key": "test_key"},
        )

        assert response.status_code == 404


class TestResearchRouterIntegration:
    """Integration tests for research router"""

    def test_api_key_validation_required(self, mock_research_service):
        """Test that API key is required for all endpoints"""
        from apps.api.routers.research_router import create_research_router

        router = create_research_router(mock_research_service)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Request without API key override
        response = client.post(
            "/api/v1/research",
            json={"query": "test"},
        )

        # Should return 403 (Forbidden - missing API key)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_camelcase_response_fields(self, mock_research_service, mock_api_key):
        """Test that response fields use camelCase"""
        from apps.api.routers.research_router import create_research_router

        mock_research_service.start_research.return_value = ("session_123", 30)

        router = create_research_router(mock_research_service)
        client = create_test_app(router, mock_api_key)

        request_data = {
            "query": "test research query",
            "config": {"maxDocuments": 50},
        }

        response = client.post(
            "/api/v1/research",
            json=request_data,
            headers={"X-API-Key": "test_key"},
        )

        # Assert response uses camelCase
        data = response.json()
        assert "sessionId" in data  # camelCase
        assert "estimatedDuration" in data  # camelCase
        assert "session_id" not in data  # not snake_case
