#!/usr/bin/env python3
"""Test script to verify the Python Knowledge Base injection hook"""

import os
import json
import sys
from pathlib import Path

def test_python_hook():
    """Test the Python knowledge injection hook"""

    print("=== Testing Python Knowledge Base Injection Hook ===")
    print()

    # Test 1: RAG Evaluation Specialist with RAGAS keywords
    print("🔧 Test 1: RAG Evaluation with RAGAS keywords")
    test_input_1 = {
        "tool_name": "Task",
        "tool_input": {
            "subagent_type": "rag-evaluation-specialist",
            "prompt": "Evaluate the RAG system using RAGAS v2.0 metrics and provide specific configuration recommendations for faithfulness scoring",
            "description": "RAG evaluation task"
        }
    }

    os.environ['CLAUDE_TOOL_INPUT'] = json.dumps(test_input_1)

    # Import and run the hook
    sys.path.insert(0, str(Path(__file__).parent))
    from knowledge_injector import KnowledgeInjector

    injector = KnowledgeInjector()
    result1 = injector.run()

    print("Response:")
    print(json.dumps(result1, indent=2, ensure_ascii=False))
    print()

    # Test 2: Database Architect with PostgreSQL keywords
    print("🔧 Test 2: Database optimization with PostgreSQL/pgvector")
    test_input_2 = {
        "tool_name": "Task",
        "tool_input": {
            "subagent_type": "database-architect",
            "prompt": "Design optimized PostgreSQL database schema with pgvector extension for high-performance vector similarity searches using HNSW indexing",
            "description": "Database optimization task"
        }
    }

    os.environ['CLAUDE_TOOL_INPUT'] = json.dumps(test_input_2)
    result2 = injector.run()

    print("Response:")
    print(json.dumps(result2, indent=2, ensure_ascii=False))
    print()

    # Test 3: Hybrid Search with BM25 + vector keywords
    print("🔧 Test 3: Hybrid search with BM25 and vector similarity")
    test_input_3 = {
        "tool_name": "Task",
        "tool_input": {
            "subagent_type": "hybrid-search-specialist",
            "prompt": "Implement hybrid search combining BM25 lexical search with vector similarity using cross-encoder reranking for improved retrieval performance",
            "description": "Hybrid search implementation"
        }
    }

    os.environ['CLAUDE_TOOL_INPUT'] = json.dumps(test_input_3)
    result3 = injector.run()

    print("Response:")
    print(json.dumps(result3, indent=2, ensure_ascii=False))
    print()

    # Test 4: Non-Task tool (should skip)
    print("🔧 Test 4: Non-Task tool (should skip)")
    test_input_4 = {
        "tool_name": "Read",
        "tool_input": {
            "file_path": "test.txt"
        }
    }

    os.environ['CLAUDE_TOOL_INPUT'] = json.dumps(test_input_4)
    result4 = injector.run()

    print("Response:")
    print(json.dumps(result4, indent=2, ensure_ascii=False))
    print()

    # Test 5: Task without subagent_type (should skip)
    print("🔧 Test 5: Task without subagent_type (should skip)")
    test_input_5 = {
        "tool_name": "Task",
        "tool_input": {
            "prompt": "General task without subagent type"
        }
    }

    os.environ['CLAUDE_TOOL_INPUT'] = json.dumps(test_input_5)
    result5 = injector.run()

    print("Response:")
    print(json.dumps(result5, indent=2, ensure_ascii=False))
    print()

    # Validation checks
    print("🔍 Validation Results:")

    # Check if real knowledge was injected
    checks = [
        ("Test 1 - Real knowledge detected", "RAGAS" in result1.get('additionalContext', '') or "evaluation" in result1.get('additionalContext', '')),
        ("Test 2 - PostgreSQL knowledge detected", "postgres" in result2.get('additionalContext', '').lower() or "pgvector" in result2.get('additionalContext', '').lower()),
        ("Test 3 - Hybrid search knowledge detected", "bm25" in result3.get('additionalContext', '').lower() or "vector" in result3.get('additionalContext', '').lower()),
        ("Test 4 - Non-Task correctly skipped", result4.get('continue') == True and 'additionalContext' not in result4),
        ("Test 5 - No subagent correctly skipped", result5.get('continue') == True and 'additionalContext' not in result5)
    ]

    for description, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {description}")

    # Summary
    passed_count = sum(1 for _, passed in checks if passed)
    total_count = len(checks)

    print()
    print(f"🎯 Summary: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("🎉 All tests passed! Python hook is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the knowledge base files and hook logic.")

    return passed_count == total_count


if __name__ == "__main__":
    success = test_python_hook()
    sys.exit(0 if success else 1)