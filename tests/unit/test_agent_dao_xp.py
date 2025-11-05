import pytest
import asyncio
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.agent_dao import AgentDAO
from apps.api.database import Agent


@pytest.fixture
def mock_session():
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def test_agent():
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
        current_xp=10.0,
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


@pytest.mark.asyncio
async def test_update_xp_and_level_single_xp(mock_session, test_agent):
    updated_agent = Agent(
        agent_id=test_agent.agent_id,
        name=test_agent.name,
        taxonomy_node_ids=test_agent.taxonomy_node_ids,
        taxonomy_version=test_agent.taxonomy_version,
        scope_description=test_agent.scope_description,
        total_documents=test_agent.total_documents,
        total_chunks=test_agent.total_chunks,
        coverage_percent=test_agent.coverage_percent,
        last_coverage_update=test_agent.last_coverage_update,
        level=test_agent.level,
        current_xp=15.0,
        total_queries=test_agent.total_queries,
        successful_queries=test_agent.successful_queries,
        avg_faithfulness=test_agent.avg_faithfulness,
        avg_response_time_ms=test_agent.avg_response_time_ms,
        retrieval_config=test_agent.retrieval_config,
        features_config=test_agent.features_config,
        created_at=test_agent.created_at,
        updated_at=datetime.utcnow(),
        last_query_at=test_agent.last_query_at,
    )

    with patch.object(
        AgentDAO, "get_agent", new_callable=AsyncMock, return_value=updated_agent
    ):
        result = await AgentDAO.update_xp_and_level(
            mock_session, test_agent.agent_id, xp_delta=5.0
        )
        assert result is not None, "Result should not be None"

        assert result.current_xp == 15.0
        assert result.level == 1
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_xp_and_level_with_level(mock_session, test_agent):
    updated_agent = Agent(
        agent_id=test_agent.agent_id,
        name=test_agent.name,
        taxonomy_node_ids=test_agent.taxonomy_node_ids,
        taxonomy_version=test_agent.taxonomy_version,
        scope_description=test_agent.scope_description,
        total_documents=test_agent.total_documents,
        total_chunks=test_agent.total_chunks,
        coverage_percent=test_agent.coverage_percent,
        last_coverage_update=test_agent.last_coverage_update,
        level=2,
        current_xp=105.0,
        total_queries=test_agent.total_queries,
        successful_queries=test_agent.successful_queries,
        avg_faithfulness=test_agent.avg_faithfulness,
        avg_response_time_ms=test_agent.avg_response_time_ms,
        retrieval_config=test_agent.retrieval_config,
        features_config=test_agent.features_config,
        created_at=test_agent.created_at,
        updated_at=datetime.utcnow(),
        last_query_at=test_agent.last_query_at,
    )

    test_agent.current_xp = 95.0
    test_agent.level = 1

    with patch.object(
        AgentDAO, "get_agent", new_callable=AsyncMock, return_value=updated_agent
    ):
        result = await AgentDAO.update_xp_and_level(
            mock_session, test_agent.agent_id, xp_delta=10.0, level=2
        )
        assert result is not None, "Result should not be None"

        assert result.current_xp == 105.0
        assert result.level == 2
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_concurrent_xp_updates(mock_session, test_agent):
    final_xp = 50.0
    test_agent.current_xp = 0.0

    call_count = 0

    async def mock_get_agent_incremental(session, agent_id):
        nonlocal call_count
        call_count += 1
        current_xp = 0.0 + (call_count * 5.0)
        return Agent(
            agent_id=agent_id,
            name=test_agent.name,
            taxonomy_node_ids=test_agent.taxonomy_node_ids,
            taxonomy_version=test_agent.taxonomy_version,
            scope_description=test_agent.scope_description,
            total_documents=test_agent.total_documents,
            total_chunks=test_agent.total_chunks,
            coverage_percent=test_agent.coverage_percent,
            last_coverage_update=test_agent.last_coverage_update,
            level=test_agent.level,
            current_xp=current_xp,
            total_queries=test_agent.total_queries,
            successful_queries=test_agent.successful_queries,
            avg_faithfulness=test_agent.avg_faithfulness,
            avg_response_time_ms=test_agent.avg_response_time_ms,
            retrieval_config=test_agent.retrieval_config,
            features_config=test_agent.features_config,
            created_at=test_agent.created_at,
            updated_at=datetime.utcnow(),
            last_query_at=test_agent.last_query_at,
        )

    with patch.object(AgentDAO, "get_agent", side_effect=mock_get_agent_incremental):
        tasks = [
            AgentDAO.update_xp_and_level(
                mock_session, test_agent.agent_id, xp_delta=5.0
            )
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)

        last_result = results[-1]
        assert last_result is not None, "Last result should not be None"
        assert last_result.current_xp == final_xp
        assert mock_session.execute.call_count == 10
        assert mock_session.commit.call_count == 10


@pytest.mark.asyncio
async def test_updated_at_timestamp(mock_session, test_agent):
    old_updated_at = test_agent.updated_at

    await asyncio.sleep(0.1)

    updated_agent = Agent(
        agent_id=test_agent.agent_id,
        name=test_agent.name,
        taxonomy_node_ids=test_agent.taxonomy_node_ids,
        taxonomy_version=test_agent.taxonomy_version,
        scope_description=test_agent.scope_description,
        total_documents=test_agent.total_documents,
        total_chunks=test_agent.total_chunks,
        coverage_percent=test_agent.coverage_percent,
        last_coverage_update=test_agent.last_coverage_update,
        level=test_agent.level,
        current_xp=11.0,
        total_queries=test_agent.total_queries,
        successful_queries=test_agent.successful_queries,
        avg_faithfulness=test_agent.avg_faithfulness,
        avg_response_time_ms=test_agent.avg_response_time_ms,
        retrieval_config=test_agent.retrieval_config,
        features_config=test_agent.features_config,
        created_at=test_agent.created_at,
        updated_at=datetime.utcnow(),
        last_query_at=test_agent.last_query_at,
    )

    with patch.object(
        AgentDAO, "get_agent", new_callable=AsyncMock, return_value=updated_agent
    ):
        result = await AgentDAO.update_xp_and_level(
            mock_session, test_agent.agent_id, xp_delta=1.0
        )
        assert result is not None, "Result should not be None"

        assert result.updated_at > old_updated_at


@pytest.mark.asyncio
async def test_negative_xp_delta(mock_session, test_agent):
    test_agent.current_xp = 20.0

    updated_agent = Agent(
        agent_id=test_agent.agent_id,
        name=test_agent.name,
        taxonomy_node_ids=test_agent.taxonomy_node_ids,
        taxonomy_version=test_agent.taxonomy_version,
        scope_description=test_agent.scope_description,
        total_documents=test_agent.total_documents,
        total_chunks=test_agent.total_chunks,
        coverage_percent=test_agent.coverage_percent,
        last_coverage_update=test_agent.last_coverage_update,
        level=test_agent.level,
        current_xp=15.0,
        total_queries=test_agent.total_queries,
        successful_queries=test_agent.successful_queries,
        avg_faithfulness=test_agent.avg_faithfulness,
        avg_response_time_ms=test_agent.avg_response_time_ms,
        retrieval_config=test_agent.retrieval_config,
        features_config=test_agent.features_config,
        created_at=test_agent.created_at,
        updated_at=datetime.utcnow(),
        last_query_at=test_agent.last_query_at,
    )

    with patch.object(
        AgentDAO, "get_agent", new_callable=AsyncMock, return_value=updated_agent
    ):
        result = await AgentDAO.update_xp_and_level(
            mock_session, test_agent.agent_id, xp_delta=-5.0
        )
        assert result is not None, "Result should not be None"

        assert result.current_xp == 15.0
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_agent_not_found(mock_session, test_agent):
    with patch.object(AgentDAO, "get_agent", new_callable=AsyncMock, return_value=None):
        result = await AgentDAO.update_xp_and_level(
            mock_session, test_agent.agent_id, xp_delta=5.0
        )

        assert result is None
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
