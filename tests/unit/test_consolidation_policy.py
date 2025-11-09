from typing import Optional, Dict, Any
# @TEST:CONSOLIDATION-001:unit
# @SPEC:CONSOLIDATION-001
# @TEST:CASEBANK-UNIFY-UNIT-001

import pytest
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import Integer, String, Float, DateTime, Text, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from sqlalchemy.types import JSON

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_consolidation.db"

TestBase = declarative_base()


class TestCaseBank(TestBase):  # type: ignore[misc,valid-type]
    """
    @TEST:CASEBANK-UNIFY-UNIT-001 - Test model synchronized with production schema
    Updated to match apps/api/database.py CaseBank model
    """
    __tablename__ = "case_bank"

    case_id: Mapped[str] = mapped_column(Text, primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)  # Added
    category_path: Mapped[str] = mapped_column(Text, nullable=False)
    quality: Mapped[Optional[float]] = mapped_column(Float)  # Renamed from quality_score
    query_vector: Mapped[str] = mapped_column(Text, nullable=False)
    usage_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    success_rate: Mapped[Optional[float]] = mapped_column(Float, default=100.0)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


test_engine = create_async_engine(
    "sqlite+aiosqlite:///test_consolidation.db", echo=False
)
test_async_session = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.drop_all)
    await test_engine.dispose()
    try:
        os.remove("test_consolidation.db")
    except FileNotFoundError:
        pass


@pytest.fixture(autouse=True)
async def cleanup_cases():
    yield
    async with test_async_session() as session:
        from sqlalchemy import delete

        stmt = delete(TestCaseBank)
        await session.execute(stmt)
        await session.commit()


@pytest.mark.asyncio
async def test_remove_low_performance_cases():
    """TEST-CONSOLIDATION-001-001: Remove cases with success_rate < 30%"""
    from apps.orchestration.src.consolidation_policy import ConsolidationPolicy

    async with test_async_session() as session:
        cases = [
            TestCaseBank(
                case_id=f"low-perf-{i}",
                query=f"query {i}",
                answer=f"response {i}",
                sources={},
                category_path='["AI", "Test"]',
                query_vector="[0.1, 0.2, 0.3]",
                success_rate=25.0,
                usage_count=20,
            )
            for i in range(3)
        ]
        for case in cases:
            session.add(case)
        await session.commit()

        policy = ConsolidationPolicy(session, dry_run=False)
        removed_ids = await policy.remove_low_performance_cases(threshold=30.0)

        assert len(removed_ids) == 3
        for case_id in removed_ids:
            assert case_id.startswith("low-perf-")


@pytest.mark.asyncio
async def test_remove_low_performance_skip_high_usage():
    """TEST-CONSOLIDATION-001-002: Skip removal if usage_count >= 500"""
    from apps.orchestration.src.consolidation_policy import ConsolidationPolicy

    async with test_async_session() as session:
        high_usage_case = TestCaseBank(
            case_id="high-usage-001",
            query="important query",
            answer="important response",
            sources={},
            category_path='["AI", "Test"]',
            query_vector="[0.1, 0.2, 0.3]",
            success_rate=20.0,
            usage_count=600,
        )
        session.add(high_usage_case)
        await session.commit()

        policy = ConsolidationPolicy(session, dry_run=False)
        removed_ids = await policy.remove_low_performance_cases(threshold=30.0)

        assert len(removed_ids) == 0


@pytest.mark.asyncio
async def test_merge_duplicate_cases():
    """TEST-CONSOLIDATION-001-003: Merge cases with similarity > 95%"""
    from apps.orchestration.src.consolidation_policy import ConsolidationPolicy

    async with test_async_session() as session:
        vec = "[" + ",".join(["0.1"] * 100) + "]"
        similar_vec = "[" + ",".join(["0.10001"] * 100) + "]"

        cases = [
            TestCaseBank(
                case_id="dup-case-1",
                query="duplicate query",
                answer="response 1",
                sources={},
                category_path='["AI", "Test"]',
                query_vector=vec,
                usage_count=50,
                success_rate=80.0,
            ),
            TestCaseBank(
                case_id="dup-case-2",
                query="duplicate query",
                answer="response 2",
                sources={},
                category_path='["AI", "Test"]',
                query_vector=similar_vec,
                usage_count=30,
                success_rate=75.0,
            ),
        ]
        for case in cases:
            session.add(case)
        await session.commit()

        policy = ConsolidationPolicy(session, dry_run=False)
        merged_pairs = await policy.merge_duplicate_cases(similarity_threshold=0.95)

        assert len(merged_pairs) >= 1
        assert any(
            pair["removed"] in ["dup-case-1", "dup-case-2"] for pair in merged_pairs
        )


@pytest.mark.asyncio
async def test_merge_keep_higher_usage():
    """TEST-CONSOLIDATION-001-004: Keep case with higher usage_count"""
    from apps.orchestration.src.consolidation_policy import ConsolidationPolicy

    async with test_async_session() as session:
        vec = "[" + ",".join(["0.2"] * 100) + "]"

        cases = [
            TestCaseBank(
                case_id="keep-this",
                query="test query",
                answer="response 1",
                sources={},
                category_path='["AI", "Test"]',
                query_vector=vec,
                usage_count=100,
                success_rate=80.0,
            ),
            TestCaseBank(
                case_id="remove-this",
                query="test query",
                answer="response 2",
                sources={},
                category_path='["AI", "Test"]',
                query_vector=vec,
                usage_count=10,
                success_rate=80.0,
            ),
        ]
        for case in cases:
            session.add(case)
        await session.commit()

        policy = ConsolidationPolicy(session, dry_run=False)
        merged_pairs = await policy.merge_duplicate_cases(similarity_threshold=0.95)

        assert len(merged_pairs) >= 1
        keeper_found = False
        for pair in merged_pairs:
            if pair["keeper"] == "keep-this" and pair["removed"] == "remove-this":
                keeper_found = True
                break

        assert keeper_found


@pytest.mark.asyncio
async def test_archive_inactive_cases():
    """TEST-CONSOLIDATION-001-005: Archive cases not accessed for 90 days"""
    from apps.orchestration.src.consolidation_policy import ConsolidationPolicy

    async with test_async_session() as session:
        old_date = datetime.now(timezone.utc) - timedelta(days=100)

        inactive_case = TestCaseBank(
            case_id="inactive-001",
            query="old query",
            answer="old response",
            sources={},
            category_path='["AI", "Test"]',
            query_vector="[0.1, 0.2, 0.3]",
            usage_count=50,
            last_used_at=old_date,
        )
        session.add(inactive_case)
        await session.commit()

        policy = ConsolidationPolicy(session, dry_run=False)
        archived_ids = await policy.archive_inactive_cases(days=90)

        assert len(archived_ids) == 1
        assert "inactive-001" in archived_ids


@pytest.mark.asyncio
async def test_archive_skip_high_usage():
    """TEST-CONSOLIDATION-001-006: Skip archiving if usage_count >= 100"""
    from apps.orchestration.src.consolidation_policy import ConsolidationPolicy

    async with test_async_session() as session:
        old_date = datetime.now(timezone.utc) - timedelta(days=100)

        high_usage_inactive = TestCaseBank(
            case_id="high-usage-inactive-001",
            query="important old query",
            answer="important old response",
            sources={},
            category_path='["AI", "Test"]',
            query_vector="[0.1, 0.2, 0.3]",
            usage_count=150,
            last_used_at=old_date,
        )
        session.add(high_usage_inactive)
        await session.commit()

        policy = ConsolidationPolicy(session, dry_run=False)
        archived_ids = await policy.archive_inactive_cases(days=90)

        assert len(archived_ids) == 0


@pytest.mark.asyncio
async def test_dry_run_mode():
    """TEST-CONSOLIDATION-001-007: Dry-run mode does not modify database"""
    from apps.orchestration.src.consolidation_policy import ConsolidationPolicy
    from sqlalchemy import select

    async with test_async_session() as session:
        low_perf_case = TestCaseBank(
            case_id="dry-run-001",
            query="test query",
            answer="test response",
            sources={},
            category_path='["AI", "Test"]',
            query_vector="[0.1, 0.2, 0.3]",
            success_rate=20.0,
            usage_count=50,
            status="active",
        )
        session.add(low_perf_case)
        await session.commit()

        policy = ConsolidationPolicy(session, dry_run=True)
        removed_ids = await policy.remove_low_performance_cases(threshold=30.0)

        assert len(removed_ids) == 1

        stmt = select(TestCaseBank).where(TestCaseBank.case_id == "dry-run-001")
        result = await session.execute(stmt)
        case = result.scalar_one()

        assert case.status == "active"


@pytest.mark.asyncio
async def test_calculate_similarity():
    """TEST-CONSOLIDATION-001-008: Cosine similarity calculation"""
    from apps.orchestration.src.consolidation_policy import ConsolidationPolicy

    async with test_async_session() as session:
        policy = ConsolidationPolicy(session, dry_run=True)

        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = policy._calculate_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.01

        vec3 = [1.0, 0.0, 0.0]
        vec4 = [0.0, 1.0, 0.0]
        similarity2 = policy._calculate_similarity(vec3, vec4)
        assert abs(similarity2 - 0.0) < 0.01

        vec5 = [0.707, 0.707, 0.0]
        vec6 = [0.707, 0.707, 0.0]
        similarity3 = policy._calculate_similarity(vec5, vec6)
        assert abs(similarity3 - 1.0) < 0.01


@pytest.mark.asyncio
async def test_run_consolidation_batch():
    """TEST-CONSOLIDATION-001-009: Full consolidation workflow"""
    from apps.orchestration.src.consolidation_policy import ConsolidationPolicy

    async with test_async_session() as session:
        old_date = datetime.now(timezone.utc) - timedelta(days=100)

        cases = [
            TestCaseBank(
                case_id="full-low-perf",
                query="low perf query",
                answer="response",
                sources={},
                category_path='["AI", "Test"]',
                query_vector="[0.1, 0.2, 0.3]",
                success_rate=15.0,
                usage_count=20,
            ),
            TestCaseBank(
                case_id="full-inactive",
                query="inactive query",
                answer="response",
                sources={},
                category_path='["AI", "Test"]',
                query_vector="[0.2, 0.3, 0.4]",
                usage_count=50,
                last_used_at=old_date,
            ),
        ]
        for case in cases:
            session.add(case)
        await session.commit()

        policy = ConsolidationPolicy(session, dry_run=False)
        results = await policy.run_consolidation(
            low_perf_threshold=30.0, similarity_threshold=0.95, inactive_days=90
        )

        assert results["removed_cases"] >= 1
        assert results["archived_cases"] >= 1
        assert results["dry_run"] is False
        assert "details" in results
