"""
Agent Config Builder - 동적 Agent 설정 생성 및 커스터마이징

AgentConfigBuilder: Agent Profile을 기반으로 동적으로 설정을 생성하고 커스터마이징
"""

from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field, replace
import json
import logging
from datetime import datetime

from .agent_profile import (
    AgentProfile, AgentCategory, AgentProfileFactory,
    RetrievalConfig, ToolConfig, PromptConfig, ProcessingConfig,
    RetrievalWeight
)

logger = logging.getLogger(__name__)


@dataclass
class CustomizationRule:
    """커스터마이징 규칙 정의"""
    condition: str  # JSON path 또는 조건식
    action: str     # 수행할 액션 (set, add, multiply, replace)
    value: Any      # 설정할 값
    description: str = ""


class AgentConfigBuilder:
    """동적 Agent 설정 생성 및 커스터마이징 클래스"""
    
    def __init__(self):
        self.customization_rules: List[CustomizationRule] = []
        self.performance_cache: Dict[str, Dict[str, float]] = {}
        
    def create_base_config(self, category: AgentCategory, 
                          custom_name: Optional[str] = None) -> AgentProfile:
        """기본 카테고리별 설정 생성"""
        try:
            base_profile = AgentProfileFactory.create_profile_by_category(category)
            
            if custom_name:
                base_profile.name = custom_name
                
            logger.info(f"Created base config for category: {category.value}")
            return base_profile
            
        except Exception as e:
            logger.error(f"Error creating base config: {e}")
            # Fallback to general profile
            return AgentProfileFactory.create_general_profile()
    
    def enhance_retrieval_config(self, profile: AgentProfile, 
                                query_characteristics: Dict[str, Any]) -> AgentProfile:
        """쿼리 특성을 바탕으로 Retrieval 설정 최적화"""
        try:
            query_length = query_characteristics.get("length", 50)
            query_complexity = query_characteristics.get("complexity", "medium")
            has_technical_terms = query_characteristics.get("has_technical_terms", False)
            domain_specificity = query_characteristics.get("domain_specificity", 0.5)
            
            # 새로운 retrieval config 생성
            new_retrieval_config = replace(profile.retrieval_config)
            
            # 쿼리 길이에 따른 조정
            if query_length > 100:  # 긴 쿼리
                new_retrieval_config.max_results = min(20, new_retrieval_config.max_results + 5)
                new_retrieval_config.context_window_size = min(6000, new_retrieval_config.context_window_size + 1000)
            elif query_length < 20:  # 짧은 쿼리
                new_retrieval_config.max_results = max(5, new_retrieval_config.max_results - 3)
                
            # 복잡도에 따른 조정
            if query_complexity == "high":
                new_retrieval_config.similarity_threshold = max(0.6, new_retrieval_config.similarity_threshold - 0.1)
                new_retrieval_config.rerank_enabled = True
            elif query_complexity == "low":
                new_retrieval_config.similarity_threshold = min(0.8, new_retrieval_config.similarity_threshold + 0.1)
                
            # 기술적 용어 포함 여부에 따른 가중치 조정
            if has_technical_terms:
                # 벡터 검색 비중 증가 (의미적 유사성 중요)
                vector_weight = min(0.8, new_retrieval_config.weights.get("vector", 0.5) + 0.2)
                bm25_weight = 1.0 - vector_weight
                new_retrieval_config.weights = {"vector": vector_weight, "bm25": bm25_weight}
            
            # 도메인 특화도에 따른 조정
            if domain_specificity > 0.7:
                # 높은 도메인 특화 - 더 정확한 검색
                new_retrieval_config.similarity_threshold = min(0.85, new_retrieval_config.similarity_threshold + 0.1)
                new_retrieval_config.filter_duplicates = True
                
            profile.retrieval_config = new_retrieval_config
            logger.info("Enhanced retrieval config based on query characteristics")
            
        except Exception as e:
            logger.error(f"Error enhancing retrieval config: {e}")
            
        return profile
    
    def build_custom_agent(self, 
                          category: AgentCategory,
                          query_characteristics: Optional[Dict[str, Any]] = None,
                          user_preferences: Optional[Dict[str, Any]] = None,
                          task_context: Optional[Dict[str, Any]] = None,
                          performance_feedback: Optional[Dict[str, float]] = None,
                          custom_name: Optional[str] = None) -> AgentProfile:
        """모든 커스터마이징을 적용한 Agent 생성"""
        
        # 1. 기본 프로필 생성
        profile = self.create_base_config(category, custom_name)
        
        # 2. 쿼리 특성에 따른 Retrieval 최적화
        if query_characteristics:
            profile = self.enhance_retrieval_config(profile, query_characteristics)
        
        # 3. 최종 검증 및 조정
        profile = self._validate_and_adjust(profile)
        
        logger.info(f"Built custom agent: {profile.name} ({profile.category.value})")
        return profile
    
    def _validate_and_adjust(self, profile: AgentProfile) -> AgentProfile:
        """설정 유효성 검증 및 자동 조정"""
        try:
            # Retrieval 설정 검증
            if profile.retrieval_config.max_results > 50:
                profile.retrieval_config.max_results = 50
            if profile.retrieval_config.similarity_threshold < 0.3:
                profile.retrieval_config.similarity_threshold = 0.3
            
            # Tool 설정 검증
            if profile.tool_config.max_tool_calls > 10:
                profile.tool_config.max_tool_calls = 10
            if profile.tool_config.tool_timeout > 120:
                profile.tool_config.tool_timeout = 120
            
            # Prompt 설정 검증
            if profile.prompt_config.max_context_tokens > 8000:
                profile.prompt_config.max_context_tokens = 8000
            
            # Processing 설정 검증
            if profile.processing_config.timeout_seconds > 300:
                profile.processing_config.timeout_seconds = 300
            if profile.processing_config.debate_rounds > 5:
                profile.processing_config.debate_rounds = 5
                
        except Exception as e:
            logger.error(f"Error validating profile: {e}")
            
        return profile
