# @TEST:AGENT-GROWTH-001:DOMAIN
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from apps.knowledge_builder.coverage.models import CoverageMetrics, Gap
from apps.knowledge_builder.coverage.meter import CoverageMeterService


def test_coverage_metrics_creation():
    metrics = CoverageMetrics(
        total_nodes=10,
        total_documents=5,
        total_chunks=50,
        coverage_percent=75.0,
        node_coverage={"node1": 10},
    )

    assert metrics.total_nodes == 10
    assert metrics.total_documents == 5
    assert metrics.total_chunks == 50
    assert metrics.coverage_percent == 75.0
    assert metrics.node_coverage == {"node1": 10}


@pytest.mark.asyncio
async def test_coverage_service_no_nodes():
    service = CoverageMeterService()
    metrics = await service.calculate_coverage(taxonomy_version="1.0.0")

    assert metrics.total_nodes == 0
    assert metrics.total_documents == 0


@pytest.mark.asyncio
async def test_coverage_service_with_mock():
    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def execute(self, query):
            result = MagicMock()
            result.scalar.return_value = 5
            return result

    def fake_factory():
        return FakeSession()

    service = CoverageMeterService(session_factory=fake_factory)
    metrics = await service.calculate_coverage(
        taxonomy_version="1.0.0", node_ids=["node1"]
    )

    assert metrics.total_nodes == 5
    assert metrics.total_documents == 5


@pytest.mark.asyncio
async def test_get_descendant_nodes():
    import networkx as nx

    with patch("apps.api.taxonomy_dag.taxonomy_dag_manager") as mock_manager:
        mock_graph = nx.DiGraph()
        mock_graph.add_edge("root", "child1")
        mock_graph.add_edge("child1", "child2")
        mock_manager._build_networkx_graph = AsyncMock(return_value=mock_graph)

        service = CoverageMeterService()
        descendants = await service._get_descendant_nodes(None, ["root"], "1.0.0")

        assert "child1" in descendants
        assert "child2" in descendants


@pytest.mark.asyncio
async def test_detect_gaps_no_gaps():
    service = CoverageMeterService()
    metrics = CoverageMetrics(
        total_nodes=2,
        total_documents=20,
        total_chunks=100,
        coverage_percent=100.0,
        node_coverage={
            "node1": 15,  # document count for this node
            "node2": 20,  # document count for this node
        },
    )

    gaps = await service.detect_gaps(metrics, threshold=0.5)

    assert len(gaps) == 0


@pytest.mark.asyncio
async def test_detect_gaps_with_gaps():
    service = CoverageMeterService()
    metrics = CoverageMetrics(
        total_nodes=2,
        total_documents=5,
        total_chunks=20,
        coverage_percent=50.0,
        node_coverage={
            "node1": 2,  # document count for this node
            "node2": 3,  # document count for this node
        },
    )

    gaps = await service.detect_gaps(metrics, threshold=0.5)

    assert len(gaps) == 2
    assert all(isinstance(gap, Gap) for gap in gaps)
    assert gaps[0].missing_docs >= gaps[1].missing_docs


@pytest.mark.asyncio
async def test_detect_gaps_threshold_variation():
    service = CoverageMeterService()
    metrics = CoverageMetrics(
        total_nodes=1,
        total_documents=3,
        total_chunks=15,
        coverage_percent=30.0,
        node_coverage={
            "node1": 3,  # document count for this node
        },
    )

    gaps_low = await service.detect_gaps(metrics, threshold=0.3)
    gaps_high = await service.detect_gaps(metrics, threshold=0.7)

    assert len(gaps_low) <= len(gaps_high)
