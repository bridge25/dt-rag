"""
Classification Router
텍스트 분류 API 엔드포인트
"""

import logging
import time
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse

from common_schemas.models import ClassifyRequest, ClassifyResponse
from ..services.database_service import get_database_service, DatabaseService
from ..middleware.monitoring import CLASSIFICATION_CONFIDENCE, HITL_QUEUE_SIZE

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=ClassifyResponse,
    summary="혼합 분류 파이프라인",
    description="""
    룰→LLM→교차검증 체인으로 문서 청크를 분류
    - 1단계: 룰 기반 1차 분류 (민감도/패턴 매칭)
    - 2단계: LLM 2차 분류 (후보 경로 + 근거≥2)
    - 3단계: 교차검증 로직 (룰 vs LLM 결과 비교)
    - 4단계: Confidence<0.7 → HITL 처리
    """,
    responses={
        200: {"description": "분류 성공"},
        400: {"description": "잘못된 요청"},
        403: {"description": "권한 부족"},
        422: {"description": "요청 데이터 검증 실패"}, 
        429: {"description": "요청 한도 초과"},
        500: {"description": "서버 내부 오류"}
    }
)
async def classify_text(
    request_data: ClassifyRequest,
    request: Request,
    db_service: DatabaseService = Depends(get_database_service)
) -> ClassifyResponse:
    """텍스트 분류 API"""
    
    start_time = time.time()
    
    try:
        # Request validation
        if not request_data.text or not request_data.text.strip():
            raise HTTPException(
                status_code=422,
                detail="Text field is required and cannot be empty"
            )
        
        if len(request_data.text) > 10000:  # 텍스트 길이 제한
            raise HTTPException(
                status_code=422,
                detail="Text length exceeds maximum limit (10,000 characters)"
            )
        
        # Set complexity factor for cost estimation
        text_length = len(request_data.text)
        if text_length > 5000:
            request.state.complexity_factor = 2.0
        elif text_length > 2000:
            request.state.complexity_factor = 1.5
        else:
            request.state.complexity_factor = 1.0
        
        # Get taxonomy version from request or use default
        taxonomy_version = getattr(request_data, "taxonomy_version", "1.8.1")
        request.state.taxonomy_version = taxonomy_version
        
        logger.info(
            f"Classification request: {len(request_data.text)} chars, "
            f"version={taxonomy_version}, request_id={request.state.request_id}"
        )
        
        # Perform classification using database service
        classification_result = await db_service.classify_text(
            text=request_data.text,
            taxonomy_version=taxonomy_version
        )
        
        # Record confidence metric
        confidence = classification_result["confidence"]
        CLASSIFICATION_CONFIDENCE.observe(confidence)
        
        # Update HITL queue size metric
        await _update_hitl_queue_metrics(db_service)
        
        # Build response according to OpenAPI spec
        response_data = ClassifyResponse(
            canonical=classification_result["canonical"],
            candidates=classification_result.get("candidates", []),
            confidence=confidence,
            reasoning=classification_result.get("reasoning", [])
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        logger.info(
            f"Classification completed: path={classification_result['canonical']}, "
            f"confidence={confidence:.3f}, time={processing_time:.3f}s"
        )
        
        # Check performance target (p95 ≤ 4s)
        if processing_time > 4.0:
            logger.warning(
                f"Classification exceeded p95 target: {processing_time:.3f}s > 4.0s"
            )
        
        return response_data
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            f"Classification failed: {e}, request_id={request.state.request_id}",
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail="Internal server error during classification"
        )


@router.get(
    "/stats",
    summary="분류 통계 정보",
    description="분류 시스템의 통계 정보 조회"
)
async def get_classification_stats(
    request: Request,
    db_service: DatabaseService = Depends(get_database_service)
) -> Dict[str, Any]:
    """분류 시스템 통계 조회"""
    
    try:
        async with db_service.get_connection() as conn:
            
            # Get classification statistics
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_classifications,
                    AVG(confidence) as avg_confidence,
                    COUNT(CASE WHEN confidence < 0.7 THEN 1 END) as low_confidence_count,
                    COUNT(CASE WHEN confidence >= 0.9 THEN 1 END) as high_confidence_count
                FROM doc_taxonomy
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """)
            
            # Get HITL queue stats
            hitl_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_queued,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved,
                    AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))) as avg_resolution_time
                FROM hitl_queue
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """)
            
            # Get taxonomy distribution
            taxonomy_dist = await conn.fetch("""
                SELECT 
                    path[1] as top_category,
                    COUNT(*) as count
                FROM doc_taxonomy
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY path[1]
                ORDER BY count DESC
                LIMIT 10
            """)
            
            return {
                "period": "24_hours",
                "classification_stats": dict(stats) if stats else {},
                "hitl_stats": dict(hitl_stats) if hitl_stats else {},
                "taxonomy_distribution": [dict(row) for row in taxonomy_dist],
                "timestamp": time.time()
            }
            
    except Exception as e:
        logger.error(f"Failed to get classification stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve classification statistics"
        )


async def _update_hitl_queue_metrics(db_service: DatabaseService):
    """HITL 큐 메트릭 업데이트"""
    try:
        async with db_service.get_connection() as conn:
            queue_size = await conn.fetchval("""
                SELECT COUNT(*) FROM hitl_queue WHERE status = 'pending'
            """)
            HITL_QUEUE_SIZE.set(queue_size or 0)
            
    except Exception as e:
        logger.warning(f"Failed to update HITL queue metrics: {e}")


# Health check specific to classification service
@router.get("/health")
async def classify_health_check(
    db_service: DatabaseService = Depends(get_database_service)
):
    """분류 서비스 건강 상태 확인"""
    
    try:
        # Test database connection
        async with db_service.get_connection() as conn:
            await conn.fetchval("SELECT 1")
        
        # Test embedding service
        from ..services.embedding_service import get_embedding_service
        embedding_service = get_embedding_service()
        
        if not embedding_service.model:
            return {"status": "degraded", "reason": "Embedding model not loaded"}
        
        # Quick classification test
        test_result = await db_service.classify_text("test classification")
        
        return {
            "status": "healthy", 
            "test_confidence": test_result["confidence"],
            "features": ["rule_based", "vector_similarity", "hitl_queue"]
        }
        
    except Exception as e:
        logger.error(f"Classify health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}