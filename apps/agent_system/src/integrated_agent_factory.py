"""
Integrated Agent Factory - Agent Factory와 Pipeline 통합
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import asyncio
from datetime import datetime

from .agent_profile import AgentProfile, AgentCategory, AgentProfileFactory
from .agent_config_builder import AgentConfigBuilder
from .prompt_template_manager import PromptTemplateManager
from .tool_selector import ToolSelector

logger = logging.getLogger(__name__)


class IntegratedAgentFactory:
    """통합 Agent Factory 클래스"""
    
    def __init__(self):
        self.config_builder = AgentConfigBuilder()
        self.prompt_manager = PromptTemplateManager()
        self.tool_selector = ToolSelector()
        self.agent_cache: Dict[str, AgentProfile] = {}
        
    async def create_agent_from_query(self, 
                                    query: str,
                                    user_context: Optional[Dict[str, Any]] = None) -> Tuple[AgentProfile, Dict[str, Any]]:
        """쿼리 기반 Agent 생성"""
        
        try:
            # 1. Intent 분류
            category = self._classify_intent(query)
            logger.info(f"Classified query intent as: {category.value}")
            
            # 2. 쿼리 특성 분석
            query_characteristics = self._analyze_query_characteristics(query)
            
            # 3. Agent Profile 생성
            agent_profile = self.config_builder.build_custom_agent(
                category=category,
                query_characteristics=query_characteristics,
                custom_name=f"{category.value}_agent_{datetime.now().strftime(\"%H%M%S\")}"
            )
            
            # 4. 프롬프트 생성
            prompts = self.prompt_manager.generate_agent_prompts(agent_profile, user_context or {})
            
            # 5. 최적 도구 선택
            optimal_tools = self.tool_selector.select_optimal_tools(
                agent_profile, 
                (user_context or {}).get("task_context", {})
            )
            
            agent_profile.tool_config.enabled_tools = optimal_tools
            
            # 6. Pipeline 설정 생성
            pipeline_config = self._generate_pipeline_config(agent_profile, prompts)
            
            logger.info(f"Created agent: {agent_profile.name} with {len(optimal_tools)} tools")
            
            return agent_profile, pipeline_config
            
        except Exception as e:
            logger.error(f"Error creating agent from query: {e}")
            fallback_profile = AgentProfileFactory.create_general_profile()
            fallback_config = self._generate_pipeline_config(
                fallback_profile, 
                {"system": fallback_profile.prompt_config.system_prompt}
            )
            return fallback_profile, fallback_config
    
    def _classify_intent(self, query: str) -> AgentCategory:
        """간단한 키워드 기반 Intent 분류"""
        query_lower = query.lower()
        
        # Technology/AI 키워드
        tech_keywords = ['ai', 'ml', 'python', 'code', 'api', 'tech']
        business_keywords = ['business', 'strategy', 'market', 'sales']
        education_keywords = ['learn', 'study', 'teach', 'explain']
        
        tech_score = sum(1 for keyword in tech_keywords if keyword in query_lower)
        business_score = sum(1 for keyword in business_keywords if keyword in query_lower)
        education_score = sum(1 for keyword in education_keywords if keyword in query_lower)
        
        scores = [
            (tech_score, AgentCategory.TECHNOLOGY_AI),
            (business_score, AgentCategory.BUSINESS),
            (education_score, AgentCategory.EDUCATION)
        ]
        
        max_score, best_category = max(scores, key=lambda x: x[0])
        return best_category if max_score > 0 else AgentCategory.GENERAL
    
    def _analyze_query_characteristics(self, query: str) -> Dict[str, Any]:
        """쿼리 특성 분석"""
        word_count = len(query.split())
        
        return {
            "length": len(query),
            "complexity": "high" if word_count > 20 else "low" if word_count < 5 else "medium",
            "has_technical_terms": any(term in query.lower() for term in ['api', 'algorithm', 'database']),
            "domain_specificity": 0.8 if any(term in query.lower() for term in ['api', 'code']) else 0.5
        }
    
    def _generate_pipeline_config(self, agent_profile: AgentProfile, 
                                prompts: Dict[str, str]) -> Dict[str, Any]:
        """Pipeline 설정 생성"""
        
        return {
            "agent_id": f"{agent_profile.category.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "agent_name": agent_profile.name,
            "agent_category": agent_profile.category.value,
            
            "retrieval_config": {
                "search_weights": agent_profile.retrieval_config.weights,
                "max_results": agent_profile.retrieval_config.max_results,
                "similarity_threshold": agent_profile.retrieval_config.similarity_threshold,
                "rerank_enabled": agent_profile.retrieval_config.rerank_enabled,
                "filter_duplicates": agent_profile.retrieval_config.filter_duplicates
            },
            
            "prompts": prompts,
            
            "tools": {
                "enabled_tools": agent_profile.tool_config.enabled_tools,
                "max_tool_calls": agent_profile.tool_config.max_tool_calls,
                "tool_timeout": agent_profile.tool_config.tool_timeout,
                "parallel_execution": agent_profile.tool_config.parallel_execution
            },
            
            "processing": {
                "enable_debate": agent_profile.processing_config.enable_debate,
                "debate_rounds": agent_profile.processing_config.debate_rounds,
                "enable_reflection": agent_profile.processing_config.enable_reflection,
                "quality_threshold": agent_profile.processing_config.quality_threshold,
                "timeout_seconds": agent_profile.processing_config.timeout_seconds
            },
            
            "response": {
                "style": agent_profile.prompt_config.response_style,
                "max_context_tokens": agent_profile.prompt_config.max_context_tokens,
                "context_integration_strategy": agent_profile.prompt_config.context_integration_strategy
            }
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        return {
            "cached_agents": len(self.agent_cache),
            "available_templates": len(self.prompt_manager.templates),
            "available_tools": len(self.tool_selector.available_tools),
            "supported_categories": [cat.value for cat in AgentCategory]
        }


# Factory 인스턴스 생성
_agent_factory_instance = None

def get_agent_factory() -> IntegratedAgentFactory:
    """Agent Factory 인스턴스 반환"""
    global _agent_factory_instance
    if _agent_factory_instance is None:
        _agent_factory_instance = IntegratedAgentFactory()
    return _agent_factory_instance


async def create_agent_for_query(query: str, 
                               user_context: Optional[Dict[str, Any]] = None) -> Tuple[AgentProfile, Dict[str, Any]]:
    """쿼리 기반 Agent 생성 편의 함수"""
    factory = get_agent_factory()
    return await factory.create_agent_from_query(query, user_context)
