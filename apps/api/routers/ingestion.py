"""
Document Ingestion API Router

문서 처리 파이프라인 API 엔드포인트:
- 파일 업로드 및 처리
- URL 스크래핑
- 배치 처리
- 처리 상태 조회
- PII 필터링 설정
"""

import asyncio
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uuid
import aiofiles

# 내부 모듈
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ingestion.ingestion_pipeline import (
    IngestionPipeline,
    ProcessingResult,
    BatchProcessingResult,
    ProcessingStatus,
    ProgressCallback
)
from ingestion.pii_filter import PIIType, MaskingStrategy
from ingestion.chunking_strategy import ChunkingStrategyFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingestion", tags=["Document Ingestion"])

# Pydantic 모델들
class ChunkingConfig(BaseModel):
    """청킹 설정"""
    strategy: str = Field(default="token_based", description="청킹 전략")
    chunk_size: int = Field(default=500, ge=50, le=2000, description="청크 크기")
    chunk_overlap: int = Field(default=128, ge=0, le=500, description="청크 오버랩")
    min_chunk_size: int = Field(default=50, ge=10, le=200, description="최소 청크 크기")

class PIIConfig(BaseModel):
    """PII 필터링 설정"""
    compliance_mode: str = Field(default="balanced", description="준수 모드 (strict/balanced/lenient)")
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="신뢰도 임계값")
    custom_strategies: Optional[Dict[str, str]] = Field(default=None, description="커스텀 마스킹 전략")

class ProcessingConfig(BaseModel):
    """문서 처리 설정"""
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    pii_filtering: PIIConfig = Field(default_factory=PIIConfig)
    enable_embeddings: bool = Field(default=True, description="임베딩 생성 활성화")
    batch_size: int = Field(default=10, ge=1, le=100, description="배치 크기")
    quality_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="품질 임계값")

class URLProcessingRequest(BaseModel):
    """URL 처리 요청"""
    urls: List[str] = Field(..., description="처리할 URL 목록")
    config: ProcessingConfig = Field(default_factory=ProcessingConfig)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="추가 메타데이터")

class ProcessingStatusResponse(BaseModel):
    """처리 상태 응답"""
    job_id: str
    status: str
    progress: float
    total_documents: int
    processed_documents: int
    successful: int
    failed: int
    estimated_remaining_time: Optional[float] = None
    current_task: Optional[str] = None

class ProcessingResultResponse(BaseModel):
    """처리 결과 응답"""
    job_id: str
    status: str
    total_documents: int
    successful: int
    failed: int
    skipped: int
    total_chunks: int
    total_embeddings: int
    processing_time: float
    error_summary: Dict[str, int]
    results: List[Dict[str, Any]]

# 진행 상황 추적을 위한 전역 저장소
processing_jobs: Dict[str, Dict[str, Any]] = {}

class JobProgressCallback(ProgressCallback):
    """작업 진행률 추적 콜백"""

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.start_time = datetime.utcnow()

    async def update(self, current: int, total: int, status: str, details: Dict[str, Any] = None):
        if details is None:
            details = {}

        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        progress = (current / total) if total > 0 else 0.0

        # 예상 남은 시간 계산
        if progress > 0:
            estimated_total_time = elapsed / progress
            estimated_remaining = max(0, estimated_total_time - elapsed)
        else:
            estimated_remaining = None

        # 작업 상태 업데이트
        if self.job_id in processing_jobs:
            processing_jobs[self.job_id].update({
                "progress": progress,
                "processed_documents": current,
                "current_task": status,
                "estimated_remaining_time": estimated_remaining,
                "last_updated": datetime.utcnow().isoformat(),
                "details": details
            })

@router.post("/upload", response_model=Dict[str, str])
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    config: ProcessingConfig = Body(default_factory=ProcessingConfig)
):
    """
    파일 업로드 및 처리

    여러 파일을 업로드하고 백그라운드에서 처리합니다.
    """
    job_id = str(uuid.uuid4())

    try:
        # 임시 디렉토리 생성
        temp_dir = Path(tempfile.mkdtemp())
        file_paths = []

        # 파일 저장
        for file in files:
            if file.filename:
                file_path = temp_dir / file.filename
                async with aiofiles.open(file_path, 'wb') as f:
                    content = await file.read()
                    await f.write(content)
                file_paths.append(file_path)

        # 작업 등록
        processing_jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "total_documents": len(file_paths),
            "processed_documents": 0,
            "successful": 0,
            "failed": 0,
            "progress": 0.0,
            "start_time": datetime.utcnow().isoformat(),
            "temp_dir": str(temp_dir)
        }

        # 백그라운드 작업 시작
        background_tasks.add_task(
            process_files_background,
            job_id,
            file_paths,
            config
        )

        return {"job_id": job_id, "status": "started"}

    except Exception as e:
        logger.error(f"파일 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/urls", response_model=Dict[str, str])
async def process_urls(
    request: URLProcessingRequest,
    background_tasks: BackgroundTasks
):
    """
    URL 스크래핑 및 처리

    여러 URL을 스크래핑하고 백그라운드에서 처리합니다.
    """
    job_id = str(uuid.uuid4())

    try:
        # 작업 등록
        processing_jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "total_documents": len(request.urls),
            "processed_documents": 0,
            "successful": 0,
            "failed": 0,
            "progress": 0.0,
            "start_time": datetime.utcnow().isoformat()
        }

        # 백그라운드 작업 시작
        background_tasks.add_task(
            process_urls_background,
            job_id,
            request.urls,
            request.config,
            request.metadata
        )

        return {"job_id": job_id, "status": "started"}

    except Exception as e:
        logger.error(f"URL 처리 요청 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}", response_model=ProcessingStatusResponse)
async def get_processing_status(job_id: str):
    """
    처리 상태 조회
    """
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job_info = processing_jobs[job_id]

    return ProcessingStatusResponse(
        job_id=job_id,
        status=job_info["status"],
        progress=job_info["progress"],
        total_documents=job_info["total_documents"],
        processed_documents=job_info["processed_documents"],
        successful=job_info["successful"],
        failed=job_info["failed"],
        estimated_remaining_time=job_info.get("estimated_remaining_time"),
        current_task=job_info.get("current_task")
    )

@router.get("/result/{job_id}", response_model=ProcessingResultResponse)
async def get_processing_result(job_id: str):
    """
    처리 결과 조회
    """
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job_info = processing_jobs[job_id]

    if job_info["status"] not in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Job not completed yet")

    result = job_info.get("result", {})

    return ProcessingResultResponse(
        job_id=job_id,
        status=job_info["status"],
        total_documents=result.get("total_documents", 0),
        successful=result.get("successful", 0),
        failed=result.get("failed", 0),
        skipped=result.get("skipped", 0),
        total_chunks=result.get("total_chunks", 0),
        total_embeddings=result.get("total_embeddings", 0),
        processing_time=result.get("processing_time", 0.0),
        error_summary=result.get("error_summary", {}),
        results=[r.__dict__ if hasattr(r, '__dict__') else r for r in result.get("results", [])]
    )

@router.get("/jobs", response_model=List[Dict[str, Any]])
async def list_processing_jobs(
    status: Optional[str] = Query(None, description="상태별 필터링"),
    limit: int = Query(50, ge=1, le=100, description="결과 개수 제한")
):
    """
    처리 작업 목록 조회
    """
    jobs = list(processing_jobs.values())

    # 상태별 필터링
    if status:
        jobs = [job for job in jobs if job["status"] == status]

    # 시간순 정렬 (최신순)
    jobs.sort(key=lambda x: x["start_time"], reverse=True)

    return jobs[:limit]

@router.delete("/job/{job_id}")
async def cancel_job(job_id: str):
    """
    작업 취소
    """
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job_info = processing_jobs[job_id]

    if job_info["status"] in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Job already finished")

    # 작업 취소 표시
    job_info["status"] = "cancelled"

    # 임시 파일 정리
    if "temp_dir" in job_info:
        temp_dir = Path(job_info["temp_dir"])
        if temp_dir.exists():
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"임시 디렉토리 삭제 실패: {e}")

    return {"status": "cancelled"}

@router.get("/config/chunking-strategies")
async def get_chunking_strategies():
    """
    사용 가능한 청킹 전략 목록
    """
    return {
        "strategies": ChunkingStrategyFactory.get_available_strategies(),
        "recommendations": {
            "code": {"strategy": "semantic", "chunk_size": 800},
            "structured": {"strategy": "adaptive", "chunk_size": 600},
            "short_text": {"strategy": "semantic", "chunk_size": 400},
            "long_text": {"strategy": "token_based", "chunk_size": 500},
            "default": {"strategy": "token_based", "chunk_size": 500}
        }
    }

@router.get("/config/pii-types")
async def get_pii_types():
    """
    지원하는 PII 타입 및 마스킹 전략
    """
    return {
        "pii_types": [pii_type.value for pii_type in PIIType],
        "masking_strategies": [strategy.value for strategy in MaskingStrategy],
        "compliance_modes": ["strict", "balanced", "lenient"],
        "default_strategies": {
            "strict": {
                "email": "redact",
                "phone": "redact",
                "ssn_kr": "redact",
                "credit_card": "redact"
            },
            "balanced": {
                "email": "partial",
                "phone": "partial",
                "ssn_kr": "hash",
                "credit_card": "partial"
            },
            "lenient": {
                "email": "mask",
                "phone": "mask",
                "ssn_kr": "partial",
                "credit_card": "mask"
            }
        }
    }

@router.get("/analytics")
async def get_ingestion_analytics():
    """
    문서 처리 분석 정보
    """
    # 최근 작업들의 통계
    recent_jobs = list(processing_jobs.values())[-100:]  # 최근 100개

    total_jobs = len(recent_jobs)
    completed_jobs = len([j for j in recent_jobs if j["status"] == "completed"])
    failed_jobs = len([j for j in recent_jobs if j["status"] == "failed"])

    # 평균 처리 시간 계산
    completed_with_result = [j for j in recent_jobs
                           if j["status"] == "completed" and "result" in j]

    avg_processing_time = 0.0
    if completed_with_result:
        total_time = sum(j["result"]["processing_time"] for j in completed_with_result)
        avg_processing_time = total_time / len(completed_with_result)

    return {
        "total_jobs": total_jobs,
        "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
        "failure_rate": (failed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
        "avg_processing_time": avg_processing_time,
        "active_jobs": len([j for j in recent_jobs if j["status"] in ["pending", "processing"]]),
        "supported_formats": [".txt", ".pdf", ".html", ".md", ".csv", ".json", "URL"],
        "pipeline_health": "healthy" if failed_jobs / max(1, total_jobs) < 0.1 else "degraded"
    }

# 백그라운드 작업 함수들
async def process_files_background(
    job_id: str,
    file_paths: List[Path],
    config: ProcessingConfig
):
    """파일 처리 백그라운드 작업"""
    try:
        processing_jobs[job_id]["status"] = "processing"

        # 파이프라인 설정
        pipeline = create_pipeline_from_config(config)

        # 진행률 콜백
        progress_callback = JobProgressCallback(job_id)

        # 배치 처리 실행
        result = await pipeline.process_batch(
            file_paths,
            progress_callback=progress_callback
        )

        # 결과 저장
        processing_jobs[job_id].update({
            "status": "completed",
            "successful": result.successful,
            "failed": result.failed,
            "result": {
                "total_documents": result.total_documents,
                "successful": result.successful,
                "failed": result.failed,
                "skipped": result.skipped,
                "total_chunks": result.total_chunks,
                "total_embeddings": result.total_embeddings,
                "processing_time": result.processing_time,
                "error_summary": result.error_summary,
                "results": result.results
            }
        })

    except Exception as e:
        logger.error(f"백그라운드 파일 처리 실패 ({job_id}): {e}")
        processing_jobs[job_id].update({
            "status": "failed",
            "error": str(e)
        })

    finally:
        # 임시 파일 정리
        if "temp_dir" in processing_jobs[job_id]:
            temp_dir = Path(processing_jobs[job_id]["temp_dir"])
            if temp_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"임시 디렉토리 삭제 실패: {e}")

async def process_urls_background(
    job_id: str,
    urls: List[str],
    config: ProcessingConfig,
    metadata: Optional[Dict[str, Any]] = None
):
    """URL 처리 백그라운드 작업"""
    try:
        processing_jobs[job_id]["status"] = "processing"

        # 파이프라인 설정
        pipeline = create_pipeline_from_config(config)

        # 진행률 콜백
        progress_callback = JobProgressCallback(job_id)

        # URL 배치 처리 실행
        result = await pipeline.process_url_batch(
            urls,
            progress_callback=progress_callback
        )

        # 결과 저장
        processing_jobs[job_id].update({
            "status": "completed",
            "successful": result.successful,
            "failed": result.failed,
            "result": {
                "total_documents": result.total_documents,
                "successful": result.successful,
                "failed": result.failed,
                "skipped": result.skipped,
                "total_chunks": result.total_chunks,
                "total_embeddings": result.total_embeddings,
                "processing_time": result.processing_time,
                "error_summary": result.error_summary,
                "results": result.results
            }
        })

    except Exception as e:
        logger.error(f"백그라운드 URL 처리 실패 ({job_id}): {e}")
        processing_jobs[job_id].update({
            "status": "failed",
            "error": str(e)
        })

def create_pipeline_from_config(config: ProcessingConfig) -> IngestionPipeline:
    """설정으로부터 파이프라인 생성"""

    # 청킹 파라미터 준비
    chunking_params = {
        "chunk_size": config.chunking.chunk_size,
        "chunk_overlap": config.chunking.chunk_overlap,
        "min_chunk_size": config.chunking.min_chunk_size
    }

    # PII 필터 설정
    from ingestion.pii_filter import PIIFilter
    pii_filter = PIIFilter(compliance_mode=config.pii_filtering.compliance_mode)

    # 파이프라인 생성
    pipeline = IngestionPipeline(
        chunking_strategy=config.chunking.strategy,
        chunking_params=chunking_params,
        pii_filter=pii_filter,
        enable_embeddings=config.enable_embeddings,
        batch_size=config.batch_size,
        quality_threshold=config.quality_threshold
    )

    return pipeline