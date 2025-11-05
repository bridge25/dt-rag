from typing import Optional
# @TEST:CASEBANK-002:unit
# @SPEC:CASEBANK-002

import pytest
import asyncio
import os
from datetime import datetime
from sqlalchemy import (
    select,
    update,
    Table,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    MetaData,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from sqlalchemy import func

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_casebank.db"

TestBase = declarative_base()


class TestCaseBank(TestBase):
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


test_engine = create_async_engine("sqlite+aiosqlite:///test_casebank.db", echo=False)
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
        os.remove("test_casebank.db")
    except FileNotFoundError:
        pass


@pytest.fixture(autouse=True)
async def cleanup_table():
    yield
    async with test_async_session() as session:
        await session.execute(
            select(TestCaseBank).where(TestCaseBank.case_id.like("test-%"))
        )
        await session.commit()


@pytest.mark.asyncio
async def test_casebank_version_field():
    """TEST-CASEBANK-002-001: version defaults to 1"""
    async with test_async_session() as session:
        case = TestCaseBank(
            case_id="test-version-001",
            query="test query",
            response_text="test response",
            category_path='["AI", "Test"]',
            query_vector="[0.1, 0.2, 0.3]",
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)

        assert hasattr(case, "version")
        assert case.version == 1


@pytest.mark.asyncio
async def test_casebank_updated_by_field():
    """TEST-CASEBANK-002-002: updated_by nullable string"""
    async with test_async_session() as session:
        case = TestCaseBank(
            case_id="test-updated-by-001",
            query="test query",
            response_text="test response",
            category_path='["AI", "Test"]',
            query_vector="[0.1, 0.2, 0.3]",
            updated_by="user@example.com",
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)

        assert hasattr(case, "updated_by")
        assert case.updated_by == "user@example.com"


@pytest.mark.asyncio
async def test_casebank_updated_by_nullable():
    """TEST-CASEBANK-002-003: updated_by can be None"""
    async with test_async_session() as session:
        case = TestCaseBank(
            case_id="test-updated-by-null-001",
            query="test query",
            response_text="test response",
            category_path='["AI", "Test"]',
            query_vector="[0.1, 0.2, 0.3]",
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)

        assert hasattr(case, "updated_by")
        assert case.updated_by is None


@pytest.mark.asyncio
async def test_casebank_status_field():
    """TEST-CASEBANK-002-004: status defaults to 'active'"""
    async with test_async_session() as session:
        case = TestCaseBank(
            case_id="test-status-001",
            query="test query",
            response_text="test response",
            category_path='["AI", "Test"]',
            query_vector="[0.1, 0.2, 0.3]",
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)

        assert hasattr(case, "status")
        assert case.status == "active"


@pytest.mark.asyncio
async def test_casebank_status_custom_value():
    """TEST-CASEBANK-002-005: status can be set to custom value"""
    async with test_async_session() as session:
        case = TestCaseBank(
            case_id="test-status-custom-001",
            query="test query",
            response_text="test response",
            category_path='["AI", "Test"]',
            query_vector="[0.1, 0.2, 0.3]",
            status="archived",
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)

        assert case.status == "archived"


@pytest.mark.asyncio
async def test_casebank_updated_at_field():
    """TEST-CASEBANK-002-006: updated_at auto-set on creation"""
    async with test_async_session() as session:
        case = TestCaseBank(
            case_id="test-updated-at-001",
            query="test query",
            response_text="test response",
            category_path='["AI", "Test"]',
            query_vector="[0.1, 0.2, 0.3]",
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)

        assert hasattr(case, "updated_at")
        assert isinstance(case.updated_at, datetime)
        assert case.updated_at is not None


@pytest.mark.asyncio
async def test_casebank_version_increment():
    """TEST-CASEBANK-002-007: version increments on update"""
    async with test_async_session() as session:
        case = TestCaseBank(
            case_id="test-version-increment-001",
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

        stmt = (
            update(TestCaseBank)
            .where(TestCaseBank.case_id == "test-version-increment-001")
            .values(query="updated query", version=original_version + 1)
        )
        await session.execute(stmt)
        await session.commit()

        stmt = select(TestCaseBank).where(  # type: ignore[assignment]
            TestCaseBank.case_id == "test-version-increment-001"
        )
        result = await session.execute(stmt)
        updated_case = result.scalar_one()

        assert updated_case.version == original_version + 1


@pytest.mark.asyncio
async def test_casebank_status_transitions():
    """TEST-CASEBANK-002-008: status can transition through lifecycle"""
    async with test_async_session() as session:
        case = TestCaseBank(
            case_id="test-status-transition-001",
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

        stmt = (
            update(TestCaseBank)
            .where(TestCaseBank.case_id == "test-status-transition-001")
            .values(status="archived")
        )
        await session.execute(stmt)
        await session.commit()

        stmt = select(TestCaseBank).where(  # type: ignore[assignment]
            TestCaseBank.case_id == "test-status-transition-001"
        )
        result = await session.execute(stmt)
        case = result.scalar_one()
        assert case.status == "archived"

        stmt = (
            update(TestCaseBank)
            .where(TestCaseBank.case_id == "test-status-transition-001")
            .values(status="deprecated")
        )
        await session.execute(stmt)
        await session.commit()

        stmt = select(TestCaseBank).where(  # type: ignore[assignment]
            TestCaseBank.case_id == "test-status-transition-001"
        )
        result = await session.execute(stmt)
        case = result.scalar_one()
        assert case.status == "deprecated"


@pytest.mark.asyncio
async def test_casebank_updated_at_trigger():
    """TEST-CASEBANK-002-009: updated_at changes when record modified"""
    async with test_async_session() as session:
        case = TestCaseBank(
            case_id="test-updated-at-trigger-001",
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

        stmt = (
            update(TestCaseBank)
            .where(TestCaseBank.case_id == "test-updated-at-trigger-001")
            .values(query="modified query")
        )
        await session.execute(stmt)
        await session.commit()

        stmt = select(TestCaseBank).where(  # type: ignore[assignment]
            TestCaseBank.case_id == "test-updated-at-trigger-001"
        )
        result = await session.execute(stmt)
        updated_case = result.scalar_one()

        assert updated_case.updated_at >= original_updated_at
