# @TEST:AGENT-GROWTH-002-PHASE2:UNIT
# @TEST:AGENT-GROWTH-003:UNIT
import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.database import Agent
from apps.api.deps import verify_api_key
from apps.api.routers.agent_router import get_session


async def mock_verify_api_key():
    return "test_key"


async def mock_get_session():
    return MagicMock()


@pytest.fixture
def test_client():
    app.dependency_overrides[verify_api_key] = mock_verify_api_key
    app.dependency_overrides[get_session] = mock_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_client_no_auth():
    return TestClient(app)


@pytest.fixture
def mock_agent():
    return Agent(
        agent_id=uuid4(),
        name="Test Agent",
        taxonomy_node_ids=[uuid4()],
        taxonomy_version="1.0.0",
        scope_description="Test scope",
        total_documents=100,
        total_chunks=500,
        coverage_percent=75.0,
        last_coverage_update=datetime.utcnow(),
        level=1,
        current_xp=0,
        total_queries=0,
        successful_queries=0,
        avg_faithfulness=0.0,
        avg_response_time_ms=0.0,
        retrieval_config={"top_k": 5, "strategy": "hybrid"},
        features_config={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_query_at=None
    )


def test_update_agent_success(test_client, mock_agent):
    with patch("apps.api.routers.agent_router.AgentDAO.get_agent", new_callable=AsyncMock, return_value=mock_agent):
        with patch("apps.api.routers.agent_router.AgentDAO.update_agent", new_callable=AsyncMock):
            response = test_client.patch(
                f"/api/v1/agents/{mock_agent.agent_id}",
                json={
                    "name": "Updated Agent Name",
                    "scope_description": "Updated description"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Agent"


def test_update_agent_not_found(test_client):
    with patch("apps.api.routers.agent_router.AgentDAO.get_agent", new_callable=AsyncMock, return_value=None):
        response = test_client.patch(
            f"/api/v1/agents/{uuid4()}",
            json={"name": "Updated Name"}
        )

        assert response.status_code == 404


def test_update_agent_empty_update(test_client, mock_agent):
    with patch("apps.api.routers.agent_router.AgentDAO.get_agent", new_callable=AsyncMock, return_value=mock_agent):
        response = test_client.patch(
            f"/api/v1/agents/{mock_agent.agent_id}",
            json={}
        )

        assert response.status_code == 200


def test_delete_agent_success(test_client, mock_agent):
    with patch("apps.api.routers.agent_router.AgentDAO.get_agent", new_callable=AsyncMock, return_value=mock_agent):
        with patch("apps.api.routers.agent_router.AgentDAO.delete_agent", new_callable=AsyncMock, return_value=True):
            response = test_client.delete(f"/api/v1/agents/{mock_agent.agent_id}")

            assert response.status_code == 204


def test_delete_agent_not_found(test_client):
    with patch("apps.api.routers.agent_router.AgentDAO.get_agent", new_callable=AsyncMock, return_value=None):
        response = test_client.delete(f"/api/v1/agents/{uuid4()}")

        assert response.status_code == 404


def test_search_agents_with_query(test_client, mock_agent):
    with patch("apps.api.routers.agent_router.AgentDAO.search_agents", new_callable=AsyncMock, return_value=[mock_agent]):
        response = test_client.get("/api/v1/agents/search?q=test")

        assert response.status_code == 200
        data = response.json()
        assert len(data["agents"]) == 1
        assert data["filters_applied"]["query"] == "test"


def test_search_agents_no_query(test_client, mock_agent):
    with patch("apps.api.routers.agent_router.AgentDAO.search_agents", new_callable=AsyncMock, return_value=[mock_agent]):
        response = test_client.get("/api/v1/agents/search")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 0


def test_search_agents_exceeding_max_results(test_client):
    response = test_client.get("/api/v1/agents/search?max_results=200")

    assert response.status_code == 422


def test_refresh_coverage_background_true(test_client, mock_agent):
    with patch("apps.api.routers.agent_router.AgentDAO.get_agent", new_callable=AsyncMock, return_value=mock_agent):
        response = test_client.post(
            f"/api/v1/agents/{mock_agent.agent_id}/coverage/refresh?background=true"
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "pending"
        assert data["task_type"] == "coverage_refresh"
        assert "task_id" in data


def test_refresh_coverage_background_false(test_client, mock_agent):
    from apps.knowledge_builder.coverage.models import CoverageMetrics

    coverage_metrics = CoverageMetrics(
        total_nodes=10,
        total_documents=100,
        total_chunks=500,
        coverage_percent=85.5,
        node_coverage={str(mock_agent.taxonomy_node_ids[0]): {"document_count": 50, "chunk_count": 250}}
    )

    with patch("apps.api.routers.agent_router.AgentDAO.get_agent", new_callable=AsyncMock, return_value=mock_agent):
        with patch("apps.api.routers.agent_router.CoverageMeterService.calculate_coverage", new_callable=AsyncMock, return_value=coverage_metrics):
            with patch("apps.api.routers.agent_router.AgentDAO.update_agent", new_callable=AsyncMock):
                response = test_client.post(
                    f"/api/v1/agents/{mock_agent.agent_id}/coverage/refresh?background=false"
                )

                assert response.status_code == 202
                data = response.json()
                assert data["status"] == "completed"
                assert data["result"]["coverage_percent"] == 85.5


def test_get_coverage_task_status(test_client, mock_agent):
    with patch("apps.api.routers.agent_router.AgentDAO.get_agent", new_callable=AsyncMock, return_value=mock_agent):
        response = test_client.get(
            f"/api/v1/agents/{mock_agent.agent_id}/coverage/status/task-123"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["task_id"] == "task-123"


def test_get_coverage_history(test_client, mock_agent):
    with patch("apps.api.routers.agent_router.AgentDAO.get_agent", new_callable=AsyncMock, return_value=mock_agent):
        response = test_client.get(
            f"/api/v1/agents/{mock_agent.agent_id}/coverage/history"
        )

        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert data["total_entries"] >= 0


def test_get_coverage_history_with_date_filters(test_client, mock_agent):
    with patch("apps.api.routers.agent_router.AgentDAO.get_agent", new_callable=AsyncMock, return_value=mock_agent):
        response = test_client.get(
            f"/api/v1/agents/{mock_agent.agent_id}/coverage/history"
            "?start_date=2025-10-01T00:00:00Z&end_date=2025-10-12T23:59:59Z"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["start_date"] is not None
        assert data["end_date"] is not None


def test_query_agent_stream_endpoint_exists(test_client, mock_agent):
    with patch("apps.api.routers.agent_router.AgentDAO.get_agent", new_callable=AsyncMock, return_value=mock_agent):
        with patch("apps.api.routers.agent_router.SearchDAO.hybrid_search", new_callable=AsyncMock, return_value=[]):
            with patch("apps.api.routers.agent_router.AgentDAO.update_agent", new_callable=AsyncMock):
                response = test_client.post(
                    f"/api/v1/agents/{mock_agent.agent_id}/query/stream",
                    json={"query": "test streaming query"}
                )

                assert response.status_code == 200
                assert response.headers["content-type"] == "text/event-stream; charset=utf-8"


def test_phase2_endpoints_require_auth(test_client_no_auth):
    agent_id = uuid4()

    endpoints = [
        ("PATCH", f"/api/v1/agents/{agent_id}", {"name": "Test"}),
        ("DELETE", f"/api/v1/agents/{agent_id}", None),
        ("GET", "/api/v1/agents/search", None),
        ("POST", f"/api/v1/agents/{agent_id}/coverage/refresh", None),
        ("GET", f"/api/v1/agents/{agent_id}/coverage/status/task-123", None),
        ("GET", f"/api/v1/agents/{agent_id}/coverage/history", None),
        ("POST", f"/api/v1/agents/{agent_id}/query/stream", {"query": "test"}),
    ]

    for method, url, json_data in endpoints:
        if method == "PATCH":
            response = test_client_no_auth.patch(url, json=json_data)
        elif method == "DELETE":
            response = test_client_no_auth.delete(url)
        elif method == "POST":
            response = test_client_no_auth.post(url, json=json_data)
        else:
            response = test_client_no_auth.get(url)

        assert response.status_code == 403, f"{method} {url} should require authentication"
