"""
Agent Profile System - 카테고리별 특화 설정 관리

AgentProfile 클래스: 각 카테고리별로 최적화된 Agent 설정을 정의
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from datetime import datetime


class AgentCategory(Enum):
    """Agent 카테고리 정의"""
    TECHNOLOGY_AI = "technology_ai"
    BUSINESS = "business"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    LEGAL = "legal"
    CREATIVE = "creative"
    GENERAL = "general"


class RetrievalWeight(Enum):
    """Retrieval 가중치 프리셋"""
    VECTOR_HEAVY = {"vector": 0.8, "bm25": 0.2}  # 의미적 유사성 중심
    BM25_HEAVY = {"vector": 0.3, "bm25": 0.7}    # 키워드 매칭 중심
    BALANCED = {"vector": 0.5, "bm25": 0.5}      # 균형잡힌 접근
    HYBRID_SMART = {"vector": 0.6, "bm25": 0.4}  # 스마트 하이브리드


@dataclass
class RetrievalConfig:
    """Retrieval 설정 클래스"""
    weights: Dict[str, float] = field(default_factory=lambda: RetrievalWeight.BALANCED.value)
    max_results: int = 10
    similarity_threshold: float = 0.7
    rerank_enabled: bool = True
    filter_duplicates: bool = True
    context_window_size: int = 4000
    chunk_overlap: int = 200


@dataclass
class ToolConfig:
    """도구 설정 클래스"""
    enabled_tools: List[str] = field(default_factory=list)
    tool_priorities: Dict[str, int] = field(default_factory=dict)
    max_tool_calls: int = 3
    tool_timeout: int = 30
    parallel_execution: bool = False


@dataclass
class PromptConfig:
    """프롬프트 설정 클래스"""
    system_prompt: str = ""
    query_enhancement_template: str = ""
    response_format_template: str = ""
    context_integration_strategy: str = "merge"  # merge, separate, priority
    max_context_tokens: int = 3000
    response_style: str = "professional"  # professional, casual, technical, educational


@dataclass
class ProcessingConfig:
    """처리 설정 클래스"""
    enable_debate: bool = False
    debate_rounds: int = 2
    enable_reflection: bool = True
    quality_threshold: float = 0.8
    timeout_seconds: int = 60
    retry_attempts: int = 2


@dataclass
class AgentProfile:
    """Agent 프로필 - 카테고리별 특화 설정"""
    
    category: AgentCategory
    name: str
    description: str
    
    # 핵심 설정
    retrieval_config: RetrievalConfig = field(default_factory=RetrievalConfig)
    tool_config: ToolConfig = field(default_factory=ToolConfig)
    prompt_config: PromptConfig = field(default_factory=PromptConfig)
    processing_config: ProcessingConfig = field(default_factory=ProcessingConfig)
    
    # 메타데이터
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: str(datetime.now()))
    specializations: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "category": self.category.value,
            "name": self.name,
            "description": self.description,
            "retrieval_config": self.retrieval_config.__dict__,
            "tool_config": self.tool_config.__dict__,
            "prompt_config": self.prompt_config.__dict__,
            "processing_config": self.processing_config.__dict__,
            "version": self.version,
            "created_at": self.created_at,
            "specializations": self.specializations,
            "performance_metrics": self.performance_metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentProfile':
        """딕셔너리에서 생성"""
        retrieval_config = RetrievalConfig(**data.get("retrieval_config", {}))
        tool_config = ToolConfig(**data.get("tool_config", {}))
        prompt_config = PromptConfig(**data.get("prompt_config", {}))
        processing_config = ProcessingConfig(**data.get("processing_config", {}))
        
        return cls(
            category=AgentCategory(data["category"]),
            name=data["name"],
            description=data["description"],
            retrieval_config=retrieval_config,
            tool_config=tool_config,
            prompt_config=prompt_config,
            processing_config=processing_config,
            version=data.get("version", "1.0.0"),
            created_at=data.get("created_at", str(datetime.now())),
            specializations=data.get("specializations", []),
            performance_metrics=data.get("performance_metrics", {})
        )


class AgentProfileFactory:
    """카테고리별 기본 Agent Profile 생성 팩토리"""
    
    @staticmethod
    def create_technology_ai_profile() -> AgentProfile:
        """Technology/AI 특화 Agent Profile"""
        return AgentProfile(
            category=AgentCategory.TECHNOLOGY_AI,
            name="Technology AI Specialist",
            description="AI, ML, Technology 분야 전문 Agent",
            retrieval_config=RetrievalConfig(
                weights=RetrievalWeight.VECTOR_HEAVY.value,
                max_results=15,
                similarity_threshold=0.75,
                rerank_enabled=True
            ),
            tool_config=ToolConfig(
                enabled_tools=["code_analyzer", "tech_search", "api_tester"],
                max_tool_calls=5,
                parallel_execution=True
            ),
            prompt_config=PromptConfig(
                system_prompt="당신은 AI와 기술 분야의 전문가입니다. 정확하고 기술적으로 깊이 있는 답변을 제공합니다.",
                response_style="technical",
                max_context_tokens=4000
            ),
            processing_config=ProcessingConfig(
                enable_debate=True,
                debate_rounds=3,
                quality_threshold=0.85
            ),
            specializations=["AI/ML", "Software Engineering", "Data Science", "Cloud Computing"]
        )
    
    @staticmethod
    def create_business_profile() -> AgentProfile:
        """Business 특화 Agent Profile"""
        return AgentProfile(
            category=AgentCategory.BUSINESS,
            name="Business Strategy Specialist",
            description="비즈니스 전략 및 경영 분야 전문 Agent",
            retrieval_config=RetrievalConfig(
                weights=RetrievalWeight.BM25_HEAVY.value,
                max_results=12,
                similarity_threshold=0.7
            ),
            tool_config=ToolConfig(
                enabled_tools=["market_analyzer", "financial_calculator", "trend_tracker"],
                max_tool_calls=4
            ),
            prompt_config=PromptConfig(
                system_prompt="당신은 비즈니스 전략과 경영 분야의 전문 컨설턴트입니다. 실용적이고 행동 지향적인 조언을 제공합니다.",
                response_style="professional",
                context_integration_strategy="priority"
            ),
            processing_config=ProcessingConfig(
                enable_debate=False,
                enable_reflection=True,
                quality_threshold=0.8
            ),
            specializations=["Strategy", "Marketing", "Finance", "Operations"]
        )
    
    @staticmethod
    def create_education_profile() -> AgentProfile:
        """Education 특화 Agent Profile"""
        return AgentProfile(
            category=AgentCategory.EDUCATION,
            name="Educational Content Specialist",
            description="교육 및 학습 분야 전문 Agent",
            retrieval_config=RetrievalConfig(
                weights=RetrievalWeight.BALANCED.value,
                max_results=20,
                similarity_threshold=0.65,
                context_window_size=5000
            ),
            tool_config=ToolConfig(
                enabled_tools=["curriculum_builder", "assessment_generator", "learning_tracker"],
                max_tool_calls=3
            ),
            prompt_config=PromptConfig(
                system_prompt="당신은 교육 전문가입니다. 학습자의 수준에 맞춰 명확하고 이해하기 쉬운 설명을 제공합니다.",
                response_style="educational",
                context_integration_strategy="separate"
            ),
            processing_config=ProcessingConfig(
                enable_debate=False,
                enable_reflection=True,
                quality_threshold=0.75
            ),
            specializations=["Curriculum Design", "Assessment", "Learning Analytics", "Pedagogy"]
        )
    
    @staticmethod
    def create_general_profile() -> AgentProfile:
        """General purpose Agent Profile"""
        return AgentProfile(
            category=AgentCategory.GENERAL,
            name="General Assistant",
            description="범용 목적 Agent",
            retrieval_config=RetrievalConfig(
                weights=RetrievalWeight.HYBRID_SMART.value,
                max_results=10,
                similarity_threshold=0.7
            ),
            tool_config=ToolConfig(
                enabled_tools=["web_search", "calculator", "text_analyzer"],
                max_tool_calls=3
            ),
            prompt_config=PromptConfig(
                system_prompt="당신은 도움이 되는 AI 어시스턴트입니다. 다양한 주제에 대해 정확하고 유용한 정보를 제공합니다.",
                response_style="professional"
            ),
            processing_config=ProcessingConfig(
                enable_debate=False,
                enable_reflection=True,
                quality_threshold=0.75
            ),
            specializations=["General Knowledge", "Information Retrieval", "Text Processing"]
        )
    
    @classmethod
    def create_profile_by_category(cls, category: AgentCategory) -> AgentProfile:
        """카테고리별 프로필 생성"""
        profile_map = {
            AgentCategory.TECHNOLOGY_AI: cls.create_technology_ai_profile,
            AgentCategory.BUSINESS: cls.create_business_profile,
            AgentCategory.EDUCATION: cls.create_education_profile,
            AgentCategory.GENERAL: cls.create_general_profile
        }
        
        factory_method = profile_map.get(category, cls.create_general_profile)
        return factory_method()
