"""
Test RAG Answer Generation with Gemini LLM

Tests the /answer endpoint with Korean and English questions.
"""

import requests
import json

API_KEY = "7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y"
BASE_URL = "http://localhost:8001"

def test_answer_generation():
    """Test LLM answer generation"""

    print("Testing RAG Answer Generation with Gemini 2.5 Flash")
    print("=" * 70)

    # Test cases: Korean and English questions
    test_cases = [
        {
            "question": "RAG가 뭐야?",
            "mode": "answer",
            "description": "Korean question about RAG (should get Korean answer)"
        },
        {
            "question": "What is RAG?",
            "mode": "answer",
            "description": "English question about RAG"
        },
        {
            "question": "벡터 임베딩에 대해 요약해줘",
            "mode": "summary",
            "description": "Korean question requesting summary"
        },
        {
            "question": "What are the key features of this system?",
            "mode": "keypoints",
            "description": "English question requesting key points"
        }
    ]

    for idx, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {idx}: {test['description']}")
        print(f"Question: {test['question']}")
        print(f"Mode: {test['mode']}")
        print("-" * 70)

        try:
            response = requests.post(
                f"{BASE_URL}/answer",
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": API_KEY
                },
                json={
                    "q": test["question"],
                    "mode": test["mode"],
                    "final_topk": 3
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()

                print(f"[OK] Status: {response.status_code}")
                print(f"\n[ANSWER]")
                print(result["answer"])
                print(f"\n[METADATA]")
                print(f"  - Language: {result['language']}")
                print(f"  - Model: {result['model']}")
                print(f"  - Sources: {result['source_count']}")
                print(f"  - Search time: {result['search_time']:.2f}s")
                print(f"  - Generation time: {result['generation_time']:.2f}s")
                print(f"  - Total time: {result['total_time']:.2f}s")

                if result['source_count'] > 0:
                    print(f"\n[TOP SOURCE]")
                    print(f"  - {result['sources'][0].get('title', 'Unknown')}")
                    print(f"  - Score: {result['sources'][0].get('hybrid_score', 0):.3f}")

            else:
                print(f"[ERROR] Status: {response.status_code}")
                print(f"Error: {response.text}")

        except requests.exceptions.Timeout:
            print("[ERROR] Request timeout (>60s)")
        except Exception as e:
            print(f"[ERROR] {e}")

    print(f"\n{'='*70}")
    print("[COMPLETE] Answer Generation Test Complete")


if __name__ == "__main__":
    test_answer_generation()
