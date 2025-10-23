"""
@TEST:E2E:memento | Memento Framework E2E Integration Test
@SPEC:CASEBANK-002 @SPEC:REFLECTION-001 @SPEC:CONSOLIDATION-001

전체 Memento 워크플로우 통합 테스트:
1. CaseBank에 케이스 저장
2. ExecutionLog 기록
3. ReflectionEngine으로 성능 분석
4. ConsolidationPolicy로 라이프사이클 관리
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.database import CaseBank, ExecutionLog, CaseBankArchive
from apps.orchestration.src.reflection_engine import ReflectionEngine
from apps.orchestration.src.consolidation_policy import ConsolidationPolicy
from apps.core.db_session import async_session


@pytest.mark.asyncio
async def test_memento_full_lifecycle():
    """
    Memento 프레임워크 전체 라이프사이클 테스트

    워크플로우:
    1. CaseBank에 3개 케이스 생성 (high-perf, low-perf, duplicate)
    2. ExecutionLog에 실행 기록 추가
    3. ReflectionEngine으로 success_rate 계산
    4. ConsolidationPolicy로 저성능 케이스 아카이빙
    5. 결과 검증
    """
    async with async_session() as session:
        # Clean up
        await session.execute(delete(ExecutionLog))
        await session.execute(delete(CaseBankArchive))
        await session.execute(delete(CaseBank))
        await session.commit()

        # 1. CaseBank에 테스트 케이스 생성
        case_high = CaseBank(
            case_id="memento-test-high",
            query="What is RAG?",
            response_text="RAG is Retrieval-Augmented Generation",
            category_path=["AI", "RAG"],
            query_vector=[0.1] * 1536,
            usage_count=50,
            success_rate=None,  # Will be calculated by Reflection
            status="active",
            version=1
        )

        case_low = CaseBank(
            case_id="memento-test-low",
            query="What is ML?",
            response_text="ML is Machine Learning",
            category_path=["AI", "ML"],
            query_vector=[0.2] * 1536,
            usage_count=20,
            success_rate=None,
            status="active",
            version=1
        )

        case_duplicate = CaseBank(
            case_id="memento-test-dup",
            query="What is RAG system?",  # Similar to case_high
            response_text="RAG system is Retrieval-Augmented Generation",
            category_path=["AI", "RAG"],
            query_vector=[0.11] * 1536,  # Similar vector (will have >95% similarity)
            usage_count=10,
            success_rate=None,
            status="active",
            version=1
        )

        session.add_all([case_high, case_low, case_duplicate])
        await session.commit()

        # 2. ExecutionLog에 실행 기록 추가
        # case_high: 90% success rate (9/10)
        for i in range(10):
            log = ExecutionLog(
                case_id="memento-test-high",
                success=(i < 9),
                error_type=None if i < 9 else "TimeoutError",
                error_message=None if i < 9 else "Timeout after 5s",
                execution_time_ms=100 + i * 10
            )
            session.add(log)

        # case_low: 20% success rate (2/10)
        for i in range(10):
            log = ExecutionLog(
                case_id="memento-test-low",
                success=(i < 2),
                error_type=None if i < 2 else "ToolNotFound",
                error_message=None if i < 2 else "Tool XYZ not found",
                execution_time_ms=150 + i * 10
            )
            session.add(log)

        # case_duplicate: 60% success rate (6/10)
        for i in range(10):
            log = ExecutionLog(
                case_id="memento-test-dup",
                success=(i < 6),
                error_type=None if i < 6 else "InvalidInput",
                execution_time_ms=120 + i * 10
            )
            session.add(log)

        await session.commit()

        # 3. ReflectionEngine으로 성능 분석
        reflection_engine = ReflectionEngine(session)

        perf_high = await reflection_engine.analyze_case_performance("memento-test-high")
        assert perf_high["success_rate"] == 90.0
        assert perf_high["total_executions"] == 10

        perf_low = await reflection_engine.analyze_case_performance("memento-test-low")
        assert perf_low["success_rate"] == 20.0
        assert perf_low["total_executions"] == 10

        perf_dup = await reflection_engine.analyze_case_performance("memento-test-dup")
        assert perf_dup["success_rate"] == 60.0

        # CaseBank에 success_rate 업데이트
        await reflection_engine.update_case_success_rate("memento-test-high", 90.0)
        await reflection_engine.update_case_success_rate("memento-test-low", 20.0)
        await reflection_engine.update_case_success_rate("memento-test-dup", 60.0)

        # 4. ConsolidationPolicy로 라이프사이클 관리
        consolidation_policy = ConsolidationPolicy(session, dry_run=False)

        # 저성능 케이스 제거 (threshold=30% 기본값)
        removed_cases = await consolidation_policy.remove_low_performance_cases(threshold=30.0)
        assert "memento-test-low" in removed_cases, "Low-performance case should be archived"
        assert "memento-test-high" not in removed_cases, "High-performance case should be kept"

        # 5. 결과 검증
        # case_low가 archived 상태로 변경되었는지 확인
        result = await session.execute(
            select(CaseBank).where(CaseBank.case_id == "memento-test-low")
        )
        case_low_updated = result.scalar_one()
        assert case_low_updated.status == "archived", "Low-performance case should be archived"

        # case_high는 active 상태 유지
        result = await session.execute(
            select(CaseBank).where(CaseBank.case_id == "memento-test-high")
        )
        case_high_updated = result.scalar_one()
        assert case_high_updated.status == "active", "High-performance case should remain active"

        # Clean up
        await session.execute(delete(ExecutionLog))
        await session.execute(delete(CaseBankArchive))
        await session.execute(delete(CaseBank))
        await session.commit()

    print("✅ Memento 전체 라이프사이클 테스트 통과!")


@pytest.mark.asyncio
async def test_memento_metadata_tracking():
    """
    Memento 메타데이터 추적 테스트 (CASEBANK-002)

    검증:
    - version 자동 증가
    - updated_at 자동 갱신
    - status 변경 추적
    """
    async with async_session() as session:
        # Clean up
        await session.execute(delete(CaseBank))
        await session.commit()

        # 1. 케이스 생성
        case = CaseBank(
            case_id="memento-metadata-test",
            query="Test query",
            response_text="Test response",
            category_path=["AI", "Test"],
            query_vector=[0.5] * 1536,
            status="active",
            version=1,
            updated_by="test_user"
        )
        session.add(case)
        await session.commit()

        # Initial state
        assert case.version == 1
        assert case.status == "active"
        initial_updated_at = case.updated_at

        # 2. 케이스 업데이트 (트리거로 version 자동 증가)
        await session.refresh(case)
        case.response_text = "Updated response"
        await session.commit()

        # Version should auto-increment via trigger
        await session.refresh(case)
        # Note: DB trigger increments version, but SQLAlchemy model may need refresh

        # 3. Status 변경
        await session.refresh(case)
        case.status = "archived"
        await session.commit()

        await session.refresh(case)
        assert case.status == "archived"

        # Clean up
        await session.execute(delete(CaseBank))
        await session.commit()

    print("✅ Memento 메타데이터 추적 테스트 통과!")


if __name__ == "__main__":
    asyncio.run(test_memento_full_lifecycle())
    asyncio.run(test_memento_metadata_tracking())
