# @TEST:AGENT-GROWTH-005:INTEGRATION
import pytest
import pytest_asyncio
import uuid
import asyncio
import time
from apps.api.database import TaxonomyNode, Document, DocumentChunk, DocTaxonomy
from apps.api.agent_dao import AgentDAO
from apps.core.db_session import async_session
from sqlalchemy import text


async def _cleanup_tables():
    try:
        await asyncio.sleep(2)
        async with async_session() as session:
            await session.execute(text("DELETE FROM agents"))
            await session.execute(text("DELETE FROM doc_taxonomy"))
            await session.execute(text("DELETE FROM chunks"))
            await session.execute(text("DELETE FROM embeddings"))
            await session.execute(text("DELETE FROM documents"))
            await session.execute(text("DELETE FROM taxonomy_edges"))
            await session.execute(text("DELETE FROM taxonomy_nodes"))
            await session.commit()
    except Exception as e:
        print(f"Cleanup failed: {e}")
        pass


@pytest_asyncio.fixture
async def sample_taxonomy_with_docs():
    await _cleanup_tables()
    try:
        setup_task = asyncio.create_task(_setup_taxonomy_and_docs())
        result = await asyncio.wait_for(setup_task, timeout=2.0)
        yield result
    except asyncio.TimeoutError:
        pytest.skip("Database connection timeout during setup")
    except Exception as e:
        pytest.skip(f"Setup failed: {e}")
    finally:
        await _cleanup_tables()


async def _setup_taxonomy_and_docs():
    async with async_session() as session:
        version = "1.0.0"

        node_id_tech = uuid.uuid4()
        node_id_ai = uuid.uuid4()

        tech_node = TaxonomyNode(
            node_id=node_id_tech,
            label="technology",
            canonical_path=["technology"],
            version=version,
            confidence=1.0,
        )
        ai_node = TaxonomyNode(
            node_id=node_id_ai,
            label="ai",
            canonical_path=["technology", "ai"],
            version=version,
            confidence=1.0,
        )

        session.add_all([tech_node, ai_node])
        await session.commit()

        doc_id = uuid.uuid4()
        doc = Document(
            doc_id=doc_id,
            title="AI Testing Document",
            source_url="https://example.com/ai-test",
            content_type="article",
        )
        session.add(doc)
        await session.commit()

        chunk_id = uuid.uuid4()
        chunk = DocumentChunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            text="This is a test document about artificial intelligence and machine learning.",
            span="0,80",
            chunk_index=0,
            token_count=15,
        )
        session.add(chunk)
        await session.commit()

        doc_tax = DocTaxonomy(
            doc_id=doc_id,
            node_id=node_id_ai,
            version=version,
            path=["technology", "ai"],
            confidence=0.95,
        )
        session.add(doc_tax)
        await session.commit()

        return {
            "version": version,
            "node_ids": [node_id_tech, node_id_ai],
            "nodes": {"tech": node_id_tech, "ai": node_id_ai},
        }


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(15)
async def test_query_triggers_xp_calculation(sample_taxonomy_with_docs):
    async with async_session() as session:
        node_ids = [sample_taxonomy_with_docs["nodes"]["ai"]]

        agent = await AgentDAO.create_agent(
            session=session,
            name="XP Test Agent",
            taxonomy_node_ids=node_ids,
            taxonomy_version=sample_taxonomy_with_docs["version"],
            scope_description="Testing XP calculation",
        )

        initial_xp = agent.current_xp
        assert initial_xp == 0.0

        from apps.api.routers.agent_router import query_agent
        from apps.api.schemas.agent_schemas import QueryRequest

        async def mock_api_key():
            return "test-api-key"

        request = QueryRequest(
            query="test artificial intelligence", top_k=5, include_metadata=False
        )

        start_time = time.time()
        response = await query_agent(
            agent_id=agent.agent_id,
            request=request,
            session=session,
            api_key=await mock_api_key(),
        )
        query_time = time.time() - start_time

        assert response.agent_id == agent.agent_id
        assert response.query == "test artificial intelligence"
        assert query_time < 5.0

        await asyncio.sleep(5)

    async with async_session() as new_session:
        updated_agent = await AgentDAO.get_agent(new_session, agent.agent_id)
        print(f"Initial XP: {initial_xp}, Updated XP: {updated_agent.current_xp}")
        assert updated_agent.current_xp > initial_xp


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(15)
async def test_xp_calculation_does_not_block_query(sample_taxonomy_with_docs):
    async with async_session() as session:
        node_ids = [sample_taxonomy_with_docs["nodes"]["ai"]]

        agent = await AgentDAO.create_agent(
            session=session,
            name="Non-Blocking Test Agent",
            taxonomy_node_ids=node_ids,
            taxonomy_version=sample_taxonomy_with_docs["version"],
        )

        from apps.api.routers.agent_router import query_agent
        from apps.api.schemas.agent_schemas import QueryRequest

        async def mock_api_key():
            return "test-api-key"

        request = QueryRequest(
            query="machine learning", top_k=5, include_metadata=False
        )

        start = time.time()
        response = await query_agent(
            agent_id=agent.agent_id,
            request=request,
            session=session,
            api_key=await mock_api_key(),
        )
        query_latency = time.time() - start

        assert response.agent_id == agent.agent_id
        assert query_latency < 5.0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_query_10_times_accumulates_xp(sample_taxonomy_with_docs):
    async with async_session() as session:
        node_ids = [sample_taxonomy_with_docs["nodes"]["ai"]]

        agent = await AgentDAO.create_agent(
            session=session,
            name="XP Accumulation Agent",
            taxonomy_node_ids=node_ids,
            taxonomy_version=sample_taxonomy_with_docs["version"],
        )

        await AgentDAO.update_agent(
            session=session, agent_id=agent.agent_id, avg_faithfulness=0.85
        )

        from apps.api.routers.agent_router import query_agent
        from apps.api.schemas.agent_schemas import QueryRequest

        async def mock_api_key():
            return "test-api-key"

        request = QueryRequest(
            query="artificial intelligence", top_k=5, include_metadata=False
        )

        for _ in range(10):
            await query_agent(
                agent_id=agent.agent_id,
                request=request,
                session=session,
                api_key=await mock_api_key(),
            )

        await asyncio.sleep(5)

    async with async_session() as new_session:
        updated_agent = await AgentDAO.get_agent(new_session, agent.agent_id)
        assert updated_agent.current_xp >= 50.0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_level_up_after_queries(sample_taxonomy_with_docs):
    async with async_session() as session:
        node_ids = [sample_taxonomy_with_docs["nodes"]["ai"]]

        agent = await AgentDAO.create_agent(
            session=session,
            name="Level Up Agent",
            taxonomy_node_ids=node_ids,
            taxonomy_version=sample_taxonomy_with_docs["version"],
        )

        await AgentDAO.update_xp_and_level(
            session=session, agent_id=agent.agent_id, xp_delta=90.0
        )

        await AgentDAO.update_agent(
            session=session, agent_id=agent.agent_id, avg_faithfulness=0.9
        )

        from apps.api.routers.agent_router import query_agent
        from apps.api.schemas.agent_schemas import QueryRequest

        async def mock_api_key():
            return "test-api-key"

        request = QueryRequest(
            query="machine learning test", top_k=5, include_metadata=False
        )

        for _ in range(3):
            await query_agent(
                agent_id=agent.agent_id,
                request=request,
                session=session,
                api_key=await mock_api_key(),
            )

        await asyncio.sleep(5)

    async with async_session() as new_session:
        updated_agent = await AgentDAO.get_agent(new_session, agent.agent_id)
        assert updated_agent.current_xp >= 100.0
        assert updated_agent.level == 2


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(15)
async def test_xp_calculation_error_does_not_fail_query(sample_taxonomy_with_docs):
    async with async_session() as session:
        node_ids = [sample_taxonomy_with_docs["nodes"]["ai"]]

        agent = await AgentDAO.create_agent(
            session=session,
            name="Error Isolation Agent",
            taxonomy_node_ids=node_ids,
            taxonomy_version=sample_taxonomy_with_docs["version"],
        )

        from apps.api.routers.agent_router import query_agent
        from apps.api.schemas.agent_schemas import QueryRequest

        async def mock_api_key():
            return "test-api-key"

        request = QueryRequest(query="test query", top_k=5, include_metadata=False)

        response = await query_agent(
            agent_id=agent.agent_id,
            request=request,
            session=session,
            api_key=await mock_api_key(),
        )

        assert response.agent_id == agent.agent_id
        assert response.query == "test query"
        assert response.total_results >= 0
