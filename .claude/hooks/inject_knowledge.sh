#!/bin/bash
# Knowledge Base Auto-injection Hook for Task tool
# Compatible with Windows Git Bash and WSL
# Version: 1.0.0

set -e  # Exit on error

# Debug logging function
log_debug() {
    echo "[KB Hook] $1" >&2
}

# Parse tool input from environment variable
# Use local jq.exe if available, fallback to system jq
if [ -f "./jq.exe" ]; then
    JQ_CMD="./jq.exe"
elif command -v jq &> /dev/null; then
    JQ_CMD="jq"
else
    log_debug "Error: jq not found"
    echo '{"continue": true, "error": "jq not available"}'
    exit 0
fi

tool_name=$(echo "$CLAUDE_TOOL_INPUT" | $JQ_CMD -r '.tool_name // empty' 2>/dev/null || echo "")
subagent_type=$(echo "$CLAUDE_TOOL_INPUT" | $JQ_CMD -r '.tool_input.subagent_type // empty' 2>/dev/null || echo "")

log_debug "Tool: $tool_name, Subagent: $subagent_type"

# Only process Task tool calls with subagent_type
if [ "$tool_name" != "Task" ] || [ -z "$subagent_type" ]; then
    log_debug "Skipping: Not a Task tool call or no subagent_type"
    echo '{"continue": true}'
    exit 0
fi

# Windows/WSL path handling
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OS" == "Windows_NT" ]]; then
    KB_BASE="C:/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/knowledge-base"
else
    KB_BASE="/mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/knowledge-base"
fi

KB_FILE="${KB_BASE}/${subagent_type}_knowledge.json"

log_debug "Looking for knowledge base: $KB_FILE"

# Check file existence
if [ ! -f "$KB_FILE" ]; then
    log_debug "Warning: Knowledge base not found for $subagent_type"
    echo '{"continue": true, "warning": "Knowledge base not found"}'
    exit 0
fi

# jq availability is already checked above

# Extract and inject top 5 items with error handling
log_debug "Loading knowledge for $subagent_type..."

# Create knowledge injection with proper error handling
KNOWLEDGE_INJECTION=$($JQ_CMD -c --arg subagent "$subagent_type" '{
    continue: true,
    suppressOutput: false,
    additionalContext: (
        "📚 Knowledge Base Loaded: " + $subagent + "\n" +
        "🔍 Found " + (.search_results | length | tostring) + " items in knowledge base\n" +
        "🎯 Top References:\n" +
        (.search_results[:5] | map("• " + .title + " (relevance: " + (.relevance_score | tostring) + ")") | join("\n")) +
        "\n\n💡 Latest Trends " + (.latest_trends_2025[0].trend // "N/A") + "\n" +
        "🔧 Key Framework: " + ((.frameworks | keys)[0] // "N/A")
    )
}' "$KB_FILE" 2>/dev/null)

# Check if jq processing was successful
if [ $? -eq 0 ] && [ -n "$KNOWLEDGE_INJECTION" ]; then
    log_debug "Successfully processed knowledge base for $subagent_type"
    echo "$KNOWLEDGE_INJECTION"
else
    log_debug "Error: Failed to process knowledge base JSON"
    echo '{"continue": true, "error": "Failed to process knowledge base"}'
fi