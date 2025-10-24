# @SPEC:TOOLS-001 @IMPL:TOOLS-001:0.2
"""
Tool Executor for MCP Tools

Handles tool execution with timeout, validation, and error handling.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from jsonschema import ValidationError, validate
from pydantic import BaseModel

from apps.orchestration.src.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolExecutionResult(BaseModel):
    """Result of tool execution"""

    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    tool_name: str
    elapsed: float


async def execute_tool(
    tool_name: str, input_data: Dict[str, Any], timeout: float = 30.0
) -> ToolExecutionResult:
    """
    Execute tool with timeout and validation

    Args:
        tool_name: Name of tool to execute
        input_data: Input data for tool
        timeout: Execution timeout in seconds (default: 30.0)

    Returns:
        ToolExecutionResult with success status, result, and error info
    """
    start = time.time()

    try:
        registry = ToolRegistry()
        tool = registry.get_tool(tool_name)

        if not tool:
            return ToolExecutionResult(
                success=False,
                error=f"Tool '{tool_name}' not found",
                tool_name=tool_name,
                elapsed=time.time() - start,
            )

        try:
            validate(instance=input_data, schema=tool.input_schema.dict())
        except ValidationError as e:
            return ToolExecutionResult(
                success=False,
                error=f"Input validation failed: {str(e.message)}",
                tool_name=tool_name,
                elapsed=time.time() - start,
            )

        result = await asyncio.wait_for(tool.execute(input_data), timeout=timeout)

        return ToolExecutionResult(
            success=True,
            result=result,
            tool_name=tool_name,
            elapsed=time.time() - start,
        )

    except asyncio.TimeoutError:
        return ToolExecutionResult(
            success=False,
            error=f"Tool execution timeout ({timeout}s)",
            tool_name=tool_name,
            elapsed=time.time() - start,
        )

    except Exception as e:
        return ToolExecutionResult(
            success=False,
            error=f"Execution error: {str(e)}",
            tool_name=tool_name,
            elapsed=time.time() - start,
        )
