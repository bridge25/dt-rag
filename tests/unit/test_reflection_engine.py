# @TEST:REFLECTION-001:unit:reflection_engine
# @SPEC:REFLECTION-001

import pytest
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import AsyncMock, MagicMock

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_reflection_engine.db"

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from apps.api.database import ExecutionLog, CaseBank
from apps.orchestration.src.reflection_engine import ReflectionEngine

test_engine = create_async_engine("sqlite+aiosqlite:///test_reflection_engine.db", echo=False)
test_async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


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
        os.remove("test_reflection_engine.db")
    except FileNotFoundError:
        pass


@pytest.fixture(autouse=True)
async def cleanup_table():
    yield
    async with test_async_session() as session:
        await session.execute(select(ExecutionLog).where(ExecutionLog.case_id.like("test-%")))
        await session.execute(select(CaseBank).where(CaseBank.case_id.like("test-%")))
        await session.commit()


@pytest.fixture
async def reflection_engine():
    async with test_async_session() as session:
        engine = ReflectionEngine(session, llm_client=None)
        return engine


@pytest.mark.asyncio
async def test_analyze_case_performance():
    """TEST-REFLECTION-001-006: Calculate success_rate from logs"""
    async with test_async_session() as session:
        case = CaseBank(
            case_id="test-case-perf-001",
            query="test query",
            response_text="test response",
            category_path=["AI", "Test"],
            query_vector=[0.1, 0.2, 0.3],
            status="active",
            version=1
        )
        session.add(case)
        await session.commit()

        for i in range(10):
            log = ExecutionLog(
                case_id="test-case-perf-001",
                success=(i < 7),
                execution_time_ms=100 + i * 10
            )
            session.add(log)
        await session.commit()

        engine = ReflectionEngine(session, llm_client=None)
        performance = await engine.analyze_case_performance("test-case-perf-001")

        assert performance["case_id"] == "test-case-perf-001"
        assert performance["total_executions"] == 10
        assert performance["successful_executions"] == 7
        assert performance["success_rate"] == 70.0
        assert performance["avg_execution_time_ms"] > 0


@pytest.mark.asyncio
async def test_error_pattern_analysis():
    """TEST-REFLECTION-001-007: Group errors by type"""
    async with test_async_session() as session:
        case = CaseBank(
            case_id="test-case-error-001",
            query="test query",
            response_text="test response",
            category_path=["AI", "Test"],
            query_vector=[0.1, 0.2, 0.3],
            status="active",
            version=1
        )
        session.add(case)
        await session.commit()

        error_types = ["ValidationError"] * 5 + ["TimeoutError"] * 3 + ["NetworkError"] * 2
        for i, error_type in enumerate(error_types):
            log = ExecutionLog(
                case_id="test-case-error-001",
                success=False,
                error_type=error_type,
                error_message=f"Error {i}"
            )
            session.add(log)
        await session.commit()

        engine = ReflectionEngine(session, llm_client=None)
        performance = await engine.analyze_case_performance("test-case-error-001")

        common_errors = performance["common_errors"]
        assert len(common_errors) == 3
        assert common_errors[0]["error_type"] == "ValidationError"
        assert common_errors[0]["count"] == 5
        assert common_errors[0]["percentage"] == 50.0


@pytest.mark.asyncio
async def test_avg_execution_time():
    """TEST-REFLECTION-001-008: Calculate average timing"""
    async with test_async_session() as session:
        case = CaseBank(
            case_id="test-case-time-001",
            query="test query",
            response_text="test response",
            category_path=["AI", "Test"],
            query_vector=[0.1, 0.2, 0.3],
            status="active",
            version=1
        )
        session.add(case)
        await session.commit()

        execution_times = [100, 200, 300, 400, 500]
        for time_ms in execution_times:
            log = ExecutionLog(
                case_id="test-case-time-001",
                success=True,
                execution_time_ms=time_ms
            )
            session.add(log)
        await session.commit()

        engine = ReflectionEngine(session, llm_client=None)
        performance = await engine.analyze_case_performance("test-case-time-001")

        assert performance["avg_execution_time_ms"] == 300.0


@pytest.mark.asyncio
async def test_success_rate_zero_logs():
    """TEST-REFLECTION-001-009: Handle no logs gracefully"""
    async with test_async_session() as session:
        case = CaseBank(
            case_id="test-case-nologs-001",
            query="test query",
            response_text="test response",
            category_path=["AI", "Test"],
            query_vector=[0.1, 0.2, 0.3],
            status="active",
            version=1
        )
        session.add(case)
        await session.commit()

        engine = ReflectionEngine(session, llm_client=None)
        performance = await engine.analyze_case_performance("test-case-nologs-001")

        assert performance["case_id"] == "test-case-nologs-001"
        assert performance["total_executions"] == 0
        assert performance["success_rate"] == 0.0
        assert performance["common_errors"] == []
        assert performance["avg_execution_time_ms"] == 0.0


@pytest.mark.asyncio
async def test_generate_improvement_suggestions_low_performance():
    """TEST-REFLECTION-001-010: LLM call for success_rate < 50%"""
    async with test_async_session() as session:
        case = CaseBank(
            case_id="test-case-low-perf-001",
            query="test query for low performance",
            response_text="test response with issues",
            category_path=["AI", "Test"],
            query_vector=[0.1, 0.2, 0.3],
            status="active",
            version=1
        )
        session.add(case)
        await session.commit()

        for i in range(10):
            log = ExecutionLog(
                case_id="test-case-low-perf-001",
                success=(i < 3),
                error_type="ValidationError" if i >= 3 else None,
                execution_time_ms=200
            )
            session.add(log)
        await session.commit()

        mock_llm = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """1. Improve input validation
2. Add better error handling
3. Optimize execution time"""
        mock_llm.chat.completions.create = AsyncMock(return_value=mock_response)

        engine = ReflectionEngine(session, llm_client=mock_llm)
        suggestions = await engine.generate_improvement_suggestions("test-case-low-perf-001")

        assert len(suggestions) > 0
        assert any("validation" in s.lower() for s in suggestions)
        mock_llm.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_improvement_suggestions_high_performance():
    """TEST-REFLECTION-001-011: Skip LLM for success_rate >= 80%"""
    async with test_async_session() as session:
        case = CaseBank(
            case_id="test-case-high-perf-001",
            query="test query",
            response_text="test response",
            category_path=["AI", "Test"],
            query_vector=[0.1, 0.2, 0.3],
            status="active",
            version=1
        )
        session.add(case)
        await session.commit()

        for i in range(10):
            log = ExecutionLog(
                case_id="test-case-high-perf-001",
                success=(i < 9),
                execution_time_ms=100
            )
            session.add(log)
        await session.commit()

        mock_llm = AsyncMock()
        engine = ReflectionEngine(session, llm_client=mock_llm)
        suggestions = await engine.generate_improvement_suggestions("test-case-high-perf-001")

        assert suggestions == []
        mock_llm.chat.completions.create.assert_not_called()


@pytest.mark.asyncio
async def test_run_reflection_batch():
    """TEST-REFLECTION-001-012: Batch process multiple cases"""
    async with test_async_session() as session:
        from sqlalchemy import delete

        await session.execute(delete(ExecutionLog).where(ExecutionLog.case_id.like("test-%")))
        await session.execute(delete(CaseBank).where(CaseBank.case_id.like("test-%")))
        await session.commit()

        for case_num in range(3):
            case = CaseBank(
                case_id=f"test-case-batch-{case_num:03d}",
                query=f"test query {case_num}",
                response_text=f"test response {case_num}",
                category_path=["AI", "Test"],
                query_vector=[0.1, 0.2, 0.3],
                status="active",
                version=1
            )
            session.add(case)
            await session.commit()

            success_count = 2 if case_num == 0 else 7
            for i in range(10):
                log = ExecutionLog(
                    case_id=f"test-case-batch-{case_num:03d}",
                    success=(i < success_count),
                    execution_time_ms=100
                )
                session.add(log)
        await session.commit()

        engine = ReflectionEngine(session, llm_client=None)
        results = await engine.run_reflection_batch(min_logs=10)

        assert results["analyzed_cases"] == 3
        assert results["low_performance_cases"] >= 1


@pytest.mark.asyncio
async def test_update_case_success_rate():
    """TEST-REFLECTION-001-013: Update CaseBank.success_rate"""
    async with test_async_session() as session:
        case = CaseBank(
            case_id="test-case-update-001",
            query="test query",
            response_text="test response",
            category_path=["AI", "Test"],
            query_vector=[0.1, 0.2, 0.3],
            status="active",
            version=1,
            success_rate=None
        )
        session.add(case)
        await session.commit()

        engine = ReflectionEngine(session, llm_client=None)
        await engine.update_case_success_rate("test-case-update-001", 85.5)

        stmt = select(CaseBank).where(CaseBank.case_id == "test-case-update-001")
        result = await session.execute(stmt)
        updated_case = result.scalar_one()

        assert updated_case.success_rate == 85.5
