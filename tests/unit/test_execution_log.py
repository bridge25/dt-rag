# @TEST:REFLECTION-001:unit:execution_log
# @SPEC:REFLECTION-001

import pytest
import os
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_execution_log.db"

TestBase = declarative_base()

import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from apps.api.database import ExecutionLog, CaseBank

test_engine = create_async_engine(
    "sqlite+aiosqlite:///test_execution_log.db", echo=False
)
test_async_session = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(CaseBank.metadata.create_all)
        await conn.run_sync(ExecutionLog.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(ExecutionLog.metadata.drop_all)
        await conn.run_sync(CaseBank.metadata.drop_all)
    await test_engine.dispose()
    try:
        os.remove("test_execution_log.db")
    except FileNotFoundError:
        pass


@pytest.fixture(autouse=True)
async def cleanup_table():
    yield
    async with test_async_session() as session:
        await session.execute(
            select(ExecutionLog).where(ExecutionLog.case_id.like("test-%"))
        )
        await session.execute(select(CaseBank).where(CaseBank.case_id.like("test-%")))
        await session.commit()


@pytest.mark.asyncio
async def test_execution_log_creation():
    """TEST-REFLECTION-001-001: Create log with success=True"""
    async with test_async_session() as session:
        case = CaseBank(
            case_id="test-case-001",
            query="test query",
            response_text="test response",
            category_path=["AI", "Test"],
            query_vector=[0.1, 0.2, 0.3],
            status="active",
            version=1,
        )
        session.add(case)
        await session.commit()

        log = ExecutionLog(case_id="test-case-001", success=True, execution_time_ms=150)
        session.add(log)
        await session.commit()
        await session.refresh(log)

        assert log.log_id is not None
        assert log.case_id == "test-case-001"
        assert log.success is True
        assert log.execution_time_ms == 150
        assert log.created_at is not None


@pytest.mark.asyncio
async def test_execution_log_failure():
    """TEST-REFLECTION-001-002: Create log with error details"""
    async with test_async_session() as session:
        case = CaseBank(
            case_id="test-case-002",
            query="test query",
            response_text="test response",
            category_path=["AI", "Test"],
            query_vector=[0.1, 0.2, 0.3],
            status="active",
            version=1,
        )
        session.add(case)
        await session.commit()

        log = ExecutionLog(
            case_id="test-case-002",
            success=False,
            error_type="ValidationError",
            error_message="Invalid input parameters",
            execution_time_ms=50,
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)

        assert log.success is False
        assert log.error_type == "ValidationError"
        assert log.error_message == "Invalid input parameters"
        assert log.execution_time_ms == 50


@pytest.mark.asyncio
async def test_execution_log_foreign_key():
    """TEST-REFLECTION-001-003: Verify case_id FK to CaseBank"""
    async with test_async_session() as session:
        case = CaseBank(
            case_id="test-case-003",
            query="test query",
            response_text="test response",
            category_path=["AI", "Test"],
            query_vector=[0.1, 0.2, 0.3],
            status="active",
            version=1,
        )
        session.add(case)
        await session.commit()

        log = ExecutionLog(case_id="test-case-003", success=True, execution_time_ms=100)
        session.add(log)
        await session.commit()

        stmt = select(ExecutionLog).where(ExecutionLog.case_id == "test-case-003")
        result = await session.execute(stmt)
        fetched_log = result.scalar_one()

        assert fetched_log.case_id == "test-case-003"
        assert fetched_log.case is not None
        assert fetched_log.case.case_id == "test-case-003"


@pytest.mark.asyncio
async def test_execution_log_nullable_fields():
    """TEST-REFLECTION-001-004: error_type, error_message can be NULL"""
    async with test_async_session() as session:
        case = CaseBank(
            case_id="test-case-004",
            query="test query",
            response_text="test response",
            category_path=["AI", "Test"],
            query_vector=[0.1, 0.2, 0.3],
            status="active",
            version=1,
        )
        session.add(case)
        await session.commit()

        log = ExecutionLog(case_id="test-case-004", success=True)
        session.add(log)
        await session.commit()
        await session.refresh(log)

        assert log.error_type is None
        assert log.error_message is None
        assert log.execution_time_ms is None


@pytest.mark.asyncio
async def test_execution_log_timestamp():
    """TEST-REFLECTION-001-005: created_at auto-sets to now()"""
    async with test_async_session() as session:
        case = CaseBank(
            case_id="test-case-005",
            query="test query",
            response_text="test response",
            category_path=["AI", "Test"],
            query_vector=[0.1, 0.2, 0.3],
            status="active",
            version=1,
        )
        session.add(case)
        await session.commit()

        log = ExecutionLog(case_id="test-case-005", success=True)
        session.add(log)
        await session.commit()
        await session.refresh(log)

        assert log.created_at is not None
        assert isinstance(log.created_at, datetime)
