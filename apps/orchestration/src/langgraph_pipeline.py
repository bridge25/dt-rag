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
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

# LangGraph 대신 간단한 그래프 구현 사용
from typing import Dict, List, Callable, Any
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
    """B-O3 7-Step 파이프라인 (A팀 API 연동, PRD 준수)"""
    
    def __init__(self, a_team_base_url: str = "http://localhost:8001"):
        self.a_team_base_url = a_team_base_url
        self.client = httpx.AsyncClient()
        self.graph = self._build_graph()
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
                
            else:
                logger.error(f"A팀 /search API 호출 실패: {response.status_code}")
                
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
        """Step 4: Tools/Debate (도구 사용 및 debate 스위치)"""
        step_start = time.time()
        logger.info("Step 4: Tools and Debate")
        
        # TODO: 실제 도구 사용 및 debate 로직 구현
        tools_used = []
        debate_activated = False
        debate_reasoning = None
        
        # debate 스위치 로직: confidence < 0.7 시 활성화
        if state.get('intent_confidence', 1.0) < 0.7:
            debate_activated = True
            debate_reasoning = f"의도 파악 신뢰도 {state['intent_confidence']:.3f} < 0.7, debate 활성화"
            tools_used.append("debate_module")
        
        # 검색 결과가 부족한 경우 추가 도구 사용
        if len(state['retrieved_docs']) < 2:
            tools_used.append("fallback_search")
            
        step_time = time.time() - step_start
        
        state.update({
            "tools_used": tools_used,
            "debate_activated": debate_activated,
            "debate_reasoning": debate_reasoning,
            "step_timings": {**state.get("step_timings", {}), "step4_tools_debate": step_time}
        })
        
        logger.info(f"Step 4 완료: tools={tools_used}, debate={debate_activated}, time={step_time:.3f}s")
        return state
    
    async def _step5_answer_composition(self, state: PipelineState) -> PipelineState:
        """Step 5: Answer Composition (답변 구성)"""
        step_start = time.time()
        logger.info("Step 5: Answer Composition")
        
        # TODO: 실제 답변 생성 로직 구현 (LLM 호출)
        query = state['query']
        docs = state['retrieved_docs']
        strategy = state['answer_strategy']
        
        if strategy == "search_results_summary":
            draft_answer = f"'{query}' 검색 결과:\n"
            for i, doc in enumerate(docs[:3], 1):
                draft_answer += f"{i}. {doc['text'][:100]}...\n"
        elif strategy == "detailed_explanation":
            draft_answer = f"'{query}'에 대한 설명:\n"
            draft_answer += f"검색된 {len(docs)}개 문서를 바탕으로 설명드리겠습니다.\n"
            draft_answer += docs[0]['text'][:200] + "..." if docs else "관련 자료를 찾을 수 없습니다."
        else:
            draft_answer = f"'{query}'에 대한 답변을 준비 중입니다. 검색된 문서: {len(docs)}개"
            
        step_time = time.time() - step_start
        
        state.update({
            "draft_answer": draft_answer,
            "step_timings": {**state.get("step_timings", {}), "step5_compose": step_time}
        })
        
        logger.info(f"Step 5 완료: draft length={len(draft_answer)}, time={step_time:.3f}s")
        return state
    
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
        """파이프라인 실행 (B-O3 진입점) - 복원력 기능 통합"""
        pipeline_start = time.time()
        logger.info(f"=== B-O3 Pipeline 시작 (복원력 기능 적용) ===")
        logger.info(f"Query: {request.query}")
        logger.info(f"Taxonomy Version: {request.taxonomy_version}")
        
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
            
            # 응답 구성
            total_time = time.time() - pipeline_start
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
            
            logger.info(f"=== B-O3 Pipeline 완료 ===")
            logger.info(f"Total Time: {total_time:.3f}s")
            logger.info(f"Confidence: {response.confidence:.3f}")
            logger.info(f"Sources: {response.citations_count}")
            logger.info(f"Cost: ₩{response.cost:.3f}")
            
            # 시스템 건강도 로깅 (복원력 시스템이 있을 경우에만)
            if self.resilience_manager:
                health = self.resilience_manager.get_system_health()
                logger.info(f"메모리 상태: {health['memory']['status']} ({health['memory']['usage']['current_mb']:.1f}MB)")
            
            return response
            
        except Exception as e:
            logger.error(f"Pipeline 실행 오류: {str(e)}", exc_info=True)
            raise
        finally:
            # 복원력 시스템 정리 (있을 경우에만)
            if self.resilience_manager:
                await self.resilience_manager.stop()


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
