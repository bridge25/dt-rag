"""
문서 수집 API 엔드포인트
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..middleware.database import get_database_service
from ..services.database_service import DatabaseService
from ...ingestion.pipeline import IngestionPipeline
from ...ingestion.models import IngestionStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingestion"])


# 응답 모델들
class IngestResponse(BaseModel):
    """수집 작업 응답"""
    job_id: str
    message: str
    status: str


class JobStatusResponse(BaseModel):
    """작업 상태 응답"""
    job_id: str
    filename: str
    doc_hash: str
    doc_type: str
    status: str
    created_at: str
    updated_at: str
    chunks_created: int
    error_message: Optional[str] = None
    retry_count: int


class JobListResponse(BaseModel):
    """작업 목록 응답"""
    jobs: List[JobStatusResponse]
    total: int


@router.post("", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(
    file: UploadFile = File(...),
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    문서 수집 작업 제출
    
    - **file**: 업로드할 문서 파일 (PDF, Markdown, HTML 지원)
    - **Returns**: 작업 ID와 상태 정보
    
    지원 파일 형식:
    - PDF: .pdf
    - Markdown: .md, .markdown  
    - HTML: .html, .htm
    """
    try:
        # 파일 크기 제한 (10MB)
        max_size = 10 * 1024 * 1024
        content = await file.read()
        
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="파일 크기가 너무 큽니다 (최대 10MB)"
            )
        
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="빈 파일은 처리할 수 없습니다"
            )
        
        # 수집 파이프라인 초기화
        pipeline = IngestionPipeline(db_service.pool, db_service.embedding_service)
        
        # 작업 제출
        job_id = await pipeline.submit_document(
            content=content,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream"
        )
        
        return IngestResponse(
            job_id=job_id,
            message="문서 수집 작업이 제출되었습니다",
            status="accepted"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"문서 수집 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 수집 중 오류가 발생했습니다"
        )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    수집 작업 상태 조회
    
    - **job_id**: 작업 ID
    - **Returns**: 작업 상세 상태 정보
    
    상태 값:
    - pending: 대기 중
    - processing: 처리 중
    - completed: 완료됨
    - failed: 실패함
    - dlq: Dead Letter Queue (재시도 한계 초과)
    """
    try:
        pipeline = IngestionPipeline(db_service.pool, db_service.embedding_service)
        
        job_status = await pipeline.get_job_status(job_id)
        if not job_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="작업을 찾을 수 없습니다"
            )
        
        return JobStatusResponse(**job_status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"작업 상태 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="작업 상태 조회 중 오류가 발생했습니다"
        )


@router.get("/jobs", response_model=JobListResponse) 
async def list_jobs(
    status_filter: Optional[str] = None,
    limit: int = Field(50, ge=1, le=100),
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    수집 작업 목록 조회
    
    - **status**: 상태 필터 (pending, processing, completed, failed, dlq)
    - **limit**: 최대 반환 개수 (1-100)
    - **Returns**: 작업 목록
    """
    try:
        pipeline = IngestionPipeline(db_service.pool, db_service.embedding_service)
        
        # 상태 필터 검증
        ingestion_status = None
        if status_filter:
            try:
                ingestion_status = IngestionStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"잘못된 상태 값: {status_filter}"
                )
        
        jobs = await pipeline.get_job_list(
            status=ingestion_status,
            limit=limit
        )
        
        job_responses = [JobStatusResponse(**job) for job in jobs]
        
        return JobListResponse(
            jobs=job_responses,
            total=len(job_responses)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"작업 목록 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="작업 목록 조회 중 오류가 발생했습니다"
        )


@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    수집 작업 취소
    
    - **job_id**: 취소할 작업 ID
    - **Returns**: 취소 결과
    
    주의: processing 상태의 작업은 즉시 취소되지 않을 수 있습니다
    """
    try:
        pipeline = IngestionPipeline(db_service.pool, db_service.embedding_service)
        
        # 작업 존재 확인
        job_status = await pipeline.get_job_status(job_id)
        if not job_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="작업을 찾을 수 없습니다"
            )
        
        current_status = IngestionStatus(job_status["status"])
        
        # 완료된 작업은 취소할 수 없음
        if current_status in [IngestionStatus.COMPLETED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="완료된 작업은 취소할 수 없습니다"
            )
        
        # 작업 상태를 failed로 변경 (취소)
        async with db_service.pool.acquire() as conn:
            await conn.execute("""
                UPDATE ingestion_jobs
                SET status = 'failed',
                    error_message = 'User cancelled',
                    updated_at = NOW()
                WHERE job_id = $1
            """, job_id)
        
        return JSONResponse(
            content={"message": "작업이 취소되었습니다", "job_id": job_id},
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"작업 취소 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="작업 취소 중 오류가 발생했습니다"
        )


@router.get("/stats")
async def get_ingestion_stats(
    db_service: DatabaseService = Depends(get_database_service)
):
    """
    수집 작업 통계 조회
    
    - **Returns**: 상태별 작업 개수, 처리 성공률 등
    """
    try:
        async with db_service.pool.acquire() as conn:
            # 상태별 통계
            status_stats = await conn.fetch("""
                SELECT status, COUNT(*) as count
                FROM ingestion_jobs
                GROUP BY status
                ORDER BY count DESC
            """)
            
            # 최근 24시간 통계
            recent_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
                    COUNT(CASE WHEN status = 'dlq' THEN 1 END) as dlq_jobs,
                    AVG(CASE WHEN status = 'completed' THEN chunks_created END) as avg_chunks_per_doc
                FROM ingestion_jobs
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """)
            
            return {
                "status_distribution": [dict(row) for row in status_stats],
                "recent_24h": dict(recent_stats) if recent_stats else {},
                "success_rate": (
                    recent_stats["completed_jobs"] / recent_stats["total_jobs"] 
                    if recent_stats and recent_stats["total_jobs"] > 0 else 0
                )
            }
            
    except Exception as e:
        logger.error(f"통계 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="통계 조회 중 오류가 발생했습니다"
        )