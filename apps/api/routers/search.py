"""
Document Search 엔드포인트
실제 BM25 + Vector 하이브리드 검색 구현
Bridge Pack ACCESS_CARD.md 스펙 100% 준수
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from deps import verify_api_key, generate_request_id, get_taxonomy_version
from database import SearchDAO, search_metrics, get_search_performance_metrics
import time

router = APIRouter()

# Common Schemas 호환 모델
class SearchRequest(BaseModel):
    q: str = Field(..., min_length=1, description="검색 쿼리")
    filters: Optional[Dict[str, Any]] = Field(None, description="검색 필터")
    bm25_topk: int = Field(12, ge=1, le=100, description="BM25 상위 K개")
    vector_topk: int = Field(12, ge=1, le=100, description="Vector 상위 K개")
    rerank_candidates: int = Field(50, ge=1, le=1000, description="재랭킹 후보 수")
    final_topk: int = Field(5, ge=1, le=50, description="최종 결과 수")

class SearchHit(BaseModel):
    chunk_id: str
    score: float = Field(ge=0.0, description="검색 점수")
    text: Optional[str] = Field(None, description="텍스트 내용")
    taxonomy_path: Optional[List[str]] = Field(None, description="분류 경로")
    source: Optional[Dict[str, Any]] = Field(None, description="소스 메타데이터")

class SearchResponse(BaseModel):
    hits: List[SearchHit]
    latency: float = Field(ge=0.0, description="검색 지연시간(초)")
    request_id: str
    total_candidates: Optional[int] = Field(None, description="전체 후보 수")
    sources_count: Optional[int] = Field(None, description="소스 문서 수")
    taxonomy_version: str = "1.8.1"

@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Bridge Pack 스펙: POST /search
    완전한 BM25 + Vector + Cross-encoder 하이브리드 검색
    Expected Request: {"q":"taxonomy tree", "filters":{"canonical_in":[["AI","RAG"]]}, ...}
    Expected Response: Bridge Pack ACCESS_CARD.md 참조
    """
    start_time = time.time()
    error_occurred = False

    try:
        # 향상된 하이브리드 검색 수행
        search_results = await SearchDAO.hybrid_search(
            query=request.q,
            filters=request.filters,
            topk=request.final_topk,
            bm25_topk=request.bm25_topk,
            vector_topk=request.vector_topk,
            rerank_candidates=request.rerank_candidates
        )

        # SearchHit 객체로 변환 (Bridge Pack 스펙 준수)
        hits = []
        for result in search_results:
            # 메타데이터 구조 개선
            source_metadata = result.get("metadata", {}).copy()
            source_metadata.update({
                "title": result.get("title"),
                "source_url": result.get("source_url"),
                "search_type": source_metadata.get("source", "hybrid")
            })

            hit = SearchHit(
                chunk_id=result["chunk_id"],
                score=result["score"],
                text=result.get("text"),
                taxonomy_path=result.get("taxonomy_path"),
                source=source_metadata
            )
            hits.append(hit)

        # 처리 시간 계산
        latency = time.time() - start_time

        # 소스 문서 수 계산 (개선된 방법)
        source_docs = set()
        for hit in hits:
            if hit.source:
                # URL 또는 제목 기반으로 중복 제거
                doc_key = hit.source.get("source_url") or hit.source.get("title") or hit.chunk_id
                source_docs.add(doc_key)

        # 성능 메트릭 기록
        search_metrics.record_search("hybrid", latency, error_occurred)

        return SearchResponse(
            hits=hits,
            latency=round(latency, 3),
            request_id=generate_request_id(),
            total_candidates=len(search_results),
            sources_count=len(source_docs),
            taxonomy_version=get_taxonomy_version()
        )

    except Exception as e:
        error_occurred = True
        latency = time.time() - start_time
        search_metrics.record_search("hybrid", latency, error_occurred)

        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(e)}"
        )


# 관리자용 엔드포인트들
class EmbeddingRequest(BaseModel):
    chunk_ids: Optional[List[str]] = Field(None, description="특정 청크 ID들 (비어있으면 모든 청크)")
    batch_size: int = Field(50, ge=1, le=200, description="배치 크기")
    model: str = Field("openai", description="임베딩 모델 (openai, sentence_transformer)")


class EmbeddingResponse(BaseModel):
    processed: int
    message: str
    error: Optional[str] = None


@router.post("/admin/create-embeddings", response_model=EmbeddingResponse)
async def create_embeddings(
    request: EmbeddingRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    청크들에 대한 임베딩 생성 (관리자용)
    """
    try:
        from database import db_manager
        async with db_manager.async_session() as session:
            result = await SearchDAO.create_embeddings_for_chunks(
                session=session,
                chunk_ids=request.chunk_ids,
                batch_size=request.batch_size
            )

            return EmbeddingResponse(**result)

    except Exception as e:
        return EmbeddingResponse(
            processed=0,
            message="임베딩 생성 실패",
            error=str(e)
        )


@router.get("/admin/search-analytics")
async def get_search_analytics(api_key: str = Depends(verify_api_key)):
    """
    검색 시스템 분석 정보 조회 (관리자용)
    """
    try:
        analytics = await get_search_performance_metrics()
        return analytics

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analytics error: {str(e)}"
        )


@router.post("/admin/optimize-indices")
async def optimize_search_indices(api_key: str = Depends(verify_api_key)):
    """
    검색 인덱스 최적화 (관리자용)
    """
    try:
        from database import db_manager
        async with db_manager.async_session() as session:
            result = await SearchDAO.optimize_search_indices(session)
            return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Index optimization error: {str(e)}"
        )


@router.get("/admin/metrics")
async def get_search_metrics(api_key: str = Depends(verify_api_key)):
    """
    실시간 검색 성능 메트릭 조회
    """
    try:
        metrics = search_metrics.get_metrics()
        return {
            "search_metrics": metrics,
            "timestamp": time.time()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Metrics error: {str(e)}"
        )


@router.post("/admin/reset-metrics")
async def reset_search_metrics(api_key: str = Depends(verify_api_key)):
    """
    검색 메트릭 초기화
    """
    try:
        search_metrics.reset()
        return {
            "message": "검색 메트릭이 초기화되었습니다.",
            "timestamp": time.time()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reset error: {str(e)}"
        )


# 개별 검색 모드 엔드포인트 (테스트/비교용)
@router.post("/dev/search-bm25")
async def search_bm25_only(
    request: SearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    BM25 전용 검색 (개발/테스트용)
    """
    start_time = time.time()

    try:
        from database import db_manager
        async with db_manager.async_session() as session:
            bm25_results = await SearchDAO._perform_bm25_search(
                session=session,
                query=request.q,
                topk=request.final_topk,
                filters=request.filters
            )

            # 처리 시간 계산
            latency = time.time() - start_time
            search_metrics.record_search("bm25", latency)

            # 응답 형식 통일
            hits = [SearchHit(**result) for result in bm25_results]

            return SearchResponse(
                hits=hits,
                latency=round(latency, 3),
                request_id=generate_request_id(),
                total_candidates=len(bm25_results),
                sources_count=len(set(hit.source.get("source_url", "") for hit in hits if hit.source)),
                taxonomy_version=get_taxonomy_version()
            )

    except Exception as e:
        search_metrics.record_search("bm25", time.time() - start_time, True)
        raise HTTPException(
            status_code=500,
            detail=f"BM25 search error: {str(e)}"
        )


@router.post("/dev/search-vector")
async def search_vector_only(
    request: SearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Vector 전용 검색 (개발/테스트용)
    """
    start_time = time.time()

    try:
        from database import EmbeddingService, db_manager

        # 쿼리 임베딩 생성
        query_embedding = await EmbeddingService.generate_embedding(request.q)

        async with db_manager.async_session() as session:
            vector_results = await SearchDAO._perform_vector_search(
                session=session,
                query_embedding=query_embedding,
                topk=request.final_topk,
                filters=request.filters
            )

            # 처리 시간 계산
            latency = time.time() - start_time
            search_metrics.record_search("vector", latency)

            # 응답 형식 통일
            hits = [SearchHit(**result) for result in vector_results]

            return SearchResponse(
                hits=hits,
                latency=round(latency, 3),
                request_id=generate_request_id(),
                total_candidates=len(vector_results),
                sources_count=len(set(hit.source.get("source_url", "") for hit in hits if hit.source)),
                taxonomy_version=get_taxonomy_version()
            )

    except Exception as e:
        search_metrics.record_search("vector", time.time() - start_time, True)
        raise HTTPException(
            status_code=500,
            detail=f"Vector search error: {str(e)}"
        )