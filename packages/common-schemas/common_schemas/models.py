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

class FromCategoryRequest(BaseModel):
    version: str
    node_paths: List[List[str]]
    options: Optional[Dict] = Field(default_factory=dict)

class RetrievalConfig(BaseModel):
    bm25_topk: int = 12
    vector_topk: int = 12
    rerank: Dict = Field(default_factory=lambda: {"candidates": 50, "final_topk": 5})
    filter: Dict = Field(default_factory=lambda: {"canonical_in": True})

class FeaturesConfig(BaseModel):
    debate: bool = False
    hitl_below_conf: float = Field(default=0.70, ge=0.0, le=1.0)
    cost_guard: bool = True

class AgentManifest(BaseModel):
    name: str
    taxonomy_version: str
    allowed_category_paths: List[List[str]]
    retrieval: RetrievalConfig
    features: FeaturesConfig
    mcp_tools_allowlist: List[str] = Field(default_factory=list)

class CaseMetadata(BaseModel):
    case_id: str
    category_path: List[str]
    quality_score: float = Field(ge=0.0, le=1.0)
    usage_count: int = Field(default=0, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    created_at: str
    last_used_at: Optional[str] = None

class CBRCase(BaseModel):
    case_id: str
    query_vector: List[float]
    response_text: str
    metadata: CaseMetadata
    similarity_score: Optional[float] = None

class CBRSuggestRequest(BaseModel):
    query: str
    category_path: Optional[List[str]] = None
    k: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

class CBRSuggestResponse(BaseModel):
    cases: List[CBRCase]
    query: str
    total_candidates: int
    similarity_method: str = "cosine"
    request_id: str
    latency: float = Field(ge=0.0)

class CBRFeedback(BaseModel):
    request_id: str
    selected_case_ids: List[str]
    user_rating: int = Field(ge=1, le=5)
    success_flag: bool
    feedback_text: Optional[str] = None