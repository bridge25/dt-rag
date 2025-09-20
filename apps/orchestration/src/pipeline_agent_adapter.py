"""
Pipeline-Agent Factory 통합 어댑터
기존 LangGraph Pipeline과 Agent Factory를 연결하여
Agent 설정이 파이프라인 동작을 실제로 제어하도록 함
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Pipeline 관련 import
from .langgraph_pipeline import (
    LangGraphPipeline, PipelineRequest, PipelineResponse, PipelineState
)

# Agent Factory 관련 import
try:
    from apps.api.agent_factory import (
        get_agent_factory, AgentProfile, CanonicalPathValidator
    )
    AGENT_FACTORY_AVAILABLE = True
except ImportError:
    AGENT_FACTORY_AVAILABLE = False
    logging.warning("Agent Factory not available")

# Intent Classification import
try:
    from .intent_classifier import get_intent_classifier, IntentRouter
    INTENT_CLASSIFIER_AVAILABLE = True
except ImportError:
    INTENT_CLASSIFIER_AVAILABLE = False
    logging.warning("Intent Classifier not available")

logger = logging.getLogger(__name__)


class AgentEnhancedPipelineRequest(PipelineRequest):
    """Agent 설정이 포함된 Pipeline 요청"""
    agent_id: Optional[str] = None
    agent_categories: Optional[List[str]] = None
    canonical_paths: Optional[List[List[str]]] = None
    agent_options: Optional[Dict[str, Any]] = None


class AgentEnhancedPipelineResponse(PipelineResponse):
    """Agent 정보가 포함된 Pipeline 응답"""
    agent_id: Optional[str] = None
    agent_category: Optional[str] = None
    canonical_paths_used: Optional[List[List[str]]] = None
    retrieval_config_applied: Optional[Dict[str, Any]] = None
    tools_available: Optional[List[str]] = None


class PipelineAgentAdapter:
    """Pipeline과 Agent Factory 연결 어댑터"""

    def __init__(self, pipeline: Optional[LangGraphPipeline] = None):
        self.pipeline = pipeline or LangGraphPipeline()
        self.agent_factory = None
        self.intent_classifier = None

        # 성능 메트릭
        self.adapter_metrics = {
            "total_requests": 0,
            "agent_enhanced_requests": 0,
            "canonical_path_filtered": 0,
            "average_retrieval_speedup": 0.0
        }

    async def initialize(self):
        """어댑터 초기화"""
        # Agent Factory 초기화
        if AGENT_FACTORY_AVAILABLE:
            self.agent_factory = get_agent_factory()
            logger.info("Agent Factory 연결 완료")

        # Intent Classifier 초기화
        if INTENT_CLASSIFIER_AVAILABLE:
            self.intent_classifier = await get_intent_classifier()
            logger.info("Intent Classifier 연결 완료")

        logger.info("Pipeline-Agent 어댑터 초기화 완료")

    async def execute_with_agent(
        self,
        request: AgentEnhancedPipelineRequest
    ) -> AgentEnhancedPipelineResponse:
        """Agent 설정을 적용한 Pipeline 실행"""
        start_time = time.time()
        self.adapter_metrics["total_requests"] += 1

        # 1. Agent 설정 로드 또는 생성
        agent_profile = await self._get_or_create_agent(request)

        # 2. Pipeline State 초기화 (Agent 설정 적용)
        initial_state = await self._create_enhanced_state(request, agent_profile)

        # 3. Enhanced Pipeline 실행
        enhanced_pipeline = EnhancedLangGraphPipeline(
            pipeline=self.pipeline,
            agent_profile=agent_profile
        )

        final_state = await enhanced_pipeline.execute_with_agent(initial_state)

        # 4. Agent 정보가 포함된 응답 생성
        response = await self._create_enhanced_response(
            final_state, agent_profile, start_time
        )

        # 5. 메트릭 업데이트
        if agent_profile:
            self.adapter_metrics["agent_enhanced_requests"] += 1

        return response

    async def _get_or_create_agent(
        self,
        request: AgentEnhancedPipelineRequest
    ) -> Optional[AgentProfile]:
        """Agent 설정 로드 또는 생성"""
        if not self.agent_factory:
            return None

        # 기존 Agent 사용
        if request.agent_id:
            agent = await self.agent_factory.get_agent(request.agent_id)
            if agent:
                logger.debug(f"기존 Agent 사용: {agent.name}")
                return agent

        # 새 Agent 생성 (카테고리와 canonical path 제공된 경우)
        if request.agent_categories and request.canonical_paths:
            try:
                agent = await self.agent_factory.create_agent_from_category(
                    categories=request.agent_categories,
                    canonical_paths=request.canonical_paths,
                    taxonomy_version=request.taxonomy_version,
                    options=request.agent_options or {}
                )
                logger.info(f"새 Agent 생성: {agent.name}")
                return agent
            except Exception as e:
                logger.error(f"Agent 생성 실패: {str(e)}")

        return None

    async def _create_enhanced_state(
        self,
        request: AgentEnhancedPipelineRequest,
        agent_profile: Optional[AgentProfile]
    ) -> PipelineState:
        """Agent 설정이 적용된 Pipeline State 생성"""
        # 기본 State 생성
        state: PipelineState = {
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

        # Agent 설정 적용
        if agent_profile:
            state["agent_profile"] = agent_profile  # type: ignore
            state["canonical_paths"] = agent_profile.canonical_paths  # type: ignore

        return state

    async def _create_enhanced_response(
        self,
        final_state: PipelineState,
        agent_profile: Optional[AgentProfile],
        start_time: float
    ) -> AgentEnhancedPipelineResponse:
        """Agent 정보가 포함된 응답 생성"""
        total_latency = time.time() - start_time

        response_data = {
            "answer": final_state["final_answer"],
            "confidence": final_state["confidence"],
            "sources": final_state["sources"],
            "taxonomy_version": final_state["taxonomy_version"],
            "cost": final_state["cost"],
            "latency": total_latency,
            "intent": final_state["intent"],
            "step_timings": final_state["step_timings"],
            "debate_activated": final_state["debate_activated"],
            "retrieved_count": len(final_state["retrieved_docs"]),
            "citations_count": final_state["citations_count"]
        }

        # Agent 정보 추가
        if agent_profile:
            response_data.update({
                "agent_id": agent_profile.id,
                "agent_category": agent_profile.category,
                "canonical_paths_used": agent_profile.canonical_paths,
                "retrieval_config_applied": agent_profile.retrieval_config,
                "tools_available": list(agent_profile.tools_config.get("allowed_tools", {}).get("primary", []))
            })

        return AgentEnhancedPipelineResponse(**response_data)

    def get_adapter_metrics(self) -> Dict[str, Any]:
        """어댑터 성능 메트릭 반환"""
        total = self.adapter_metrics["total_requests"]
        enhancement_rate = (self.adapter_metrics["agent_enhanced_requests"] / total * 100) if total > 0 else 0

        return {
            "total_requests": total,
            "agent_enhanced_requests": self.adapter_metrics["agent_enhanced_requests"],
            "enhancement_rate_percent": enhancement_rate,
            "canonical_path_filtered": self.adapter_metrics["canonical_path_filtered"],
            "average_retrieval_speedup": self.adapter_metrics["average_retrieval_speedup"]
        }


class EnhancedLangGraphPipeline:
    """Agent 설정이 적용된 향상된 Pipeline"""

    def __init__(self, pipeline: LangGraphPipeline, agent_profile: Optional[AgentProfile]):
        self.pipeline = pipeline
        self.agent_profile = agent_profile

    async def execute_with_agent(self, state: PipelineState) -> PipelineState:
        """Agent 설정을 적용하여 Pipeline 실행"""
        # 1. Agent 기반 Intent Classification
        state = await self._enhanced_intent_classification(state)

        # 2. Agent 기반 Retrieval
        state = await self._enhanced_retrieval(state)

        # 3. Agent 기반 Planning
        state = await self._enhanced_planning(state)

        # 4. Agent 기반 Tools/Debate
        state = await self._enhanced_tools_debate(state)

        # 5. Agent 기반 Composition
        state = await self._enhanced_composition(state)

        # 6. 기본 Citation 처리
        state = await self.pipeline._step6_citation_extraction(state)

        # 7. 기본 Response 처리
        state = await self.pipeline._step7_final_response(state)

        return state

    async def _enhanced_intent_classification(self, state: PipelineState) -> PipelineState:
        """Agent 설정을 고려한 향상된 Intent Classification"""
        step_start = time.time()

        # Intent Classifier 사용 (있는 경우)
        if INTENT_CLASSIFIER_AVAILABLE:
            try:
                from .intent_classifier import classify_intent
                intent_result = await classify_intent(state["query"])

                state["intent"] = intent_result.intent
                state["intent_confidence"] = intent_result.confidence

                logger.info(f"Enhanced Intent: {intent_result.intent} (confidence: {intent_result.confidence:.3f})")

                # Agent 카테고리와 의도의 일치성 확인
                if self.agent_profile:
                    category_intent_match = self._check_category_intent_match(
                        self.agent_profile.category, intent_result.intent
                    )
                    if not category_intent_match:
                        logger.warning(f"의도와 Agent 카테고리 불일치: {intent_result.intent} vs {self.agent_profile.category}")

            except Exception as e:
                logger.error(f"Enhanced Intent Classification 실패: {str(e)}")
                # Fallback to original
                state = await self.pipeline._step1_intent_classification(state)
        else:
            # 기본 Intent Classification 사용
            state = await self.pipeline._step1_intent_classification(state)

        step_time = time.time() - step_start
        state["step_timings"]["enhanced_step1_intent"] = step_time

        return state

    async def _enhanced_retrieval(self, state: PipelineState) -> PipelineState:
        """Agent 설정을 적용한 향상된 Retrieval"""
        step_start = time.time()

        if not self.agent_profile:
            # Agent 없으면 기본 Retrieval
            return await self.pipeline._step2_hybrid_retrieval(state)

        # Agent의 retrieval 설정 적용
        retrieval_config = self.agent_profile.retrieval_config
        canonical_paths = self.agent_profile.canonical_paths

        try:
            # A팀 /search API 호출 시 Agent 설정 적용
            search_request = {
                "q": state['query'],
                "filters": {
                    "canonical_in": canonical_paths  # PRD: canonical path 필터링
                },
                "bm25_topk": retrieval_config.get("bm25_topk", 12),
                "vector_topk": retrieval_config.get("vector_topk", 12),
                "rerank_candidates": retrieval_config.get("rerank_candidates", 50),
                "final_topk": retrieval_config.get("final_topk", 5),
                "weights": {
                    "bm25": retrieval_config.get("bm25_weight", 0.5),
                    "vector": retrieval_config.get("vector_weight", 0.5)
                }
            }

            logger.info(f"Agent 설정 적용된 검색: canonical_paths={canonical_paths}")
            logger.debug(f"검색 설정: {search_request}")

            # A팀 API 호출 (기존 로직 재사용하되 설정 적용)
            response = await self.pipeline.client.post(
                f"{self.pipeline.a_team_base_url}/search",
                json=search_request
            )
            response.raise_for_status()

            search_result = response.json()
            retrieved_docs = search_result.get("hits", [])

            # 결과 포맷팅
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

            step_time = time.time() - step_start

            state.update({
                "bm25_results": [],  # A팀에서 이미 통합 처리됨
                "vector_results": [],  # A팀에서 이미 통합 처리됨
                "retrieved_docs": formatted_docs,
                "retrieval_filter_applied": True,
                "step_timings": {**state.get("step_timings", {}), "enhanced_step2_retrieve": step_time}
            })

            logger.info(f"Enhanced Retrieval 완료: {len(formatted_docs)}개 문서, canonical 필터 적용")

        except Exception as e:
            logger.error(f"Enhanced Retrieval 실패: {str(e)}")
            # Fallback to original
            state = await self.pipeline._step2_hybrid_retrieval(state)

        return state

    async def _enhanced_planning(self, state: PipelineState) -> PipelineState:
        """Agent 설정을 고려한 향상된 Planning"""
        step_start = time.time()

        # Agent 카테고리별 특화 계획
        if self.agent_profile:
            category = self.agent_profile.category
            intent = state["intent"]

            strategy = self._determine_agent_strategy(category, intent, state)
            reasoning = self._generate_agent_reasoning(category, intent, state)

            state.update({
                "answer_strategy": strategy,
                "plan_reasoning": reasoning,
                "step_timings": {**state.get("step_timings", {}), "enhanced_step3_plan": time.time() - step_start}
            })

            logger.info(f"Enhanced Planning ({category}): {strategy}")
        else:
            # 기본 Planning
            state = await self.pipeline._step3_answer_planning(state)

        return state

    async def _enhanced_tools_debate(self, state: PipelineState) -> PipelineState:
        """Agent 설정을 적용한 향상된 Tools/Debate"""
        step_start = time.time()

        if not self.agent_profile:
            return await self.pipeline._step4_tools_and_debate(state)

        tools_used = []
        debate_activated = False
        debate_reasoning = None

        # Agent 설정에 따른 debate 활성화
        if self.agent_profile.debate_enabled:
            # 기본 debate 조건 + Agent 특화 조건
            debate_triggers = []

            intent_confidence = state.get('intent_confidence', 1.0)
            if intent_confidence < 0.7:
                debate_triggers.append(f"의도 신뢰도 낮음 ({intent_confidence:.3f})")

            retrieved_docs = state['retrieved_docs']
            if len(retrieved_docs) < 2:
                debate_triggers.append(f"검색 결과 부족 ({len(retrieved_docs)}개)")

            # Agent 카테고리별 특화 조건
            category = self.agent_profile.category
            if category == "technology_ai" and intent_confidence < 0.8:
                debate_triggers.append("기술 분야 정확성 요구")
            elif category == "research" and len(retrieved_docs) < 3:
                debate_triggers.append("연구 분야 충분한 근거 요구")

            if debate_triggers:
                debate_activated = True
                debate_reasoning = "; ".join(debate_triggers)

        # Agent 허용 도구 사용
        allowed_tools = self.agent_profile.tools_config.get("allowed_tools", {})
        tools_used.extend(allowed_tools.get("primary", []))

        step_time = time.time() - step_start

        state.update({
            "tools_used": tools_used,
            "debate_activated": debate_activated,
            "debate_reasoning": debate_reasoning,
            "step_timings": {**state.get("step_timings", {}), "enhanced_step4_tools_debate": step_time}
        })

        logger.info(f"Enhanced Tools/Debate: tools={len(tools_used)}, debate={debate_activated}")
        return state

    async def _enhanced_composition(self, state: PipelineState) -> PipelineState:
        """Agent 설정을 적용한 향상된 Composition"""
        if not self.agent_profile:
            return await self.pipeline._step5_answer_composition(state)

        step_start = time.time()

        # Agent 프롬프트 설정 적용
        prompt_config = self.agent_profile.prompt_config
        category = self.agent_profile.category

        # 카테고리별 특화 답변 생성
        draft_answer = await self._generate_agent_specific_answer(state, category, prompt_config)

        step_time = time.time() - step_start

        state.update({
            "draft_answer": draft_answer,
            "step_timings": {**state.get("step_timings", {}), "enhanced_step5_compose": step_time}
        })

        logger.info(f"Enhanced Composition ({category}): {len(draft_answer)} characters")
        return state

    def _check_category_intent_match(self, category: str, intent: str) -> bool:
        """Agent 카테고리와 의도의 일치성 확인"""
        category_intent_map = {
            "technology_ai": ["search", "explain", "analyze", "troubleshoot"],
            "business": ["search", "analyze", "generate", "compare"],
            "education": ["explain", "search", "generate"],
            "research": ["analyze", "compare", "search", "explain"],
            "customer_support": ["search", "troubleshoot", "explain"],
            "general": ["search", "explain", "analyze", "generate", "compare", "troubleshoot"]
        }

        compatible_intents = category_intent_map.get(category, [])
        return intent in compatible_intents

    def _determine_agent_strategy(self, category: str, intent: str, state: PipelineState) -> str:
        """Agent 카테고리별 답변 전략 결정"""
        docs_count = len(state['retrieved_docs'])

        if category == "technology_ai":
            if intent == "explain":
                return "technical_detailed_explanation"
            elif intent == "analyze":
                return "technical_analysis_with_evidence"
            else:
                return "technical_accurate_response"

        elif category == "business":
            if intent == "analyze":
                return "business_strategic_analysis"
            elif intent == "generate":
                return "business_actionable_proposal"
            else:
                return "business_practical_response"

        elif category == "education":
            return "educational_step_by_step"

        elif category == "research":
            return "research_comprehensive_analysis"

        else:
            return "general_balanced_response"

    def _generate_agent_reasoning(self, category: str, intent: str, state: PipelineState) -> List[str]:
        """Agent 카테고리별 계획 추론 생성"""
        base_reasoning = [
            f"Agent 카테고리: {category}",
            f"파악된 의도: {intent}",
            f"검색된 문서: {len(state['retrieved_docs'])}개"
        ]

        if category == "technology_ai":
            base_reasoning.append("기술적 정확성과 근거 중심 답변 계획")
        elif category == "business":
            base_reasoning.append("실용적이고 실행 가능한 비즈니스 답변 계획")
        elif category == "education":
            base_reasoning.append("이해하기 쉬운 단계별 설명 계획")

        return base_reasoning

    async def _generate_agent_specific_answer(
        self,
        state: PipelineState,
        category: str,
        prompt_config: Dict[str, Any]
    ) -> str:
        """Agent 특화 답변 생성"""
        query = state['query']
        docs = state['retrieved_docs']

        # 카테고리별 템플릿 적용
        if category == "technology_ai":
            answer = self._generate_technical_answer(query, docs)
        elif category == "business":
            answer = self._generate_business_answer(query, docs)
        elif category == "education":
            answer = self._generate_educational_answer(query, docs)
        else:
            answer = self._generate_general_answer(query, docs)

        return answer

    def _generate_technical_answer(self, query: str, docs: List[Dict]) -> str:
        """기술 전문 답변 생성"""
        answer = f"'{query}'에 대한 기술적 분석:\n\n"

        if docs:
            answer += "📋 기술적 근거:\n"
            for i, doc in enumerate(docs[:3], 1):
                answer += f"{i}. {doc['text'][:200]}...\n"
                answer += f"   (신뢰도: {doc.get('score', 0):.3f})\n\n"

            answer += "🔬 기술적 결론:\n"
            answer += "제공된 문서들의 기술적 내용을 종합하면, 이는 검증된 기술적 접근방법으로 평가됩니다."
        else:
            answer += "기술 문서를 찾을 수 없어 일반적인 기술 지식을 바탕으로 답변드립니다."

        return answer

    def _generate_business_answer(self, query: str, docs: List[Dict]) -> str:
        """비즈니스 전문 답변 생성"""
        answer = f"'{query}'에 대한 비즈니스 분석:\n\n"

        if docs:
            answer += "💼 비즈니스 관점:\n"
            for i, doc in enumerate(docs[:3], 1):
                answer += f"• {doc['text'][:150]}...\n"

            answer += "\n🎯 실행 방안:\n"
            answer += "분석된 정보를 바탕으로 다음과 같은 실행 가능한 방안을 제안드립니다."
        else:
            answer += "관련 비즈니스 자료를 찾을 수 없어 일반적인 비즈니스 관점에서 답변드립니다."

        return answer

    def _generate_educational_answer(self, query: str, docs: List[Dict]) -> str:
        """교육 전문 답변 생성"""
        answer = f"'{query}' 단계별 설명:\n\n"

        answer += "📚 1단계: 기본 개념\n"
        if docs:
            answer += f"   {docs[0]['text'][:100]}...\n\n"

        answer += "📚 2단계: 상세 내용\n"
        if len(docs) > 1:
            answer += f"   {docs[1]['text'][:100]}...\n\n"

        answer += "📚 3단계: 실제 적용\n"
        answer += "   학습한 내용을 실제로 적용해보세요.\n"

        return answer

    def _generate_general_answer(self, query: str, docs: List[Dict]) -> str:
        """일반 답변 생성"""
        answer = f"'{query}'에 대한 답변:\n\n"

        if docs:
            for i, doc in enumerate(docs[:3], 1):
                answer += f"{i}. {doc['text'][:120]}...\n"
        else:
            answer += "관련 정보를 찾을 수 없습니다."

        return answer


# 전역 인스턴스
_adapter_instance: Optional[PipelineAgentAdapter] = None

async def get_pipeline_agent_adapter() -> PipelineAgentAdapter:
    """Pipeline-Agent 어댑터 싱글톤 인스턴스 반환"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = PipelineAgentAdapter()
        await _adapter_instance.initialize()
    return _adapter_instance


# 편의 함수
async def execute_with_agent_categories(
    query: str,
    agent_categories: List[str],
    canonical_paths: List[List[str]],
    taxonomy_version: str = "1.8.1",
    **kwargs
) -> AgentEnhancedPipelineResponse:
    """Agent 카테고리로 Pipeline 실행"""
    adapter = await get_pipeline_agent_adapter()

    request = AgentEnhancedPipelineRequest(
        query=query,
        taxonomy_version=taxonomy_version,
        agent_categories=agent_categories,
        canonical_paths=canonical_paths,
        agent_options=kwargs
    )

    return await adapter.execute_with_agent(request)


# 사용 예시
if __name__ == "__main__":
    async def main():
        # Pipeline-Agent 어댑터 테스트
        adapter = await get_pipeline_agent_adapter()

        # Technology AI Agent로 실행
        response = await execute_with_agent_categories(
            query="RAG 시스템의 기술적 아키텍처를 설명해주세요",
            agent_categories=["Technology", "AI"],
            canonical_paths=[["AI", "RAG"], ["Technology", "Architecture"]],
            accuracy_priority=True
        )

        print(f"Agent 카테고리: {response.agent_category}")
        print(f"검색 범위: {response.canonical_paths_used}")
        print(f"답변: {response.answer}")
        print(f"출처: {len(response.sources)}개")

        # 어댑터 메트릭 확인
        metrics = adapter.get_adapter_metrics()
        print(f"어댑터 성능: {metrics}")

    asyncio.run(main())