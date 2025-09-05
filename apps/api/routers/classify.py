"""
Document Classification 엔드포인트
Bridge Pack ACCESS_CARD.md 스펙 100% 준수
실제 데이터베이스 연결 및 ML 분류 구현
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from deps import verify_api_key, generate_request_id, get_taxonomy_version
from database import ClassifyDAO

router = APIRouter()

# Common Schemas 호환 모델
class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, description="분류할 텍스트")
    chunk_id: Optional[str] = Field(None, description="청크 ID (선택사항)")

class TaxonomyNode(BaseModel):
    node_id: str
    label: str
    canonical_path: List[str]
    version: str
    confidence: float = Field(ge=0.0, le=1.0)

class ClassifyResponse(BaseModel):
    canonical: List[str]
    candidates: List[TaxonomyNode]
    hitl: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: List[str]
    request_id: str
    taxonomy_version: str = "1.8.1"

@router.post("/classify", response_model=ClassifyResponse)
async def classify_text(
    request: ClassifyRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Bridge Pack 스펙: POST /classify
    실제 ML 모델 기반 분류 (키워드 방식 제거)
    Expected Request: {"text":"RAG taxonomy spec example"}
    Expected Response: Bridge Pack ACCESS_CARD.md 참조
    """
    try:
        # 실제 ML 모델 기반 분류 수행
        classification_result = await ClassifyDAO.classify_text(
            text=request.text,
            hint_paths=getattr(request, 'hint_paths', None)
        )
        
        # 후보 노드 생성
        candidate_node = TaxonomyNode(
            node_id=classification_result["node_id"],
            label=classification_result["label"],
            canonical_path=classification_result["canonical"],
            version=classification_result["version"],
            confidence=classification_result["confidence"]
        )
        
        return ClassifyResponse(
            canonical=classification_result["canonical"],
            candidates=[candidate_node],
            hitl=classification_result["confidence"] < 0.70,  # 신뢰도 70% 미만시 HITL
            confidence=classification_result["confidence"],
            reasoning=classification_result["reasoning"],
            request_id=generate_request_id(),
            taxonomy_version=get_taxonomy_version()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Classification error: {str(e)}"
        )