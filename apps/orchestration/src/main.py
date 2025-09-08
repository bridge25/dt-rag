from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import sys
import time
import httpx
import asyncio
import random
import logging
sys.path.append('../../../packages')

# A팀 API 클라이언트 (PRD 준수 + Connection Pool + Retry Logic)
class ATaxonomyAPIClient:
    def __init__(self, base_url: str = "http://localhost:8001", api_key: str = None):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["X-API-Key"] = api_key
        
        # Connection Pool 설정
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        timeout = httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=10.0)
        
        self.client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            headers=self.headers
        )
    
    async def _request_with_retry(self, method: str, url: str, **kwargs) -> dict:
        """지수 백오프를 사용한 재시도 로직"""
        max_retries = 3
        backoff_factor = 1.0
        
        for attempt in range(max_retries + 1):
            try:
                if method.upper() == "POST":
                    response = await self.client.post(url, **kwargs)
                else:
                    response = await self.client.get(url, **kwargs)
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                # 429 (Too Many Requests) 또는 5xx 에러만 재시도
                if e.response.status_code in [429, 500, 502, 503, 504]:
                    if attempt < max_retries:
                        # 지수 백오프 + 지터
                        delay = backoff_factor * (2 ** attempt) + random.uniform(0, 0.2)
                        logging.warning(f"API 호출 실패 (시도 {attempt + 1}/{max_retries + 1}): {e.response.status_code}. {delay:.2f}초 후 재시도")
                        await asyncio.sleep(delay)
                        continue
                raise HTTPException(status_code=e.response.status_code, detail=f"A팀 API 호출 실패: {str(e)}")
                
            except Exception as e:
                if attempt < max_retries:
                    delay = backoff_factor * (2 ** attempt) + random.uniform(0, 0.2)
                    logging.warning(f"API 연결 오류 (시도 {attempt + 1}/{max_retries + 1}): {str(e)}. {delay:.2f}초 후 재시도")
                    await asyncio.sleep(delay)
                    continue
                raise HTTPException(status_code=500, detail=f"A팀 API 연결 실패: {str(e)}")
    
    async def classify(self, request: dict) -> dict:
        """A팀 /classify API 호출 (재시도 로직 포함)"""
        return await self._request_with_retry("POST", f"{self.base_url}/classify", json=request)
    
    async def search(self, request: dict) -> dict:
        """A팀 /search API 호출 (재시도 로직 포함)"""
        return await self._request_with_retry("POST", f"{self.base_url}/search", json=request)
    
    async def get_taxonomy_tree(self, version: str) -> dict:
        """A팀 /taxonomy/{version}/tree API 호출 (재시도 로직 포함)"""
        return await self._request_with_retry("GET", f"{self.base_url}/taxonomy/{version}/tree")

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

# A팀 API 클라이언트 인스턴스 (PRD 준수)
a_team_client = ATaxonomyAPIClient()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "orchestration"}

@app.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    """
    B팀 오케스트레이션: A팀 분류 API를 호출하여 결과 반환 (PRD 준수)
    """
    try:
        # A팀 /classify API 호출 (PRD 준수)
        a_team_request = {
            "chunk_id": request.chunk_id,
            "text": request.text,
            "hint_paths": request.hint_paths
        }
        
        result = await a_team_client.classify(a_team_request)
        
        # A팀 응답을 B팀 응답 형식으로 변환
        return ClassifyResponse(
            canonical=result.get("canonical", []),
            candidates=[
                TaxonomyNode(**candidate) for candidate in result.get("candidates", [])
            ],
            hitl=result.get("hitl", False),
            confidence=result.get("confidence", 0.0),
            reasoning=result.get("reasoning", ["A팀 분류 API 호출"])
        )
        
    except Exception as e:
        # A팀 API 호출 실패 시 폴백
        return ClassifyResponse(
            canonical=["Unknown"],
            candidates=[],
            hitl=True,
            confidence=0.0,
            reasoning=[f"A팀 API 호출 실패: {str(e)}", "수동 검토 필요"]
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
    B팀 오케스트레이션: A팀 검색 API를 호출하여 결과 반환 (PRD 준수)
    """
    try:
        # A팀 /search API 호출 (PRD 준수)
        a_team_request = {
            "q": request.q,
            "filters": request.filters,
            "bm25_topk": request.bm25_topk,
            "vector_topk": request.vector_topk,
            "rerank_candidates": request.rerank_candidates,
            "final_topk": request.final_topk
        }
        
        result = await a_team_client.search(a_team_request)
        
        # A팀 응답을 B팀 응답 형식으로 변환
        return SearchResponse(
            hits=result.get("hits", []),
            latency=result.get("latency", 0.0),
            request_id=result.get("request_id", f"search_{int(time.time() * 1000)}"),
            total_candidates=result.get("total_candidates"),
            sources_count=result.get("sources_count"),
            taxonomy_version=result.get("taxonomy_version")
        )
        
    except Exception as e:
        # A팀 API 호출 실패 시 폴백
        request_id = f"search_{int(time.time() * 1000)}"
        return SearchResponse(
            hits=[],
            latency=0.0,
            request_id=request_id,
            total_candidates=0,
            sources_count=0,
            taxonomy_version="unknown"
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
    from cbr_system import CBRRecommendationEngine, CBRUsageLogger, create_query_vector_real
    import uuid
    
    start_time = time.time()
    request_id = f"cbr_{int(time.time() * 1000)}"
    
    # CBR 엔진 초기화
    cbr_engine = CBRRecommendationEngine()
    cbr_logger = CBRUsageLogger()
    
    # 쿼리 벡터 생성 (실제 임베딩 모델 사용)
    query_vector = create_query_vector_real(request.query)
    
    # A팀 case_bank에서 유사한 케이스 검색 (PRD 준수)
    similar_cases = await cbr_engine.find_similar_cases(
        query_vector=query_vector,
        category_path=request.category_path,
        k=request.k,
        similarity_threshold=request.similarity_threshold,
        similarity_method="cosine"
    )
    
    # A팀 case_bank에서 케이스 데이터 로드하여 응답 구성
    all_cases_data = await cbr_engine.case_bank.load_cases()
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
    """
    B팀 오케스트레이션: A팀 택소노미 트리 API 호출 (PRD 준수)
    """
    try:
        # A팀 /taxonomy/{version}/tree API 호출 (PRD 준수)
        result = await a_team_client.get_taxonomy_tree(version)
        return result
        
    except Exception as e:
        # A팀 API 호출 실패 시 폴백
        return {
            "version": version, 
            "tree": [],
            "error": f"A팀 API 호출 실패: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)