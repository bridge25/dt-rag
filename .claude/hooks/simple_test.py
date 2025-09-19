#!/usr/bin/env python3
"""Simple test for Python Knowledge Base injection hook"""

import os
import json
import sys
from pathlib import Path

def simple_test():
    """Simple test of the Python knowledge injection hook"""

    # Test with RAG evaluation specialist
    test_input = {
        "tool_name": "Task",
        "tool_input": {
            "subagent_type": "rag-evaluation-specialist",
            "prompt": "Evaluate the RAG system using RAGAS v2.0 metrics",
            "description": "RAG evaluation task"
        }
    }

    os.environ['CLAUDE_TOOL_INPUT'] = json.dumps(test_input)

    # Import and run the hook
    sys.path.insert(0, str(Path(__file__).parent))

    try:
        from knowledge_injector import KnowledgeInjector

        injector = KnowledgeInjector()
        result = injector.run()

        print("Hook Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Simple validation
        if 'additionalContext' in result:
            context = result['additionalContext']
            if 'RAGAS' in context or 'evaluation' in context:
                print("\nVALIDATION: PASS - Real knowledge detected!")
                return True
            else:
                print("\nVALIDATION: FAIL - Generic response")
                return False
        else:
            print("\nVALIDATION: FAIL - No context injected")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = simple_test()
    if success:
        print("\nPython hook test: SUCCESS")
    else:
        print("\nPython hook test: FAILED")
    sys.exit(0 if success else 1)