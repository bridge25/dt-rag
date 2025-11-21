# @SPEC:TOOLS-001 @IMPL:TOOLS-001:0.1
"""
Tool Registry for MCP Tools

Manages tool registration, retrieval, and whitelist validation.

@CODE:ORCHESTRATION-001
"""

import os
import logging
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ToolSchema(BaseModel):
    """Tool input/output schema (JSON Schema)"""

    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class Tool(BaseModel):
    """MCP Tool definition"""

    name: str
    description: str
    input_schema: ToolSchema
    execute: Callable

    class Config:
        arbitrary_types_allowed = True


class ToolRegistry:
    """Central registry for MCP Tools (Singleton)"""

    _instance: Optional["ToolRegistry"] = None
    _tools: Dict[str, Tool] = {}

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, tool: Tool) -> None:
        """Register a new tool"""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get tool by name"""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools (metadata only)"""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema.dict(),
            }
            for t in self._tools.values()
        ]

    def validate_tool(self, name: str) -> bool:
        """Validate tool against whitelist policy"""
        whitelist = os.getenv("TOOL_WHITELIST", "")
        if not whitelist:
            return True

        allowed_tools = [t.strip() for t in whitelist.split(",")]
        return name in allowed_tools
