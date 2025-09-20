"""
Tool Selector - Agent별 도구 선택 및 관리
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from .agent_profile import AgentCategory, AgentProfile, ToolConfig

logger = logging.getLogger(__name__)


class ToolType(Enum):
    """도구 타입 분류"""
    SEARCH = "search"
    ANALYSIS = "analysis" 
    COMPUTATION = "computation"
    CODE = "code"


@dataclass
class ToolDefinition:
    """도구 정의"""
    tool_id: str
    name: str
    description: str
    tool_type: ToolType
    categories: List[AgentCategory]
    priority: int = 5


class ToolSelector:
    """Agent별 도구 선택 및 관리 클래스"""
    
    def __init__(self):
        self.available_tools: Dict[str, ToolDefinition] = {}
        self.category_tool_mapping: Dict[AgentCategory, List[str]] = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """기본 도구 초기화"""
        tools = [
            ToolDefinition("web_search", "Web Search", "실시간 웹 검색",
                         ToolType.SEARCH, [AgentCategory.GENERAL], 8),
            ToolDefinition("tech_search", "Tech Search", "기술 문서 검색", 
                         ToolType.SEARCH, [AgentCategory.TECHNOLOGY_AI], 10),
            ToolDefinition("code_analyzer", "Code Analyzer", "코드 분석",
                         ToolType.ANALYSIS, [AgentCategory.TECHNOLOGY_AI], 9),
            ToolDefinition("market_analyzer", "Market Analyzer", "시장 분석",
                         ToolType.ANALYSIS, [AgentCategory.BUSINESS], 9),
            ToolDefinition("calculator", "Calculator", "수학 계산",
                         ToolType.COMPUTATION, [AgentCategory.GENERAL], 7)
        ]
        
        for tool in tools:
            self.register_tool(tool)
    
    def register_tool(self, tool: ToolDefinition):
        """도구 등록"""
        self.available_tools[tool.tool_id] = tool
        
        for category in tool.categories:
            if category not in self.category_tool_mapping:
                self.category_tool_mapping[category] = []
            self.category_tool_mapping[category].append(tool.tool_id)
    
    def select_optimal_tools(self, profile: AgentProfile, 
                           task_context: Dict[str, Any]) -> List[str]:
        """최적 도구 선택"""
        category_tools = self.category_tool_mapping.get(profile.category, [])
        
        selected_tools = []
        for tool_id in category_tools:
            tool = self.available_tools.get(tool_id)
            if tool and tool.priority >= 7:
                selected_tools.append(tool_id)
        
        max_tools = profile.tool_config.max_tool_calls
        return selected_tools[:max_tools]
    
    def get_tool_info(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """도구 정보 조회"""
        tool = self.available_tools.get(tool_id)
        if not tool:
            return None
        
        return {
            "name": tool.name,
            "description": tool.description,
            "type": tool.tool_type.value,
            "priority": tool.priority
        }
    
    def list_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """사용 가능한 모든 도구 목록"""
        return {tool_id: self.get_tool_info(tool_id) 
                for tool_id in self.available_tools.keys()}

