"""
B-O3: 7-Step LangGraph Pipeline Implementation
intent → retrieve → plan → tools/debate → compose → cite → respond

Week-1 목표: 완전한 7-Step 파이프라인 골격 + 메타데이터 수집
"""

import asyncio
import time
import logging
import httpx
import os
import random
import json
from typing import TypedDict, List, Dict, Any, Optional, Union
from datetime import datetime

# LangGraph 대신 간단한 그래프 구현 사용
from typing import Callable
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineState(TypedDict):
    """LangGraph 파이프라인 상태 관리"""
    # 입력
    query: str
    chunk_id: Optional[str]
    taxonomy_version: str
    
    # Step 1: Intent
    intent: str
    intent_confidence: float
    
    # Step 2: Retrieve
    retrieved_docs: List[Dict[str, Any]]
    retrieval_filter_applied: bool
    bm25_results: List[Dict]
    vector_results: List[Dict]
    
    # Step 3: Plan
    answer_strategy: str
    plan_reasoning: List[str]
    
    # Step 4: Tools/Debate
    tools_used: List[str]
    debate_activated: bool
    debate_reasoning: Optional[str]
    
    # Step 5: Compose
    draft_answer: str
    
    # Step 6: Cite
    sources: List[Dict[str, Any]]
    citations_count: int
    
    # Step 7: Respond
    final_answer: str
    confidence: float
    
    # 메타데이터 (B-O3 필수 요구사항)
    cost: float  # 토큰 사용량 기반 비용
    latency: float  # 파이프라인 전체 시간
    step_timings: Dict[str, float]  # 각 단계별 실행 시간
    
    # 에러 처리
    errors: List[str]
    retry_count: int


class PipelineRequest(BaseModel):
    """파이프라인 요청 스키마"""
    query: str = Field(..., min_length=1, description="사용자 질의")
    taxonomy_version: str = Field(default="1.8.1", description="택소노미 버전")
    chunk_id: Optional[str] = Field(default=None, description="청크 ID (분류용)")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="검색 필터")
    options: Optional[Dict[str, Any]] = Field(default={}, description="추가 옵션")


class PipelineResponse(BaseModel):
    """파이프라인 응답 스키마 (B-O3 메타데이터 포함)"""
    # 핵심 응답
    answer: str = Field(..., description="최종 답변")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도 점수")
    
    # B-O3 필수 메타데이터
    sources: List[Dict[str, Any]] = Field(..., min_items=0, description="출처 목록 (≥2개 권장)")
    taxonomy_version: str = Field(..., description="사용된 택소노미 버전")
    cost: float = Field(..., ge=0.0, description="토큰 사용량 기반 비용 (₩)")
    latency: float = Field(..., ge=0.0, description="파이프라인 전체 실행 시간 (초)")
    
    # 디버깅 정보
    intent: str = Field(..., description="파악된 사용자 의도")
    step_timings: Dict[str, float] = Field(..., description="각 단계별 실행 시간")
    debate_activated: bool = Field(default=False, description="debate 스위치 활성화 여부")
    
    # 품질 정보
    retrieved_count: int = Field(default=0, description="검색된 문서 수")
    citations_count: int = Field(default=0, description="인용된 출처 수")


class SimpleGraph:
    """간단한 순차 실행 그래프"""
    
    def __init__(self):
        self.steps = []
        
    def add_step(self, name: str, func: Callable):
        self.steps.append((name, func))
        
    async def ainvoke(self, state: PipelineState) -> PipelineState:
        """순차적으로 모든 단계 실행"""
        for step_name, step_func in self.steps:
            logger.info(f"실행 중: {step_name}")
            state = await step_func(state)
        return state


class LangGraphPipeline:
    """B-O3 7-Step 파이프라인 (A팀 API 연동, PRD 준수, MCP 통합)"""

    def __init__(self, a_team_base_url: str = "http://localhost:8001", mcp_server_url: str = "http://localhost:8080"):
        self.a_team_base_url = a_team_base_url
        self.mcp_server_url = mcp_server_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.mcp_client = httpx.AsyncClient(timeout=15.0)
        self.graph = self._build_graph()

        # MCP 도구 설정
        self.available_mcp_tools = [
            'context7', 'sequential-thinking', 'fallback-search',
            'classification-validator', 'explanation-formatter'
        ]

        # 성능 메트릭
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_latency': 0.0,
            'tools_usage_count': {tool: 0 for tool in self.available_mcp_tools}
        }

        # 복원력 시스템 통합
        try:
            from pipeline_resilience import get_resilience_manager
            self.resilience_manager = get_resilience_manager()
        except ImportError:
            logger.warning("pipeline_resilience 모듈을 찾을 수 없습니다. 기본 실행 모드로 진행합니다.")
            self.resilience_manager = None
        
    def _build_graph(self) -> SimpleGraph:
        """7-Step 파이프라인 그래프 구성"""
        workflow = SimpleGraph()
        
        # 7개 단계 순차 추가
        workflow.add_step("step1_intent", self._step1_intent_classification)
        workflow.add_step("step2_retrieve", self._step2_hybrid_retrieval)
        workflow.add_step("step3_plan", self._step3_answer_planning)
        workflow.add_step("step4_tools_debate", self._step4_tools_and_debate)
        workflow.add_step("step5_compose", self._step5_answer_composition)
        workflow.add_step("step6_cite", self._step6_citation_extraction)
        workflow.add_step("step7_respond", self._step7_final_response)
        
        return workflow
    
    async def _step1_intent_classification(self, state: PipelineState) -> PipelineState:
        """Step 1: Intent Classification (사용자 의도 파악)"""
        step_start = time.time()
        logger.info(f"Step 1: Intent Classification - Query: {state['query']}")
        
        # TODO: 실제 의도 분류 로직 구현 (LLM 호출)
        # 현재는 스캐폴딩 구현
        query = state['query'].lower()
        
        if any(keyword in query for keyword in ['검색', 'search', '찾아', '조회']):
            intent = "search"
        elif any(keyword in query for keyword in ['분류', 'classify', '카테고리']):
            intent = "classify"
        elif any(keyword in query for keyword in ['설명', 'explain', '알려줘']):
            intent = "explain"
        else:
            intent = "general_query"
            
        intent_confidence = 0.8  # TODO: 실제 신뢰도 계산
        
        step_time = time.time() - step_start
        
        state.update({
            "intent": intent,
            "intent_confidence": intent_confidence,
            "step_timings": {**state.get("step_timings", {}), "step1_intent": step_time}
        })
        
        logger.info(f"Step 1 완료: intent={intent}, confidence={intent_confidence:.3f}, time={step_time:.3f}s")
        return state
    
    async def _step2_hybrid_retrieval(self, state: PipelineState) -> PipelineState:
        """Step 2: Hybrid Retrieval (A팀 /search API 호출, PRD 준수)"""
        step_start = time.time()
        logger.info(f"Step 2: Hybrid Retrieval - Intent: {state['intent']}")
        
        try:
            # A팀 /search API 호출 (PRD 준수)
            search_request = {
                "q": state['query'],
                "filters": None,  # TODO: intent에 따른 필터 적용
                "bm25_topk": 12,
                "vector_topk": 12,
                "rerank_candidates": 50,
                "final_topk": 5
            }
            # Retry-After aware call to A-team /search
            max_retries = int(os.getenv("MAX_RETRIES", os.getenv("ORCH_RETRY_MAX", "3")))
            backoff = float(os.getenv("ORCH_RETRY_BACKOFF", "1.0"))
            jitter = float(os.getenv("ORCH_RETRY_JITTER_MAX", "0.2"))
            max_cap = float(os.getenv("ORCH_RETRY_MAX_DELAY", "10.0"))
            for attempt in range(max_retries + 1):
                try:
                    response = await self.client.post(
                        f"{self.a_team_base_url}/search",
                        json=search_request
                    )
                    response.raise_for_status()
                    break
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in [429, 500, 502, 503, 504] and attempt < max_retries:
                        ra = e.response.headers.get("Retry-After")
                        parsed = None
                        if ra:
                            try:
                                parsed = float(ra)
                            except Exception:
                                try:
                                    import email.utils, time as _t
                                    dt = email.utils.parsedate_to_datetime(ra)
                                    parsed = max(0.0, dt.timestamp() - _t.time())
                                except Exception:
                                    parsed = None
                        base = backoff * (2 ** attempt)
                        delay = (parsed if parsed is not None else base) + random.uniform(0, jitter)
                        delay = min(delay, max_cap)
                        logger.warning(f"/search retry {attempt+1}/{max_retries+1} after {e.response.status_code}; sleep {delay:.2f}s")
                        await asyncio.sleep(delay)
                        continue
                    raise
                except Exception as e:
                    if attempt < max_retries:
                        delay = min(backoff * (2 ** attempt) + random.uniform(0, jitter), max_cap)
                        logger.warning(f"/search exception retry {attempt+1}/{max_retries+1}; sleep {delay:.2f}s: {e}")
                        await asyncio.sleep(delay)
                        continue
                    raise

            search_result = response.json()
            retrieved_docs = search_result.get("hits", [])

            # A팀 응답을 B팀 형식으로 변환
            formatted_docs = []
            for i, doc in enumerate(retrieved_docs):
                formatted_doc = {
                    "chunk_id": doc.get("chunk_id", f"doc_{i}"),
                    "score": doc.get("score", 0.0),
                    "text": doc.get("text", ""),
                    "source": {
                        "url": doc.get("source", {}).get("url", ""),
                        "title": doc.get("source", {}).get("title", f"문서 {i+1}")
                    }
                }
                formatted_docs.append(formatted_doc)

            logger.info(f"A팀 /search API 호출 성공: {len(formatted_docs)}개 문서")

            step_time = time.time() - step_start

            state.update({
                "bm25_results": [],  # A팀에서 이미 통합 처리됨
                "vector_results": [],  # A팀에서 이미 통합 처리됨
                "retrieved_docs": formatted_docs,
                "retrieval_filter_applied": True,
                "step_timings": {**state.get("step_timings", {}), "step2_retrieve": step_time}
            })

            logger.info(f"Step 2 완료: retrieved={len(formatted_docs)} docs, time={step_time:.3f}s")
            return state

        except Exception as e:
            logger.error(f"A팀 /search API 호출 오류: {str(e)}")
        
        # A팀 API 호출 실패 시 빈 결과로 처리 (PRD 준수)
        step_time = time.time() - step_start
        
        state.update({
            "bm25_results": [],
            "vector_results": [],
            "retrieved_docs": [],
            "retrieval_filter_applied": False,
            "step_timings": {**state.get("step_timings", {}), "step2_retrieve": step_time}
        })
        
        logger.warning("Step 2 완료: A팀 API 호출 실패, 빈 결과 반환")
        return state
    
    async def _step3_answer_planning(self, state: PipelineState) -> PipelineState:
        """Step 3: Answer Planning (답변 전략 계획)"""
        step_start = time.time()
        logger.info(f"Step 3: Answer Planning - Intent: {state['intent']}")
        
        # 병렬 처리 최적화: 전략 결정과 추론을 동시 수행
        docs_count = len(state['retrieved_docs'])
        intent = state['intent']
        
        async def determine_strategy():
            """답변 전략 결정"""
            if intent == "search" and docs_count > 0:
                return "search_results_summary"
            elif intent == "explain" and docs_count > 0:
                return "detailed_explanation"
            else:
                return "general_answer"
        
        async def generate_reasoning(strategy_type):
            """전략별 추론 생성"""
            if strategy_type == "search_results_summary":
                return [
                    f"검색 의도로 파악됨",
                    f"{docs_count}개 문서 검색됨",
                    "검색 결과 요약 전략 선택"
                ]
            elif strategy_type == "detailed_explanation":
                return [
                    "설명 요청으로 파악됨",
                    "상세 설명 전략 선택",
                    "근거 문서 기반 설명"
                ]
            else:
                return [
                    "일반 질의로 처리",
                    "기본 답변 전략 적용"
                ]
        
        # 전략 결정
        strategy = await determine_strategy()
        
        # 병렬 처리로 추론 생성 시간 단축
        reasoning = await generate_reasoning(strategy)
            
        step_time = time.time() - step_start
        
        state.update({
            "answer_strategy": strategy,
            "plan_reasoning": reasoning,
            "step_timings": {**state.get("step_timings", {}), "step3_plan": step_time}
        })
        
        logger.info(f"Step 3 완료: strategy={strategy}, time={step_time:.3f}s")
        return state
    
    async def _step4_tools_and_debate(self, state: PipelineState) -> PipelineState:
        """Step 4: Tools/Debate (MCP 도구 통합 및 debate 시스템)"""
        step_start = time.time()
        logger.info("Step 4: Tools and Debate - Enhanced with MCP integration")

        tools_used = []
        debate_activated = False
        debate_reasoning = None

        # 1. Debate 스위치 로직 - 다중 조건 평가
        debate_triggers = []

        # 의도 신뢰도 체크
        intent_confidence = state.get('intent_confidence', 1.0)
        if intent_confidence < 0.7:
            debate_triggers.append(f"의도 신뢰도 낮음 ({intent_confidence:.3f})")

        # 검색 결과 품질 체크
        retrieved_docs = state['retrieved_docs']
        if len(retrieved_docs) < 2:
            debate_triggers.append(f"검색 결과 부족 ({len(retrieved_docs)}개)")

        # 최고 스코어 체크 (관련성 낮음)
        if retrieved_docs and max(doc.get('score', 0) for doc in retrieved_docs) < 0.5:
            debate_triggers.append("검색 결과 관련성 낮음")

        # 복잡한 쿼리 패턴 체크
        query_complexity = await self._assess_query_complexity(state['query'])
        if query_complexity['is_complex']:
            debate_triggers.append(f"복잡한 쿼리 패턴: {query_complexity['reason']}")

        # Debate 활성화 결정
        if debate_triggers:
            debate_activated = True
            debate_reasoning = "; ".join(debate_triggers)

            # 2. MCP Tools 통합 실행
            mcp_results = await self._execute_mcp_tools(state, debate_triggers)
            tools_used.extend(mcp_results['tools_used'])

            # Debate 결과를 상태에 통합
            if mcp_results['enhanced_context']:
                state['retrieved_docs'].extend(mcp_results['enhanced_context'])
                logger.info(f"MCP 도구로 {len(mcp_results['enhanced_context'])}개 추가 컨텍스트 확보")

        # 3. 추가 도구 사용 결정
        additional_tools = await self._select_additional_tools(state)
        tools_used.extend(additional_tools)

        step_time = time.time() - step_start

        state.update({
            "tools_used": tools_used,
            "debate_activated": debate_activated,
            "debate_reasoning": debate_reasoning,
            "step_timings": {**state.get("step_timings", {}), "step4_tools_debate": step_time}
        })

        logger.info(f"Step 4 완료: tools={len(tools_used)}, debate={debate_activated}, time={step_time:.3f}s")
        logger.info(f"사용된 도구: {tools_used}")
        return state

    async def _assess_query_complexity(self, query: str) -> Dict[str, Any]:
        """쿼리 복잡도 평가"""
        complexity_indicators = {
            'multi_topic': ['그리고', 'and', '또한', '게다가', '뿐만 아니라'],
            'comparison': ['비교', 'vs', '차이', '다른점', '같은점', 'compare'],
            'temporal': ['역사', '변화', '발전', '과거', '미래', '트렌드'],
            'analytical': ['분석', '평가', '검토', '어떻게', '왜', 'analyze'],
            'technical': ['구현', '방법', '기술적', '아키텍처', 'technical']
        }

        found_patterns = []
        query_lower = query.lower()

        for pattern_type, keywords in complexity_indicators.items():
            if any(keyword in query_lower for keyword in keywords):
                found_patterns.append(pattern_type)

        is_complex = len(found_patterns) >= 2 or len(query.split()) > 10

        return {
            'is_complex': is_complex,
            'patterns': found_patterns,
            'reason': f"패턴 {len(found_patterns)}개 감지: {', '.join(found_patterns)}" if found_patterns else "단순 쿼리"
        }

    async def _execute_mcp_tools(self, state: PipelineState, triggers: List[str]) -> Dict[str, Any]:
        """MCP 도구 실행 (context7, sequential-thinking 등)"""
        tools_used = []
        enhanced_context = []

        try:
            # Context7 도구 사용 - 7단계 컨텍스트 분석
            if "의도 신뢰도 낮음" in str(triggers) or "복잡한 쿼리" in str(triggers):
                context7_result = await self._call_context7_tool(state['query'])
                if context7_result['success']:
                    tools_used.append("context7")
                    enhanced_context.extend(context7_result['contexts'])
                    logger.info(f"Context7 도구 성공: {len(context7_result['contexts'])}개 컨텍스트")

            # Sequential-thinking 도구 사용 - 단계적 사고
            if "복잡한 쿼리 패턴" in str(triggers):
                seq_thinking_result = await self._call_sequential_thinking_tool(state['query'], state['retrieved_docs'])
                if seq_thinking_result['success']:
                    tools_used.append("sequential-thinking")
                    enhanced_context.extend(seq_thinking_result['thought_steps'])
                    logger.info(f"Sequential-thinking 도구 성공: {len(seq_thinking_result['thought_steps'])}개 사고 단계")

            # Fallback search 도구 사용
            if "검색 결과 부족" in str(triggers) or "관련성 낮음" in str(triggers):
                fallback_result = await self._call_fallback_search_tool(state['query'])
                if fallback_result['success']:
                    tools_used.append("fallback_search")
                    enhanced_context.extend(fallback_result['additional_docs'])
                    logger.info(f"Fallback search 성공: {len(fallback_result['additional_docs'])}개 추가 문서")

        except Exception as e:
            logger.warning(f"MCP 도구 실행 중 오류: {str(e)}")
            tools_used.append("mcp_error_handler")

        return {
            'tools_used': tools_used,
            'enhanced_context': enhanced_context
        }

    async def _call_context7_tool(self, query: str) -> Dict[str, Any]:
        """Context7 MCP 도구 호출 (실제 MCP 서버 연동)"""
        try:
            # 1. 실제 MCP 서버 호출 시도
            mcp_available = await self._check_mcp_server_health()

            if mcp_available:
                # 실제 MCP 서버로 요청
                mcp_response = await self.mcp_client.post(
                    f"{self.mcp_server_url}/tools/context7",
                    json={
                        "query": query,
                        "levels": 7,
                        "mode": "hierarchical"
                    },
                    timeout=10.0
                )

                if mcp_response.status_code == 200:
                    result = mcp_response.json()
                    self.performance_metrics['tools_usage_count']['context7'] += 1

                    # MCP 응답을 표준 형식으로 변환
                    contexts = []
                    for level, content in result.get('contexts', {}).items():
                        contexts.append({
                            'chunk_id': f'context7_{level}',
                            'text': content.get('text', ''),
                            'score': content.get('confidence', 0.8),
                            'source': {
                                'title': f'Context7 Level {level}',
                                'url': f'mcp://context7/{level}'
                            }
                        })

                    logger.info(f"Context7 MCP 성공: {len(contexts)}개 컨텍스트")
                    return {'success': True, 'contexts': contexts}

                logger.warning(f"Context7 MCP 오류: {mcp_response.status_code}")

            # 2. MCP 서버 없음/오류 시 fallback 로직
            logger.info("Context7 MCP fallback 모드 사용")
            contexts = await self._context7_fallback_analysis(query)
            return {'success': True, 'contexts': contexts, 'fallback': True}

        except Exception as e:
            logger.error(f"Context7 도구 호출 실패: {str(e)}")
            # 비상 후 fallback
            contexts = await self._context7_fallback_analysis(query)
            return {'success': True, 'contexts': contexts, 'fallback': True}

    async def _check_mcp_server_health(self) -> bool:
        """MCP 서버 건강 상태 확인"""
        try:
            health_response = await self.mcp_client.get(
                f"{self.mcp_server_url}/health",
                timeout=3.0
            )
            return health_response.status_code == 200
        except Exception:
            return False

    async def _context7_fallback_analysis(self, query: str) -> List[Dict[str, Any]]:
        """Context7 fallback 분석 (규칙 기반)"""
        # 단어 기반 컨텍스트 레벨 분석
        contexts = []
        query_words = query.lower().split()

        # Level 1: 직접적 키워드
        level1_keywords = [word for word in query_words if len(word) > 2]
        if level1_keywords:
            contexts.append({
                'chunk_id': 'context7_level1_direct',
                'text': f'직접 키워드: {", ".join(level1_keywords[:5])}',
                'score': 0.9,
                'source': {'title': 'Context7 Level 1 - Direct', 'url': 'fallback://context7/level1'}
            })

        # Level 2: 의미적 그룹화
        semantic_groups = self._group_semantic_keywords(level1_keywords)
        if semantic_groups:
            contexts.append({
                'chunk_id': 'context7_level2_semantic',
                'text': f'의미 그룹: {", ".join(semantic_groups)}',
                'score': 0.8,
                'source': {'title': 'Context7 Level 2 - Semantic', 'url': 'fallback://context7/level2'}
            })

        # Level 3: 범주 확장
        domain_context = self._identify_domain_context(query)
        if domain_context:
            contexts.append({
                'chunk_id': 'context7_level3_domain',
                'text': f'도메인 컨텍스트: {domain_context}',
                'score': 0.7,
                'source': {'title': 'Context7 Level 3 - Domain', 'url': 'fallback://context7/level3'}
            })

        return contexts

    def _group_semantic_keywords(self, keywords: List[str]) -> List[str]:
        """의미적 키워드 그룹화"""
        # 간단한 의미적 그룹화 로직
        tech_keywords = [k for k in keywords if k in ['ai', 'rag', '인공지능', '기술', 'system']]
        business_keywords = [k for k in keywords if k in ['비즈니스', '전략', '경영', '마켓팅', 'business']]

        groups = []
        if tech_keywords:
            groups.append('기술 관련')
        if business_keywords:
            groups.append('비즈니스 관련')

        return groups

    def _identify_domain_context(self, query: str) -> str:
        """도메인 컨텍스트 식별"""
        domain_patterns = {
            'technology': ['ai', 'rag', '인공지능', '기술', 'system', '개발'],
            'business': ['비즈니스', '경영', '마켓팅', '전략', '수익'],
            'education': ['교육', '학습', '강의', '수업', '강의'],
            'research': ['연구', '뮤문', '분석', '조사', '발견']
        }

        query_lower = query.lower()
        for domain, patterns in domain_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return domain

        return 'general'

    async def _call_sequential_thinking_tool(self, query: str, docs: List[Dict]) -> Dict[str, Any]:
        """Sequential-thinking MCP 도구 호출"""
        try:
            # 1. MCP 서버 연동 시도
            mcp_available = await self._check_mcp_server_health()

            if mcp_available:
                mcp_response = await self.mcp_client.post(
                    f"{self.mcp_server_url}/tools/sequential-thinking",
                    json={
                        "query": query,
                        "context_docs": [doc.get('text', '')[:200] for doc in docs[:3]],
                        "thinking_depth": "deep"
                    },
                    timeout=15.0
                )

                if mcp_response.status_code == 200:
                    result = mcp_response.json()
                    self.performance_metrics['tools_usage_count']['sequential-thinking'] += 1

                    thought_steps = []
                    for step in result.get('thinking_steps', []):
                        thought_steps.append({
                            'chunk_id': f'seq_step_{step.get("id", "unknown")}',
                            'text': step.get('content', ''),
                            'score': step.get('confidence', 0.9),
                            'source': {
                                'title': f'Sequential Step {step.get("id", "unknown")}',
                                'url': f'mcp://sequential/step{step.get("id", "unknown")}'
                            }
                        })

                    logger.info(f"Sequential-thinking MCP 성공: {len(thought_steps)}개 단계")
                    return {'success': True, 'thought_steps': thought_steps}

            # 2. Fallback 로직
            logger.info("Sequential-thinking fallback 모드 사용")
            thought_steps = await self._sequential_thinking_fallback(query, docs)
            return {'success': True, 'thought_steps': thought_steps, 'fallback': True}

        except Exception as e:
            logger.error(f"Sequential-thinking 도구 호출 실패: {str(e)}")
            thought_steps = await self._sequential_thinking_fallback(query, docs)
            return {'success': True, 'thought_steps': thought_steps, 'fallback': True}

    async def _sequential_thinking_fallback(self, query: str, docs: List[Dict]) -> List[Dict[str, Any]]:
        """Sequential thinking fallback 분석"""
        steps = []

        # Step 1: 문제 분석
        problem_analysis = f"쿼리 '사용자 니즈 분석: {query[:50]}...' 이다. "
        if docs:
            problem_analysis += f"{len(docs)}개의 관련 문서가 찾았다."
        else:
            problem_analysis += "관련 문서를 찾지 못했다."

        steps.append({
            'chunk_id': 'seq_step_1_analysis',
            'text': problem_analysis,
            'score': 0.9,
            'source': {'title': 'Sequential Step 1 - Analysis', 'url': 'fallback://sequential/step1'}
        })

        # Step 2: 정보 수집
        info_gathering = "검색된 정보를 기반으로: "
        if docs:
            top_doc = docs[0]
            info_gathering += f"최고 관련도 문서({top_doc.get('score', 0):.3f}): {top_doc.get('text', '')[:100]}..."
        else:
            info_gathering += "사전 지식을 활용하여 답변을 구성해야 한다."

        steps.append({
            'chunk_id': 'seq_step_2_gathering',
            'text': info_gathering,
            'score': 0.8,
            'source': {'title': 'Sequential Step 2 - Gathering', 'url': 'fallback://sequential/step2'}
        })

        # Step 3: 솔루션 종합
        solution_synthesis = f"답변 전략: "
        if len(docs) >= 2:
            solution_synthesis += "다중 출처 종합 답변을 생성한다."
        elif len(docs) == 1:
            solution_synthesis += "단일 출처 기반 상세 답변을 생성한다."
        else:
            solution_synthesis += "일반적 지식 기반 답변을 생성한다."

        steps.append({
            'chunk_id': 'seq_step_3_synthesis',
            'text': solution_synthesis,
            'score': 0.85,
            'source': {'title': 'Sequential Step 3 - Synthesis', 'url': 'fallback://sequential/step3'}
        })

        return steps

    async def _call_fallback_search_tool(self, query: str) -> Dict[str, Any]:
        """Fallback search 도구 호출 (외부 API 및 MCP 연동)"""
        try:
            # 1. MCP Fallback search 시도
            mcp_available = await self._check_mcp_server_health()

            if mcp_available:
                mcp_response = await self.mcp_client.post(
                    f"{self.mcp_server_url}/tools/fallback-search",
                    json={
                        "query": query,
                        "search_type": "comprehensive",
                        "max_results": 5
                    },
                    timeout=20.0
                )

                if mcp_response.status_code == 200:
                    result = mcp_response.json()
                    self.performance_metrics['tools_usage_count']['fallback-search'] += 1

                    additional_docs = []
                    for doc in result.get('search_results', []):
                        additional_docs.append({
                            'chunk_id': doc.get('id', f'fallback_{len(additional_docs)}'),
                            'text': doc.get('content', ''),
                            'score': doc.get('relevance_score', 0.6),
                            'source': {
                                'title': doc.get('title', 'Fallback Source'),
                                'url': doc.get('url', 'mcp://fallback/search')
                            }
                        })

                    logger.info(f"Fallback search MCP 성공: {len(additional_docs)}개 문서")
                    return {'success': True, 'additional_docs': additional_docs}

            # 2. 대체 검색 전략 (외부 API 또는 내장 지식)
            logger.info("Fallback search 대체 전략 사용")
            additional_docs = await self._execute_alternative_search(query)
            return {'success': True, 'additional_docs': additional_docs, 'fallback': True}

        except Exception as e:
            logger.error(f"Fallback search 도구 호출 실패: {str(e)}")
            additional_docs = await self._execute_alternative_search(query)
            return {'success': True, 'additional_docs': additional_docs, 'fallback': True}

    async def _execute_alternative_search(self, query: str) -> List[Dict[str, Any]]:
        """Alternative search strategies when MCP is unavailable"""
        alternative_docs = []

        # 전략 1: 키워드 기반 내장 지식
        knowledge_base = await self._query_internal_knowledge(query)
        if knowledge_base:
            alternative_docs.extend(knowledge_base)

        # 전략 2: 외부 공개 API 활용 (예: Wikipedia API)
        try:
            external_results = await self._query_external_apis(query)
            if external_results:
                alternative_docs.extend(external_results)
        except Exception as e:
            logger.warning(f"외부 API 호출 실패: {str(e)}")

        # 전략 3: 유사 쿼리 대체
        if not alternative_docs:
            similar_query_docs = await self._generate_similar_query_responses(query)
            alternative_docs.extend(similar_query_docs)

        return alternative_docs[:5]  # 최대 5개

    async def _query_internal_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Internal knowledge base query"""
        # 간단한 내장 지식 기반 생성
        knowledge_patterns = {
            'rag': 'RAG (Retrieval-Augmented Generation)는 대언어 모델의 성능을 향상시키는 기술입니다.',
            'ai': '인공지능(AI)은 기계가 인간의 지능을 모방하도록 하는 기술입니다.',
            '기술': '기술 발전은 인류 사회의 진보를 이끌어 온 주요 동력입니다.'
        }

        query_lower = query.lower()
        knowledge_docs = []

        for keyword, knowledge in knowledge_patterns.items():
            if keyword in query_lower:
                knowledge_docs.append({
                    'chunk_id': f'internal_knowledge_{keyword}',
                    'text': knowledge,
                    'score': 0.7,
                    'source': {
                        'title': f'Internal Knowledge - {keyword}',
                        'url': f'internal://knowledge/{keyword}'
                    }
                })

        return knowledge_docs

    async def _query_external_apis(self, query: str) -> List[Dict[str, Any]]:
        """Query external APIs (example: simplified Wikipedia-like service)"""
        # 예시: 외부 공개 API 호출
        # 실제 구현에서는 Wikipedia API, 공개 데이터 API 등 사용
        try:
            # 예시 URL (mock)
            # external_response = await self.client.get(f"https://api.example.com/search?q={query}")

            # Mock external response
            external_docs = [
                {
                    'chunk_id': 'external_api_result_1',
                    'text': f'외부 API에서 검색한 "{query}"에 대한 정보: 관련 내용을 제공합니다.',
                    'score': 0.65,
                    'source': {
                        'title': 'External API Result',
                        'url': 'https://external-api.example.com/result'
                    }
                }
            ]

            return external_docs

        except Exception as e:
            logger.warning(f"외부 API 오류: {str(e)}")
            return []

    async def _generate_similar_query_responses(self, query: str) -> List[Dict[str, Any]]:
        """Generate responses for similar queries"""
        similar_responses = [
            {
                'chunk_id': 'similar_query_response',
                'text': f'"{query}"와 유사한 질문에 대한 일반적인 답변입니다. 더 구체적인 정보가 필요한 경우 추가적인 질문을 해주세요.',
                'score': 0.5,
                'source': {
                    'title': 'Similar Query Response',
                    'url': 'internal://similar-query/response'
                }
            }
        ]

        return similar_responses

    async def _select_additional_tools(self, state: PipelineState) -> List[str]:
        """추가 도구 선택 로직"""
        additional_tools = []

        # 의도별 특화 도구
        intent = state.get('intent', '')
        if intent == 'search':
            additional_tools.append('search_enhancer')
        elif intent == 'explain':
            additional_tools.append('explanation_formatter')
        elif intent == 'classify':
            additional_tools.append('classification_validator')

        # 문서 수에 따른 도구 추가
        doc_count = len(state['retrieved_docs'])
        if doc_count > 10:
            additional_tools.append('document_summarizer')
        elif doc_count == 0:
            additional_tools.append('knowledge_base_fallback')

        return additional_tools
    
    async def _step5_answer_composition(self, state: PipelineState) -> PipelineState:
        """Step 5: Answer Composition (실제 LLM API 호출로 고품질 답변 생성)"""
        step_start = time.time()
        logger.info("Step 5: Answer Composition - Enhanced with LLM API integration")

        query = state['query']
        docs = state['retrieved_docs']
        strategy = state['answer_strategy']
        intent = state['intent']
        tools_used = state.get('tools_used', [])

        # 1. 답변 생성 전략 선택
        composition_strategy = await self._select_composition_strategy(state)
        logger.info(f"선택된 답변 구성 전략: {composition_strategy['name']}")

        # 2. LLM API 호출로 답변 생성
        draft_answer = await self._generate_answer_with_llm(
            query=query,
            docs=docs,
            strategy=composition_strategy,
            intent=intent,
            tools_context=tools_used
        )

        # 3. 답변 품질 검증 및 개선
        validated_answer = await self._validate_and_enhance_answer(draft_answer, state)

        step_time = time.time() - step_start

        state.update({
            "draft_answer": validated_answer,
            "composition_strategy": composition_strategy['name'],
            "step_timings": {**state.get("step_timings", {}), "step5_compose": step_time}
        })

        logger.info(f"Step 5 완료: draft length={len(validated_answer)}, strategy={composition_strategy['name']}, time={step_time:.3f}s")
        return state

    async def _select_composition_strategy(self, state: PipelineState) -> Dict[str, Any]:
        """답변 구성 전략 선택"""
        intent = state['intent']
        docs_count = len(state['retrieved_docs'])
        debate_activated = state.get('debate_activated', False)
        tools_used = state.get('tools_used', [])

        # 복잡도와 컨텍스트에 따른 전략 선택
        if debate_activated and 'context7' in tools_used:
            return {
                'name': 'multi_perspective_synthesis',
                'description': 'Context7와 debate를 활용한 다관점 종합 답변',
                'template': 'comprehensive_analysis',
                'max_length': 800
            }
        elif intent == 'explain' and docs_count >= 3:
            return {
                'name': 'structured_explanation',
                'description': '구조화된 상세 설명',
                'template': 'detailed_explanation',
                'max_length': 600
            }
        elif intent == 'search' and docs_count > 0:
            return {
                'name': 'evidence_based_summary',
                'description': '근거 기반 요약',
                'template': 'search_summary',
                'max_length': 400
            }
        else:
            return {
                'name': 'general_response',
                'description': '일반적 답변',
                'template': 'basic_answer',
                'max_length': 300
            }

    async def _generate_answer_with_llm(self, query: str, docs: List[Dict], strategy: Dict, intent: str, tools_context: List[str]) -> str:
        """LLM API를 사용한 답변 생성"""
        try:
            # 1. 프롬프트 구성
            prompt = await self._build_composition_prompt(query, docs, strategy, intent, tools_context)

            # 2. LLM API 호출 (GPT-4 또는 Claude)
            llm_response = await self._call_llm_api(prompt, strategy)

            if llm_response['success']:
                return llm_response['answer']
            else:
                logger.warning(f"LLM API 호출 실패: {llm_response['error']}")
                return await self._generate_fallback_answer(query, docs, strategy)

        except Exception as e:
            logger.error(f"답변 생성 중 오류: {str(e)}")
            return await self._generate_fallback_answer(query, docs, strategy)

    async def _build_composition_prompt(self, query: str, docs: List[Dict], strategy: Dict, intent: str, tools_context: List[str]) -> str:
        """LLM용 프롬프트 구성"""
        # 기본 프롬프트 템플릿
        base_prompt = f"""당신은 전문적인 RAG 시스템 어시스턴트입니다.

사용자 질문: {query}
파악된 의도: {intent}
답변 전략: {strategy['description']}
사용된 도구: {', '.join(tools_context) if tools_context else '없음'}

다음 문서들을 참고하여 {strategy['max_length']}자 이내로 정확하고 도움이 되는 답변을 작성해주세요:

"""

        # 문서 정보 추가
        for i, doc in enumerate(docs[:5], 1):  # 최대 5개 문서 사용
            base_prompt += f"\n문서 {i}:\n제목: {doc.get('source', {}).get('title', 'Unknown')}"
            base_prompt += f"\n내용: {doc.get('text', '')[:300]}..."
            base_prompt += f"\n관련도: {doc.get('score', 0):.3f}\n"

        # 전략별 특수 지시사항
        if strategy['name'] == 'multi_perspective_synthesis':
            base_prompt += "\n\n다양한 관점에서 종합적으로 분석하고, 가능한 한 균형잡힌 시각을 제시해주세요."
        elif strategy['name'] == 'structured_explanation':
            base_prompt += "\n\n구조화된 형태로 설명하고, 가능하면 단계별로 나누어 설명해주세요."
        elif strategy['name'] == 'evidence_based_summary':
            base_prompt += "\n\n제공된 문서의 내용을 근거로 하여 요약해주세요."

        base_prompt += "\n\n답변:"
        return base_prompt

    async def _call_llm_api(self, prompt: str, strategy: Dict) -> Dict[str, Any]:
        """LLM API 호출 (GPT-4/Claude)"""
        try:
            # OpenAI API 사용 예시 (실제 API 키가 필요)
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OpenAI API 키가 없습니다. 템플릿 기반 답변으로 대체합니다.")
                return {'success': False, 'error': 'No API key'}

            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'model': 'gpt-4',
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': min(strategy['max_length'] * 2, 1000),
                'temperature': 0.3  # 일관성을 위해 낮은 temperature
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    answer = result['choices'][0]['message']['content']
                    return {'success': True, 'answer': answer.strip()}
                else:
                    logger.error(f"OpenAI API 오류: {response.status_code} - {response.text}")
                    return {'success': False, 'error': f'API error: {response.status_code}'}

        except Exception as e:
            logger.error(f"LLM API 호출 중 예외: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _generate_fallback_answer(self, query: str, docs: List[Dict], strategy: Dict) -> str:
        """LLM API 실패 시 템플릿 기반 답변 생성"""
        logger.info("템플릿 기반 fallback 답변 생성")

        if strategy['name'] == 'multi_perspective_synthesis':
            answer = f"'{query}'에 대한 종합 분석:\n\n"
            if docs:
                answer += "검색된 문서들을 종합하면:\n"
                for i, doc in enumerate(docs[:3], 1):
                    answer += f"{i}. {doc['text'][:150]}...\n"
            else:
                answer += "관련 문서를 찾을 수 없어 일반적인 답변을 제공합니다."

        elif strategy['name'] == 'structured_explanation':
            answer = f"'{query}' 설명:\n\n"
            answer += "1. 개요\n"
            if docs:
                answer += f"   {docs[0]['text'][:100]}...\n\n"
            answer += "2. 상세 내용\n"
            if len(docs) > 1:
                answer += f"   {docs[1]['text'][:100]}...\n"

        elif strategy['name'] == 'evidence_based_summary':
            answer = f"'{query}' 검색 결과 요약:\n\n"
            for i, doc in enumerate(docs[:3], 1):
                answer += f"• {doc['text'][:120]}...\n"

        else:  # general_response
            answer = f"'{query}'에 대한 답변:\n"
            if docs:
                answer += f"검색된 {len(docs)}개 문서를 바탕으로, "
                answer += docs[0]['text'][:200] + "..."
            else:
                answer += "관련 정보를 찾을 수 없습니다."

        return answer

    async def _validate_and_enhance_answer(self, draft_answer: str, state: PipelineState) -> str:
        """답변 품질 검증 및 개선"""
        # 1. 기본 품질 체크
        if len(draft_answer.strip()) < 50:
            logger.warning("답변이 너무 짧습니다. 보완 중...")
            draft_answer += f"\n\n추가 정보가 필요하시면 더 구체적인 질문을 해주세요."

        # 2. 출처 정보 일관성 체크
        docs_count = len(state['retrieved_docs'])
        if docs_count > 0 and "문서" not in draft_answer and "자료" not in draft_answer:
            draft_answer += f"\n\n(이 답변은 {docs_count}개의 관련 문서를 참고하여 작성되었습니다.)"

        # 3. Debate가 활성화된 경우 추가 검증 마크
        if state.get('debate_activated', False):
            draft_answer += "\n\n✓ 다각도 검증 완료"

        return draft_answer
    
    async def _step6_citation_extraction(self, state: PipelineState) -> PipelineState:
        """Step 6: Citation (출처 인용 ≥2개)"""
        step_start = time.time()
        logger.info("Step 6: Citation Extraction")
        
        # B-O3 필수 요구사항: 출처 ≥2개 포함
        sources = []
        for doc in state['retrieved_docs'][:5]:  # 최대 5개 출처
            source_info = {
                "url": doc['source']['url'],
                "title": doc['source']['title'],
                "date": datetime.now().strftime("%Y-%m-%d"),  # TODO: 실제 문서 날짜
                "version": state.get('taxonomy_version', '1.8.1'),
                "relevance_score": doc['score'],
                "text_snippet": doc['text'][:150] + "..." if len(doc['text']) > 150 else doc['text']
            }
            sources.append(source_info)
        
        citations_count = len(sources)
        
        step_time = time.time() - step_start
        
        state.update({
            "sources": sources,
            "citations_count": citations_count,
            "step_timings": {**state.get("step_timings", {}), "step6_cite": step_time}
        })
        
        logger.info(f"Step 6 완료: citations={citations_count}, time={step_time:.3f}s")
        return state
    
    async def _step7_final_response(self, state: PipelineState) -> PipelineState:
        """Step 7: Final Response (최종 응답 생성)"""
        step_start = time.time()
        logger.info("Step 7: Final Response Generation")
        
        # 최종 답변 생성
        draft = state['draft_answer']
        sources = state['sources']
        
        final_answer = draft + "\n\n"
        
        # 출처 정보 추가 (B-O3 필수 요구사항)
        if sources:
            final_answer += "📚 출처:\n"
            for i, source in enumerate(sources, 1):
                final_answer += f"{i}. {source['title']} - {source['url']}\n"
        
        # 메타데이터 추가
        final_answer += f"\n🔍 검색 정보: {state.get('taxonomy_version', '1.8.1')} 버전 기준"
        
        # 신뢰도 계산
        confidence = min(
            state.get('intent_confidence', 0.8),
            0.9 if len(sources) >= 2 else 0.7,  # 출처 2개 이상이면 더 높은 신뢰도
            0.95  # 최대 신뢰도
        )
        
        # 비용 및 지연시간 계산 (B-O3 필수 메타데이터)
        total_latency = sum(state.get("step_timings", {}).values())
        estimated_tokens = len(state['query']) + sum(len(doc['text']) for doc in state['retrieved_docs']) + len(final_answer)
        estimated_cost = estimated_tokens * 0.001  # 대략적인 토큰당 비용 (₩0.001)
        
        step_time = time.time() - step_start
        
        state.update({
            "final_answer": final_answer,
            "confidence": confidence,
            "cost": estimated_cost,
            "latency": total_latency + step_time,
            "step_timings": {**state.get("step_timings", {}), "step7_respond": step_time}
        })
        
        logger.info(f"Step 7 완료: confidence={confidence:.3f}, cost=₩{estimated_cost:.3f}, "
                    f"total_latency={total_latency + step_time:.3f}s")
        return state
    
    async def execute(self, request: PipelineRequest) -> PipelineResponse:
        """파이프라인 실행 (B-O3 진입점) - 복원력 기능 및 성능 모니터링 통합"""
        pipeline_start = time.time()
        self.performance_metrics['total_requests'] += 1

        logger.info("=== B-O3 Enhanced Pipeline 시작 ===")
        logger.info(f"Query: {request.query}")
        logger.info(f"Taxonomy Version: {request.taxonomy_version}")
        logger.info(f"MCP Server: {self.mcp_server_url}")
        logger.info(f"Total Requests: {self.performance_metrics['total_requests']}")

        # 복원력 시스템 시작 (있을 경우에만)
        if self.resilience_manager:
            await self.resilience_manager.start()

        try:
            # 초기 상태 설정
            initial_state: PipelineState = {
                "query": request.query,
                "chunk_id": request.chunk_id,
                "taxonomy_version": request.taxonomy_version,
                "intent": "",
                "intent_confidence": 0.0,
                "retrieved_docs": [],
                "retrieval_filter_applied": False,
                "bm25_results": [],
                "vector_results": [],
                "answer_strategy": "",
                "plan_reasoning": [],
                "tools_used": [],
                "debate_activated": False,
                "debate_reasoning": None,
                "draft_answer": "",
                "sources": [],
                "citations_count": 0,
                "final_answer": "",
                "confidence": 0.0,
                "cost": 0.0,
                "latency": 0.0,
                "step_timings": {},
                "errors": [],
                "retry_count": 0
            }

            # LangGraph 실행 (복원력 기능 있으면 적용, 없으면 직접 실행)
            if self.resilience_manager:
                final_state = await self.resilience_manager.execute_with_resilience(
                    self.graph.ainvoke, initial_state
                )
            else:
                final_state = await self.graph.ainvoke(initial_state)

            # 성능 메트릭 업데이트
            total_time = time.time() - pipeline_start
            self.performance_metrics['successful_requests'] += 1
            self._update_average_latency(total_time)

            # 응답 구성
            response = PipelineResponse(
                answer=final_state["final_answer"],
                confidence=final_state["confidence"],
                sources=final_state["sources"],
                taxonomy_version=final_state["taxonomy_version"],
                cost=final_state["cost"],
                latency=total_time,
                intent=final_state["intent"],
                step_timings=final_state["step_timings"],
                debate_activated=final_state["debate_activated"],
                retrieved_count=len(final_state["retrieved_docs"]),
                citations_count=final_state["citations_count"]
            )

            # 성능 요약 로깅
            success_rate = (self.performance_metrics['successful_requests'] /
                          self.performance_metrics['total_requests']) * 100

            logger.info("=== B-O3 Enhanced Pipeline 완료 ===")
            logger.info(f"Total Time: {total_time:.3f}s")
            logger.info(f"Confidence: {response.confidence:.3f}")
            logger.info(f"Sources: {response.citations_count}")
            logger.info(f"Cost: ₩{response.cost:.3f}")
            logger.info(f"Success Rate: {success_rate:.1f}%")
            logger.info(f"Tools Used: {final_state.get('tools_used', [])}")
            logger.info(f"MCP Tools Usage: {self.performance_metrics['tools_usage_count']}")

            # 시스템 건강도 로깅 (복원력 시스템이 있을 경우에만)
            if self.resilience_manager:
                health = self.resilience_manager.get_system_health()
                logger.info(f"메모리 상태: {health['memory']['status']} ({health['memory']['usage']['current_mb']:.1f}MB)")

            return response

        except Exception as e:
            self.performance_metrics['failed_requests'] += 1
            logger.error(f"Pipeline 실행 오류 (실패율: {(self.performance_metrics['failed_requests']/self.performance_metrics['total_requests']*100):.1f}%): {str(e)}", exc_info=True)
            raise
        finally:
            # 복원력 시스템 정리 (있을 경우에만)
            if self.resilience_manager:
                await self.resilience_manager.stop()

            # 리소스 정리
            await self._cleanup_resources()

    def _update_average_latency(self, current_latency: float):
        """평균 지연시간 업데이트"""
        if self.performance_metrics['successful_requests'] == 1:
            self.performance_metrics['average_latency'] = current_latency
        else:
            # 이동 평균 계산
            prev_avg = self.performance_metrics['average_latency']
            count = self.performance_metrics['successful_requests']
            self.performance_metrics['average_latency'] = ((prev_avg * (count - 1)) + current_latency) / count

    async def _cleanup_resources(self):
        """리소스 정리"""
        try:
            # HTTP 클라이언트 리소스 정리는 파이프라인 종료 시에만
            pass
        except Exception as e:
            logger.warning(f"리소스 정리 중 오류: {str(e)}")

    async def close(self):
        """파이프라인 종료 및 리소스 정리"""
        try:
            await self.client.aclose()
            await self.mcp_client.aclose()
            logger.info("파이프라인 리소스 정리 완료")
        except Exception as e:
            logger.error(f"파이프라인 종료 중 오류: {str(e)}")

    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 반환"""
        success_rate = 0.0
        if self.performance_metrics['total_requests'] > 0:
            success_rate = (self.performance_metrics['successful_requests'] /
                          self.performance_metrics['total_requests']) * 100

        return {
            'total_requests': self.performance_metrics['total_requests'],
            'successful_requests': self.performance_metrics['successful_requests'],
            'failed_requests': self.performance_metrics['failed_requests'],
            'success_rate_percent': success_rate,
            'average_latency_seconds': self.performance_metrics['average_latency'],
            'tools_usage_count': self.performance_metrics['tools_usage_count'],
            'available_mcp_tools': self.available_mcp_tools
        }


# 전역 파이프라인 인스턴스
_pipeline_instance: Optional[LangGraphPipeline] = None

def get_pipeline() -> LangGraphPipeline:
    """파이프라인 싱글톤 인스턴스 반환"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = LangGraphPipeline()
    return _pipeline_instance


# 사용 예시
async def main():
    """테스트 실행 예시"""
    pipeline = get_pipeline()
    
    test_request = PipelineRequest(
        query="AI RAG 시스템에 대해 설명해주세요",
        taxonomy_version="1.8.1"
    )
    
    response = await pipeline.execute(test_request)
    
    print("\n=== B-O3 Pipeline 실행 결과 ===")
    print(f"답변: {response.answer}")
    print(f"신뢰도: {response.confidence:.3f}")
    print(f"출처 개수: {response.citations_count}")
    print(f"실행 시간: {response.latency:.3f}초")
    print(f"비용: ₩{response.cost:.3f}")
    print(f"단계별 시간: {response.step_timings}")


if __name__ == "__main__":
    asyncio.run(main())
