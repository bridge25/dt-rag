# @TEST:REFLECTION-001:integration
# @SPEC:REFLECTION-001

import pytest
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_reflection_workflow.db"

import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from apps.api.database import (
    ExecutionLog,
    CaseBank,
    optimize_execution_log_indices,
)
from apps.orchestration.src.reflection_engine import ReflectionEngine

test_engine = create_async_engine(
    "sqlite+aiosqlite:///test_reflection_workflow.db", echo=False
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
        os.remove("test_reflection_workflow.db")
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
async def test_full_reflection_workflow():
    """TEST-REFLECTION-001-014: Full reflection workflow end-to-end"""
    async with test_async_session() as session:
        # 1. Create test case
        case = CaseBank(
            case_id="test-workflow-001",
            query="How does RAG work?",
            answer="RAG combines retrieval with generation",
            category_path=["AI", "RAG"],
            query_vector=[0.1, 0.2, 0.3],
            status="active",
            version=1,
        )
        session.add(case)
        await session.commit()

        # 2. Record execution logs (low performance)
        for i in range(15):
            log = ExecutionLog(
                case_id="test-workflow-001",
                success=(i < 5),  # 33.3% success rate
                error_type="ValidationError" if i >= 5 else None,
                error_message=f"Error {i}" if i >= 5 else None,
                execution_time_ms=100 + i * 10,
            )
            session.add(log)
        await session.commit()

        # 3. Run reflection analysis
        engine = ReflectionEngine(session, llm_client=None)
        performance = await engine.analyze_case_performance("test-workflow-001")

        # 4. Verify performance metrics
        assert performance["case_id"] == "test-workflow-001"
        assert performance["total_executions"] == 15
        assert performance["successful_executions"] == 5
        assert performance["success_rate"] == 33.33

        # 5. Generate improvement suggestions
        suggestions = await engine.generate_improvement_suggestions("test-workflow-001")
        assert len(suggestions) > 0

        # 6. Update case success rate
        await engine.update_case_success_rate(
            "test-workflow-001", performance["success_rate"]
        )

        # 7. Verify CaseBank updated
        stmt = select(CaseBank).where(CaseBank.case_id == "test-workflow-001")
        result = await session.execute(stmt)
        updated_case = result.scalar_one()
        assert updated_case.success_rate == 33.33


@pytest.mark.asyncio
async def test_batch_reflection_with_multiple_cases():
    """TEST-REFLECTION-001-015: Batch reflection with mixed performance"""
    async with test_async_session() as session:
        # Clean up all test data first
        from sqlalchemy import delete

        await session.execute(
            delete(ExecutionLog).where(ExecutionLog.case_id.like("test-%"))
        )
        await session.execute(delete(CaseBank).where(CaseBank.case_id.like("test-%")))
        await session.commit()

        # Create 3 cases with different performance levels
        cases_data = [
            ("test-batch-low-001", 2, 10),  # 20% success
            ("test-batch-medium-001", 6, 10),  # 60% success
            ("test-batch-high-001", 9, 10),  # 90% success
        ]

        for case_id, success_count, total_count in cases_data:
            case = CaseBank(
                case_id=case_id,
                query=f"Query for {case_id}",
                answer=f"Response for {case_id}",
                category_path=["AI", "Test"],
                query_vector=[0.1, 0.2, 0.3],
                status="active",
                version=1,
            )
            session.add(case)
            await session.commit()

            for i in range(total_count):
                log = ExecutionLog(
                    case_id=case_id,
                    success=(i < success_count),
                    execution_time_ms=100,
                )
                session.add(log)
        await session.commit()

        # Run batch reflection
        engine = ReflectionEngine(session, llm_client=None)
        results = await engine.run_reflection_batch(min_logs=10)

        # Verify batch results
        assert results["analyzed_cases"] == 3
        assert results["low_performance_cases"] >= 1  # At least the 20% case


@pytest.mark.asyncio
async def test_index_optimization():
    """TEST-REFLECTION-001-016: ExecutionLog index optimization"""
    async with test_async_session() as session:
        # Create indices
        result = await optimize_execution_log_indices(session)

        # Verify indices created
        assert result["success"] is True
        assert len(result["indices_created"]) == 3
        assert "execution_log_case_id" in result["indices_created"]
        assert "execution_log_created_at" in result["indices_created"]
        assert "execution_log_success" in result["indices_created"]
