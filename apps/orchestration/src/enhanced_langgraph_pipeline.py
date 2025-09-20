"""
Enhanced LangGraph Pipeline - Agent Factory 통합 버전
"""

import asyncio
import time
import logging
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

from apps.agent_system.src.pipeline_adapter import get_pipeline_adapter, enhance_pipeline_with_agent

logger = logging.getLogger(__name__)


class EnhancedPipelineState(TypedDict):
    """향상된 Pipeline State (Agent 정보 포함)"""
    query: str
    chunk_id: Optional[str]
    taxonomy_version: str
    
    # Agent 정보
    agent_id: Optional[str]
    agent_category: Optional[str]
    agent_config: Optional[Dict[str, Any]]
    
    # Pipeline 단계별 결과
    intent: str
    retrieved_docs: List[Dict[str, Any]]
    final_response: str


class EnhancedLangGraphPipeline:
    """Agent Factory가 통합된 향상된 Pipeline"""
    
    def __init__(self):
        self.pipeline_adapter = get_pipeline_adapter()
        
    async def execute_pipeline(self, 
                             query: str,
                             chunk_id: Optional[str] = None,
                             user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """향상된 파이프라인 실행"""
        
        # 초기 상태
        initial_state = EnhancedPipelineState(
            query=query,
            chunk_id=chunk_id,
            taxonomy_version="v1.8.1",
            agent_id=None,
            agent_category=None,
            agent_config=None,
            intent="",
            retrieved_docs=[],
            final_response=""
        )
        
        # Step 0: Agent Enhancement
        state = await self.step_0_agent_enhancement(initial_state, user_context)
        
        # Step 1: Intent (Agent에서 처리됨)
        state = await self.step_1_intent(state)
        
        # Step 2: Retrieve (Agent 설정 적용)
        state = await self.step_2_retrieve(state)
        
        # Step 3: Compose (Agent 프롬프트 적용)
        state = await self.step_3_compose(state)
        
        return state
    
    async def step_0_agent_enhancement(self, state, user_context):
        """Step 0: Agent Enhancement"""
        logger.info("Step 0: Agent Enhancement 시작")
        
        try:
            enhanced_state = await enhance_pipeline_with_agent(
                state["query"], dict(state), user_context
            )
            
            for key, value in enhanced_state.items():
                if key in state:
                    state[key] = value
                    
            logger.info(f"Agent 카테고리: {state.get('agent_category')}")
            
        except Exception as e:
            logger.error(f"Agent Enhancement 실패: {e}")
            state["agent_category"] = "general"
        
        return state
    
    async def step_1_intent(self, state):
        """Step 1: Intent (Agent에서 분류됨)"""
        state["intent"] = state.get("agent_category", "general")
        return state
    
    async def step_2_retrieve(self, state):
        """Step 2: Enhanced Retrieval"""
        logger.info("Step 2: Enhanced Retrieval 시작")
        
        # Mock 검색 결과
        mock_docs = [
            {"content": f"검색 결과 {i+1}: {state['query']} 관련 내용", "score": 0.9-i*0.1}
            for i in range(5)
        ]
        
        state["retrieved_docs"] = mock_docs
        return state
    
    async def step_3_compose(self, state):
        """Step 3: Compose (Agent 프롬프트 적용)"""
        logger.info("Step 3: Compose 시작")
        
        # 검색된 컨텍스트 준비
        retrieved_context = "\n".join([
            f"- {doc['content']}" for doc in state["retrieved_docs"][:3]
        ])
        
        # Agent 설정에 따른 프롬프트 생성
        agent_config = state.get("agent_config", {})
        if agent_config:
            context_prompt = self.pipeline_adapter.generate_context_prompt(
                state["query"], retrieved_context, agent_config
            )
        else:
            context_prompt = f"질문: {state['query']}\n\n참고자료:\n{retrieved_context}"
        
        # 최종 응답 생성
        state["final_response"] = f"""[{state.get('agent_category', 'general')} Agent 답변]

{context_prompt}

이 답변은 Agent Factory에서 최적화된 설정으로 생성되었습니다."""
        
        return state


async def execute_enhanced_pipeline(query: str, 
                                  chunk_id: Optional[str] = None,
                                  user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """향상된 파이프라인 실행"""
    pipeline = EnhancedLangGraphPipeline()
    return await pipeline.execute_pipeline(query, chunk_id, user_context)

