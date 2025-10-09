import requests
import json

API_KEY = "7geU8-mQTM01zSG5pm6gLpdv4Tg25zbSk8cHm6Um62Y"
BASE_URL = "http://localhost:8001"

print("Testing Frontend Integration with Backend API\n")
print("=" * 60)

# 1. Health Check
print("\n1. Health Check")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   Error: {e}")

# 2. Search Test
print("\n2. Search Test")
try:
    response = requests.post(
        f"{BASE_URL}/search",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        json={
            "q": "What is RAG system?",
            "final_topk": 5
        }
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Found {len(data.get('hits', []))} results")
        print(f"   Latency: {data.get('latency', 0):.2f}s")
        for i, hit in enumerate(data.get('hits', [])[:3], 1):
            print(f"   {i}. Score: {hit.get('score', 0):.3f}")
            print(f"      Text: {hit.get('text', '')[:60]}...")
    else:
        print(f"   Error Response: {response.text}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 60)
print("Frontend API Integration Test Complete")
