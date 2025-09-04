# packages/common-schemas/models.py (문서의 공통 스키마 예시 블록을 아래로 교체)

from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class TaxonomyNode(BaseModel):
    node_id: str
    label: str
    canonical_path: List[str]
    version: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

class SourceMeta(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD
    version: Optional[str] = None
    span: Optional[List[int]] = None  # [start, end]

class ClassifyRequest(BaseModel):
    chunk_id: str
    text: str
    hint_paths: Optional[List[List[str]]] = None

class ClassifyResponse(BaseModel):
    canonical: List[str]
    candidates: List[TaxonomyNode]
    hitl: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: List[str]          # 근거≥2

class SearchHit(BaseModel):
    chunk_id: str
    score: float = Field(ge=0.0)
    source: Optional[SourceMeta] = None
    text: Optional[str] = None
    taxonomy_path: Optional[List[str]] = None

class SearchRequest(BaseModel):
    q: str
    filters: Optional[Dict] = None     # 예: {"canonical_in":[["AI","RAG"]]}
    bm25_topk: int = 12
    vector_topk: int = 12
    rerank_candidates: int = 50
    final_topk: int = 5

class SearchResponse(BaseModel):
    hits: List[SearchHit]
    latency: float = Field(ge=0.0)
    request_id: str
    total_candidates: Optional[int] = None
    sources_count: Optional[int] = None
    taxonomy_version: Optional[str] = None