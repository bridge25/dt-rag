# 📁 dt-rag/apps/taxonomy/main.py (수정된 완벽 버전)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
import os

# common-schemas import (정확한 방법)
sys.path.append('../../packages')
try:
    from common_schemas.models import (
        ClassifyRequest, ClassifyResponse, TaxonomyNode,
        SearchRequest, SearchResponse, SearchHit, SourceMeta
    )
except ImportError:
    # Fallback: 직접 정의
    class ClassifyRequest(BaseModel):
        chunk_id: str
        text: str
        hint_paths: Optional[List[List[str]]] = None
    
    class TaxonomyNode(BaseModel):
        node_id: str
        label: str
        canonical_path: List[str]
        version: str
        confidence: float = 0.0
    
    class ClassifyResponse(BaseModel):
        canonical: List[str]
        candidates: List[TaxonomyNode]
        hitl: bool = False
        confidence: float
        reasoning: List[str]
    
    class SearchHit(BaseModel):
        chunk_id: str
        score: float
        source: Optional[Dict] = None
        text: Optional[str] = None
        taxonomy_path: Optional[List[str]] = None
    
    class SearchRequest(BaseModel):
        q: str
        filters: Optional[Dict] = None
        bm25_topk: int = 12
        vector_topk: int = 12
        rerank_candidates: int = 50
        final_topk: int = 5
    
    class SearchResponse(BaseModel):
        hits: List[SearchHit]
        latency: float
        request_id: str

app = FastAPI(
    title="A팀 Taxonomy API", 
    version="1.0.0",
    description="Dynamic Taxonomy RAG - A팀 데이터베이스 및 분류 API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy", 
        "team": "A", 
        "service": "taxonomy",
        "version": "1.0.0",
        "database": "postgresql://localhost:5432/dt_rag"  # 실제 DB 정보
    }

@app.post("/classify", response_model=ClassifyResponse)
async def classify_request(request: ClassifyRequest):
    """텍스트 분류 API - common_schemas 완전 준수"""
    try:
        # TODO: 실제 분류 로직으로 교체
        # 현재는 Mock 데이터지만 응답 형식은 스키마 완전 준수
        
        return ClassifyResponse(
            canonical=["AI", "ML", "Classification"],  # List[str] - 스키마 준수
            candidates=[
                TaxonomyNode(
                    node_id="ai-ml-class-001",
                    label="머신러닝 분류",
                    canonical_path=["AI", "ML", "Classification"],
                    version="v1.0",
                    confidence=0.85
                )
            ],
            hitl=False,
            confidence=0.85,
            reasoning=[
                "텍스트에서 '분류' 키워드 감지",
                "머신러닝 컨텍스트 확인됨"
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분류 처리 오류: {str(e)}")

@app.post("/search", response_model=SearchResponse)
async def hybrid_search(request: SearchRequest):
    """하이브리드 검색 API - BM25 + Vector 검색"""
    try:
        # TODO: 실제 PostgreSQL + pgvector 검색으로 교체
        
        return SearchResponse(
            hits=[
                SearchHit(
                    chunk_id="chunk-001",
                    score=0.95,
                    text=f"'{request.q}'와 관련된 Mock 검색 결과입니다.",
                    taxonomy_path=["AI", "ML"],
                    source={"title": "Mock Document", "url": "http://example.com"}
                )
            ],
            latency=0.15,  # 150ms
            request_id=f"search-{hash(request.q) % 10000}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 처리 오류: {str(e)}")

@app.get("/taxonomy/{version}/tree")
async def get_taxonomy_tree(version: str):
    """분류체계 트리 조회 API"""
    try:
        # TODO: 실제 taxonomy_nodes, taxonomy_edges 테이블 조회로 교체
        
        return {
            "version": version,
            "nodes": [
                {"id": "1", "name": "AI", "path": "AI", "parent_id": None},
                {"id": "2", "name": "ML", "path": "AI/ML", "parent_id": "1"},
                {"id": "3", "name": "Classification", "path": "AI/ML/Classification", "parent_id": "2"},
                {"id": "4", "name": "RAG", "path": "AI/RAG", "parent_id": "1"},
                {"id": "5", "name": "Taxonomy", "path": "AI/Taxonomy", "parent_id": "1"}
            ],
            "edges": [
                {"parent_id": "1", "child_id": "2"},
                {"parent_id": "2", "child_id": "3"},
                {"parent_id": "1", "child_id": "4"},
                {"parent_id": "1", "child_id": "5"}
            ],
            "total_nodes": 5
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분류체계 조회 오류: {str(e)}")

@app.get("/case_bank")
async def get_case_bank(category: Optional[str] = None, limit: int = 10):
    """케이스 뱅크 조회 API - CBR 시스템용"""
    try:
        # TODO: 실제 case_bank 테이블 조회로 교체
        
        return {
            "cases": [
                {
                    "case_id": "case-001",
                    "query": "머신러닝 분류 알고리즘 추천",
                    "category": category or "AI/ML",
                    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],  # 768차원 Mock
                    "metadata": {"source": "expert_knowledge", "date": "2025-09-05"}
                },
                {
                    "case_id": "case-002", 
                    "query": "RAG 시스템 성능 최적화",
                    "category": "AI/RAG",
                    "embedding": [0.2, 0.3, 0.4, 0.5, 0.6],
                    "metadata": {"source": "production_data", "date": "2025-09-04"}
                }
            ],
            "total": 2,
            "filters_applied": {"category": category} if category else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"케이스 뱅크 조회 오류: {str(e)}")

# 추가 디버깅 엔드포인트
@app.get("/debug/db")
async def debug_database():
    """데이터베이스 연결 디버그"""
    try:
        # TODO: 실제 PostgreSQL 연결 테스트
        return {
            "status": "mock",
            "message": "실제 PostgreSQL 연결 구현 필요",
            "expected_tables": [
                "taxonomy_nodes", "taxonomy_edges", 
                "chunks", "embeddings", "case_bank"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 디버그 오류: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 A팀 Taxonomy API 서버 시작")
    print("📡 포트: 8001")
    print("📋 엔드포인트: /health, /classify, /search, /taxonomy/{version}/tree, /case_bank")
    print("🔍 디버그: /debug/db")
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)