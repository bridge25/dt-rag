"""
@CODE:CONSOLIDATION-001:API | SPEC: SPEC-CONSOLIDATION-001.md | TEST: tests/unit/test_consolidation.py
@CODE:MYPY-001:PHASE2:BATCH4 | SPEC: SPEC-MYPY-001.md | TEST: N/A
Consolidation API Router - 메모리 정리 및 최적화
"""

import logging
import os

# Import ConsolidationPolicy
import sys
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

# Import database session
from ..database import db_manager

# Import API Key authentication
from ..deps import verify_api_key
from ..security.api_key_storage import APIKeyInfo

# Add orchestration to path
orchestration_src = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../apps/orchestration/src")
)
if orchestration_src not in sys.path:
    sys.path.insert(0, orchestration_src)

from consolidation_policy import ConsolidationPolicy  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/consolidation", tags=["consolidation"])


# Pydantic Models
class ConsolidationRequest(BaseModel):
    """Consolidation 실행 요청"""

    dry_run: bool = Field(default=False, description="시뮬레이션 모드 (실제 변경 없음)")
    threshold: float = Field(
        default=30.0, description="성공률 임계값 (%)", ge=0, le=100
    )
    similarity_threshold: float = Field(
        default=0.95, description="유사도 임계값", ge=0, le=1.0
    )
    inactive_days: int = Field(default=90, description="비활성 케이스 기준 (일)", ge=1)


class ConsolidationResponse(BaseModel):
    """Consolidation 실행 응답"""

    removed_cases: int
    merged_cases: int
    archived_cases: int
    dry_run: bool
    details: Dict[str, Any]
    timestamp: str


class ConsolidationSummaryResponse(BaseModel):
    """Consolidation 후보 요약"""

    total_active_cases: int
    low_performance_candidates: int
    inactive_candidates: int
    potential_savings: int
    timestamp: str


# API Endpoints
@router.post("/run", response_model=ConsolidationResponse)
async def run_consolidation(
    request: ConsolidationRequest, api_key: APIKeyInfo = Depends(verify_api_key)
) -> ConsolidationResponse:
    """
    메모리 Consolidation 실행

    다음 3가지 정책을 실행:
    1. 저성능 케이스 제거 (success_rate < threshold)
    2. 중복 케이스 병합 (similarity > similarity_threshold)
    3. 비활성 케이스 아카이빙 (inactive_days 초과)
    """
    try:
        async with await db_manager.get_session() as session:
            policy = ConsolidationPolicy(db_session=session, dry_run=request.dry_run)
            results = await policy.run_consolidation()

        logger.info(
            f"Consolidation {'simulated' if request.dry_run else 'executed'}: "
            f"removed={results['removed_cases']}, "
            f"merged={results['merged_cases']}, "
            f"archived={results['archived_cases']}"
        )

        return ConsolidationResponse(**results)

    except Exception as e:
        logger.error(f"Consolidation 실행 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Consolidation 실행 중 오류 발생: {str(e)}",
        )


@router.post("/dry-run", response_model=ConsolidationResponse)
async def dry_run_consolidation(
    api_key: APIKeyInfo = Depends(verify_api_key),
) -> ConsolidationResponse:
    """
    Consolidation 시뮬레이션 (변경 없음)

    실제 변경 없이 Consolidation 결과를 미리 확인합니다.
    """
    try:
        async with await db_manager.get_session() as session:
            policy = ConsolidationPolicy(db_session=session, dry_run=True)
            results = await policy.run_consolidation()

        logger.info(f"Consolidation dry-run completed: {results}")
        return ConsolidationResponse(**results)

    except Exception as e:
        logger.error(f"Consolidation dry-run 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Consolidation dry-run 중 오류 발생: {str(e)}",
        )


@router.get("/summary", response_model=ConsolidationSummaryResponse)
async def get_consolidation_summary(
    api_key: APIKeyInfo = Depends(verify_api_key),
) -> ConsolidationSummaryResponse:
    """
    Consolidation 후보 요약 조회

    현재 Consolidation 대상이 될 수 있는 케이스 통계를 반환합니다.
    """
    try:
        async with await db_manager.get_session() as session:
            policy = ConsolidationPolicy(db_session=session)
            summary = await policy.get_consolidation_summary()

        return ConsolidationSummaryResponse(**summary)

    except Exception as e:
        logger.error(f"Consolidation 요약 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Consolidation 요약 조회 중 오류 발생: {str(e)}",
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Consolidation 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "consolidation",
        "timestamp": datetime.utcnow().isoformat(),
    }
