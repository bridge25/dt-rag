from typing import Optional
# @TEST:CONSOLIDATION-001:integration
# @SPEC:CONSOLIDATION-001

import pytest
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import Integer, String, Float, DateTime, Text, func, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, declarative_base

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_consolidation_integration.db"

TestBase = declarative_base()


class TestCaseBank(TestBase):  # type: ignore[misc,valid-type]
    __tablename__ = "case_bank"

    case_id: Mapped[str] = mapped_column(Text, primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    category_path: Mapped[str] = mapped_column(Text, nullable=False)
    query_vector: Mapped[str] = mapped_column(Text, nullable=False)
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
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
    "sqlite+aiosqlite:///test_consolidation_integration.db", echo=False
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
        os.remove("test_consolidation_integration.db")
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
async def test_full_consolidation_workflow():
    """TEST-CONSOLIDATION-001-INT-001: Complete consolidation cycle"""
    from apps.orchestration.src.consolidation_policy import ConsolidationPolicy

    async with test_async_session() as session:
        old_date = datetime.now(timezone.utc) - timedelta(days=100)

        cases = [
            TestCaseBank(
                case_id="workflow-low-perf-001",
                query="low performance query",
                response_text="response",
                category_path='["AI", "Test"]',
                query_vector="[0.1, 0.2, 0.3]",
                success_rate=15.0,
                usage_count=20,
            ),
            TestCaseBank(
                case_id="workflow-inactive-001",
                query="inactive query",
                response_text="response",
                category_path='["AI", "Test"]',
                query_vector="[0.2, 0.3, 0.4]",
                usage_count=50,
                last_used_at=old_date,
            ),
            TestCaseBank(
                case_id="workflow-active-001",
                query="active query",
                response_text="response",
                category_path='["AI", "Test"]',
                query_vector="[0.3, 0.4, 0.5]",
                usage_count=200,
                success_rate=90.0,
                last_used_at=datetime.now(timezone.utc),
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
        assert results["dry_run"] is False

        stmt = select(TestCaseBank).where(TestCaseBank.status == "active")
        result = await session.execute(stmt)
        active_cases = result.scalars().all()

        assert len(active_cases) >= 1
        assert any(case.case_id == "workflow-active-001" for case in active_cases)

        stmt = select(TestCaseBank).where(TestCaseBank.status == "archived")
        result = await session.execute(stmt)
        archived_cases = result.scalars().all()

        assert len(archived_cases) >= 1


@pytest.mark.asyncio
async def test_dry_run_no_changes():
    """TEST-CONSOLIDATION-001-INT-002: Verify dry-run doesn't modify DB"""
    from apps.orchestration.src.consolidation_policy import ConsolidationPolicy

    async with test_async_session() as session:
        old_date = datetime.now(timezone.utc) - timedelta(days=100)

        cases = [
            TestCaseBank(
                case_id="dryrun-low-perf-001",
                query="low performance query",
                response_text="response",
                category_path='["AI", "Test"]',
                query_vector="[0.1, 0.2, 0.3]",
                success_rate=15.0,
                usage_count=20,
            ),
            TestCaseBank(
                case_id="dryrun-inactive-001",
                query="inactive query",
                response_text="response",
                category_path='["AI", "Test"]',
                query_vector="[0.2, 0.3, 0.4]",
                usage_count=50,
                last_used_at=old_date,
            ),
        ]
        for case in cases:
            session.add(case)
        await session.commit()

        policy = ConsolidationPolicy(session, dry_run=True)
        results = await policy.run_consolidation()

        assert results["dry_run"] is True

        stmt = select(TestCaseBank).where(TestCaseBank.status == "active")
        result = await session.execute(stmt)
        active_cases = result.scalars().all()

        assert len(active_cases) == 2


@pytest.mark.asyncio
async def test_restore_archived_case():
    """TEST-CONSOLIDATION-001-INT-003: Archive then restore"""
    from apps.orchestration.src.consolidation_policy import ConsolidationPolicy

    async with test_async_session() as session:
        case = TestCaseBank(
            case_id="restore-test-001",
            query="test query",
            response_text="response",
            category_path='["AI", "Test"]',
            query_vector="[0.1, 0.2, 0.3]",
            success_rate=20.0,
            usage_count=30,
        )
        session.add(case)
        await session.commit()

        policy = ConsolidationPolicy(session, dry_run=False)
        removed_ids = await policy.remove_low_performance_cases(threshold=30.0)

        assert "restore-test-001" in removed_ids

        await session.refresh(case)
        assert case.status == "archived"

        stmt = select(TestCaseBank).where(TestCaseBank.case_id == "restore-test-001")
        result = await session.execute(stmt)
        archived_case = result.scalar_one()
        assert archived_case.status == "archived"

        restore_success = await policy.restore_archived_case("restore-test-001")
        assert restore_success is True

        await session.refresh(case)
        assert case.status == "active"


@pytest.mark.asyncio
async def test_consolidation_with_real_vectors():
    """TEST-CONSOLIDATION-001-INT-004: Test with actual embeddings"""
    from apps.orchestration.src.consolidation_policy import ConsolidationPolicy

    async with test_async_session() as session:
        vec = "[" + ",".join([str(0.1)] * 100) + "]"
        similar_vec = "[" + ",".join([str(0.10001)] * 100) + "]"
        different_vec = "[" + ",".join([str(0.9)] * 100) + "]"

        cases = [
            TestCaseBank(
                case_id="real-vec-1",
                query="similar query",
                response_text="response 1",
                category_path='["AI", "Test"]',
                query_vector=vec,
                usage_count=100,
                success_rate=80.0,
            ),
            TestCaseBank(
                case_id="real-vec-2",
                query="similar query",
                response_text="response 2",
                category_path='["AI", "Test"]',
                query_vector=similar_vec,
                usage_count=50,
                success_rate=80.0,
            ),
            TestCaseBank(
                case_id="real-vec-3",
                query="different query",
                response_text="response 3",
                category_path='["AI", "Test"]',
                query_vector=different_vec,
                usage_count=75,
                success_rate=85.0,
            ),
        ]
        for case in cases:
            session.add(case)
        await session.commit()

        policy = ConsolidationPolicy(session, dry_run=False)
        merged_pairs = await policy.merge_duplicate_cases(similarity_threshold=0.95)

        assert len(merged_pairs) >= 1

        stmt = select(TestCaseBank).where(TestCaseBank.status == "active")
        result = await session.execute(stmt)
        active_cases = result.scalars().all()

        assert len(active_cases) == 2


@pytest.mark.asyncio
async def test_safety_constraints():
    """TEST-CONSOLIDATION-001-INT-005: Verify high-usage cases not removed"""
    from apps.orchestration.src.consolidation_policy import ConsolidationPolicy

    async with test_async_session() as session:
        old_date = datetime.now(timezone.utc) - timedelta(days=100)

        safety_cases = [
            TestCaseBank(
                case_id="safety-high-usage-low-perf",
                query="important query",
                response_text="response",
                category_path='["AI", "Test"]',
                query_vector="[0.1, 0.2, 0.3]",
                success_rate=10.0,
                usage_count=600,
            ),
            TestCaseBank(
                case_id="safety-high-usage-inactive",
                query="important inactive query",
                response_text="response",
                category_path='["AI", "Test"]',
                query_vector="[0.2, 0.3, 0.4]",
                usage_count=150,
                last_used_at=old_date,
            ),
        ]
        for case in safety_cases:
            session.add(case)
        await session.commit()

        policy = ConsolidationPolicy(session, dry_run=False)
        await policy.run_consolidation()

        stmt = select(TestCaseBank)
        result = await session.execute(stmt)
        all_cases = result.scalars().all()

        high_usage_low_perf = next(
            (c for c in all_cases if c.case_id == "safety-high-usage-low-perf"), None
        )
        high_usage_inactive = next(
            (c for c in all_cases if c.case_id == "safety-high-usage-inactive"), None
        )

        assert high_usage_low_perf is not None
        assert high_usage_low_perf.status == "active"

        assert high_usage_inactive is not None
        assert high_usage_inactive.status == "active"
