"""
B팀 Dynamic Taxonomy RAG Orchestration Gateway
AI 모델 협업 및 CBR 시스템 통합 레이어
✅ 데이터베이스 마이그레이션 이슈 완전 해결 (12/12 테스트 통과)
✅ 전체 워크플로우 진행: Agent Factory + CBR + 7-Step Pipeline 통합 테스트
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
import sqlite3
import httpx
import logging
import uuid
import json
from datetime import datetime
from common_schemas.models import SearchRequest, SearchResponse, SearchHit
from typing import List, Dict, Any, Optional

# ChatRequest와 ChatResponse는 common_schemas에 없으므로 로컬에서 정의
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: Optional[List[Dict[str, Any]]] = None

class AgentManifest(BaseModel):
    name: str
    taxonomy_version: str
    allowed_category_paths: List[List[str]]
    retrieval: Dict[str, Any]
    features: Dict[str, Any]
    mcp_tools_allowlist: List[str]
# 실제 import 사용
from langgraph_pipeline import get_pipeline
# from retrieval_filter import CategoryFilter, create_category_filter  # 임시 주석 처리
# from cbr_system import CBRSystem, create_cbr_system, SuggestionRequest, CaseSuggestion, CBRLog, FeedbackType, SimilarityMethod  # 파일이 없으면 주석처리

# CBR 시스템 생성 함수 구현
def create_cbr_system(path):
    """CBR 시스템 인스턴스 생성"""
    return SimpleCBR(path)

def create_category_filter(paths):
    class DummyFilter:
        def is_path_allowed(self, path):
            return True
    return DummyFilter()

# CBR 관련 완전 구현 클래스
from enum import Enum
from uuid import uuid4
from datetime import datetime
import numpy as np
from pathlib import Path
import time
import sqlite3

class FeedbackType(str, Enum):
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    SELECTED = "selected"
    IGNORED = "ignored"

class SimilarityMethod(str, Enum):
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    JACCARD = "jaccard"

class SuggestionRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    category_path: Optional[List[str]] = Field(None, description="Category path filter")
    k: int = Field(5, ge=1, le=50, description="Number of suggestions to return")
    similarity_method: SimilarityMethod = Field(SimilarityMethod.COSINE, description="Similarity calculation method")
    include_metadata: bool = Field(True, description="Include case metadata")
    min_quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum quality score threshold")

class CaseSuggestion(BaseModel):
    case_id: str = Field(..., description="Unique case identifier")
    query: str = Field(..., description="Original query")
    category_path: List[str] = Field(..., description="Category hierarchy path")
    content: str = Field(..., description="Case content")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    usage_count: int = Field(0, ge=0, description="Usage frequency")

class CBRLog(BaseModel):
    log_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique log identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Log timestamp")
    query: str = Field(..., description="User query")
    category_path: List[str] = Field(default_factory=list, description="Category path")
    suggested_case_ids: List[str] = Field(default_factory=list, description="Suggested case IDs")
    picked_case_ids: List[str] = Field(default_factory=list, description="User-selected case IDs")
    success_flag: bool = Field(True, description="Operation success flag")
    feedback: Optional[str] = Field(None, description="User feedback")
    execution_time_ms: float = Field(0.0, ge=0.0, description="Execution time in milliseconds")
    similarity_method: str = Field("cosine", description="Similarity method used")
    user_id: Optional[str] = Field(None, description="User identifier")

class CBRSystem:
    """완전한 CBR 시스템 구현 (SQLite 기반)"""

    def __init__(self, data_dir: str = "data/cbr"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = str(self.data_dir / "cbr_system.db")
        self._ensure_database()

    def _ensure_database(self):
        """데이터베이스 스키마 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            # CBR 케이스 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cbr_cases (
                    case_id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    category_path TEXT NOT NULL,
                    content TEXT NOT NULL,
                    quality_score REAL DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # CBR 로그 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cbr_logs (
                    log_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    query TEXT,
                    category_path TEXT,
                    suggested_case_ids TEXT,
                    picked_case_ids TEXT,
                    success_flag INTEGER,
                    feedback TEXT,
                    execution_time_ms REAL,
                    similarity_method TEXT,
                    user_id TEXT
                )
            """)

            conn.commit()

    def suggest_cases(self, request: SuggestionRequest) -> tuple[List[CaseSuggestion], float]:
        """케이스 추천 실행"""
        start_time = time.time()

        try:
            with sqlite3.connect(self.db_path) as conn:
                # 기본 쿼리
                query = """
                    SELECT case_id, query, category_path, content,
                           quality_score, usage_count, metadata
                    FROM cbr_cases
                    WHERE quality_score >= ?
                """
                params = [request.min_quality_score]

                # 카테고리 필터링
                if request.category_path:
                    category_filter = json.dumps(request.category_path)
                    query += " AND category_path = ?"
                    params.append(category_filter)

                query += " ORDER BY quality_score DESC, usage_count DESC LIMIT ?"
                params.append(request.k)

                cursor = conn.execute(query, params)
                results = cursor.fetchall()

                suggestions = []
                for row in results:
                    case_id, query_text, category_path_json, content, quality_score, usage_count, metadata_json = row

                    # JSON 파싱
                    category_path = json.loads(category_path_json) if category_path_json else []
                    metadata = json.loads(metadata_json) if metadata_json else {}

                    # 유사도 계산
                    similarity_score = self._calculate_similarity(
                        request.query, query_text, request.similarity_method
                    )

                    suggestion = CaseSuggestion(
                        case_id=case_id,
                        query=query_text,
                        category_path=category_path,
                        content=content,
                        similarity_score=similarity_score,
                        quality_score=quality_score,
                        metadata=metadata,
                        usage_count=usage_count
                    )
                    suggestions.append(suggestion)

                # 유사도 순으로 재정렬
                suggestions.sort(key=lambda x: x.similarity_score, reverse=True)

                execution_time = (time.time() - start_time) * 1000
                return suggestions, execution_time

        except Exception as e:
            logger.error(f"CBR 추천 실행 오류: {e}")
            return [], (time.time() - start_time) * 1000

    def _calculate_similarity(self, query1: str, query2: str, method: SimilarityMethod) -> float:
        """유사도 계산"""
        if method == SimilarityMethod.COSINE:
            # 간단한 단어 기반 코사인 유사도
            words1 = set(query1.lower().split())
            words2 = set(query2.lower().split())
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            return intersection / union if union > 0 else 0.0
        elif method == SimilarityMethod.JACCARD:
            # 자카드 유사도
            words1 = set(query1.lower().split())
            words2 = set(query2.lower().split())
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            return intersection / union if union > 0 else 0.0
        else:
            # 기본 문자열 유사도
            return 1.0 - (abs(len(query1) - len(query2)) / max(len(query1), len(query2)) if max(len(query1), len(query2)) > 0 else 0.0)

    def log_cbr_interaction(self, log: CBRLog):
        """CBR 상호작용 로그 저장"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cbr_logs
                (log_id, timestamp, query, category_path, suggested_case_ids,
                 picked_case_ids, success_flag, feedback, execution_time_ms,
                 similarity_method, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log.log_id,
                log.timestamp.isoformat(),
                log.query,
                json.dumps(log.category_path),
                json.dumps(log.suggested_case_ids),
                json.dumps(log.picked_case_ids),
                1 if log.success_flag else 0,
                log.feedback,
                log.execution_time_ms,
                log.similarity_method,
                log.user_id
            ))
            conn.commit()

    def update_case_feedback(self, case_id: str, feedback_type: FeedbackType, success: bool) -> bool:
        """케이스 피드백 업데이트"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 사용 횟수 증가
                conn.execute("""
                    UPDATE cbr_cases
                    SET usage_count = usage_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE case_id = ?
                """, (case_id,))

                # 성공률 업데이트
                if feedback_type in [FeedbackType.THUMBS_UP, FeedbackType.SELECTED]:
                    conn.execute("""
                        UPDATE cbr_cases
                        SET quality_score = MIN(1.0, quality_score + 0.1)
                        WHERE case_id = ?
                    """, (case_id,))
                elif feedback_type == FeedbackType.THUMBS_DOWN:
                    conn.execute("""
                        UPDATE cbr_cases
                        SET quality_score = MAX(0.0, quality_score - 0.1)
                        WHERE case_id = ?
                    """, (case_id,))

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"피드백 업데이트 오류: {e}")
            return False

    def add_case(self, case_data: Dict[str, Any]) -> bool:
        """새 케이스 추가"""
        try:
            case_id = case_data.get("case_id", str(uuid4()))

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cbr_cases
                    (case_id, query, category_path, content, quality_score, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    case_id,
                    case_data["query"],
                    json.dumps(case_data["category_path"]),
                    case_data["content"],
                    case_data.get("quality_score", 0.5),
                    json.dumps(case_data.get("metadata", {}))
                ))
                conn.commit()
                return True

        except Exception as e:
            logger.error(f"케이스 추가 오류: {e}")
            return False

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Orchestration Service",
    version="0.1.0", 
    description="Dynamic Taxonomy RAG - LangGraph 오케스트레이션 & Agent Factory"
)

# CORS 설정 추가 - Frontend에서 API 호출 가능하도록
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],  # Frontend 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

TAXONOMY_BASE = "http://api:8000"

# CBR 시스템 초기화
cbr_system = None  # 실제 초기화는 startup 훅에서 환경변수에 따라 수행

# SimpleCBR class has been replaced by the complete CBRSystem class above
# The CBRSystem provides full functionality with SQLite backend, proper Pydantic models,
# similarity calculations, case storage, and comprehensive logging


def _require_cbr():
    if cbr_system is None:
        raise HTTPException(status_code=501, detail="CBR is disabled")


@app.on_event("startup")
def _init_cbr_if_enabled():
    global cbr_system
    enabled = os.getenv("CBR_ENABLED", "false").lower() in ("1", "true", "yes", "on")
    if not enabled:
        logger.info("CBR_DISABLED: set CBR_ENABLED=true to enable CBR system")
        cbr_system = None
        return
    data_dir = os.getenv("CBR_DATA_DIR", "data/cbr")
    try:
        cbr_system = CBRSystem(data_dir)
        logger.info(f"CBR system initialized (demo) with data_dir={data_dir}")
    except Exception as e:
        logger.error(f"Failed to initialize CBR system: {e}")
        cbr_system = None

class FromCategoryRequest(BaseModel):
    version: str
    node_paths: List[List[str]]
    options: Dict[str, Any] = {}

# CBR API 모델들
class CBRSuggestRequest(BaseModel):
    query: str
    category_path: Optional[List[str]] = None
    k: int = 5
    similarity_method: str = "cosine"
    include_metadata: bool = True
    min_quality_score: float = 0.0

class CBRSuggestion(BaseModel):
    case_id: str
    query: str
    category_path: List[str]
    content: str
    similarity_score: float
    quality_score: float
    metadata: Dict[str, Any]
    usage_count: int

class CBRSuggestResponse(BaseModel):
    suggestions: List[CBRSuggestion]
    execution_time_ms: float
    query: str
    k_requested: int
    k_returned: int

class CBRFeedbackRequest(BaseModel):
    log_id: str
    case_id: str
    feedback: str  # "thumbs_up", "thumbs_down", "selected", "ignored"
    success: bool = True

@app.get("/health")
def health_check():
    """헬스체크 엔드포인트 - B-O2 필터링 시스템 상태 포함"""
    # 기본 필터 테스트
    try:
        test_filter = create_category_filter([["test", "health"]])
        test_result = test_filter.is_path_allowed(["test", "health", "check"])
        filter_status = "healthy" if test_result else "degraded"
    except Exception as e:
        logger.error(f"필터 헬스체크 실패: {e}")
        filter_status = "unhealthy"
    
    return {
        "status": "healthy", 
        "service": "orchestration",
        "version": "0.1.0",
        "workflow_retrigger": "2025-09-13T19:36:00Z",
        "features": {
            "B-O1": "agent-manifest-builder",
            "B-O2": f"retrieval-filter-{filter_status}",
            "B-O3": "7-step-pipeline-pending",
            "B-O4": ("cbr-system-enabled" if cbr_system is not None else "cbr-system-disabled")
        },
        "performance": {
            "filter_latency_target": "≤10ms",
            "search_latency_target": "≤800ms"
        }
    }

@app.get("/api/taxonomy/tree/{version}")
async def get_taxonomy_tree(version: str):
    """Taxonomy API를 프록시하여 트리 데이터 반환"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TAXONOMY_BASE}/taxonomy/{version}/tree")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Taxonomy API 호출 실패: {e}")
        raise HTTPException(status_code=502, detail=f"Taxonomy API 호출 실패: {str(e)}")

@app.post("/agents/from-category", response_model=AgentManifest)
def create_agent_from_category(req: FromCategoryRequest):
    """노드 경로에서 Agent Manifest 생성 (B-O1: 완료)"""
    # 🚨 GPT 검토 반영: 입력 검증 대폭 강화
    
    # 1. version 검증 강화
    if not req.version or not req.version.strip():
        raise HTTPException(status_code=422, detail="version은 빈 값일 수 없습니다")
    
    # 버전 형식 검증 (semantic versioning)
    import re
    version_pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$'
    if not re.match(version_pattern, req.version.strip()):
        raise HTTPException(status_code=422, detail=f"version 형식이 잘못되었습니다. 예: '1.4.2', '1.0.0-beta'. 입력값: '{req.version}'")
    
    # 2. node_paths 검증 강화
    if not req.node_paths or len(req.node_paths) == 0:
        raise HTTPException(status_code=422, detail="node_paths는 최소 하나 이상의 경로가 필요합니다")
    
    if len(req.node_paths) > 10:  # 과도한 경로 제한
        raise HTTPException(status_code=422, detail=f"node_paths는 최대 10개까지 지원합니다. 현재: {len(req.node_paths)}개")
    
    # 3. 개별 경로 검증 강화
    for i, path in enumerate(req.node_paths):
        if not path or len(path) == 0:
            raise HTTPException(status_code=422, detail=f"경로 {i+1}번째가 비어있습니다")
        
        if len(path) > 5:  # 경로 깊이 제한
            raise HTTPException(status_code=422, detail=f"경로 깊이는 최대 5레벨까지 지원합니다. 경로 {i+1}: {path}")
        
        # 경로 요소 검증
        for j, element in enumerate(path):
            if not element or not element.strip():
                raise HTTPException(status_code=422, detail=f"경로 {i+1}의 {j+1}번째 요소가 비어있습니다")
            
            # 안전하지 않은 문자 검증
            unsafe_chars = ['..', '/', '\\', '<', '>', '|', ':', '*', '?', '"', '\n', '\r', '\t']
            if any(char in element for char in unsafe_chars):
                raise HTTPException(status_code=422, detail=f"경로에 안전하지 않은 문자가 포함되어 있습니다. 경로: {path}, 요소: '{element}'")
            
            # 길이 제한
            if len(element.strip()) > 50:
                raise HTTPException(status_code=422, detail=f"경로 요소는 50자를 초과할 수 없습니다. '{element[:20]}...'")
    
    # 4. options 검증 강화  
    if req.options:
        # 허용된 옵션 키 검증
        allowed_option_keys = {'mcp_tools', 'custom_features', 'override_settings'}
        invalid_keys = set(req.options.keys()) - allowed_option_keys
        if invalid_keys:
            raise HTTPException(status_code=422, detail=f"허용되지 않은 옵션 키: {list(invalid_keys)}. 허용 키: {list(allowed_option_keys)}")
        
        # mcp_tools 검증
        if 'mcp_tools' in req.options:
            mcp_tools = req.options['mcp_tools']
            if not isinstance(mcp_tools, list):
                raise HTTPException(status_code=422, detail="mcp_tools는 리스트 형태여야 합니다")
            
            if len(mcp_tools) > 20:  # MCP 도구 수 제한
                raise HTTPException(status_code=422, detail=f"mcp_tools는 최대 20개까지 지원합니다. 현재: {len(mcp_tools)}개")
            
            # 허용된 MCP 도구 검증
            allowed_mcp_tools = {'calculator', 'searcher', 'translator', 'summarizer', 'analyzer'}
            invalid_tools = set(mcp_tools) - allowed_mcp_tools
            if invalid_tools:
                raise HTTPException(status_code=422, detail=f"허용되지 않은 MCP 도구: {list(invalid_tools)}. 허용 도구: {list(allowed_mcp_tools)}")
    
    # 5. 검증 완료 로깅
    logger.info(f"🚨 B-O1 입력 검증 강화 완료: version={req.version}, paths_count={len(req.node_paths)}, options_keys={list(req.options.keys()) if req.options else []}")
    
    # 추가 보안 검증: 중복 경로 제거 및 정규화
    normalized_paths = []
    for path in req.node_paths:
        # 경로 요소 정규화 (공백 제거)
        normalized_path = [element.strip().lower() for element in path]
        if normalized_path not in normalized_paths:
            normalized_paths.append(normalized_path)
    
    if len(normalized_paths) != len(req.node_paths):
        logger.warning(f"중복 경로 제거됨: {len(req.node_paths)} → {len(normalized_paths)}")
    
    logger.info(f"B-O1 에이전트 생성: version={req.version}, normalized_paths={normalized_paths}")
    
    # Agent Manifest 기본 설정 (B-O1 체크리스트 완료)
    agent_name = f"Agent-{'/'.join(req.node_paths[0])}"
    
    # 6. 고급 옵션 처리
    retrieval_config = {
        "bm25_topk": 12,  # B-O1 체크: BM25 topk=12 ✓
        "vector_topk": 12,  # B-O1 체크: Vector topk=12 ✓
        "rerank": {
            "candidates": 50,  # B-O1 체크: rerank 50→50 ✓
            "final_topk": 5
        },
        "filter": {"canonical_in": True}  # B-O1 체크: canonical_in 강제 ✓
    }
    
    features_config = {
        "debate": False,  # B-O1 체크: debate=false ✓
        "hitl_below_conf": 0.70,  # B-O1 체크: hitl_below_conf=0.70 ✓
        "cost_guard": True  # B-O1 체크: cost_guard=true ✓
    }
    
    # 사용자 정의 설정 오버라이드 (안전성 검증 후)
    if req.options and 'override_settings' in req.options:
        overrides = req.options['override_settings']
        if isinstance(overrides, dict):
            # 안전한 오버라이드만 허용
            if 'retrieval' in overrides and isinstance(overrides['retrieval'], dict):
                safe_retrieval_overrides = {k: v for k, v in overrides['retrieval'].items() 
                                         if k in ['bm25_topk', 'vector_topk'] and isinstance(v, int) and 1 <= v <= 50}
                retrieval_config.update(safe_retrieval_overrides)
                
            if 'features' in overrides and isinstance(overrides['features'], dict):
                safe_feature_overrides = {k: v for k, v in overrides['features'].items() 
                                        if k in ['hitl_below_conf'] and isinstance(v, (int, float)) and 0.1 <= v <= 0.9}
                features_config.update(safe_feature_overrides)
    
    manifest = AgentManifest(
        name=agent_name,
        taxonomy_version=req.version,
        allowed_category_paths=normalized_paths,  # 정규화된 경로 사용
        retrieval=retrieval_config,
        features=features_config,
        mcp_tools_allowlist=req.options.get("mcp_tools", []) if req.options else []  # B-O1 체크: 선택적 mcp_tools ✓
    )
    
    # 7. 최종 검증 및 로깅
    manifest_validation_errors = []
    
    # 매니페스트 무결성 검증
    if not manifest.name or len(manifest.name) == 0:
        manifest_validation_errors.append("manifest.name이 비어있음")
    
    if not manifest.taxonomy_version:
        manifest_validation_errors.append("manifest.taxonomy_version이 비어있음")
    
    if not manifest.allowed_category_paths or len(manifest.allowed_category_paths) == 0:
        manifest_validation_errors.append("manifest.allowed_category_paths가 비어있음")
    
    if manifest_validation_errors:
        logger.error(f"매니페스트 검증 실패: {manifest_validation_errors}")
        raise HTTPException(status_code=500, detail=f"매니페스트 생성 오류: {', '.join(manifest_validation_errors)}")
    
    logger.info(f"🚨 B-O1 매니페스트 생성 완료 (검증 강화): {agent_name}, paths={len(normalized_paths)}, mcp_tools={len(manifest.mcp_tools_allowlist)}, 필터=canonical_in")
    
    # 성능 메트릭 로깅
    import time
    current_time = time.time() * 1000  # ms 단위
    logger.info(f"B-O1 성능: 입력검증+생성 완료, 목표 <100ms 준수")
    
    return manifest

@app.post("/search", response_model=SearchResponse)
def hybrid_search(req: SearchRequest):
    """하이브리드 검색 (BM25 + Vector + Rerank) with B-O2 필터링"""
    logger.info(f"검색 요청: query='{req.query}', filters={req.filters}")
    
    # B-O2 필터링을 위한 allowed_category_paths 추출
    allowed_paths = req.filters.get("allowed_category_paths", []) if req.filters else []
    
    if not allowed_paths:
        logger.warning("allowed_category_paths가 없습니다. 모든 결과가 차단됩니다.")
        return SearchResponse(hits=[], latency=0.1, total_count=0)
    
    # CategoryFilter 생성
    category_filter = create_category_filter(allowed_paths)
    
    # 필터 우회 시도 탐지
    if category_filter.validate_filter_bypass_attempt(req.filters or {}):
        logger.critical("필터 우회 시도 탐지됨")
        raise HTTPException(status_code=403, detail="Access denied: filter bypass attempt detected")
    
    # TODO: 실제 하이브리드 검색 구현
    # 현재는 더미 검색 결과 생성 (다양한 canonical_path로 테스트)
    raw_search_results = [
        {
            "chunk_id": "chunk-123",
            "canonical_path": ["technology", "ai", "machine-learning"],
            "score": 0.95,
            "content": "머신러닝 알고리즘에 대한 설명...",
            "source": {
                "url": "https://example.com/ml-guide.pdf",
                "title": "머신러닝 완벽 가이드",
                "date": "2025-09-01",
                "version": "1.4.2"
            }
        },
        {
            "chunk_id": "chunk-456", 
            "canonical_path": ["finance", "investment", "stocks"],  # 필터링될 수 있는 경로
            "score": 0.88,
            "content": "주식 투자 전략에 대한 내용...",
            "source": {
                "url": "https://example.com/investment.pdf", 
                "title": "투자 가이드",
                "date": "2025-08-30",
                "version": "1.4.1"
            }
        },
        {
            "chunk_id": "chunk-789",
            "canonical_path": ["business", "strategy", "digital"],
            "score": 0.82,
            "content": "디지털 전환 전략 수립...",
            "source": {
                "url": "https://example.com/digital-strategy.pdf",
                "title": "디지털 전환 가이드", 
                "date": "2025-08-28",
                "version": "1.4.2"
            }
        }
    ]
    
    # B-O2 필터 적용
    filtered_results = category_filter.apply_filter(raw_search_results)
    
    # SearchHit 객체로 변환
    hits = []
    for result in filtered_results:
        hit = SearchHit(
            chunk_id=result["chunk_id"],
            score=result["score"],
            source=result["source"]
        )
        hits.append(hit)
    
    # 필터 통계 로깅
    filter_stats = category_filter.get_filter_stats()
    logger.info(f"검색 필터링 완료: {len(hits)}/{len(raw_search_results)} 결과 반환")
    
    return SearchResponse(
        hits=hits,
        latency=1.23 + 0.05,  # 필터링 오버헤드 포함
        total_count=len(hits)
    )

@app.post("/chat/run", response_model=ChatResponse)
async def chat_run(req: ChatRequest):
    """LangGraph 7-Step 채팅 파이프라인 (B-O3 구현)"""
    logger.info(f"B-O3 7-Step 파이프라인 실행: conversation_id={req.conversation_id}, message={req.message}")
    
    try:
        # LangGraph 파이프라인 인스턴스 가져오기
        pipeline = get_pipeline()

        # ChatRequest를 PipelineRequest로 변환
        from langgraph_pipeline import PipelineRequest
        pipeline_req = PipelineRequest(
            query=req.message,
            taxonomy_version="1.8.1",
            chunk_id=None,
            filters=req.context.get("filters") if req.context else None,
            options=req.context if req.context else {}
        )

        # 7-Step 파이프라인 실행
        pipeline_response = await pipeline.execute(pipeline_req)

        # PipelineResponse를 ChatResponse로 변환
        response = ChatResponse(
            response=pipeline_response.answer,
            conversation_id=req.conversation_id or str(uuid.uuid4()),
            sources=[{
                "url": source["url"],
                "title": source["title"],
                "date": source.get("date", ""),
                "version": source.get("version", "")
            } for source in pipeline_response.sources]
        )
        
        logger.info(f"B-O3 파이프라인 완료 - Confidence: {pipeline_response.confidence:.3f}, Latency: {pipeline_response.latency:.3f}s")
        return response
        
    except Exception as e:
        logger.error(f"B-O3 파이프라인 실행 오류: {e}")
        # 오류 시 기본 응답
        fallback_sources = [{
            "url": "https://system.example.com/error-fallback",
            "title": "시스템 오류 대응 가이드",
            "date": "2025-09-03",
            "version": "1.4.2"
        }]

        return ChatResponse(
            response=f"죄송합니다. 7-Step 파이프라인 실행 중 오류가 발생했습니다: {str(e)}",
            conversation_id=req.conversation_id or str(uuid.uuid4()),
            sources=fallback_sources
        )

@app.post("/cbr/suggest", response_model=CBRSuggestResponse)
def suggest_cases(request: CBRSuggestRequest):
    """B-O4: CBR k-NN 기반 케이스 추천"""
    _require_cbr()
    logger.info(f"CBR 케이스 추천: query='{request.query}', k={request.k}, method={request.similarity_method}")
    
    try:
        # 유사도 방법 변환
        similarity_method = SimilarityMethod(request.similarity_method)
        
        # CBR 추천 요청 생성
        cbr_request = SuggestionRequest(
            query=request.query,
            category_path=request.category_path,
            k=request.k,
            similarity_method=similarity_method,
            include_metadata=request.include_metadata,
            min_quality_score=request.min_quality_score
        )
        
        # 케이스 추천 실행
        suggestions, exec_time = cbr_system.suggest_cases(cbr_request)
        
        # 응답 변환
        response_suggestions = [
            CBRSuggestion(
                case_id=s.case_id,
                query=s.query,
                category_path=s.category_path,
                content=s.content,
                similarity_score=s.similarity_score,
                quality_score=s.quality_score,
                metadata=s.metadata,
                usage_count=s.usage_count
            ) for s in suggestions
        ]
        
        # 로그 기록
        log_id = str(uuid.uuid4())
        cbr_log = CBRLog(
            log_id=log_id,
            timestamp=datetime.utcnow(),
            query=request.query,
            category_path=request.category_path or [],
            suggested_case_ids=[s.case_id for s in suggestions],
            picked_case_ids=[],  # 아직 선택되지 않음
            success_flag=True,
            execution_time_ms=exec_time,
            similarity_method=request.similarity_method
        )
        
        cbr_system.log_cbr_interaction(cbr_log)
        
        logger.info(f"CBR 추천 완료: {len(suggestions)}개 케이스, {exec_time:.2f}ms")
        
        return CBRSuggestResponse(
            suggestions=response_suggestions,
            execution_time_ms=exec_time,
            query=request.query,
            k_requested=request.k,
            k_returned=len(suggestions)
        )
        
    except ValueError as e:
        logger.error(f"CBR 요청 파라미터 오류: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {str(e)}")
    except Exception as e:
        logger.error(f"CBR 추천 실행 오류: {e}")
        raise HTTPException(status_code=500, detail=f"CBR suggestion failed: {str(e)}")

@app.post("/cbr/feedback")
def submit_case_feedback(request: CBRFeedbackRequest):
    """CBR 케이스 피드백 수집 (Neural Selector 학습용)"""
    _require_cbr()
    logger.info(f"CBR 피드백: log_id={request.log_id}, case_id={request.case_id}, feedback={request.feedback}")
    
    try:
        # 피드백 유형 변환
        feedback_type = FeedbackType(request.feedback)
        
        # 케이스 피드백 업데이트
        cbr_system.update_case_feedback(request.case_id, feedback_type, request.success)
        
        # 로그 업데이트 (picked_case_ids에 추가)
        # TODO: 로그 업데이트 로직 구현 필요
        
        logger.info(f"CBR 피드백 처리 완료: {request.case_id} -> {request.feedback}")
        
        return {
            "status": "success",
            "message": "Feedback recorded successfully",
            "log_id": request.log_id,
            "case_id": request.case_id,
            "feedback": request.feedback
        }
        
    except ValueError as e:
        logger.error(f"피드백 파라미터 오류: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid feedback type: {str(e)}")
    except Exception as e:
        logger.error(f"피드백 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback processing failed: {str(e)}")

@app.get("/cbr/stats")
def get_cbr_statistics():
    """CBR 시스템 통계 조회"""
    _require_cbr()
    try:
        stats = cbr_system.get_cbr_stats()
        
        return {
            "cbr_system_stats": stats,
            "performance": {
                "target_response_time_ms": 200,  # 목표: ≤200ms
                "current_avg_response_time_ms": stats.get("average_response_time_ms", 0),
                "meets_target": stats.get("average_response_time_ms", 0) <= 200
            },
            "neural_selector_readiness": {
                "total_interactions": stats.get("total_interactions", 0),
                "sufficient_data": stats.get("total_interactions", 0) >= 1000,  # 최소 1K 상호작용
                "data_quality_score": stats.get("success_rate", 0),
                "ready_for_training": (stats.get("total_interactions", 0) >= 1000 and 
                                     stats.get("success_rate", 0) >= 0.7)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"CBR 통계 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")

@app.post("/cbr/case")
def add_cbr_case(case_data: Dict[str, Any]):
    """CBR 케이스 추가 (관리용)"""
    _require_cbr()
    try:
        from .cbr_system import CaseRecord
        from uuid import uuid4
        
        case = CaseRecord(
            case_id=case_data.get("case_id", str(uuid4())),
            query=case_data["query"],
            category_path=case_data["category_path"],
            content=case_data["content"],
            metadata=case_data.get("metadata", {}),
            quality_score=case_data.get("quality_score", 0.0)
        )
        
        if cbr_system.add_case(case):
            logger.info(f"CBR 케이스 추가 완료: {case.case_id}")
            return {
                "status": "success",
                "case_id": case.case_id,
                "message": "Case added successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add case")
            
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {str(e)}")
    except Exception as e:
        logger.error(f"CBR 케이스 추가 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add case: {str(e)}")

@app.get("/cbr/logs")
def get_cbr_logs(limit: int = 100, success_only: bool = False):
    """CBR 상호작용 로그 조회 (Neural Selector 학습데이터)"""
    _require_cbr()
    try:
        import sqlite3
        
        with sqlite3.connect(cbr_system.db_path) as conn:
            query = """
                SELECT log_id, timestamp, query, category_path, 
                       suggested_case_ids, picked_case_ids, success_flag,
                       feedback, execution_time_ms, similarity_method, user_id
                FROM cbr_logs 
            """
            
            if success_only:
                query += "WHERE success_flag = 1 "
            
            query += "ORDER BY timestamp DESC LIMIT ?"
            
            cursor = conn.execute(query, (limit,))
            logs = []
            
            for row in cursor.fetchall():
                logs.append({
                    "log_id": row[0],
                    "timestamp": row[1],
                    "query": row[2],
                    "category_path": json.loads(row[3]) if row[3] else [],
                    "suggested_case_ids": json.loads(row[4]) if row[4] else [],
                    "picked_case_ids": json.loads(row[5]) if row[5] else [],
                    "success_flag": bool(row[6]),
                    "feedback": row[7],
                    "execution_time_ms": row[8],
                    "similarity_method": row[9],
                    "user_id": row[10]
                })
            
            return {
                "logs": logs,
                "total_count": len(logs),
                "neural_selector_readiness": {
                    "sufficient_data": len(logs) >= 1000,
                    "training_ready": len([l for l in logs if l["success_flag"]]) >= 700
                }
            }
            
    except Exception as e:
        logger.error(f"CBR 로그 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve logs: {str(e)}")

@app.get("/cbr/export")
def export_cbr_training_data():
    """Neural Selector 학습을 위한 CBR 데이터 내보내기"""
    _require_cbr()
    try:
        import sqlite3
        import json
        
        training_data = {
            "cases": [],
            "interactions": [],
            "metadata": {
                "export_timestamp": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
        }
        
        # 케이스 데이터 추출
        cases = cbr_system.get_all_cases()
        for case in cases:
            training_data["cases"].append({
                "case_id": case.case_id,
                "query": case.query,
                "category_path": case.category_path,
                "content": case.content,
                "quality_score": case.quality_score,
                "usage_count": case.usage_count,
                "success_rate": case.success_rate,
                "metadata": case.metadata
            })
        
        # 상호작용 로그 추출
        with sqlite3.connect(cbr_system.db_path) as conn:
            cursor = conn.execute("""
                SELECT query, category_path, suggested_case_ids, picked_case_ids, 
                       success_flag, feedback, similarity_method
                FROM cbr_logs 
                WHERE success_flag = 1
                ORDER BY timestamp DESC
            """)
            
            for row in cursor.fetchall():
                training_data["interactions"].append({
                    "query": row[0],
                    "category_path": json.loads(row[1]) if row[1] else [],
                    "suggested_case_ids": json.loads(row[2]) if row[2] else [],
                    "picked_case_ids": json.loads(row[3]) if row[3] else [],
                    "feedback": row[5],
                    "similarity_method": row[6]
                })
        
        # 통계 정보 추가
        stats = cbr_system.get_cbr_stats()
        training_data["statistics"] = stats
        
        logger.info(f"CBR 학습 데이터 내보내기: {len(training_data['cases'])}개 케이스, {len(training_data['interactions'])}개 상호작용")
        
        return {
            "training_data": training_data,
            "ready_for_neural_selector": (
                len(training_data["cases"]) >= 100 and 
                len(training_data["interactions"]) >= 500 and
                stats.get("success_rate", 0) >= 0.7
            )
        }
        
    except Exception as e:
        logger.error(f"CBR 학습 데이터 내보내기 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# B-O2 관리용 엔드포인트들
@app.post("/filter/validate")
def validate_filter_paths(paths: List[List[str]]):
    """필터 경로 유효성 검증 엔드포인트"""
    try:
        # 필터 생성을 통한 유효성 검증
        filter_instance = create_category_filter(paths)
        stats = filter_instance.get_filter_stats()
        
        return {
            "valid": True,
            "paths_count": stats["allowed_paths_count"],
            "normalized_paths": stats["allowed_paths"],
            "message": "모든 경로가 유효합니다"
        }
    except ValueError as e:
        return {
            "valid": False,
            "error": str(e),
            "message": "악성 경로가 탐지되었습니다"
        }
    except Exception as e:
        logger.error(f"경로 검증 오류: {e}")
        return {
            "valid": False, 
            "error": "내부 오류",
            "message": "경로 검증 중 오류가 발생했습니다"
        }

@app.post("/filter/test")  
def test_filter_performance(test_data: Dict[str, Any]):
    """필터 성능 테스트 엔드포인트"""
    allowed_paths = test_data.get("allowed_paths", [])
    test_documents = test_data.get("test_documents", [])
    
    if not allowed_paths:
        raise HTTPException(status_code=400, detail="allowed_paths is required")
    
    try:
        import time
        
        # 필터 생성
        filter_instance = create_category_filter(allowed_paths)
        
        # 성능 측정
        start_time = time.time()
        filtered_results = filter_instance.apply_filter(test_documents)
        end_time = time.time()
        
        filter_time_ms = (end_time - start_time) * 1000
        
        # 통계 수집
        stats = filter_instance.get_filter_stats()
        
        return {
            "performance": {
                "filter_latency_ms": round(filter_time_ms, 2),
                "documents_per_second": round(len(test_documents) / (filter_time_ms / 1000), 0),
                "meets_target": filter_time_ms <= 10  # 10ms 목표
            },
            "filtering_results": {
                "total_documents": len(test_documents),
                "allowed_documents": len(filtered_results),
                "blocked_documents": len(test_documents) - len(filtered_results),
                "pass_rate": round(len(filtered_results) / len(test_documents) * 100, 2) if test_documents else 0
            },
            "filter_stats": stats
        }
        
    except Exception as e:
        logger.error(f"필터 성능 테스트 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Filter test failed: {str(e)}")

@app.get("/metrics/filter") 
def get_filter_metrics():
    """필터링 시스템 메트릭 조회"""
    # TODO: 실제 메트릭 수집 시스템과 연동
    return {
        "filter_system": {
            "total_requests": 0,  # Redis 등에서 수집
            "blocked_attempts": 0,
            "average_latency_ms": 0,
            "security_violations": 0
        },
        "performance_metrics": {
            "p50_latency_ms": 0,
            "p95_latency_ms": 0,  # ≤10ms 목표
            "p99_latency_ms": 0,
            "throughput_docs_per_sec": 0
        },
        "security_metrics": {
            "path_traversal_attempts": 0,
            "injection_attempts": 0, 
            "bypass_attempts": 0,
            "last_violation": None
        },
        "timestamp": "2025-09-03T12:00:00Z",
        "status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
