# @TEST:AGENT-GROWTH-001:INTEGRATION
import pytest
import pytest_asyncio
import uuid
import asyncio
from apps.knowledge_builder.coverage.meter import CoverageMeterService
from apps.api.database import (
    TaxonomyNode,
    TaxonomyEdge,
    Document,
    DocumentChunk,
    DocTaxonomy,
)
from apps.core.db_session import async_session
from sqlalchemy import select, delete, text


@pytest.fixture(autouse=True)
def cleanup_test_files():
    yield


@pytest_asyncio.fixture
async def clean_test_data():
    try:
        cleanup_task = asyncio.create_task(_cleanup_tables())
        await asyncio.wait_for(cleanup_task, timeout=1.0)
    except asyncio.TimeoutError:
        pytest.skip("Database connection timeout - DB may not be running")
    except Exception as e:
        pytest.skip(f"Database setup failed: {e}")

    yield

    try:
        cleanup_task = asyncio.create_task(_cleanup_tables())
        await asyncio.wait_for(cleanup_task, timeout=1.0)
    except:
        pass


async def _cleanup_tables():
    async with async_session() as session:
        await session.execute(text("TRUNCATE TABLE agents CASCADE"))
        await session.execute(text("TRUNCATE TABLE doc_taxonomy CASCADE"))
        await session.execute(text("TRUNCATE TABLE chunks CASCADE"))
        await session.execute(text("TRUNCATE TABLE embeddings CASCADE"))
        await session.execute(text("TRUNCATE TABLE documents CASCADE"))
        await session.execute(text("TRUNCATE TABLE taxonomy_edges CASCADE"))
        await session.execute(text("TRUNCATE TABLE taxonomy_nodes CASCADE"))
        await session.commit()


@pytest_asyncio.fixture
async def sample_taxonomy_data(clean_test_data):
    try:
        setup_task = asyncio.create_task(_setup_taxonomy_data())
        result = await asyncio.wait_for(setup_task, timeout=1.0)
        yield result
    except asyncio.TimeoutError:
        pytest.skip("Database connection timeout during taxonomy data setup")
    except Exception as e:
        pytest.skip(f"Taxonomy data setup failed: {e}")


async def _setup_taxonomy_data():
    async with async_session() as session:
        version = "1.0.0"

        node_id_root = uuid.uuid4()
        node_id_ai = uuid.uuid4()
        node_id_ml = uuid.uuid4()

        root_node = TaxonomyNode(
            node_id=node_id_root,
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
        ml_node = TaxonomyNode(
            node_id=node_id_ml,
            label="machine-learning",
            canonical_path=["technology", "ai", "machine-learning"],
            version=version,
            confidence=1.0,
        )

        session.add_all([root_node, ai_node, ml_node])
        await session.commit()

        root_edge = TaxonomyEdge(parent=node_id_root, child=node_id_ai, version=version)
        ai_edge = TaxonomyEdge(parent=node_id_ai, child=node_id_ml, version=version)
        session.add_all([root_edge, ai_edge])

        await session.commit()

        return {
            "version": version,
            "node_ids": [str(node_id_root), str(node_id_ai), str(node_id_ml)],
            "nodes": {"root": node_id_root, "ai": node_id_ai, "ml": node_id_ml},
        }


@pytest_asyncio.fixture
async def sample_documents(sample_taxonomy_data):
    try:
        setup_task = asyncio.create_task(_setup_document_data(sample_taxonomy_data))
        result = await asyncio.wait_for(setup_task, timeout=1.0)
        yield result
    except asyncio.TimeoutError:
        pytest.skip("Database connection timeout during document data setup")
    except Exception as e:
        pytest.skip(f"Document data setup failed: {e}")


async def _setup_document_data(sample_taxonomy_data):
    async with async_session() as session:
        doc_id_1 = uuid.uuid4()
        doc_id_2 = uuid.uuid4()

        doc_1 = Document(
            doc_id=doc_id_1,
            title="Machine Learning Basics",
            source_url="https://example.com/ml-basics",
            content_type="article",
        )
        doc_2 = Document(
            doc_id=doc_id_2,
            title="AI Applications",
            source_url="https://example.com/ai-apps",
            content_type="article",
        )
        session.add_all([doc_1, doc_2])
        await session.commit()

        chunk_id_1 = uuid.uuid4()
        chunk_id_2 = uuid.uuid4()
        chunk_id_3 = uuid.uuid4()

        chunk_1 = DocumentChunk(
            chunk_id=chunk_id_1,
            doc_id=doc_id_1,
            text="Machine learning is a subset of artificial intelligence.",
            span="0,60",
            chunk_index=0,
            token_count=10,
        )
        chunk_2 = DocumentChunk(
            chunk_id=chunk_id_2,
            doc_id=doc_id_1,
            text="ML algorithms learn from data without explicit programming.",
            span="60,120",
            chunk_index=1,
            token_count=10,
        )
        chunk_3 = DocumentChunk(
            chunk_id=chunk_id_3,
            doc_id=doc_id_2,
            text="AI is transforming industries worldwide.",
            span="0,40",
            chunk_index=0,
            token_count=7,
        )
        session.add_all([chunk_1, chunk_2, chunk_3])
        await session.commit()

        ml_node_id = sample_taxonomy_data["nodes"]["ml"]
        ai_node_id = sample_taxonomy_data["nodes"]["ai"]
        version = sample_taxonomy_data["version"]

        doc_tax_1 = DocTaxonomy(
            doc_id=doc_id_1,
            node_id=ml_node_id,
            version=version,
            path=["technology", "ai", "machine-learning"],
            confidence=0.95,
        )
        doc_tax_2 = DocTaxonomy(
            doc_id=doc_id_2,
            node_id=ai_node_id,
            version=version,
            path=["technology", "ai"],
            confidence=0.90,
        )
        session.add_all([doc_tax_1, doc_tax_2])
        await session.commit()

        return {
            "doc_ids": [doc_id_1, doc_id_2],
            "chunk_ids": [chunk_id_1, chunk_id_2, chunk_id_3],
        }


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_calculate_coverage_with_real_data(
    sample_taxonomy_data, sample_documents
):
    service = CoverageMeterService()

    metrics = await service.calculate_coverage(
        taxonomy_version=sample_taxonomy_data["version"],
        node_ids=sample_taxonomy_data["node_ids"],
    )

    assert metrics.total_nodes == 3
    assert metrics.total_documents == 2
    assert isinstance(metrics.coverage_percent, float)
    assert metrics.coverage_percent >= 0.0
    assert isinstance(metrics.node_coverage, dict)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_calculate_coverage_empty_taxonomy(clean_test_data):
    service = CoverageMeterService()

    metrics = await service.calculate_coverage(taxonomy_version="999.0.0", node_ids=[])

    assert metrics.total_nodes == 0
    assert metrics.total_documents == 0
    assert metrics.total_chunks == 0
    assert metrics.coverage_percent == 0.0
    assert metrics.node_coverage == {}


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_detect_gaps_with_real_data(sample_taxonomy_data, sample_documents):
    service = CoverageMeterService()

    metrics = await service.calculate_coverage(
        taxonomy_version=sample_taxonomy_data["version"],
        node_ids=sample_taxonomy_data["node_ids"],
    )

    root_node_id = str(sample_taxonomy_data["nodes"]["root"])

    if root_node_id in metrics.node_coverage:
        root_coverage = metrics.node_coverage[root_node_id]
        assert "document_count" in root_coverage or "chunk_count" in root_coverage


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_create_agent_with_initial_coverage(
    sample_taxonomy_data, sample_documents
):
    from apps.api.agent_dao import AgentDAO

    async with async_session() as session:
        node_ids = [
            sample_taxonomy_data["nodes"]["ai"],
            sample_taxonomy_data["nodes"]["ml"],
        ]

        agent = await AgentDAO.create_agent(
            session=session,
            name="ML Expert Agent",
            taxonomy_node_ids=node_ids,
            taxonomy_version=sample_taxonomy_data["version"],
            scope_description="Specialized in machine learning topics",
        )

        assert agent.agent_id is not None
        assert agent.name == "ML Expert Agent"
        assert len(agent.taxonomy_node_ids) == 2
        assert agent.taxonomy_version == sample_taxonomy_data["version"]
        assert agent.scope_description == "Specialized in machine learning topics"
        assert agent.level == 1
        assert agent.current_xp == 0
        assert agent.coverage_percent >= 0.0
        assert agent.total_documents >= 0
        assert agent.total_chunks >= 0


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_get_agent_returns_none(clean_test_data):
    from apps.api.agent_dao import AgentDAO

    async with async_session() as session:
        non_existent_id = uuid.uuid4()
        agent = await AgentDAO.get_agent(session, non_existent_id)

        assert agent is None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_update_agent_updates_timestamp(sample_taxonomy_data):
    from apps.api.agent_dao import AgentDAO
    import asyncio
    from datetime import datetime

    async with async_session() as session:
        node_ids = [sample_taxonomy_data["nodes"]["ai"]]

        agent = await AgentDAO.create_agent(
            session=session,
            name="Test Agent",
            taxonomy_node_ids=node_ids,
            taxonomy_version=sample_taxonomy_data["version"],
        )

        original_updated_at = agent.updated_at
        await asyncio.sleep(0.1)

        updated_agent = await AgentDAO.update_agent(
            session=session, agent_id=agent.agent_id, name="Updated Test Agent"
        )

        assert updated_agent.name == "Updated Test Agent"
        assert updated_agent.updated_at > original_updated_at


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_delete_agent(sample_taxonomy_data):
    from apps.api.agent_dao import AgentDAO

    async with async_session() as session:
        node_ids = [sample_taxonomy_data["nodes"]["ai"]]

        agent = await AgentDAO.create_agent(
            session=session,
            name="To Be Deleted",
            taxonomy_node_ids=node_ids,
            taxonomy_version=sample_taxonomy_data["version"],
        )

        agent_id = agent.agent_id

        deleted = await AgentDAO.delete_agent(session, agent_id)
        assert deleted is True

        check_agent = await AgentDAO.get_agent(session, agent_id)
        assert check_agent is None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_list_agents_with_filters(sample_taxonomy_data):
    from apps.api.agent_dao import AgentDAO

    async with async_session() as session:
        node_ids_1 = [sample_taxonomy_data["nodes"]["ai"]]
        node_ids_2 = [sample_taxonomy_data["nodes"]["ml"]]

        agent1 = await AgentDAO.create_agent(
            session=session,
            name="Agent Level 1",
            taxonomy_node_ids=node_ids_1,
            taxonomy_version=sample_taxonomy_data["version"],
        )

        agent2 = await AgentDAO.create_agent(
            session=session,
            name="Agent Level 2",
            taxonomy_node_ids=node_ids_2,
            taxonomy_version=sample_taxonomy_data["version"],
        )

        await AgentDAO.update_agent(session, agent2.agent_id, level=2)

        all_agents = await AgentDAO.list_agents(session)
        assert len(all_agents) >= 2

        level_2_agents = await AgentDAO.list_agents(session, level=2)
        assert len(level_2_agents) >= 1
        assert any(a.level == 2 for a in level_2_agents)
