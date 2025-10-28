"""
벡터 임베딩 서비스 API 라우터
Sentence Transformers 기반 실제 벡터 생성 및 관리
"""

# @CODE:EMBED-001 | SPEC: .moai/specs/SPEC-EMBED-001/spec.md | TEST: tests/test_embedding_service.py

from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..embedding_service import (
    embedding_service,
    generate_embedding,
    generate_embeddings,
    calculate_similarity,
    update_document_embeddings,
    get_embedding_status,
    get_service_info,
    health_check,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/embeddings",
    tags=["embeddings"],
    responses={404: {"description": "Not found"}},
)


@router.get("/health", response_model=Dict[str, Any])
async def get_embedding_health():
    """임베딩 서비스 헬스체크"""
    try:
        health_status = health_check()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "embedding_service",
            **health_status,
        }
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info", response_model=Dict[str, Any])
async def get_embedding_info():
    """임베딩 서비스 정보 조회"""
    try:
        service_info = get_service_info()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "embedding_service",
            **service_info,
        }
    except Exception as e:
        logger.error(f"서비스 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=Dict[str, Any])
async def get_embeddings_status():
    """임베딩 데이터베이스 상태 조회"""
    try:
        status = await get_embedding_status()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "document_embedding_service",
            **status,
        }
    except Exception as e:
        logger.error(f"임베딩 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=Dict[str, Any])
async def generate_text_embedding(
    text: str = Body(..., description="임베딩을 생성할 텍스트", embed=True),
    use_cache: bool = Body(True, description="캐시 사용 여부", embed=True),
):
    """단일 텍스트의 임베딩 생성"""
    try:
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="텍스트가 비어있습니다")

        embedding = await generate_embedding(text, use_cache=use_cache)

        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "embedding": embedding,
            "dimensions": len(embedding),
            "model": embedding_service.model_name,
            "cached": use_cache,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"임베딩 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/batch", response_model=Dict[str, Any])
async def generate_batch_embeddings(
    texts: List[str] = Body(..., description="임베딩을 생성할 텍스트 목록"),
    batch_size: int = Body(32, description="배치 크기", ge=1, le=100),
):
    """여러 텍스트의 배치 임베딩 생성"""
    try:
        if not texts:
            raise HTTPException(status_code=400, detail="텍스트 목록이 비어있습니다")

        if len(texts) > 1000:
            raise HTTPException(
                status_code=400, detail="텍스트 개수가 1000개를 초과할 수 없습니다"
            )

        # 빈 텍스트 필터링
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            raise HTTPException(status_code=400, detail="유효한 텍스트가 없습니다")

        embeddings = await generate_embeddings(valid_texts, batch_size=batch_size)

        return {
            "total_texts": len(texts),
            "valid_texts": len(valid_texts),
            "embeddings": embeddings,
            "dimensions": len(embeddings[0]) if embeddings else 0,
            "model": embedding_service.model_name,
            "batch_size": batch_size,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"배치 임베딩 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similarity", response_model=Dict[str, Any])
async def calculate_embedding_similarity(
    embedding1: List[float] = Body(..., description="첫 번째 임베딩 벡터"),
    embedding2: List[float] = Body(..., description="두 번째 임베딩 벡터"),
):
    """두 임베딩 간의 코사인 유사도 계산"""
    try:
        if not embedding1 or not embedding2:
            raise HTTPException(status_code=400, detail="임베딩 벡터가 비어있습니다")

        if len(embedding1) != len(embedding2):
            raise HTTPException(
                status_code=400,
                detail=f"임베딩 차원이 다릅니다: {len(embedding1)} vs {len(embedding2)}",
            )

        similarity = calculate_similarity(embedding1, embedding2)

        return {
            "similarity": similarity,
            "embedding1_dimensions": len(embedding1),
            "embedding2_dimensions": len(embedding2),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"유사도 계산 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/update", response_model=Dict[str, Any])
async def update_documents_embeddings(
    background_tasks: BackgroundTasks,
    document_ids: Optional[List[str]] = Body(
        None, description="업데이트할 문서 ID 목록 (None이면 모든 문서)"
    ),
    batch_size: int = Body(10, description="배치 크기", ge=1, le=50),
    run_in_background: bool = Body(False, description="백그라운드에서 실행할지 여부"),
):
    """문서들의 임베딩 업데이트"""
    try:
        if run_in_background:
            # 백그라운드에서 실행
            background_tasks.add_task(
                update_document_embeddings, document_ids, batch_size
            )

            return {
                "message": "임베딩 업데이트가 백그라운드에서 시작되었습니다",
                "document_ids": document_ids,
                "batch_size": batch_size,
                "started_at": datetime.utcnow().isoformat(),
            }
        else:
            # 동기 실행
            result = await update_document_embeddings(document_ids, batch_size)
            return {"completed_at": datetime.utcnow().isoformat(), **result}

    except Exception as e:
        logger.error(f"문서 임베딩 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear", response_model=Dict[str, Any])
async def clear_embedding_cache():
    """임베딩 캐시 클리어"""
    try:
        cleared_count = embedding_service.clear_cache()

        return {
            "message": "임베딩 캐시가 클리어되었습니다",
            "cleared_items": cleared_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"캐시 클리어 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=Dict[str, Any])
async def get_supported_models():
    """지원하는 모델 목록 조회"""
    try:
        return {
            "supported_models": embedding_service.SUPPORTED_MODELS,
            "current_model": embedding_service.model_name,
            "target_dimensions": embedding_service.TARGET_DIMENSIONS,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"모델 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics", response_model=Dict[str, Any])
async def get_embedding_analytics():
    """임베딩 시스템 분석 정보"""
    try:
        # 서비스 상태
        service_health = health_check()
        service_info = get_service_info()
        db_status = await get_embedding_status()

        # @CODE:MYPY-CONSOLIDATION-002 | Phase 2: Fix attr-defined (list type annotation)
        recommendations: List[str] = []

        # 권장사항 생성
        if service_health.get("status") != "healthy":
            recommendations.append("임베딩 서비스 상태를 확인하세요")

        if not service_info.get("sentence_transformers_available"):
            recommendations.append(
                "sentence-transformers 라이브러리를 설치하세요"
            )

        embedding_coverage = db_status.get("embedding_coverage_percent", 0)
        if embedding_coverage < 100:
            recommendations.append(
                f"임베딩 커버리지가 {embedding_coverage:.1f}%입니다. 문서 임베딩 업데이트를 실행하세요"
            )

        if not recommendations:
            recommendations.append("시스템이 정상 상태입니다")

        # 종합 분석
        analysis = {
            "service_health": service_health,
            "service_info": service_info,
            "database_status": db_status,
            "recommendations": recommendations,
        }

        return {"timestamp": datetime.utcnow().isoformat(), **analysis}

    except Exception as e:
        logger.error(f"임베딩 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
