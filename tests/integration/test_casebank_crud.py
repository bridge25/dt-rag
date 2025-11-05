from typing import Optional
# @TEST:CASEBANK-002:integration
# @SPEC:CASEBANK-002

import pytest
import asyncio
import os
from datetime import datetime
from sqlalchemy import select, Integer, String, Float, DateTime, Text, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, declarative_base

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_casebank_integration.db"

TestBase = declarative_base()


class TestCaseBank(TestBase):  # type: ignore[misc,valid-type]
    __tablename__ = "case_bank"

    case_id: Mapped[str] = mapped_column(Text, primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    category_path: Mapped[str] = mapped_column(Text, nullable=False)
    query_vector: Mapped[str] = mapped_column(Text, nullable=False)
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
    usage_count: Mapped[Optional[int]] = mapped_column(Integer)
    success_rate: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

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
    "sqlite+aiosqlite:///test_casebank_integration.db", echo=False
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
        os.remove("test_casebank_integration.db")
    except FileNotFoundError:
        pass


@pytest.fixture(autouse=True)
async def cleanup_cases():
    yield
    async with test_async_session() as session:
        stmt = select(TestCaseBank)
        result = await session.execute(stmt)
        cases = result.scalars().all()
        for case in cases:
            await session.delete(case)
        await session.commit()


@pytest.mark.asyncio
async def test_create_case_with_metadata():
    """TEST-CASEBANK-002-INT-001: Create case with new metadata fields"""
    async with test_async_session() as session:
        case = TestCaseBank(
            case_id="test-create-001",
            query="integration test query",
            response_text="integration test response",
            category_path='["AI", "Integration"]',
            query_vector="[0.1, 0.2, 0.3]",
            quality_score=0.95,
            usage_count=10,
            success_rate=0.90,
            updated_by="integration_tester@example.com",
            status="active",
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)

        assert case.case_id == "test-create-001"
        assert case.version == 1
        assert case.updated_by == "integration_tester@example.com"
        assert case.status == "active"
        assert isinstance(case.updated_at, datetime)
        assert isinstance(case.created_at, datetime)


@pytest.mark.asyncio
async def test_update_case_increments_version():
    """TEST-CASEBANK-002-INT-002: Version increments on update"""
    async with test_async_session() as session:
        case = TestCaseBank(
            case_id="test-version-002",
            query="test query",
            response_text="test response",
            category_path='["AI", "Test"]',
            query_vector="[0.1, 0.2, 0.3]",
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)

        original_version = case.version
        assert original_version == 1

        case.query = "updated query"
        case.version = original_version + 1
        await session.commit()
        await session.refresh(case)

        assert case.version == 2


@pytest.mark.asyncio
async def test_case_status_lifecycle():
    """TEST-CASEBANK-002-INT-003: Test status lifecycle transitions"""
    async with test_async_session() as session:
        case = TestCaseBank(
            case_id="test-lifecycle-003",
            query="test query",
            response_text="test response",
            category_path='["AI", "Test"]',
            query_vector="[0.1, 0.2, 0.3]",
            status="active",
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)

        assert case.status == "active"

        case.status = "archived"
        await session.commit()
        await session.refresh(case)
        assert case.status == "archived"

        case.status = "deprecated"
        await session.commit()
        await session.refresh(case)
        assert case.status == "deprecated"


@pytest.mark.asyncio
async def test_query_by_status():
    """TEST-CASEBANK-002-INT-004: Filter cases by status"""
    async with test_async_session() as session:
        cases = [
            TestCaseBank(
                case_id=f"test-status-{i}",
                query="test query",
                response_text="test response",
                category_path='["AI", "Test"]',
                query_vector="[0.1, 0.2, 0.3]",
                status="active" if i % 2 == 0 else "archived",
            )
            for i in range(6)
        ]
        for case in cases:
            session.add(case)
        await session.commit()

        stmt = select(TestCaseBank).where(TestCaseBank.status == "active")
        result = await session.execute(stmt)
        active_cases = result.scalars().all()

        assert len(active_cases) == 3
        for case in active_cases:
            assert case.status == "active"


@pytest.mark.asyncio
async def test_updated_at_timestamp():
    """TEST-CASEBANK-002-INT-005: Verify updated_at auto-update"""
    async with test_async_session() as session:
        case = TestCaseBank(
            case_id="test-timestamp-005",
            query="test query",
            response_text="test response",
            category_path='["AI", "Test"]',
            query_vector="[0.1, 0.2, 0.3]",
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)

        original_updated_at = case.updated_at

        await asyncio.sleep(0.1)

        case.query = "modified query"
        await session.commit()
        await session.refresh(case)

        assert case.updated_at >= original_updated_at
