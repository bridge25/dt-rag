"""
Document Search 엔드포인트
Bridge Pack ACCESS_CARD.md 스펙 100% 준수
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from deps import verify_api_key, generate_request_id, get_taxonomy_version
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
def search_documents(
    request: SearchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Bridge Pack 스펙: POST /search
    Expected Request: {"q":"taxonomy tree", "filters":{"canonical_in":[["AI","RAG"]]}, ...}
    Expected Response: Bridge Pack ACCESS_CARD.md 참조
    """
    start_time = time.time()
    
    try:
        query = request.q.lower()
        
        # MVP: 쿼리 키워드 기반 모의 검색 결과 생성
        mock_hits = []
        
        # 1. RAG 관련 검색
        if any(keyword in query for keyword in ["rag", "retrieval", "augmented"]):
            mock_hits.extend([
                SearchHit(
                    chunk_id="chunk_rag_001",
                    score=0.95,
                    text="RAG taxonomy specification and implementation guide...",
                    taxonomy_path=["AI", "RAG"],
                    source={
                        "doc_id": "rag-guide-v1.8.1",
                        "title": "RAG Implementation Guide",
                        "url": "https://docs.example.com/rag-guide"
                    }
                ),
                SearchHit(
                    chunk_id="chunk_rag_002", 
                    score=0.89,
                    text="Retrieval-Augmented Generation systems for dynamic taxonomy...",
                    taxonomy_path=["AI", "RAG", "Dynamic"],
                    source={
                        "doc_id": "dynamic-rag-paper",
                        "title": "Dynamic RAG Systems",
                        "url": "https://arxiv.org/abs/2024.dynamic-rag"
                    }
                )
            ])
        
        # 2. Taxonomy 관련 검색
        if any(keyword in query for keyword in ["taxonomy", "tree", "classification"]):
            mock_hits.extend([
                SearchHit(
                    chunk_id="chunk_tax_001",
                    score=0.88,
                    text="Taxonomy tree structure for hierarchical document classification...",
                    taxonomy_path=["AI", "Taxonomy", "Hierarchical"],
                    source={
                        "doc_id": "taxonomy-structure",
                        "title": "Hierarchical Taxonomy Design",
                        "url": "https://docs.example.com/taxonomy"
                    }
                )
            ])
        
        # 3. 기본 AI 검색 결과
        if len(mock_hits) == 0:
            mock_hits.append(
                SearchHit(
                    chunk_id=f"chunk_general_{hash(query) % 1000:03d}",
                    score=0.72,
                    text=f"General AI content related to query: {request.q}",
                    taxonomy_path=["AI", "General"],
                    source={
                        "doc_id": "general-ai-docs",
                        "title": "General AI Documentation",
                        "url": "https://docs.example.com/ai"
                    }
                )
            )
        
        # 필터 적용 (canonical_in)
        if request.filters and "canonical_in" in request.filters:
            canonical_filter = request.filters["canonical_in"]
            if isinstance(canonical_filter, list) and len(canonical_filter) > 0:
                # 필터링된 결과만 유지
                filtered_hits = []
                for hit in mock_hits:
                    if hit.taxonomy_path:
                        for allowed_path in canonical_filter:
                            if isinstance(allowed_path, list) and len(allowed_path) >= 2:
                                if (hit.taxonomy_path[:len(allowed_path)] == allowed_path):
                                    filtered_hits.append(hit)
                                    break
                mock_hits = filtered_hits
        
        # final_topk만큼 결과 제한
        final_hits = mock_hits[:request.final_topk]
        
        # 응답 생성
        latency = time.time() - start_time
        
        return SearchResponse(
            hits=final_hits,
            latency=round(latency, 3),
            request_id=generate_request_id(),
            total_candidates=request.rerank_candidates,
            sources_count=len(set(hit.source.get("doc_id") if hit.source else None for hit in final_hits)),
            taxonomy_version=get_taxonomy_version()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(e)}"
        )