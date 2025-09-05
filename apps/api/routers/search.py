"""
Document Search 엔드포인트
실제 BM25 + Vector 하이브리드 검색 구현
Bridge Pack ACCESS_CARD.md 스펙 100% 준수
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from deps import verify_api_key, generate_request_id, get_taxonomy_version
from database import SearchDAO
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
    실제 BM25 + Vector 하이브리드 검색 수행
    Expected Request: {"q":"taxonomy tree", "filters":{"canonical_in":[["AI","RAG"]]}, ...}
    Expected Response: Bridge Pack ACCESS_CARD.md 참조
    """
    start_time = time.time()
    
    try:
        # 실제 하이브리드 검색 수행
        search_results = await SearchDAO.hybrid_search(
            query=request.q,
            filters=request.filters,
            topk=request.final_topk
        )
        
        # SearchHit 객체로 변환 (Bridge Pack 스펙 준수)
        hits = []
        for result in search_results:
            hit = SearchHit(
                chunk_id=result["chunk_id"],
                score=result["score"],
                text=result.get("text"),
                taxonomy_path=result.get("taxonomy_path"),
                source=result.get("metadata", {})
            )
            hits.append(hit)
        
        # 처리 시간 계산
        latency = time.time() - start_time
        
        # 소스 문서 수 계산
        source_docs = set()
        for hit in hits:
            if hit.source and "title" in hit.source:
                source_docs.add(hit.source["title"])
        
        return SearchResponse(
            hits=hits,
            latency=round(latency, 3),
            request_id=generate_request_id(),
            total_candidates=len(search_results),
            sources_count=len(source_docs),
            taxonomy_version=get_taxonomy_version()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(e)}"
        )