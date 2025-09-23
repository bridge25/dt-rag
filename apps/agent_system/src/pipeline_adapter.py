"""
Pipeline Adapter - LangGraph Pipeline과 Agent Factory 통합
"""

from typing import Dict, List, Any, Optional
import logging

from .integrated_agent_factory import get_agent_factory
from .agent_profile import AgentProfile

logger = logging.getLogger(__name__)


class PipelineAdapter:
    """LangGraph Pipeline 통합 어댑터"""
    
    def __init__(self):
        self.agent_factory = get_agent_factory()
        
    async def enhance_pipeline_state(self, 
                                   query: str,
                                   pipeline_state: Dict[str, Any],
                                   user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Pipeline State를 Agent 설정으로 강화"""
        
        try:
            agent_profile, pipeline_config = await self.agent_factory.create_agent_from_query(
                query, user_context
            )
            
            enhanced_state = pipeline_state.copy()
            enhanced_state.update({
                "agent_id": pipeline_config["agent_id"],
                "agent_category": pipeline_config["agent_category"],
                "agent_profile": agent_profile,
                "agent_config": pipeline_config,
                "retrieval_weights": pipeline_config["retrieval_config"]["search_weights"],
                "max_retrieval_results": pipeline_config["retrieval_config"]["max_results"],
                "enabled_tools": pipeline_config["tools"]["enabled_tools"],
                "system_prompt": pipeline_config["prompts"].get("system", "")
            })
            
            logger.info(f"Enhanced pipeline state with agent: {agent_profile.name}")
            return enhanced_state
            
        except Exception as e:
            logger.error(f"Error enhancing pipeline state: {e}")
            return pipeline_state
    
    def apply_retrieval_weights(self, 
                              vector_results: List[Dict], 
                              bm25_results: List[Dict],
                              weights: Dict[str, float]) -> List[Dict]:
        """검색 결과 가중치 적용"""
        
        try:
            vector_weight = weights.get("vector", 0.5)
            bm25_weight = weights.get("bm25", 0.5)
            
            weighted_results = []
            
            for result in vector_results:
                score = result.get("score", 0.0)
                result_copy = result.copy()
                result_copy["weighted_score"] = score * vector_weight
                result_copy["source"] = "vector"
                weighted_results.append(result_copy)
            
            for result in bm25_results:
                score = result.get("score", 0.0)
                result_copy = result.copy()
                result_copy["weighted_score"] = score * bm25_weight
                result_copy["source"] = "bm25"
                weighted_results.append(result_copy)
            
            weighted_results.sort(key=lambda x: x["weighted_score"], reverse=True)
            return weighted_results
            
        except Exception as e:
            logger.error(f"Error applying retrieval weights: {e}")
            return vector_results + bm25_results
    
    def generate_context_prompt(self, 
                              query: str,
                              retrieved_context: str,
                              agent_config: Dict[str, Any]) -> str:
        """Agent 설정에 따른 컨텍스트 프롬프트 생성"""
        
        try:
            prompts = agent_config.get("prompts", {})
            system_prompt = prompts.get("system", "")
            
            context_prompt = f"""질문: {query}

참고 자료:
{retrieved_context}

위 자료를 참고하여 질문에 답변해주세요."""
            
            return f"{system_prompt}\n\n{context_prompt}"
            
        except Exception as e:
            logger.error(f"Error generating context prompt: {e}")
            return f"질문: {query}\n\n참고 자료:\n{retrieved_context}\n\n답변:"


# 글로벌 어댑터 인스턴스
_pipeline_adapter_instance = None

def get_pipeline_adapter():
    """Pipeline Adapter 인스턴스 반환"""
    global _pipeline_adapter_instance
    if _pipeline_adapter_instance is None:
        _pipeline_adapter_instance = PipelineAdapter()
    return _pipeline_adapter_instance


async def enhance_pipeline_with_agent(query: str,
                                     pipeline_state: Dict[str, Any],
                                     user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Pipeline을 Agent로 강화하는 헬퍼 함수"""
    adapter = get_pipeline_adapter()
    return await adapter.enhance_pipeline_state(query, pipeline_state, user_context)

