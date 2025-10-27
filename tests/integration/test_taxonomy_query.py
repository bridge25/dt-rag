# @TEST:SCHEMA-SYNC-001:INTEGRATION
"""
taxonomy_path → node_id 쿼리 로직 테스트
"""
import pytest
import uuid
from sqlalchemy import select, cast, Text
from sqlalchemy.dialects.postgresql import ARRAY
from apps.api.database import TaxonomyNode
from apps.core.db_session import async_session


@pytest.mark.asyncio
async def test_node_id_query_success(setup_taxonomy_nodes):
    """정상 taxonomy_path → node_id 변환"""
    taxonomy_path = ["technology", "ai", "machine-learning"]

    async with async_session() as session:
        query = select(TaxonomyNode.node_id).where(
            TaxonomyNode.canonical_path == cast(taxonomy_path, ARRAY(Text))
        )
        result = await session.execute(query)
        node_id = result.scalar_one_or_none()

    assert node_id is not None, f"node_id not found for path {taxonomy_path}"
    assert isinstance(node_id, uuid.UUID)


@pytest.mark.asyncio
async def test_node_id_query_not_found(setup_taxonomy_nodes):
    """존재하지 않는 taxonomy_path 에러 처리"""
    taxonomy_path = ["nonexistent", "path"]

    async with async_session() as session:
        query = select(TaxonomyNode.node_id).where(
            TaxonomyNode.canonical_path == cast(taxonomy_path, ARRAY(Text))
        )
        result = await session.execute(query)
        node_id = result.scalar_one_or_none()

    assert node_id is None, "Should return None for non-existent path"


@pytest.mark.asyncio
async def test_node_id_query_performance(setup_taxonomy_nodes):
    """쿼리 성능 p95 < 10ms 검증"""
    import time

    taxonomy_path = ["technology", "ai", "machine-learning"]
    latencies = []

    for _ in range(100):
        start = time.perf_counter()

        async with async_session() as session:
            query = select(TaxonomyNode.node_id).where(
                TaxonomyNode.canonical_path == cast(taxonomy_path, ARRAY(Text))
            )
            result = await session.execute(query)
            _ = result.scalar_one_or_none()

        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)

    latencies.sort()
    p95 = latencies[94]

    assert p95 < 10.0, f"p95 latency {p95:.2f}ms exceeds 10ms threshold"
