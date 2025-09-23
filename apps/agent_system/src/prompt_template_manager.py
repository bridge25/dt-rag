"""
Prompt Template Manager - Agent별 프롬프트 템플릿 관리
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
import logging
from datetime import datetime

from .agent_profile import AgentCategory, AgentProfile

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """프롬프트 타입 정의"""
    SYSTEM = "system"
    QUERY_ENHANCEMENT = "query_enhancement"
    CONTEXT_INTEGRATION = "context_integration"
    RESPONSE_FORMAT = "response_format"


@dataclass
class PromptTemplate:
    """프롬프트 템플릿 정의"""
    template_id: str
    category: AgentCategory
    prompt_type: PromptType
    template: str
    variables: List[str]
    description: str = ""
    version: str = "1.0.0"


class PromptTemplateManager:
    """프롬프트 템플릿 관리 클래스"""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """기본 프롬프트 템플릿 로드"""
        
        # Technology/AI 템플릿
        tech_system = PromptTemplate(
            template_id="tech_ai_system",
            category=AgentCategory.TECHNOLOGY_AI,
            prompt_type=PromptType.SYSTEM,
            template="당신은 AI와 기술 분야의 전문가입니다. 기술적으로 정확하고 깊이 있는 답변을 제공합니다.",
            variables=[],
            description="Technology/AI 분야 전문 시스템 프롬프트"
        )
        
        # Business 템플릿
        business_system = PromptTemplate(
            template_id="business_system",
            category=AgentCategory.BUSINESS,
            prompt_type=PromptType.SYSTEM,
            template="당신은 비즈니스 전략과 경영 분야의 전문 컨설턴트입니다. 실용적이고 실행 가능한 조언을 제공합니다.",
            variables=[],
            description="비즈니스 전문 시스템 프롬프트"
        )
        
        # Education 템플릿
        education_system = PromptTemplate(
            template_id="education_system",
            category=AgentCategory.EDUCATION,
            prompt_type=PromptType.SYSTEM,
            template="당신은 교육 전문가입니다. 학습자 수준에 맞춰 단계적이고 명확한 설명을 제공합니다.",
            variables=[],
            description="교육 전문 시스템 프롬프트"
        )
        
        # General 템플릿
        general_system = PromptTemplate(
            template_id="general_system",
            category=AgentCategory.GENERAL,
            prompt_type=PromptType.SYSTEM,
            template="당신은 도움이 되는 AI 어시스턴트입니다. 정확하고 유용한 정보를 제공합니다.",
            variables=[],
            description="범용 시스템 프롬프트"
        )
        
        self.templates.update({
            "tech_ai_system": tech_system,
            "business_system": business_system,
            "education_system": education_system,
            "general_system": general_system
        })
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """템플릿 ID로 템플릿 조회"""
        return self.templates.get(template_id)
    
    def generate_agent_prompts(self, profile: AgentProfile, 
                              context: Dict[str, Any]) -> Dict[str, str]:
        """Agent Profile을 위한 프롬프트 생성"""
        prompts = {}
        
        try:
            # System Prompt 생성
            system_template_id = f"{profile.category.value}_system"
            template = self.get_template(system_template_id)
            
            if template:
                prompts["system"] = template.template
            else:
                prompts["system"] = profile.prompt_config.system_prompt
            
            logger.info(f"Generated prompts for {profile.category.value} agent")
            
        except Exception as e:
            logger.error(f"Error generating agent prompts: {e}")
            prompts["system"] = profile.prompt_config.system_prompt
            
        return prompts
    
    def list_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """사용 가능한 템플릿 목록"""
        template_info = {}
        
        for template_id, template in self.templates.items():
            template_info[template_id] = {
                "category": template.category.value,
                "type": template.prompt_type.value,
                "description": template.description
            }
        
        return template_info
