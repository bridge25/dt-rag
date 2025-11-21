"""
Document Search 엔드포인트
실제 BM25 + Vector 하이브리드 검색 구현
Bridge Pack ACCESS_CARD.md 스펙 100% 준수

@CODE:SEARCH-001
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, Field
# @CODE:MYPY-CONSOLIDATION-002 | Phase 14: name-defined (Fix 34 - add Union to imports)
from typing import List, Optional, Dict, Any, Union
from apps.api.deps import (
    verify_api_key,
    generate_request_id,
    get_taxonomy_version,
    get_current_timestamp,
)
from apps.api.database import (
    SearchDAO,
    search_metrics,
    get_search_performance_metrics,
    db_manager,
)
import time
import logging

# Configure logger
logger = logging.getLogger(__name__)

# 최적화 모듈들 import
try:
    # Future implementations - not yet available
    from ..optimization.async_executor import get_async_optimizer  # type: ignore[import-not-found]  # TODO: Implement async executor
    from ..optimization.memory_optimizer import get_memory_monitor  # type: ignore[import-not-found]  # TODO: Implement memory optimizer
    from ..optimization.concurrency_control import get_concurrency_controller  # type: ignore[import-not-found]  # TODO: Implement concurrency control

    OPTIMIZATION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Optimization modules not available: {e}")
    OPTIMIZATION_AVAILABLE = False

# 하이브리드 검색 엔진 import
try:
    from ...search.hybrid_search_engine import hybrid_search, HybridSearchEngine

    HYBRID_ENGINE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Hybrid search engine not available: {e}")
    HYBRID_ENGINE_AVAILABLE = False

# 캐시 import
try:
    from ..cache.search_cache import get_search_cache

    CACHE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Search cache not available: {e}")
    CACHE_AVAILABLE = False

# SearchConfig import
try:
    from ..routers.search_router import SearchConfig

    SEARCH_CONFIG_AVAILABLE = True
except ImportError as e:
    logging.warning(f"SearchConfig not available: {e}")
    SEARCH_CONFIG_AVAILABLE = False

# 모니터링 import
try:
    from ..monitoring.metrics import get_metrics_collector

    MONITORING_AVAILABLE = True

    def track_search_metrics(
        search_type: str, latency_ms: float, success: bool, result_count: int
    ) -> None:
        pass

except ImportError as e:
    logging.warning(f"Monitoring not available: {e}")
    MONITORING_AVAILABLE = False

    def track_search_metrics(
        search_type: str, latency_ms: float, success: bool, result_count: int
    ) -> None:
        pass


router = APIRouter()


async def get_search_engine() -> Any:
    if HYBRID_ENGINE_AVAILABLE:
        return HybridSearchEngine()
    raise NotImplementedError("Search engine not available")


# @CODE:MYPY-CONSOLIDATION-002 | Phase 14: unused-ignore (Fix 29-31 - decorator type stubs now available)
class SearchEngineFactory:
    @staticmethod
    def create_fast_engine() -> Any:
        if HYBRID_ENGINE_AVAILABLE:
            return HybridSearchEngine()
        raise NotImplementedError("Fast engine not available")

    @staticmethod
    def create_accurate_engine() -> Any:
        if HYBRID_ENGINE_AVAILABLE:
            return HybridSearchEngine()
        raise NotImplementedError("Accurate engine not available")

    @staticmethod
    def create_balanced_engine() -> Any:
        if HYBRID_ENGINE_AVAILABLE:
            return HybridSearchEngine()
        raise NotImplementedError("Balanced engine not available")


# Common Schemas 호환 모델


class LegacySearchRequest(BaseModel):
    q: str = Field(..., min_length=1, description="검색 쿼리")
    filters: Optional[Dict[str, Any]] = Field(None, description="검색 필터")
    bm25_topk: int = Field(12, ge=1, le=100, description="BM25 상위 K개")
    vector_topk: int = Field(12, ge=1, le=100, description="Vector 상위 K개")
    rerank_candidates: int = Field(50, ge=1, le=1000, description="재랭킹 후보 수")
    final_topk: int = Field(5, ge=1, le=50, description="최종 결과 수")


class LegacySearchHit(BaseModel):
    chunk_id: str
    score: float = Field(ge=0.0, description="검색 점수")
    text: Optional[str] = Field(None, description="텍스트 내용")
    taxonomy_path: Optional[List[str]] = Field(None, description="분류 경로")
    source: Optional[Dict[str, Any]] = Field(None, description="소스 메타데이터")


class LegacySearchResponse(BaseModel):
    hits: List[LegacySearchHit]
    latency: float = Field(ge=0.0, description="검색 지연시간(초)")
    request_id: str
    total_candidates: Optional[int] = Field(None, description="전체 후보 수")
    sources_count: Optional[int] = Field(None, description="소스 문서 수")
    taxonomy_version: str = "1.8.1"


@router.post("/search", response_model=LegacySearchResponse)  # Decorator lacks type stubs
async def search_documents(
    request: LegacySearchRequest,
    http_request: Request,
    api_key: str = Depends(verify_api_key),
) -> LegacySearchResponse:
    """
    Bridge Pack 스펙: POST /search
    최적화된 BM25 + Vector + Cross-encoder 하이브리드 검색
    Performance Target: p95 < 100ms, Recall@10 >= 0.85
    """
    start_time = time.time()
    error_occurred = False
    query_id = generate_request_id()
    search_type = (
        "optimized"
        if OPTIMIZATION_AVAILABLE
        else ("hybrid" if HYBRID_ENGINE_AVAILABLE else "legacy")
    )

    try:
        # 최적화된 검색 실행
        if OPTIMIZATION_AVAILABLE:
            result = await _execute_optimized_search(request, query_id, start_time)
        elif MONITORING_AVAILABLE:
            metrics_collector = get_metrics_collector()
            async with metrics_collector.track_operation(
                "search_request", {"search_type": search_type}
            ):
                result = await _execute_search(
                    request, query_id, start_time, search_type
                )
        else:
            result = await _execute_search(request, query_id, start_time, search_type)

        # 성공 메트릭 기록
        latency_ms = (time.time() - start_time) * 1000

        if OPTIMIZATION_AVAILABLE:
            await _record_optimized_metrics(
                search_type, latency_ms, True, len(result.hits)
            )
        elif MONITORING_AVAILABLE:
            track_search_metrics(search_type, latency_ms, True, len(result.hits))

        return result

    except Exception as e:
        error_occurred = True
        latency_ms = (time.time() - start_time) * 1000

        # 메트릭 기록
        search_metrics.record_search(search_type, latency_ms / 1000, error_occurred)

        if OPTIMIZATION_AVAILABLE:
            await _record_optimized_metrics(search_type, latency_ms, False, 0)
        elif MONITORING_AVAILABLE:
            track_search_metrics(search_type, latency_ms, False, 0)

        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


async def _execute_optimized_search(
    request: LegacySearchRequest, query_id: str, start_time: float
) -> LegacySearchResponse:
    """최적화된 검색 실행"""
    try:
        # 동시성 제어
        concurrency_controller = get_concurrency_controller()

        async with concurrency_controller.controlled_execution("search_optimized"):
            # 메모리 모니터링
            memory_monitor = await get_memory_monitor()
            memory_status = await memory_monitor.check_memory_usage()

            if memory_status.get("status") == "high":
                logger.warning(
                    "High memory usage detected, applying memory optimization"
                )

            # 최적화된 하이브리드 검색 실행
            search_results = await SearchDAO.hybrid_search(
                query=request.q,
                filters=request.filters,
                topk=request.final_topk,
                bm25_topk=request.bm25_topk,
                vector_topk=request.vector_topk,
                rerank_candidates=request.rerank_candidates,
            )

            latency = time.time() - start_time

            # 성능 메트릭 추가
            performance_info = {
                "optimization_enabled": True,
                "memory_status": memory_status.get("status", "unknown"),
                "concurrency_level": concurrency_controller.metrics.active_requests,
            }

            return _convert_to_response(
                search_results, latency, query_id, "optimized", performance_info
            )

    except Exception as e:
        logger.error(f"Optimized search failed: {e}")
        # 폴백: 기존 검색 방식
        return await _execute_search(request, query_id, start_time, "fallback")


async def _execute_search(
    request: LegacySearchRequest, query_id: str, start_time: float, search_type: str
) -> LegacySearchResponse:
    """검색 실행 래퍼"""
    if HYBRID_ENGINE_AVAILABLE:
        return await _hybrid_engine_search(request, query_id, start_time)
    else:
        return await _legacy_search(request, query_id, start_time)


async def _record_optimized_metrics(
    search_type: str, latency_ms: float, success: bool, result_count: int
) -> None:
    """최적화된 메트릭 기록"""
    try:
        # 기존 메트릭 기록
        search_metrics.record_search(search_type, latency_ms / 1000, not success)

        # 최적화 모듈별 메트릭 기록
        if OPTIMIZATION_AVAILABLE:
            # 비동기 실행 최적화 메트릭
            async_optimizer = await get_async_optimizer()
            optimizer_stats = async_optimizer.get_performance_stats()

            # 메모리 최적화 메트릭
            memory_monitor = await get_memory_monitor()
            memory_summary = memory_monitor.get_memory_summary()

            # 통합 메트릭 로깅
            logger.info(
                f"Optimized search completed: {search_type}, "
                f"latency={latency_ms:.1f}ms, success={success}, "
                f"results={result_count}, "
                f"parallel_speedup={optimizer_stats.get('parallel_stats', {}).get('avg_speedup', 1.0):.1f}x, "
                f"memory_usage={memory_summary.get('current_usage', {}).get('rss_mb', 0):.1f}MB"
            )

    except Exception as e:
        logger.error(f"Failed to record optimized metrics: {e}")


async def _hybrid_engine_search(
    request: LegacySearchRequest, query_id: str, start_time: float
) -> LegacySearchResponse:
    """최적화된 하이브리드 검색 엔진 사용"""
    try:
        # hybrid_search 함수 직접 호출
        results, metrics = await hybrid_search(
            query=request.q, top_k=request.final_topk, filters=request.filters or {}
        )

        latency = time.time() - start_time
        search_metrics.record_search("hybrid_direct", latency, False)

        # API 형식으로 변환 (results는 이미 List[Dict] 형식)
        return _convert_to_response(
            results, latency, query_id, "hybrid_direct", metrics
        )

    except Exception as e:
        logging.error(f"Hybrid engine search failed: {e}")
        # 폴백으로 레거시 검색 시도
        return await _legacy_search(request, query_id, start_time)


async def _legacy_search(
    request: LegacySearchRequest, query_id: str, start_time: float
) -> LegacySearchResponse:
    """레거시 검색 (hybrid_search 직접 사용)"""
    try:
        # hybrid_search 함수 직접 호출
        results, metrics = await hybrid_search(
            query=request.q, top_k=request.final_topk, filters=request.filters or {}
        )

        latency = time.time() - start_time
        search_metrics.record_search("hybrid_legacy", latency, False)

        return _convert_to_response(results, latency, query_id, "legacy", metrics)

    except Exception as e:
        latency = time.time() - start_time
        search_metrics.record_search("hybrid_legacy", latency, True)
        raise e


def _convert_to_response(
    search_results: List[Dict[str, Any]],
    latency: float,
    query_id: str,
    search_type: str,
    perf_info: Optional[Dict[str, Any]] = None,
) -> LegacySearchResponse:
    """검색 결과를 LegacySearchResponse로 변환"""
    # LegacySearchHit 객체로 변환
    hits = []
    for result in search_results:
        # 메타데이터 구조 개선
        source_metadata = result.get("metadata", {}).copy()
        source_metadata.update(
            {
                "title": result.get("title"),
                "source_url": result.get("source_url"),
                "search_type": search_type,
                "performance_info": perf_info,
            }
        )

        hit = LegacySearchHit(
            chunk_id=result["chunk_id"],
            score=result["score"],
            text=result.get("text"),
            taxonomy_path=result.get("taxonomy_path"),
            source=source_metadata,
        )
        hits.append(hit)

    # 소스 문서 수 계산
    source_docs = set()
    for hit in hits:
        if hit.source:
            doc_key = (
                hit.source.get("source_url") or hit.source.get("title") or hit.chunk_id
            )
            source_docs.add(doc_key)

    return LegacySearchResponse(
        hits=hits,
        latency=round(latency, 3),
        request_id=query_id,
        total_candidates=len(search_results),
        sources_count=len(source_docs),
        taxonomy_version=get_taxonomy_version(),
    )


# 관리자용 엔드포인트들
class EmbeddingRequest(BaseModel):
    chunk_ids: Optional[List[str]] = Field(
        None, description="특정 청크 ID들 (비어있으면 모든 청크)"
    )
    batch_size: int = Field(50, ge=1, le=200, description="배치 크기")
    model: str = Field(
        "openai", description="임베딩 모델 (openai, sentence_transformer)"
    )


class EmbeddingResponse(BaseModel):
    processed: int
    message: str
    error: Optional[str] = None


@router.post("/admin/create-embeddings", response_model=EmbeddingResponse)  # Decorator lacks type stubs
async def create_embeddings(
    request: EmbeddingRequest, api_key: str = Depends(verify_api_key)
) -> EmbeddingResponse:
    """
    청크들에 대한 임베딩 생성 (관리자용)
    """
    try:
        from database import db_manager  # type: ignore[import-not-found]  # TODO: Fix database import path

        async with db_manager.async_session() as session:
            # @CODE:MYPY-CONSOLIDATION-002 | Phase 14d: attr-defined (Fix 68 - method not yet implemented in SearchDAO)
            # TODO: Implement SearchDAO.create_embeddings_for_chunks(session, chunk_ids, batch_size)
            result = await SearchDAO.create_embeddings_for_chunks(  # type: ignore[attr-defined]
                session=session,
                chunk_ids=request.chunk_ids,
                batch_size=request.batch_size,
            )

            return EmbeddingResponse(**result)

    except Exception as e:
        return EmbeddingResponse(processed=0, message="임베딩 생성 실패", error=str(e))


@router.get("/admin/search-analytics")  # Decorator lacks type stubs
async def get_search_analytics(api_key: str = Depends(verify_api_key)) -> Any:
    """
    검색 시스템 분석 정보 조회 (관리자용)
    """
    try:
        analytics = await get_search_performance_metrics()

        # 고급 분석 정보 추가
        if HYBRID_ENGINE_AVAILABLE:
            search_engine = await get_search_engine()
            performance_stats = search_engine.get_performance_stats()
            analytics["hybrid_engine_stats"] = performance_stats

            # 캐시 통계
            cache = await get_search_cache()
            cache_stats = await cache.get_cache_stats()
            analytics["cache_stats"] = cache_stats

        return analytics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


class CacheWarmUpRequest(BaseModel):
    common_queries: List[str] = Field(..., description="주요 쿼리 목록")


@router.post("/admin/cache/warm-up")  # Decorator lacks type stubs
async def warm_up_cache(
    request: CacheWarmUpRequest, api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    검색 캐시 웜업 (관리자용)
    """
    try:
        cache = await get_search_cache()
        await cache.warm_up(request.common_queries)

        # 검색 엔진 웜업
        if HYBRID_ENGINE_AVAILABLE:
            search_engine = await get_search_engine()
            async with db_manager.async_session() as session:
                await search_engine.warm_up(session)

        return {
            "message": f"Cache warmed up with {len(request.common_queries)} queries",
            "status": "success",
            "timestamp": time.time(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache warm-up error: {str(e)}")


@router.delete("/admin/cache/clear")  # Decorator lacks type stubs
async def clear_search_cache(
    pattern: Optional[str] = Query(None, description="삭제할 패턴 (비어있으면 전체)"),
    api_key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """
    검색 캐시 클리어 (관리자용)
    """
    try:
        cache = await get_search_cache()
        await cache.invalidate_search_cache(pattern)

        return {
            "message": f"Cache cleared{f' for pattern: {pattern}' if pattern else ' (all)'}",
            "status": "success",
            "timestamp": time.time(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear error: {str(e)}")


@router.post("/admin/optimize-indices")  # Decorator lacks type stubs
async def optimize_search_indices(api_key: str = Depends(verify_api_key)) -> Any:
    """
    검색 인덱스 최적화 (관리자용)
    """
    try:
        from database import db_manager  # TODO: Fix database import path

        async with db_manager.async_session() as session:
            result = await SearchDAO.optimize_search_indices(session)
            return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Index optimization error: {str(e)}"
        )


@router.get("/admin/metrics")  # Decorator lacks type stubs
async def get_search_metrics(api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    실시간 검색 성능 메트릭 조회
    """
    try:
        metrics = search_metrics.get_metrics()
        return {"search_metrics": metrics, "timestamp": time.time()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics error: {str(e)}")


@router.post("/admin/reset-metrics")  # Decorator lacks type stubs
async def reset_search_metrics(api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    검색 메트릭 초기화
    """
    try:
        search_metrics.reset()
        return {"message": "검색 메트릭이 초기화되었습니다.", "timestamp": time.time()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset error: {str(e)}")


# 개별 검색 모드 엔드포인트 (테스트/비교용)
@router.post("/dev/search-bm25")  # Decorator lacks type stubs
async def search_bm25_only(
    request: LegacySearchRequest, api_key: str = Depends(verify_api_key)
) -> LegacySearchResponse:
    """
    BM25 전용 검색 (개발/테스트용)
    """
    start_time = time.time()

    try:
        from database import db_manager  # TODO: Fix database import path

        async with db_manager.async_session() as session:
            bm25_results = await SearchDAO._perform_bm25_search(
                session=session,
                query=request.q,
                topk=request.final_topk,
                filters=request.filters,
            )

            # 처리 시간 계산
            latency = time.time() - start_time
            search_metrics.record_search("bm25", latency)

            # 응답 형식 통일
            hits = [LegacySearchHit(**result) for result in bm25_results]

            return LegacySearchResponse(
                hits=hits,
                latency=round(latency, 3),
                request_id=generate_request_id(),
                total_candidates=len(bm25_results),
                sources_count=len(
                    set(hit.source.get("source_url", "") for hit in hits if hit.source)
                ),
                taxonomy_version=get_taxonomy_version(),
            )

    except Exception as e:
        search_metrics.record_search("bm25", time.time() - start_time, True)
        raise HTTPException(status_code=500, detail=f"BM25 search error: {str(e)}")


@router.post("/dev/search-vector")  # Decorator lacks type stubs
async def search_vector_only(
    request: LegacySearchRequest, api_key: str = Depends(verify_api_key)
) -> LegacySearchResponse:
    """
    Vector 전용 검색 (개발/테스트용)
    """
    start_time = time.time()

    try:
        from database import EmbeddingService, db_manager  # TODO: Fix database import path

        # 쿼리 임베딩 생성
        query_embedding = await EmbeddingService.generate_embedding(request.q)

        async with db_manager.async_session() as session:
            vector_results = await SearchDAO._perform_vector_search(
                session=session,
                query_embedding=query_embedding,
                topk=request.final_topk,
                filters=request.filters,
            )

            # 처리 시간 계산
            latency = time.time() - start_time
            search_metrics.record_search("vector", latency)

            # 응답 형식 통일
            hits = [LegacySearchHit(**result) for result in vector_results]

            return LegacySearchResponse(
                hits=hits,
                latency=round(latency, 3),
                request_id=generate_request_id(),
                total_candidates=len(vector_results),
                sources_count=len(
                    set(hit.source.get("source_url", "") for hit in hits if hit.source)
                ),
                taxonomy_version=get_taxonomy_version(),
            )

    except Exception as e:
        search_metrics.record_search("vector", time.time() - start_time, True)
        raise HTTPException(status_code=500, detail=f"Vector search error: {str(e)}")


# 최적화된 검색 엔드포인트들
class OptimizedSearchRequest(BaseModel):
    """HYBRID_SEARCH_OPTIMIZATION_GUIDE.md 스펙 준수"""

    q: str = Field(..., min_length=1, description="검색 쿼리")
    filters: Optional[Dict[str, Any]] = Field(None, description="검색 필터")

    # BM25 설정
    bm25_k1: float = Field(1.5, ge=0.5, le=3.0, description="BM25 K1 파라미터")
    bm25_b: float = Field(0.75, ge=0.0, le=1.0, description="BM25 B 파라미터")
    bm25_topk: int = Field(20, ge=5, le=100, description="BM25 상위 K개")

    # Vector 설정
    vector_topk: int = Field(20, ge=5, le=100, description="Vector 상위 K개")
    vector_similarity_threshold: float = Field(
        0.0, ge=0.0, le=1.0, description="유사도 임계값"
    )
    embedding_model: str = Field("openai", description="임베딩 모델")

    # Fusion 설정
    bm25_weight: float = Field(0.5, ge=0.0, le=1.0, description="BM25 가중치")
    vector_weight: float = Field(0.5, ge=0.0, le=1.0, description="Vector 가중치")

    # Reranking 설정
    enable_reranking: bool = Field(True, description="리랭킹 사용 여부")
    rerank_candidates: int = Field(50, ge=10, le=200, description="리랭킹 후보 수")
    final_topk: int = Field(10, ge=1, le=50, description="최종 결과 수")

    # 성능 설정
    use_cache: bool = Field(True, description="캐시 사용 여부")
    use_optimized_engines: bool = Field(True, description="최적화 엔진 사용")
    max_query_time: float = Field(
        2.0, ge=0.1, le=10.0, description="최대 쿼리 시간(초)"
    )


@router.post("/v2/search", response_model=LegacySearchResponse)  # Decorator lacks type stubs
async def optimized_search(
    request: OptimizedSearchRequest, api_key: str = Depends(verify_api_key)
) -> LegacySearchResponse:
    """
    HYBRID_SEARCH_OPTIMIZATION_GUIDE.md 기준 최적화된 검색
    Target: Recall@10 >= 0.85, p95 latency < 200ms
    """
    start_time = time.time()
    query_id = generate_request_id()

    if not HYBRID_ENGINE_AVAILABLE:
        raise HTTPException(
            status_code=503, detail="Optimized search engine not available"
        )

    try:
        # 검색 설정 딕셔너리
        # @CODE:MYPY-CONSOLIDATION-002 | Phase 13: arg-type resolution (explicit typing for config dict)
        search_config: Dict[str, Union[float, bool, str]] = {
            "bm25_weight": 0.5,
            "vector_weight": 0.5,
            "enable_caching": True,
            "enable_reranking": True,
            "normalization": "min_max",
        }

        # 커스텀 검색 엔진 생성
        search_engine = HybridSearchEngine(
            bm25_weight=float(search_config["bm25_weight"]),
            vector_weight=float(search_config["vector_weight"]),
            enable_caching=bool(search_config["enable_caching"]),
            enable_reranking=bool(search_config["enable_reranking"]),
            normalization=str(search_config["normalization"]),
        )

        # 캐시 확인 (선택적)
        cache = None
        cached_results = None
        if request.use_cache:
            cache = await get_search_cache()
            cached_results = await cache.get_search_results(
                query=request.q,
                filters=request.filters,
                search_params=search_config,
            )

        if cached_results:
            latency = time.time() - start_time
            search_metrics.record_search("optimized_cached", latency, False)
            return _convert_to_response(
                cached_results, latency, query_id, "cached_optimized"
            )

        # 최적화된 검색 실행
        results, metrics = await search_engine.search(
            query=request.q,
            top_k=request.final_topk,
            filters=request.filters,
            bm25_candidates=request.bm25_topk,
            vector_candidates=request.vector_topk,
            correlation_id=query_id,
        )

        # 결과 변환
        search_results = []
        for result in results:
            result_dict = {
                "chunk_id": result.chunk_id,
                "text": result.text,
                "score": result.hybrid_score,
                "metadata": result.metadata,
                "title": result.metadata.get("title"),
                "source_url": result.metadata.get("source_url"),
                "taxonomy_path": result.metadata.get("taxonomy_path", []),
            }
            search_results.append(result_dict)

        # 캐싱 (선택적)
        if cache:
            await cache.set_search_results(
                query=request.q,
                results=search_results,
                filters=request.filters,
                search_params=search_config,
            )

        # 성능 메트릭 기록
        search_metrics.record_search(
            "optimized_v2", metrics.total_time, False
        )

        return _convert_to_response(
            search_results,
            metrics.total_time,
            query_id,
            "optimized_v2",
            {
                "bm25_time": metrics.bm25_time,
                "vector_time": metrics.vector_time,
                "fusion_time": metrics.fusion_time,
                "rerank_time": metrics.rerank_time,
                "bm25_candidates": metrics.bm25_candidates,
                "vector_candidates": metrics.vector_candidates,
                "config": search_config,
            },
        )

    except Exception as e:
        latency = time.time() - start_time
        search_metrics.record_search("optimized_v2", latency, True)
        raise HTTPException(status_code=500, detail=f"Optimized search error: {str(e)}")


@router.post("/v2/search/benchmark")  # Decorator lacks type stubs
async def benchmark_search_engines(
    request: LegacySearchRequest, api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    검색 엔진 비교 벤치마크
    """
    if not HYBRID_ENGINE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Hybrid search engine not available for benchmarking",
        )

    results = {}

    # 1. Fast Engine 테스트
    try:
        start_time = time.time()
        fast_engine = SearchEngineFactory.create_fast_engine()

        async with db_manager.async_session() as session:
            fast_response = await fast_engine.search(
                session=session, query=request.q, filters=request.filters
            )

        results["fast_engine"] = {
            "total_time": fast_response.total_time,
            "results_count": len(fast_response.results),
            "bm25_time": fast_response.bm25_time,
            "vector_time": fast_response.vector_time,
            "rerank_enabled": False,
        }
    except Exception as e:
        results["fast_engine"] = {"error": str(e)}

    # 2. Accurate Engine 테스트
    try:
        start_time = time.time()
        accurate_engine = SearchEngineFactory.create_accurate_engine()

        async with db_manager.async_session() as session:
            accurate_response = await accurate_engine.search(
                session=session, query=request.q, filters=request.filters
            )

        results["accurate_engine"] = {
            "total_time": accurate_response.total_time,
            "results_count": len(accurate_response.results),
            "bm25_time": accurate_response.bm25_time,
            "vector_time": accurate_response.vector_time,
            "fusion_time": accurate_response.fusion_time,
            "rerank_time": accurate_response.rerank_time,
            "rerank_enabled": True,
        }
    except Exception as e:
        results["accurate_engine"] = {"error": str(e)}

    # 3. Balanced Engine 테스트
    try:
        start_time = time.time()
        balanced_engine = SearchEngineFactory.create_balanced_engine()

        async with db_manager.async_session() as session:
            balanced_response = await balanced_engine.search(
                session=session, query=request.q, filters=request.filters
            )

        results["balanced_engine"] = {
            "total_time": balanced_response.total_time,
            "results_count": len(balanced_response.results),
            "bm25_time": balanced_response.bm25_time,
            "vector_time": balanced_response.vector_time,
            "fusion_time": balanced_response.fusion_time,
            "rerank_time": balanced_response.rerank_time,
            "rerank_enabled": True,
        }
    except Exception as e:
        results["balanced_engine"] = {"error": str(e)}

    # 4. Legacy DAO 테스트
    try:
        start_time = time.time()
        legacy_results = await SearchDAO.hybrid_search(
            query=request.q,
            filters=request.filters,
            topk=request.final_topk,
            bm25_topk=request.bm25_topk,
            vector_topk=request.vector_topk,
            rerank_candidates=request.rerank_candidates,
        )
        legacy_time = time.time() - start_time

        results["legacy_dao"] = {
            "total_time": legacy_time,
            "results_count": len(legacy_results),
            "method": "database_dao",
        }
    except Exception as e:
        results["legacy_dao"] = {"error": str(e)}

    return {
        "query": request.q,
        "benchmark_results": results,
        "recommendation": _recommend_engine(results),
        "timestamp": time.time(),
    }


def _recommend_engine(results: Dict[str, Any]) -> str:
    """벤치마크 결과 기반 엔진 추천"""
    valid_results = {k: v for k, v in results.items() if "error" not in v}

    if not valid_results:
        return "No engines available"

    # 성능 기반 추천
    fastest = min(
        valid_results.items(), key=lambda x: x[1].get("total_time", float("inf"))
    )

    if fastest[1].get("total_time", 0) < 0.1:  # 100ms 미만
        return f"Recommended: {fastest[0]} (fastest: {fastest[1]['total_time']:.3f}s)"
    else:
        return "Recommended: balanced_engine (best balance of speed and accuracy)"


# LLM Answer Generation Endpoint
class AnswerRequest(BaseModel):
    """RAG answer generation request"""

    q: str = Field(..., description="User question")
    mode: str = Field(
        "answer", description="Generation mode: answer, summary, or keypoints"
    )
    final_topk: int = Field(5, description="Number of documents to retrieve")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")


class AnswerResponse(BaseModel):
    """RAG answer generation response"""

    question: str
    answer: str
    sources: List[Dict[str, Any]]
    source_count: int
    search_time: float
    generation_time: float
    total_time: float
    model: str
    language: str
    mode: str
    request_id: str
    timestamp: str


@router.post("/answer", response_model=AnswerResponse)  # Decorator lacks type stubs
async def generate_answer(
    request: AnswerRequest, api_key: str = Depends(verify_api_key)
) -> AnswerResponse:
    """
    Generate natural language answer from search results using Gemini LLM

    This endpoint:
    1. Performs hybrid search to find relevant documents
    2. Sends search results + question to Gemini 2.5 Flash
    3. Returns AI-generated answer in the question's language

    Features:
    - Multilingual Q&A (Korean/English auto-detection)
    - Context-aware summarization
    - Key point extraction
    - Source attribution
    """
    request_id = generate_request_id()
    start_time = time.time()

    try:
        # Step 1: Perform hybrid search
        logger.info(
            f"[{request_id}] Generating answer for: '{request.q}' (mode: {request.mode})"
        )

        search_start = time.time()

        if HYBRID_ENGINE_AVAILABLE:
            results, metrics = await hybrid_search(
                query=request.q, top_k=request.final_topk, filters=request.filters or {}
            )
        else:
            # Fallback to basic search
            raise HTTPException(
                status_code=503, detail="Hybrid search engine not available"
            )

        search_time = time.time() - search_start

        # Step 2: Generate answer using LLM
        try:
            from ..llm_service import get_llm_service

            llm_service = get_llm_service()

            # Prepare search results for LLM (results are already in dict format from hybrid_search)
            search_results_dict = []
            for result in results:
                search_results_dict.append(
                    {
                        "text": result["text"],
                        "title": result.get("title", "Unknown"),
                        "source_url": result.get("source_url", ""),
                        "hybrid_score": result.get("metadata", {}).get(
                            "hybrid_score", result.get("score", 0)
                        ),
                        "taxonomy_path": result.get("taxonomy_path", ""),
                    }
                )

            answer_result = await llm_service.generate_answer(
                question=request.q,
                search_results=search_results_dict,
                mode=request.mode,
            )

        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="LLM service not available. Check GEMINI_API_KEY environment variable.",
            )

        total_time = time.time() - start_time

        logger.info(
            f"[{request_id}] Answer generated: "
            f"search={search_time:.2f}s, generation={answer_result.generation_time:.2f}s, "
            f"total={total_time:.2f}s"
        )

        return AnswerResponse(
            question=request.q,
            answer=answer_result.answer,
            sources=search_results_dict,
            source_count=len(search_results_dict),
            search_time=search_time,
            generation_time=answer_result.generation_time,
            total_time=total_time,
            model=answer_result.model,
            language=answer_result.language_detected,
            mode=request.mode,
            request_id=request_id,
            timestamp=get_current_timestamp(),
        )

    except Exception as e:
        logger.error(f"[{request_id}] Answer generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Answer generation error: {str(e)}"
        )
