# @SPEC:TOOLS-001 @IMPL:TOOLS-001:0.3
"""
Calculator Tool

Basic calculator tool for testing MCP tool execution.
"""

from typing import cast

from apps.orchestration.src.tool_registry import Tool, ToolRegistry, ToolSchema


async def calculator_execute(input_data: dict) -> float:
    """Add two numbers"""
    a = cast(float, input_data.get("a", 0))
    b = cast(float, input_data.get("b", 0))
    return a + b


CALCULATOR_TOOL = Tool(
    name="calculator",
    description="Add two numbers",
    input_schema=ToolSchema(
        type="object",
        properties={"a": {"type": "number"}, "b": {"type": "number"}},
        required=["a", "b"],
    ),
    execute=calculator_execute,
)

# Auto-register tool
registry = ToolRegistry()
registry.register(CALCULATOR_TOOL)
