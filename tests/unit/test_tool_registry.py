# @SPEC:TOOLS-001 @TEST:TOOLS-001:0.1
"""
Unit tests for Tool Registry

Tests tool registration, retrieval, and whitelist validation.
"""

import os
import pytest
from apps.orchestration.src.tool_registry import Tool, ToolRegistry, ToolSchema


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset tool registry before each test"""
    registry = ToolRegistry()
    registry._tools.clear()
    yield
    registry._tools.clear()


class TestToolRegistry:
    """Test suite for ToolRegistry"""

    def test_register_and_get_tool(self):
        """TEST-TOOLS-001: Register tool and retrieve it"""
        registry = ToolRegistry()

        tool = Tool(
            name="web_search",
            description="Search the web",
            input_schema=ToolSchema(
                type="object",
                properties={"query": {"type": "string"}},
                required=["query"]
            ),
            execute=lambda x: {"result": "search result"}
        )

        registry.register(tool)
        retrieved_tool = registry.get_tool("web_search")

        assert retrieved_tool is not None
        assert retrieved_tool.name == "web_search"
        assert retrieved_tool.description == "Search the web"

    def test_list_tools(self):
        """TEST-TOOLS-002: List all registered tools"""
        registry = ToolRegistry()

        # Register 3 tools
        for i in range(3):
            tool = Tool(
                name=f"tool_{i}",
                description=f"Tool {i}",
                input_schema=ToolSchema(type="object", properties={}, required=[]),
                execute=lambda x: {}
            )
            registry.register(tool)

        tools_list = registry.list_tools()

        assert len(tools_list) == 3
        assert all("name" in tool for tool in tools_list)
        assert all("description" in tool for tool in tools_list)

    def test_get_nonexistent_tool(self):
        """TEST-TOOLS-003: Retrieve non-existent tool returns None"""
        registry = ToolRegistry()

        result = registry.get_tool("unknown_tool")

        assert result is None

    def test_validate_tool_with_whitelist(self):
        """TEST-TOOLS-004: Validate tool against whitelist (allowed)"""
        registry = ToolRegistry()

        # Set whitelist environment variable
        os.environ["TOOL_WHITELIST"] = "web_search,calculator"

        result = registry.validate_tool("web_search")

        assert result is True

        # Clean up
        del os.environ["TOOL_WHITELIST"]

    def test_validate_tool_blocked_by_whitelist(self):
        """TEST-TOOLS-005: Validate tool against whitelist (blocked)"""
        registry = ToolRegistry()

        # Set whitelist environment variable
        os.environ["TOOL_WHITELIST"] = "calculator"

        result = registry.validate_tool("web_search")

        assert result is False

        # Clean up
        del os.environ["TOOL_WHITELIST"]

    def test_validate_tool_no_whitelist(self):
        """TEST-TOOLS-006: Validate tool with no whitelist (dev mode)"""
        registry = ToolRegistry()

        # Ensure no whitelist is set
        if "TOOL_WHITELIST" in os.environ:
            del os.environ["TOOL_WHITELIST"]

        result = registry.validate_tool("any_tool")

        assert result is True

    def test_singleton_pattern(self):
        """TEST-TOOLS-007: ToolRegistry should use singleton pattern"""
        registry1 = ToolRegistry()
        registry2 = ToolRegistry()

        tool = Tool(
            name="test_tool",
            description="Test",
            input_schema=ToolSchema(type="object", properties={}, required=[]),
            execute=lambda x: {}
        )

        registry1.register(tool)

        # Both instances should share the same tools
        assert registry2.get_tool("test_tool") is not None
