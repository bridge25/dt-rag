#!/bin/bash

# Gemini Assistant Helper Script
# Provides convenient functions for using Gemini subagent

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "❌ Error: .env file not found. Please create it with GEMINI_API_KEY."
    exit 1
fi

# Check if Gemini CLI is available
if ! command -v gemini &> /dev/null; then
    echo "❌ Error: Gemini CLI not found. Please install it first."
    echo "   npm install -g @google/generative-ai-cli"
    exit 1
fi

# Check if API key is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Error: GEMINI_API_KEY not set in .env file."
    exit 1
fi

# Function to review code
review_code() {
    local file_path="$1"
    if [ ! -f "$file_path" ]; then
        echo "❌ Error: File not found: $file_path"
        return 1
    fi

    echo "🔍 Reviewing code in: $file_path"
    echo "Please review this code for best practices, security issues, and optimization opportunities:" | \
    cat - "$file_path" | \
    gemini -m gemini-2.5-pro
}

# Function to analyze bugs
debug_code() {
    local code="$1"
    local error_msg="$2"

    echo "🐛 Analyzing bug..."
    echo "I'm getting this error: '$error_msg' with this code. Please help identify and fix the issue:

$code" | gemini -m gemini-2.5-pro
}

# Function to optimize code
optimize_code() {
    local file_path="$1"
    if [ ! -f "$file_path" ]; then
        echo "❌ Error: File not found: $file_path"
        return 1
    fi

    echo "⚡ Optimizing code in: $file_path"
    echo "Please optimize this code for better performance, memory usage, and readability:" | \
    cat - "$file_path" | \
    gemini -m gemini-2.5-pro
}

# Function to generate documentation
generate_docs() {
    local file_path="$1"
    if [ ! -f "$file_path" ]; then
        echo "❌ Error: File not found: $file_path"
        return 1
    fi

    echo "📚 Generating documentation for: $file_path"
    echo "Generate comprehensive documentation for this code including API docs, usage examples, and comments:" | \
    cat - "$file_path" | \
    gemini -m gemini-2.5-pro
}

# Function to generate tests
generate_tests() {
    local file_path="$1"
    local test_framework="${2:-pytest}"

    if [ ! -f "$file_path" ]; then
        echo "❌ Error: File not found: $file_path"
        return 1
    fi

    echo "🧪 Generating tests for: $file_path (framework: $test_framework)"
    echo "Generate comprehensive unit tests for this code using $test_framework. Include edge cases, error scenarios, and mocking where appropriate:" | \
    cat - "$file_path" | \
    gemini -m gemini-2.5-pro
}

# Function to ask general question
ask_gemini() {
    local question="$1"
    if [ -z "$question" ]; then
        echo "❌ Error: Please provide a question."
        return 1
    fi

    echo "💭 Asking Gemini..."
    echo "$question" | gemini -m gemini-2.5-pro
}

# Function to ask quick question (using flash model)
ask_quick() {
    local question="$1"
    if [ -z "$question" ]; then
        echo "❌ Error: Please provide a question."
        return 1
    fi

    echo "⚡ Quick question to Gemini..."
    echo "$question" | gemini -m gemini-2.5-flash
}

# Function to check rate limits
check_limits() {
    echo "📊 Gemini API Rate Limits (Free Tier):"
    echo "   • 5 requests per minute"
    echo "   • 25 requests per day"
    echo "   • Use 'ask_quick' for simple questions to save quota"
}

# Help function
show_help() {
    echo "🤖 Gemini Assistant Helper Script"
    echo ""
    echo "Usage:"
    echo "  $0 review <file>              - Review code for best practices"
    echo "  $0 debug '<code>' '<error>'   - Debug code with error message"
    echo "  $0 optimize <file>            - Optimize code performance"
    echo "  $0 docs <file>                - Generate documentation"
    echo "  $0 tests <file> [framework]   - Generate unit tests"
    echo "  $0 ask '<question>'           - Ask general question"
    echo "  $0 quick '<question>'         - Ask quick question (flash model)"
    echo "  $0 limits                     - Show rate limits"
    echo "  $0 help                       - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 review app.py"
    echo "  $0 debug 'print(x)' 'NameError: name x is not defined'"
    echo "  $0 ask 'What is the best Python web framework?'"
    echo "  $0 tests calculator.py pytest"
}

# Main script logic
case "$1" in
    review)
        review_code "$2"
        ;;
    debug)
        debug_code "$2" "$3"
        ;;
    optimize)
        optimize_code "$2"
        ;;
    docs)
        generate_docs "$2"
        ;;
    tests)
        generate_tests "$2" "$3"
        ;;
    ask)
        ask_gemini "$2"
        ;;
    quick)
        ask_quick "$2"
        ;;
    limits)
        check_limits
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Error: Unknown command '$1'"
        echo "Use '$0 help' for usage information."
        exit 1
        ;;
esac