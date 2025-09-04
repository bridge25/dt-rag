from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import sys
sys.path.append('../../../packages')

try:
    from common_schemas.models import ClassifyRequest, ClassifyResponse, SearchRequest, SearchResponse, TaxonomyNode
except ImportError:
    # Fallback for local development
    from pydantic import BaseModel
    class TaxonomyNode(BaseModel):
        node_id: str
        label: str
        canonical_path: List[str]
        version: str
        confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    class ClassifyRequest(BaseModel):
        chunk_id: str
        text: str
        hint_paths: Optional[List[List[str]]] = None

    class ClassifyResponse(BaseModel):
        canonical: List[str]
        candidates: List[TaxonomyNode]
        hitl: bool = False
        confidence: float = Field(ge=0.0, le=1.0)
        reasoning: List[str]

    class SearchRequest(BaseModel):
        query: str
        taxonomy_filters: Optional[List[str]] = None
        limit: int = Field(default=10, ge=1, le=100)

    class SearchResponse(BaseModel):
        results: List[Dict]
        total: int
        query: str

app = FastAPI(title="Dynamic Taxonomy RAG - Orchestration")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "orchestration"}

@app.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    """
    7-Step LangGraph 매니페스트 빌더
    
    Phase 1: 룰 기반 1차 분류 (민감도/패턴 매칭)
    Phase 2: LLM 2차 분류 (후보 경로 + 근거≥2)
    Phase 3: 교차검증 로직 (룰 vs LLM 결과 비교)
    Phase 4: Confidence<0.7 → HITL 처리
    """
    
    # TODO: 실제 LangGraph 7-Step 파이프라인 구현
    # 현재는 스캐폴딩 응답
    
    # Phase 1: 룰 기반 분류 (임시)
    canonical_path = ["AI", "RAG"]  # 실제 룰 엔진으로 교체 필요
    
    # Phase 2: LLM 분류 (임시)
    confidence = 0.8
    
    # Phase 3: 교차검증 (임시)
    # Phase 4: HITL 처리
    needs_hitl = confidence < 0.7
    
    return ClassifyResponse(
        canonical=canonical_path,
        candidates=[],
        hitl=needs_hitl,
        confidence=confidence,
        reasoning=["스캐폴딩 단계", "실제 구현 필요", "LangGraph 7-Step 파이프라인 구현 예정"]
    )

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    하이브리드 검색 + Cross-Encoder Reranking
    BM25 + Vector 검색 → 50→5 rerank
    """
    # TODO: 하이브리드 검색 구현
    return SearchResponse(
        results=[],
        total=0,
        query=request.query
    )

@app.get("/taxonomy/{version}/tree")
async def get_taxonomy_tree(version: str):
    """트리 구조 조회"""
    # TODO: 택소노미 트리 API 구현
    return {"version": version, "tree": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)