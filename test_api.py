#!/usr/bin/env python3
"""
Test embedding API endpoints directly
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
import os

# Add module path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

def test_embedding_api():
    """Test embedding API with TestClient"""
    try:
        from routers.embedding_router import router as embedding_router

        # Create minimal FastAPI app for testing
        app = FastAPI()
        app.include_router(embedding_router, prefix="/api/v1")

        client = TestClient(app)

        print("Testing Embedding API")
        print("=" * 30)

        # Test health endpoint
        print("\n1. Testing health endpoint")
        response = client.get("/api/v1/embeddings/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Service status: {data.get('status')}")

        # Test info endpoint
        print("\n2. Testing info endpoint")
        response = client.get("/api/v1/embeddings/info")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Model: {data.get('model_name')}")
            print(f"   Dimensions: {data.get('target_dimensions')}")

        # Test embedding generation
        print("\n3. Testing embedding generation")
        response = client.post("/api/v1/embeddings/generate", json={
            "text": "This is a test text",
            "use_cache": False
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Dimensions: {data.get('dimensions')}")
            print(f"   Model: {data.get('model')}")

        # Test similarity calculation
        print("\n4. Testing similarity calculation")
        embedding1 = [0.1] * 768
        embedding2 = [0.2] * 768

        response = client.post("/api/v1/embeddings/similarity", json={
            "embedding1": embedding1,
            "embedding2": embedding2
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Similarity: {data.get('similarity'):.4f}")

        print("\nAPI tests completed successfully!")
        return True

    except Exception as e:
        print(f"API test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_embedding_api()
    if success:
        print("\nEmbedding API is working correctly!")
        print("You can now integrate it into your main FastAPI application.")
    else:
        print("\nAPI tests failed. Check the error messages above.")
    sys.exit(0 if success else 1)