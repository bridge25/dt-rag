# @SPEC:TOOLS-001 @TEST:TOOLS-001:0.3
"""
Integration tests for Tool Execution in LangGraph Pipeline

Tests step4_tools_debate integration with feature flags and Meta-Planner.
"""

import os
import pytest
from apps.orchestration.src.langgraph_pipeline import PipelineState, step4_tools_debate
from apps.orchestration.src.tool_registry import Tool, ToolRegistry, ToolSchema
from apps.api.env_manager import get_env_manager


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset tool registry before each test"""
    registry = ToolRegistry()
    registry._tools.clear()
    yield
    registry._tools.clear()


@pytest.mark.asyncio
class TestToolExecutionIntegration:
    """Integration tests for step4_tools_debate"""

    async def test_step4_with_mcp_tools_flag_on(self):
        """TEST-TOOLS-014: step4 executes tools when mcp_tools flag is ON"""
        # Register calculator tool
        registry = ToolRegistry()

        async def calculator_fn(input_data):
            return input_data.get("a", 0) + input_data.get("b", 0)

        tool = Tool(
            name="calculator",
            description="Add numbers",
            input_schema=ToolSchema(
                type="object",
                properties={"a": {"type": "number"}, "b": {"type": "number"}},
                required=[],
            ),
            execute=calculator_fn,
        )

        registry.register(tool)

        # Enable mcp_tools flag
        os.environ["FEATURE_MCP_TOOLS"] = "true"

        # Create state with plan.tools
        state = PipelineState(
            query="What is 1 + 2?",
            plan={"tools": ["calculator"], "calculator_input": {"a": 1, "b": 2}},
        )

        # Execute step4
        result_state = await step4_tools_debate(state)

        # Verify tool_results is populated
        assert hasattr(result_state, "tool_results")
        assert len(result_state.tool_results) == 1
        assert result_state.tool_results[0]["tool"] == "calculator"
        assert result_state.tool_results[0]["success"] is True
        assert result_state.tool_results[0]["result"] == 3

        # Clean up
        del os.environ["FEATURE_MCP_TOOLS"]

    async def test_step4_with_mcp_tools_flag_off(self):
        """TEST-TOOLS-015: step4 skips when mcp_tools flag is OFF"""
        # Ensure flag is OFF
        if "FEATURE_MCP_TOOLS" in os.environ:
            del os.environ["FEATURE_MCP_TOOLS"]

        state = PipelineState(query="Test query", plan={"tools": ["calculator"]})

        result_state = await step4_tools_debate(state)

        # Verify state is unchanged
        assert (
            not hasattr(result_state, "tool_results")
            or len(result_state.tool_results) == 0
        )

    async def test_step4_no_tools_in_plan(self):
        """TEST-TOOLS-016: step4 skips when plan.tools is empty"""
        os.environ["FEATURE_MCP_TOOLS"] = "true"

        state = PipelineState(query="Test query", plan={"tools": []})

        result_state = await step4_tools_debate(state)

        # Verify no tools executed
        assert (
            not hasattr(result_state, "tool_results")
            or len(result_state.tool_results) == 0
        )

        # Clean up
        del os.environ["FEATURE_MCP_TOOLS"]

    async def test_step4_with_whitelist_policy(self):
        """TEST-TOOLS-017: step4 validates whitelist when tools_policy is ON"""
        registry = ToolRegistry()

        async def web_search_fn(input_data):
            return "search result"

        tool = Tool(
            name="web_search",
            description="Search web",
            input_schema=ToolSchema(type="object", properties={}, required=[]),
            execute=web_search_fn,
        )

        registry.register(tool)

        # Enable both flags
        os.environ["FEATURE_MCP_TOOLS"] = "true"
        os.environ["FEATURE_TOOLS_POLICY"] = "true"
        os.environ["TOOL_WHITELIST"] = "calculator"  # web_search not allowed

        state = PipelineState(
            query="Search for something", plan={"tools": ["web_search"]}
        )

        result_state = await step4_tools_debate(state)

        # Verify tool was blocked
        assert len(result_state.tool_results) == 1
        assert result_state.tool_results[0]["success"] is False
        assert "whitelist" in result_state.tool_results[0]["error"].lower()

        # Clean up
        del os.environ["FEATURE_MCP_TOOLS"]
        del os.environ["FEATURE_TOOLS_POLICY"]
        del os.environ["TOOL_WHITELIST"]

    async def test_step4_partial_failure(self):
        """TEST-TOOLS-018: step4 continues on partial tool failure"""
        registry = ToolRegistry()

        async def good_tool_fn(input_data):
            return "success"

        async def bad_tool_fn(input_data):
            raise RuntimeError("Tool failed")

        good_tool = Tool(
            name="good_tool",
            description="Works",
            input_schema=ToolSchema(type="object", properties={}, required=[]),
            execute=good_tool_fn,
        )

        bad_tool = Tool(
            name="bad_tool",
            description="Fails",
            input_schema=ToolSchema(type="object", properties={}, required=[]),
            execute=bad_tool_fn,
        )

        registry.register(good_tool)
        registry.register(bad_tool)

        os.environ["FEATURE_MCP_TOOLS"] = "true"

        state = PipelineState(query="Test", plan={"tools": ["good_tool", "bad_tool"]})

        result_state = await step4_tools_debate(state)

        # Verify both tools were attempted
        assert len(result_state.tool_results) == 2
        assert result_state.tool_results[0]["success"] is True
        assert result_state.tool_results[1]["success"] is False

        # Clean up
        del os.environ["FEATURE_MCP_TOOLS"]
