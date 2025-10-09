#!/usr/bin/env python3
"""
Simple embedding service test - ASCII only
"""
# @TEST:EMBED-001 | SPEC: .moai/specs/SPEC-EMBED-001/spec.md

import asyncio
import sys
import os

# Add module path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

async def test_embeddings():
    """Test embedding service"""
    try:
        from embedding_service import (
            generate_embedding,
            get_service_info,
            health_check
        )

        print("Embedding Service Test")
        print("=" * 40)

        # 1. Health check
        print("\n1. Health check")
        health = health_check()
        print(f"   Status: {health.get('status')}")

        # 2. Service info
        print("\n2. Service info")
        info = get_service_info()
        print(f"   Model: {info.get('model_name')}")
        print(f"   Dimensions: {info.get('target_dimensions')}")
        print(f"   Transformers available: {info.get('sentence_transformers_available')}")

        # 3. Generate embedding
        print("\n3. Generate embedding")
        test_text = "This is a test text for embedding generation"

        embedding = await generate_embedding(test_text)
        print(f"   Text: {test_text}")
        print(f"   Embedding dimensions: {len(embedding)}")
        print(f"   First 3 values: {embedding[:3]}")

        print("\nTest completed successfully!")
        return True

    except ImportError as e:
        print(f"Import error: {e}")
        print("Install required packages:")
        print("  pip install sentence-transformers torch")
        return False
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_embeddings())
    if success:
        print("\nNext steps:")
        print("1. Start FastAPI server: python apps/api/main.py")
        print("2. Test API: curl http://localhost:8000/api/v1/embeddings/health")
    sys.exit(0 if success else 1)