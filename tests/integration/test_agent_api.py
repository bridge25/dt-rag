# @TEST:AGENT-GROWTH-002:INTEGRATION
import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.main import app
from apps.api.database import Agent, TaxonomyNode
from apps.core.db_session import async_session, Base, engine


@pytest.fixture
async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_session(test_db):
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_taxonomy_node(test_session):
    node = TaxonomyNode(
        node_id=uuid4(),
        label="Test Node",
        canonical_path=["AI", "Test"],
        version="1.0.0",
        confidence=1.0,
    )
    test_session.add(node)
    await test_session.commit()
    await test_session.refresh(node)
    return node


@pytest.mark.asyncio
async def test_create_agent_e2e(test_session, test_taxonomy_node):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/agents/from-taxonomy",
            json={
                "name": "E2E Test Agent",
                "taxonomy_node_ids": [str(test_taxonomy_node.node_id)],
                "taxonomy_version": "1.0.0",
            },
            headers={"X-API-Key": "test-api-key"},
        )

        assert response.status_code == 201
        agent_id = response.json()["agent_id"]

        from sqlalchemy import select

        result = await test_session.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        agent = result.scalar_one()
        assert agent.name == "E2E Test Agent"


@pytest.mark.asyncio
async def test_agent_coverage_updates(test_session, test_taxonomy_node):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/agents/from-taxonomy",
            json={
                "name": "Coverage Test Agent",
                "taxonomy_node_ids": [str(test_taxonomy_node.node_id)],
                "taxonomy_version": "1.0.0",
            },
            headers={"X-API-Key": "test-api-key"},
        )

        agent_id = create_response.json()["agent_id"]

        coverage_response = await client.get(
            f"/api/v1/agents/{agent_id}/coverage", headers={"X-API-Key": "test-api-key"}
        )

        assert coverage_response.status_code == 200
        coverage_data = coverage_response.json()
        assert "overall_coverage" in coverage_data


@pytest.mark.asyncio
async def test_agent_query_increments_total_queries(test_session, test_taxonomy_node):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/agents/from-taxonomy",
            json={
                "name": "Query Test Agent",
                "taxonomy_node_ids": [str(test_taxonomy_node.node_id)],
                "taxonomy_version": "1.0.0",
            },
            headers={"X-API-Key": "test-api-key"},
        )

        agent_id = create_response.json()["agent_id"]

        query_response = await client.post(
            f"/api/v1/agents/{agent_id}/query",
            json={"query": "test query"},
            headers={"X-API-Key": "test-api-key"},
        )

        assert query_response.status_code == 200

        from sqlalchemy import select

        result = await test_session.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        agent = result.scalar_one()
        assert agent.total_queries == 1
        assert agent.last_query_at is not None


@pytest.mark.asyncio
async def test_list_agents_with_filters(test_session, test_taxonomy_node):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for i in range(3):
            await client.post(
                "/api/v1/agents/from-taxonomy",
                json={
                    "name": f"Filter Test Agent {i}",
                    "taxonomy_node_ids": [str(test_taxonomy_node.node_id)],
                    "taxonomy_version": "1.0.0",
                },
                headers={"X-API-Key": "test-api-key"},
            )

        list_response = await client.get(
            "/api/v1/agents?level=1", headers={"X-API-Key": "test-api-key"}
        )

        assert list_response.status_code == 200
        data = list_response.json()
        assert data["total"] == 3
        assert all(agent["level"] == 1 for agent in data["agents"])
