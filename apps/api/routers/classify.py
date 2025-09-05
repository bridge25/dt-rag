"""
Document Classification 엔드포인트
Bridge Pack ACCESS_CARD.md 스펙 100% 준수
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from deps import verify_api_key, generate_request_id, get_taxonomy_version

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
def classify_text(
    request: ClassifyRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Bridge Pack 스펙: POST /classify
    Expected Request: {"text":"RAG taxonomy spec example"}
    Expected Response: Bridge Pack ACCESS_CARD.md 참조
    """
    try:
        # MVP: 텍스트 키워드 기반 간단한 분류 로직
        text = request.text.lower()
        
        # AI/RAG 관련 키워드 감지
        if any(keyword in text for keyword in ["rag", "retrieval", "augmented", "generation"]):
            canonical = ["AI", "RAG"]
            label = "RAG Systems"
            confidence = 0.85
            reasoning = [
                "High confidence match for RAG taxonomy", 
                "Clear AI domain classification"
            ]
        elif any(keyword in text for keyword in ["machine learning", "ml", "model", "training"]):
            canonical = ["AI", "ML"]
            label = "Machine Learning"
            confidence = 0.78
            reasoning = [
                "Machine learning keywords detected",
                "AI domain classification confirmed"
            ]
        elif any(keyword in text for keyword in ["taxonomy", "classification", "category"]):
            canonical = ["AI", "Taxonomy"]
            label = "Taxonomy Systems"
            confidence = 0.72
            reasoning = [
                "Taxonomy-related content identified",
                "Classification domain match"
            ]
        else:
            # 기본 AI 분류
            canonical = ["AI", "General"]
            label = "General AI"
            confidence = 0.60
            reasoning = [
                "General AI content classification",
                "Default taxonomy assignment"
            ]
        
        # 후보 노드 생성
        candidate_node = TaxonomyNode(
            node_id=f"ai_{canonical[-1].lower()}_{hash(text) % 1000:03d}",
            label=label,
            canonical_path=canonical,
            version=get_taxonomy_version(),
            confidence=confidence
        )
        
        return ClassifyResponse(
            canonical=canonical,
            candidates=[candidate_node],
            hitl=confidence < 0.70,  # 신뢰도 70% 미만시 HITL
            confidence=confidence,
            reasoning=reasoning,
            request_id=generate_request_id(),
            taxonomy_version=get_taxonomy_version()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Classification error: {str(e)}"
        )