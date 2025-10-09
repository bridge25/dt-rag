# @SPEC:TOOLS-001 @TEST:TOOLS-001:0.2
"""
Unit tests for Tool Executor

Tests tool execution pipeline including timeout, validation, and error handling.
"""

import asyncio
import pytest
from jsonschema import ValidationError
from apps.orchestration.src.tool_registry import Tool, ToolRegistry, ToolSchema
from apps.orchestration.src.tool_executor import execute_tool, ToolExecutionResult


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset tool registry before each test"""
    registry = ToolRegistry()
    registry._tools.clear()
    yield
    registry._tools.clear()


@pytest.mark.asyncio
class TestToolExecutor:
    """Test suite for Tool Executor"""

    async def test_execute_tool_success(self):
        """TEST-TOOLS-008: Execute tool successfully"""
        registry = ToolRegistry()

        async def calculator_fn(input_data):
            return input_data["a"] + input_data["b"]

        tool = Tool(
            name="calculator",
            description="Add two numbers",
            input_schema=ToolSchema(
                type="object",
                properties={
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                required=["a", "b"]
            ),
            execute=calculator_fn
        )

        registry.register(tool)

        result = await execute_tool("calculator", {"a": 1, "b": 2})

        assert result.success is True
        assert result.result == 3
        assert result.error is None
        assert result.tool_name == "calculator"
        assert result.elapsed >= 0

    async def test_execute_tool_timeout(self):
        """TEST-TOOLS-009: Execute tool with timeout"""
        registry = ToolRegistry()

        async def slow_tool_fn(input_data):
            await asyncio.sleep(5)
            return "done"

        tool = Tool(
            name="slow_tool",
            description="Slow tool",
            input_schema=ToolSchema(type="object", properties={}, required=[]),
            execute=slow_tool_fn
        )

        registry.register(tool)

        result = await execute_tool("slow_tool", {}, timeout=0.1)

        assert result.success is False
        assert "timeout" in result.error.lower()
        assert result.tool_name == "slow_tool"

    async def test_execute_tool_validation_error(self):
        """TEST-TOOLS-010: Execute tool with invalid input schema"""
        registry = ToolRegistry()

        async def tool_fn(input_data):
            return "ok"

        tool = Tool(
            name="strict_tool",
            description="Requires 'a' field",
            input_schema=ToolSchema(
                type="object",
                properties={"a": {"type": "string"}},
                required=["a"]
            ),
            execute=tool_fn
        )

        registry.register(tool)

        result = await execute_tool("strict_tool", {})

        assert result.success is False
        assert "validation" in result.error.lower()
        assert result.tool_name == "strict_tool"

    async def test_execute_nonexistent_tool(self):
        """TEST-TOOLS-011: Execute non-existent tool"""
        result = await execute_tool("nonexistent", {})

        assert result.success is False
        assert "not found" in result.error.lower()
        assert result.tool_name == "nonexistent"

    async def test_execute_tool_runtime_error(self):
        """TEST-TOOLS-012: Execute tool that raises exception"""
        registry = ToolRegistry()

        async def error_tool_fn(input_data):
            raise RuntimeError("Tool execution failed")

        tool = Tool(
            name="error_tool",
            description="Raises error",
            input_schema=ToolSchema(type="object", properties={}, required=[]),
            execute=error_tool_fn
        )

        registry.register(tool)

        result = await execute_tool("error_tool", {})

        assert result.success is False
        assert "error" in result.error.lower()
        assert result.tool_name == "error_tool"

    async def test_execute_tool_elapsed_time(self):
        """TEST-TOOLS-013: Verify elapsed time is tracked"""
        registry = ToolRegistry()

        async def quick_tool_fn(input_data):
            await asyncio.sleep(0.1)
            return "done"

        tool = Tool(
            name="quick_tool",
            description="Quick tool",
            input_schema=ToolSchema(type="object", properties={}, required=[]),
            execute=quick_tool_fn
        )

        registry.register(tool)

        result = await execute_tool("quick_tool", {})

        assert result.success is True
        assert result.elapsed >= 0.1
        assert result.elapsed < 1.0
