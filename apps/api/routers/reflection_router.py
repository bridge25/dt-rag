"""
@CODE:REFLECTION-001:API @CODE:TEST-003:REFLECTION-ROUTER | SPEC: SPEC-REFLECTION-001.md | TEST: tests/unit/test_reflection_engine.py
@CODE:TEST-003 | SPEC: SPEC-TEST-003.md | TEST: tests/performance/
Reflection API Router - 케이스 성능 분석 및 개선 제안
"""

import logging
import os

# Import ReflectionEngine
import sys
from datetime import datetime
from typing import Any, Dict, Optional

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

from reflection_engine import ReflectionEngine

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/reflection", tags=["reflection"])


# Pydantic Models
class ReflectionAnalysisRequest(BaseModel):
    """케이스 성능 분석 요청"""

    case_id: str = Field(..., description="분석할 케이스 ID")
    limit: int = Field(default=100, description="분석할 최근 로그 개수", ge=1, le=1000)


class ReflectionAnalysisResponse(BaseModel):
    """케이스 성능 분석 응답"""

    case_id: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    avg_execution_time_ms: float
    common_errors: list[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReflectionBatchResponse(BaseModel):
    """배치 Reflection 응답"""

    analyzed_cases: int
    low_performance_cases: int
    suggestions: list[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ImprovementSuggestionsRequest(BaseModel):
    """개선 제안 생성 요청"""

    case_id: str = Field(..., description="케이스 ID")


class ImprovementSuggestionsResponse(BaseModel):
    """개선 제안 응답"""

    case_id: str
    suggestions: list[str]
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Dependency: Get ReflectionEngine instance
async def get_reflection_engine() -> None:
    """ReflectionEngine 인스턴스 생성"""
    async with db_manager.get_session() as session:
        engine = ReflectionEngine(db_session=session)
        yield engine


# API Endpoints
@router.post("/analyze", response_model=ReflectionAnalysisResponse)
async def analyze_case_performance(
    request: ReflectionAnalysisRequest, api_key: APIKeyInfo = Depends(verify_api_key)
):
    """
    단일 케이스 성능 분석

    케이스의 실행 로그를 분석하여:
    - 성공률 계산
    - 평균 실행 시간 측정
    - 공통 에러 패턴 추출
    """
    try:
        async with db_manager.get_session() as session:
            engine = ReflectionEngine(db_session=session)
            performance = await engine.analyze_case_performance(
                case_id=request.case_id, limit=request.limit
            )

        return ReflectionAnalysisResponse(**performance)

    except Exception as e:
        logger.error(f"케이스 성능 분석 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"케이스 성능 분석 중 오류 발생: {str(e)}",
        )


@router.post("/batch", response_model=ReflectionBatchResponse)
async def run_reflection_batch(api_key: APIKeyInfo = Depends(verify_api_key)) -> None:
    """
    배치 Reflection 실행

    모든 활성 케이스를 분석하여:
    - 성공률 업데이트
    - 저성능 케이스 발견
    - 개선 제안 생성
    """
    try:
        async with db_manager.get_session() as session:
            engine = ReflectionEngine(db_session=session)
            results = await engine.run_reflection_batch()

        return ReflectionBatchResponse(**results)

    except Exception as e:
        logger.error(f"배치 Reflection 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"배치 Reflection 중 오류 발생: {str(e)}",
        )


@router.post("/suggestions", response_model=ImprovementSuggestionsResponse)
async def generate_improvement_suggestions(
    request: ImprovementSuggestionsRequest,
    api_key: APIKeyInfo = Depends(verify_api_key),
):
    """
    개선 제안 생성 (LLM 기반)

    케이스의 성능 데이터를 분석하여 LLM으로 개선 제안 생성
    """
    try:
        async with db_manager.get_session() as session:
            engine = ReflectionEngine(db_session=session)
            suggestions = await engine.generate_improvement_suggestions(
                case_id=request.case_id
            )

        # Determine confidence based on suggestions count and LLM availability
        confidence = 0.8 if len(suggestions) > 0 else 0.0

        return ImprovementSuggestionsResponse(
            case_id=request.case_id, suggestions=suggestions, confidence=confidence
        )

    except Exception as e:
        logger.error(f"개선 제안 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"개선 제안 생성 중 오류 발생: {str(e)}",
        )


@router.get("/health")
async def health_check() -> None:
    """Reflection 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "reflection",
        "timestamp": datetime.utcnow().isoformat(),
    }
