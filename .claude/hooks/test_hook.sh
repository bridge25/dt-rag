#!/bin/bash
# Test script to verify the Knowledge Base injection hook
# This simulates a Task tool call

echo "=== Testing Knowledge Base Injection Hook ==="
echo

# Simulate Task tool call environment
export CLAUDE_TOOL_INPUT='{
  "tool_name": "Task",
  "tool_input": {
    "subagent_type": "rag-evaluation-specialist",
    "prompt": "Evaluate the RAG system using RAGAS v2.0 metrics and provide specific configuration recommendations",
    "description": "RAG evaluation task"
  }
}'

echo "🔧 Simulated CLAUDE_TOOL_INPUT:"
echo "$CLAUDE_TOOL_INPUT" | ./jq.exe '.'
echo

echo "🚀 Running hook script..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run the hook script
bash .claude/hooks/inject_knowledge.sh

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Hook test completed!"
echo

# Test with non-Task tool (should skip)
echo "🔧 Testing with non-Task tool (should skip):"
export CLAUDE_TOOL_INPUT='{"tool_name": "Read", "tool_input": {"file_path": "test.txt"}}'
bash .claude/hooks/inject_knowledge.sh

echo
echo "🔧 Testing with Task but no subagent_type (should skip):"
export CLAUDE_TOOL_INPUT='{"tool_name": "Task", "tool_input": {"prompt": "general task"}}'
bash .claude/hooks/inject_knowledge.sh

echo
echo "🎯 All tests completed!"