# @TEST:AGENT-GROWTH-002:UNIT
import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.database import Agent
from apps.knowledge_builder.coverage.models import CoverageMetrics, Gap
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
        last_query_at=None,
    )


def test_create_agent_success(test_client, mock_agent):
    with patch(
        "apps.api.routers.agent_router.validate_taxonomy_nodes", new_callable=AsyncMock
    ) as mock_validate:
        with patch(
            "apps.api.routers.agent_router.AgentDAO.create_agent",
            new_callable=AsyncMock,
            return_value=mock_agent,
        ):
            response = test_client.post(
                "/api/v1/agents/from-taxonomy",
                json={"name": "Test Agent", "taxonomy_node_ids": [str(uuid4())]},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Agent"
            assert "agent_id" in data


def test_create_agent_invalid_taxonomy_nodes(test_client):
    with patch(
        "apps.api.routers.agent_router.validate_taxonomy_nodes",
        side_effect=ValueError("Invalid taxonomy node IDs"),
    ):
        response = test_client.post(
            "/api/v1/agents/from-taxonomy",
            json={"name": "Test Agent", "taxonomy_node_ids": [str(uuid4())]},
        )

        assert response.status_code == 400
        assert "Invalid taxonomy node IDs" in response.json()["detail"]


def test_create_agent_empty_name(test_client):
    response = test_client.post(
        "/api/v1/agents/from-taxonomy",
        json={"name": "", "taxonomy_node_ids": [str(uuid4())]},
    )

    assert response.status_code == 422


def test_create_agent_missing_api_key(test_client_no_auth):
    response = test_client_no_auth.post(
        "/api/v1/agents/from-taxonomy",
        json={"name": "Test Agent", "taxonomy_node_ids": [str(uuid4())]},
    )

    assert response.status_code == 403


def test_get_agent_success(test_client, mock_agent):
    with patch(
        "apps.api.routers.agent_router.AgentDAO.get_agent",
        new_callable=AsyncMock,
        return_value=mock_agent,
    ):
        response = test_client.get(f"/api/v1/agents/{mock_agent.agent_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Agent"


def test_get_agent_not_found(test_client):
    with patch(
        "apps.api.routers.agent_router.AgentDAO.get_agent",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = test_client.get(f"/api/v1/agents/{uuid4()}")

        assert response.status_code == 404
        assert "Agent not found" in response.json()["detail"]


def test_get_agent_invalid_uuid(test_client):
    response = test_client.get("/api/v1/agents/invalid-uuid")

    assert response.status_code == 422


def test_list_agents_no_filters(test_client, mock_agent):
    with patch(
        "apps.api.routers.agent_router.AgentDAO.list_agents",
        new_callable=AsyncMock,
        return_value=[mock_agent],
    ):
        response = test_client.get("/api/v1/agents")

        assert response.status_code == 200
        data = response.json()
        assert len(data["agents"]) == 1
        assert data["total"] == 1


def test_list_agents_with_level_filter(test_client, mock_agent):
    with patch(
        "apps.api.routers.agent_router.AgentDAO.list_agents",
        new_callable=AsyncMock,
        return_value=[mock_agent],
    ):
        response = test_client.get("/api/v1/agents?level=1")

        assert response.status_code == 200
        data = response.json()
        assert data["filters_applied"]["level"] == 1


def test_list_agents_exceeding_max_results(test_client):
    response = test_client.get("/api/v1/agents?max_results=200")

    assert response.status_code == 422


def test_get_agent_coverage_success(test_client, mock_agent):
    coverage_metrics = CoverageMetrics(
        total_nodes=10,
        total_documents=100,
        total_chunks=500,
        coverage_percent=75.0,
        node_coverage={
            str(mock_agent.taxonomy_node_ids[0]): {
                "document_count": 50,
                "chunk_count": 250,
            }
        },
    )

    with patch(
        "apps.api.routers.agent_router.AgentDAO.get_agent",
        new_callable=AsyncMock,
        return_value=mock_agent,
    ):
        with patch(
            "apps.api.routers.agent_router.CoverageMeterService.calculate_coverage",
            new_callable=AsyncMock,
            return_value=coverage_metrics,
        ):
            with patch(
                "apps.api.routers.agent_router.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ):
                response = test_client.get(
                    f"/api/v1/agents/{mock_agent.agent_id}/coverage"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["overall_coverage"] == 75.0


def test_detect_coverage_gaps_success(test_client, mock_agent):
    coverage_metrics = CoverageMetrics(
        total_nodes=10,
        total_documents=100,
        total_chunks=500,
        coverage_percent=30.0,
        node_coverage={
            str(mock_agent.taxonomy_node_ids[0]): {
                "document_count": 30,
                "chunk_count": 150,
            }
        },
    )

    gaps_list = [
        Gap(
            node_id=str(mock_agent.taxonomy_node_ids[0]),
            current_coverage=30.0,
            target_coverage=50.0,
            missing_docs=20,
            recommendation="Collect 20 more documents",
        )
    ]

    with patch(
        "apps.api.routers.agent_router.AgentDAO.get_agent",
        new_callable=AsyncMock,
        return_value=mock_agent,
    ):
        with patch(
            "apps.api.routers.agent_router.CoverageMeterService.calculate_coverage",
            new_callable=AsyncMock,
            return_value=coverage_metrics,
        ):
            with patch(
                "apps.api.routers.agent_router.CoverageMeterService.detect_gaps",
                new_callable=AsyncMock,
                return_value=gaps_list,
            ):
                response = test_client.get(
                    f"/api/v1/agents/{mock_agent.agent_id}/gaps?threshold=0.5"
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data["gaps"]) == 1
                assert data["threshold"] == 0.5


def test_detect_gaps_invalid_threshold(test_client):
    response = test_client.get(f"/api/v1/agents/{uuid4()}/gaps?threshold=1.5")

    assert response.status_code == 422


def test_query_agent_success(test_client, mock_agent):
    search_results = [
        {
            "chunk_id": str(uuid4()),
            "text": "Test content",
            "score": 0.9,
            "metadata": {"title": "Test Document"},
        }
    ]

    with patch(
        "apps.api.routers.agent_router.AgentDAO.get_agent",
        new_callable=AsyncMock,
        return_value=mock_agent,
    ):
        with patch(
            "apps.api.routers.agent_router.SearchDAO.hybrid_search",
            new_callable=AsyncMock,
            return_value=search_results,
        ):
            with patch(
                "apps.api.routers.agent_router.AgentDAO.update_agent",
                new_callable=AsyncMock,
            ):
                response = test_client.post(
                    f"/api/v1/agents/{mock_agent.agent_id}/query",
                    json={"query": "test query"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["query"] == "test query"
                assert len(data["results"]) == 1


def test_query_agent_empty_query(test_client):
    response = test_client.post(f"/api/v1/agents/{uuid4()}/query", json={"query": ""})

    assert response.status_code == 422


def test_query_agent_not_found(test_client):
    with patch(
        "apps.api.routers.agent_router.AgentDAO.get_agent",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = test_client.post(
            f"/api/v1/agents/{uuid4()}/query", json={"query": "test query"}
        )

        assert response.status_code == 404
