from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import sys
import time
sys.path.append('../../../packages')

try:
    from common_schemas.models import (
        ClassifyRequest, ClassifyResponse, SearchRequest, SearchResponse, TaxonomyNode,
        FromCategoryRequest, AgentManifest, RetrievalConfig, FeaturesConfig,
        CBRSuggestRequest, CBRSuggestResponse, CBRCase, CaseMetadata, CBRFeedback
    )
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

@app.post("/chat/run")
async def run_chat_pipeline(request: dict):
    """
    B-O3: 7-Step LangGraph 파이프라인 실행
    intent→retrieve→plan→(tools/debate)→compose→cite→respond
    """
    from langgraph_pipeline import get_pipeline, PipelineRequest
    
    try:
        # 요청 파싱
        pipeline_request = PipelineRequest(
            query=request.get("query", request.get("message", "")),
            taxonomy_version=request.get("taxonomy_version", "1.8.1"),
            chunk_id=request.get("chunk_id"),
            filters=request.get("filters"),
            options=request.get("options", {})
        )
        
        # LangGraph 파이프라인 실행
        pipeline = get_pipeline()
        response = await pipeline.execute(pipeline_request)
        
        return {
            "answer": response.answer,
            "confidence": response.confidence,
            "sources": response.sources,
            "taxonomy_version": response.taxonomy_version,
            "cost": response.cost,
            "latency": response.latency,
            "metadata": {
                "intent": response.intent,
                "step_timings": response.step_timings,
                "debate_activated": response.debate_activated,
                "retrieved_count": response.retrieved_count,
                "citations_count": response.citations_count
            }
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "answer": "파이프라인 실행 중 오류가 발생했습니다.",
            "confidence": 0.0,
            "sources": [],
            "cost": 0.0,
            "latency": 0.0
        }

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    B-O2: 하이브리드 검색 + Cross-Encoder Reranking + 스코프 제한 필터
    BM25 + Vector 검색 → 50→5 rerank → canonical_path 필터링
    """
    from retrieval_filter import apply_retrieval_filter
    import uuid
    
    request_id = f"search_{int(time.time() * 1000)}"
    
    # TODO: 실제 하이브리드 검색 구현 (현재는 Mock 데이터)
    # Mock 검색 결과 생성
    mock_search_results = [
        {
            "chunk_id": "chunk_001",
            "score": 0.95,
            "text": "RAG 시스템 구축 방법에 대한 설명입니다...",
            "taxonomy_path": ["AI", "RAG"],
            "source": {
                "url": "https://example.com/rag-guide",
                "title": "RAG 시스템 가이드",
                "date": "2025-09-04",
                "version": "v1.0",
                "span": [0, 100]
            }
        },
        {
            "chunk_id": "chunk_002", 
            "score": 0.87,
            "text": "머신러닝 모델 훈련에 대한 내용입니다...",
            "taxonomy_path": ["AI", "ML"],
            "source": {
                "url": "https://example.com/ml-training",
                "title": "ML 모델 훈련 가이드",
                "date": "2025-09-04",
                "version": "v1.1",
                "span": [50, 150]
            }
        },
        {
            "chunk_id": "chunk_003",
            "score": 0.72,
            "text": "블록체인 기술 개요입니다...",
            "taxonomy_path": ["Blockchain", "Basics"],
            "source": {
                "url": "https://example.com/blockchain",
                "title": "블록체인 기초",
                "date": "2025-09-04",
                "version": "v2.0",
                "span": [100, 200]
            }
        }
    ]
    
    # B-O2: canonical_in 필터가 활성화된 경우 스코프 제한 적용
    if request.filters and request.filters.get("canonical_in"):
        # 허용된 카테고리 경로 추출
        allowed_paths = request.filters.get("canonical_paths", [])
        
        if allowed_paths:
            # 스코프 제한 필터 적용
            filter_result = apply_retrieval_filter(
                search_results=mock_search_results,
                allowed_category_paths=allowed_paths,
                query=request.q,
                request_id=request_id
            )
            
            # 필터링된 결과를 SearchHit 형태로 변환
            hits = []
            for result in filter_result.filtered_results:
                hits.append({
                    "chunk_id": result["chunk_id"],
                    "score": result["score"],
                    "text": result["text"],
                    "taxonomy_path": result["taxonomy_path"],
                    "source": result["source"]
                })
            
            return SearchResponse(
                hits=hits,
                latency=0.123,
                request_id=request_id,
                total_candidates=filter_result.original_count,
                sources_count=len(hits),
                taxonomy_version="1.8.1"
            )
    
    # 필터가 없는 경우 모든 결과 반환
    hits = []
    for result in mock_search_results:
        hits.append({
            "chunk_id": result["chunk_id"],
            "score": result["score"], 
            "text": result["text"],
            "taxonomy_path": result["taxonomy_path"],
            "source": result["source"]
        })
    
    return SearchResponse(
        hits=hits,
        latency=0.098,
        request_id=request_id,
        total_candidates=len(hits),
        sources_count=len(hits),
        taxonomy_version="1.8.1"
    )

@app.post("/agents/from-category", response_model=AgentManifest)
async def create_agent_from_category(request: FromCategoryRequest):
    """
    B-O1: Agent Manifest Builder
    노드 경로 입력 → AgentManifest 생성 (필터 canonical 강제)
    """
    
    # Agent name 생성 (첫 번째 경로 기반)
    if not request.node_paths:
        raise HTTPException(status_code=422, detail="node_paths cannot be empty")
    
    first_path = request.node_paths[0]
    agent_name = f"Agent-{'/'.join(first_path)}"
    
    # 기본 retrieval 설정
    retrieval_config = RetrievalConfig(
        bm25_topk=12,
        vector_topk=12,
        rerank={"candidates": 50, "final_topk": 5},
        filter={"canonical_in": True}  # 강제 설정
    )
    
    # 기본 features 설정
    features_config = FeaturesConfig(
        debate=False,
        hitl_below_conf=0.70,
        cost_guard=True
    )
    
    # MCP 도구 허용 목록 (옵션에서 가져오기)
    mcp_tools_allowlist = request.options.get("mcp_tools", [])
    
    # AgentManifest 생성
    manifest = AgentManifest(
        name=agent_name,
        taxonomy_version=request.version,
        allowed_category_paths=request.node_paths,
        retrieval=retrieval_config,
        features=features_config,
        mcp_tools_allowlist=mcp_tools_allowlist
    )
    
    return manifest

@app.post("/cbr/suggest", response_model=CBRSuggestResponse)
async def suggest_cbr_cases(request: CBRSuggestRequest):
    """
    B-O4: CBR 조회/로그 수집 (Neural Selector 데이터)
    k-NN 조회 엔드포인트 + 유사도 계산 + 성과 로깅
    """
    from cbr_system import CBRRecommendationEngine, CBRUsageLogger, create_query_vector_mock
    import uuid
    
    start_time = time.time()
    request_id = f"cbr_{int(time.time() * 1000)}"
    
    # CBR 엔진 초기화
    cbr_engine = CBRRecommendationEngine()
    cbr_logger = CBRUsageLogger()
    
    # 쿼리 벡터 생성 (Mock - 실제로는 임베딩 모델 사용)
    query_vector = create_query_vector_mock(request.query)
    
    # 유사한 케이스 검색
    similar_cases = cbr_engine.find_similar_cases(
        query_vector=query_vector,
        category_path=request.category_path,
        k=request.k,
        similarity_threshold=request.similarity_threshold,
        similarity_method="cosine"
    )
    
    # 케이스 데이터 로드하여 응답 구성
    all_cases_data = cbr_engine.case_bank.load_cases()
    case_data_map = {case["case_id"]: case for case in all_cases_data}
    
    # CBRCase 객체 생성
    cbr_cases = []
    picked_case_ids = []
    similarity_scores = []
    
    for similarity_result in similar_cases:
        case_data = case_data_map.get(similarity_result.case_id)
        if case_data:
            # CaseMetadata 생성
            metadata = CaseMetadata(**case_data["metadata"])
            
            # CBRCase 생성
            cbr_case = CBRCase(
                case_id=case_data["case_id"],
                query_vector=case_data["query_vector"],
                response_text=case_data["response_text"],
                metadata=metadata,
                similarity_score=similarity_result.similarity_score
            )
            
            cbr_cases.append(cbr_case)
            picked_case_ids.append(case_data["case_id"])
            similarity_scores.append(similarity_result.similarity_score)
    
    # 실행 시간 측정
    latency = time.time() - start_time
    
    # 사용 로그 기록
    cbr_logger.log_query(
        request_id=request_id,
        query=request.query,
        category_path=request.category_path,
        picked_case_ids=picked_case_ids,
        similarity_scores=similarity_scores
    )
    
    return CBRSuggestResponse(
        cases=cbr_cases,
        query=request.query,
        total_candidates=len(all_cases_data),
        similarity_method="cosine",
        request_id=request_id,
        latency=latency
    )

@app.post("/cbr/feedback")
async def submit_cbr_feedback(feedback: CBRFeedback):
    """
    B-O4: CBR 피드백 수집
    사용자 피드백 수집 (thumbs up/down + 성공 여부)
    """
    from cbr_system import CBRUsageLogger
    
    cbr_logger = CBRUsageLogger()
    
    # 피드백 로그 기록
    cbr_logger.log_feedback(
        request_id=feedback.request_id,
        selected_case_ids=feedback.selected_case_ids,
        user_rating=feedback.user_rating,
        success_flag=feedback.success_flag,
        feedback_text=feedback.feedback_text
    )
    
    return {
        "status": "success",
        "message": "피드백이 성공적으로 기록되었습니다.",
        "request_id": feedback.request_id
    }

@app.get("/taxonomy/{version}/tree")
async def get_taxonomy_tree(version: str):
    """트리 구조 조회"""
    # TODO: 택소노미 트리 API 구현
    return {"version": version, "tree": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)