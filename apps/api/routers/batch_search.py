"""
배치 검색 API 엔드포인트
HYBRID_SEARCH_OPTIMIZATION_GUIDE.md 배치 처리 API 구현

핵심 기능:
- 다중 쿼리 배치 검색
- 스트리밍 응답 지원
- 우선순위 기반 처리
- 성능 최적화 메트릭
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, AsyncGenerator
import asyncio
import time
import json
import logging
from deps import verify_api_key, generate_request_id

# 최적화 모듈들 import
from ..optimization.batch_processor import (
    get_batch_search_processor, get_batch_embedding_processor,
    get_batch_connection_pool, BatchConfig
)
from ..optimization.async_executor import get_async_optimizer
from ..optimization.memory_optimizer import get_streaming_processor
from ..optimization.concurrency_control import get_concurrency_controller

logger = logging.getLogger(__name__)
router = APIRouter()

# 요청/응답 모델들
class BatchSearchQuery(BaseModel):
    """배치 검색 개별 쿼리"""
    query_id: Optional[str] = Field(None, description="쿼리 식별자")
    q: str = Field(..., min_length=1, description="검색 쿼리")
    filters: Optional[Dict[str, Any]] = Field(None, description="검색 필터")
    bm25_topk: int = Field(12, ge=1, le=100, description="BM25 상위 K개")
    vector_topk: int = Field(12, ge=1, le=100, description="Vector 상위 K개")
    final_topk: int = Field(5, ge=1, le=50, description="최종 결과 수")
    priority: int = Field(0, ge=0, le=10, description="우선순위 (0-10)")

class BatchSearchRequest(BaseModel):
    """배치 검색 요청"""
    queries: List[BatchSearchQuery] = Field(..., min_items=1, max_items=100, description="검색 쿼리 리스트")
    batch_config: Optional[Dict[str, Any]] = Field(None, description="배치 처리 설정")
    response_format: str = Field("json", regex="^(json|stream)$", description="응답 형식")
    timeout_seconds: int = Field(30, ge=1, le=300, description="타임아웃 (초)")

    @validator('queries')
    def assign_query_ids(cls, v):
        """쿼리 ID 자동 할당"""
        for i, query in enumerate(v):
            if not query.query_id:
                query.query_id = f"query_{i}_{int(time.time() * 1000)}"
        return v

class BatchSearchResult(BaseModel):
    """배치 검색 개별 결과"""
    query_id: str
    success: bool
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    latency_ms: float
    source: str  # "batch", "individual", "cached"

class BatchSearchResponse(BaseModel):
    """배치 검색 응답"""
    request_id: str
    total_queries: int
    successful_queries: int
    failed_queries: int
    total_latency_ms: float
    avg_latency_ms: float
    batch_efficiency: float  # 배치 처리 효율성
    results: List[BatchSearchResult]
    performance_metrics: Dict[str, Any]

class StreamingBatchItem(BaseModel):
    """스트리밍 배치 아이템"""
    type: str  # "result", "progress", "complete", "error"
    query_id: Optional[str] = None
    data: Dict[str, Any]
    timestamp: float = Field(default_factory=time.time)

# 배치 검색 엔드포인트
@router.post("/batch/search", response_model=BatchSearchResponse)
async def batch_search(
    request: BatchSearchRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    배치 검색 API
    여러 쿼리를 효율적으로 배치 처리
    """
    request_id = generate_request_id()
    start_time = time.time()

    # 동시성 제어
    concurrency_controller = get_concurrency_controller()

    async with concurrency_controller.controlled_execution("batch_search"):
        try:
            if request.response_format == "stream":
                # 스트리밍 응답
                return StreamingResponse(
                    _stream_batch_search(request, request_id),
                    media_type="application/x-ndjson"
                )
            else:
                # 일반 JSON 응답
                return await _execute_batch_search(request, request_id, start_time)

        except Exception as e:
            logger.error(f"Batch search failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Batch search error: {str(e)}"
            )

async def _execute_batch_search(
    request: BatchSearchRequest,
    request_id: str,
    start_time: float
) -> BatchSearchResponse:
    """배치 검색 실행 (일반 응답)"""
    batch_processor = get_batch_search_processor()

    # 배치 설정 적용
    if request.batch_config:
        batch_config = BatchConfig(**request.batch_config)
        batch_processor.config = batch_config

    results = []
    successful_count = 0
    failed_count = 0

    try:
        # 모든 쿼리를 배치 프로세서에 제출
        search_tasks = []
        for query in request.queries:
            search_params = {
                "filters": query.filters,
                "bm25_topk": query.bm25_topk,
                "vector_topk": query.vector_topk,
                "final_topk": query.final_topk,
                "rerank_candidates": 50
            }

            task = batch_processor.submit_search_request(
                query.q,
                search_params,
                query.priority
            )
            search_tasks.append((query.query_id, task, time.time()))

        # 타임아웃과 함께 모든 검색 완료 대기
        completed_results = await asyncio.wait_for(
            asyncio.gather(*[task for _, task, _ in search_tasks], return_exceptions=True),
            timeout=request.timeout_seconds
        )

        # 결과 처리
        for (query_id, _, task_start), search_result in zip(search_tasks, completed_results):
            task_latency = (time.time() - task_start) * 1000

            if isinstance(search_result, Exception):
                results.append(BatchSearchResult(
                    query_id=query_id,
                    success=False,
                    error=str(search_result),
                    latency_ms=task_latency,
                    source="batch"
                ))
                failed_count += 1
            else:
                results.append(BatchSearchResult(
                    query_id=query_id,
                    success=True,
                    results=search_result,
                    latency_ms=task_latency,
                    source="batch"
                ))
                successful_count += 1

        # 성능 메트릭 수집
        total_latency = (time.time() - start_time) * 1000
        avg_latency = total_latency / len(request.queries) if request.queries else 0

        # 배치 효율성 계산 (예상 순차 처리 시간 대비)
        estimated_sequential_time = sum(r.latency_ms for r in results)
        batch_efficiency = estimated_sequential_time / total_latency if total_latency > 0 else 1.0

        # 배치 프로세서 메트릭
        batch_metrics = batch_processor.get_metrics()

        return BatchSearchResponse(
            request_id=request_id,
            total_queries=len(request.queries),
            successful_queries=successful_count,
            failed_queries=failed_count,
            total_latency_ms=total_latency,
            avg_latency_ms=avg_latency,
            batch_efficiency=batch_efficiency,
            results=results,
            performance_metrics={
                "batch_processor": batch_metrics.__dict__,
                "processing_breakdown": {
                    "queue_time_ms": 0,  # 큐 대기 시간 (미구현)
                    "execution_time_ms": total_latency,
                    "overhead_time_ms": max(0, total_latency - estimated_sequential_time)
                }
            }
        )

    except asyncio.TimeoutError:
        logger.error(f"Batch search timeout after {request.timeout_seconds}s")
        raise HTTPException(
            status_code=408,
            detail=f"Batch search timeout after {request.timeout_seconds} seconds"
        )

async def _stream_batch_search(
    request: BatchSearchRequest,
    request_id: str
) -> AsyncGenerator[str, None]:
    """배치 검색 스트리밍 실행"""
    batch_processor = get_batch_search_processor()
    streaming_processor = get_streaming_processor()

    try:
        # 진행 상황 초기화
        yield _format_streaming_item(StreamingBatchItem(
            type="progress",
            data={
                "message": "Starting batch search",
                "total_queries": len(request.queries),
                "completed": 0
            }
        ))

        # 각 쿼리 개별 처리 및 스트리밍
        completed_count = 0
        for query in request.queries:
            query_start = time.time()

            try:
                search_params = {
                    "filters": query.filters,
                    "bm25_topk": query.bm25_topk,
                    "vector_topk": query.vector_topk,
                    "final_topk": query.final_topk,
                    "rerank_candidates": 50
                }

                # 개별 검색 실행
                search_result = await batch_processor.submit_search_request(
                    query.q,
                    search_params,
                    query.priority
                )

                query_latency = (time.time() - query_start) * 1000

                # 결과 스트리밍
                result_item = StreamingBatchItem(
                    type="result",
                    query_id=query.query_id,
                    data={
                        "success": True,
                        "results": search_result,
                        "latency_ms": query_latency,
                        "source": "batch_stream"
                    }
                )

                yield _format_streaming_item(result_item)

                completed_count += 1

                # 진행 상황 업데이트
                if completed_count % 5 == 0 or completed_count == len(request.queries):
                    yield _format_streaming_item(StreamingBatchItem(
                        type="progress",
                        data={
                            "message": f"Completed {completed_count}/{len(request.queries)} queries",
                            "completed": completed_count,
                            "total_queries": len(request.queries),
                            "progress_percent": (completed_count / len(request.queries)) * 100
                        }
                    ))

            except Exception as e:
                # 개별 쿼리 오류
                error_item = StreamingBatchItem(
                    type="result",
                    query_id=query.query_id,
                    data={
                        "success": False,
                        "error": str(e),
                        "latency_ms": (time.time() - query_start) * 1000,
                        "source": "batch_stream"
                    }
                )
                yield _format_streaming_item(error_item)

        # 완료 메시지
        batch_metrics = batch_processor.get_metrics()
        completion_item = StreamingBatchItem(
            type="complete",
            data={
                "message": "Batch search completed",
                "request_id": request_id,
                "total_processed": completed_count,
                "batch_metrics": batch_metrics.__dict__
            }
        )
        yield _format_streaming_item(completion_item)

    except Exception as e:
        # 전체 배치 오류
        error_item = StreamingBatchItem(
            type="error",
            data={
                "message": "Batch search failed",
                "error": str(e),
                "request_id": request_id
            }
        )
        yield _format_streaming_item(error_item)

def _format_streaming_item(item: StreamingBatchItem) -> str:
    """스트리밍 아이템 포맷팅 (NDJSON)"""
    return json.dumps(item.dict()) + "\n"

# 배치 임베딩 생성 엔드포인트
class BatchEmbeddingRequest(BaseModel):
    """배치 임베딩 요청"""
    texts: List[str] = Field(..., min_items=1, max_items=1000, description="텍스트 리스트")
    model: str = Field("openai", description="임베딩 모델")
    batch_size: int = Field(100, ge=1, le=200, description="배치 크기")

class BatchEmbeddingResponse(BaseModel):
    """배치 임베딩 응답"""
    request_id: str
    total_embeddings: int
    processing_time_ms: float
    embeddings_per_second: float
    embeddings: List[List[float]]
    processing_stats: Dict[str, Any]

@router.post("/batch/embeddings", response_model=BatchEmbeddingResponse)
async def batch_generate_embeddings(
    request: BatchEmbeddingRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    배치 임베딩 생성 API
    대량 텍스트에 대한 효율적인 임베딩 생성
    """
    request_id = generate_request_id()
    start_time = time.time()

    concurrency_controller = get_concurrency_controller()

    async with concurrency_controller.controlled_execution("batch_embedding"):
        try:
            embedding_processor = get_batch_embedding_processor()

            # 배치 크기 설정
            embedding_processor.batch_size = request.batch_size

            # 배치 임베딩 생성
            embeddings = await embedding_processor.generate_batch_embeddings(
                request.texts,
                request.model
            )

            processing_time = (time.time() - start_time) * 1000
            embeddings_per_second = len(embeddings) / (processing_time / 1000) if processing_time > 0 else 0

            # 처리 통계
            processing_stats = embedding_processor.get_embedding_stats()

            return BatchEmbeddingResponse(
                request_id=request_id,
                total_embeddings=len(embeddings),
                processing_time_ms=processing_time,
                embeddings_per_second=embeddings_per_second,
                embeddings=embeddings,
                processing_stats=processing_stats
            )

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Batch embedding error: {str(e)}"
            )

# 배치 성능 분석 엔드포인트
@router.get("/batch/analytics")
async def get_batch_analytics(api_key: str = Depends(verify_api_key)):
    """
    배치 처리 성능 분석
    """
    try:
        # 각 배치 프로세서의 메트릭 수집
        search_processor = get_batch_search_processor()
        embedding_processor = get_batch_embedding_processor()
        connection_pool = get_batch_connection_pool()
        async_optimizer = await get_async_optimizer()
        streaming_processor = get_streaming_processor()

        analytics = {
            "timestamp": time.time(),
            "batch_search": {
                "metrics": search_processor.get_metrics().__dict__,
                "embedding_cache": {
                    "size": len(search_processor.embedding_cache),
                    "hits": search_processor.cache_hits,
                    "misses": search_processor.cache_misses,
                    "hit_rate": search_processor.cache_hits / max(1, search_processor.cache_hits + search_processor.cache_misses)
                }
            },
            "batch_embedding": {
                "stats": embedding_processor.get_embedding_stats()
            },
            "connection_pool": {
                "stats": connection_pool.get_connection_stats()
            },
            "async_optimizer": {
                "stats": async_optimizer.get_performance_stats()
            },
            "streaming": {
                "stats": streaming_processor.get_streaming_stats()
            }
        }

        return analytics

    except Exception as e:
        logger.error(f"Batch analytics failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analytics error: {str(e)}"
        )

# 배치 설정 업데이트 엔드포인트
class BatchConfigUpdate(BaseModel):
    """배치 설정 업데이트"""
    max_batch_size: Optional[int] = Field(None, ge=1, le=200)
    max_wait_time_ms: Optional[int] = Field(None, ge=10, le=5000)
    auto_flush: Optional[bool] = None
    enable_prioritization: Optional[bool] = None

@router.post("/batch/config")
async def update_batch_config(
    config_update: BatchConfigUpdate,
    api_key: str = Depends(verify_api_key)
):
    """
    배치 처리 설정 업데이트
    """
    try:
        search_processor = get_batch_search_processor()

        # 설정 업데이트
        if config_update.max_batch_size is not None:
            search_processor.config.max_batch_size = config_update.max_batch_size
        if config_update.max_wait_time_ms is not None:
            search_processor.config.max_wait_time_ms = config_update.max_wait_time_ms
        if config_update.auto_flush is not None:
            search_processor.config.auto_flush = config_update.auto_flush
        if config_update.enable_prioritization is not None:
            search_processor.config.enable_prioritization = config_update.enable_prioritization

        return {
            "message": "Batch configuration updated successfully",
            "current_config": search_processor.config.__dict__,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Batch config update failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Config update error: {str(e)}"
        )

# 배치 프로세서 재시작 엔드포인트
@router.post("/batch/restart")
async def restart_batch_processors(api_key: str = Depends(verify_api_key)):
    """
    배치 프로세서 재시작 (메모리 정리)
    """
    try:
        # 기존 프로세서들 정리
        search_processor = get_batch_search_processor()
        await search_processor.cleanup()

        # 전역 인스턴스 재설정
        global _global_search_processor, _global_embedding_processor, _global_connection_pool
        _global_search_processor = None
        _global_embedding_processor = None
        _global_connection_pool = None

        return {
            "message": "Batch processors restarted successfully",
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Batch processor restart failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Restart error: {str(e)}"
        )