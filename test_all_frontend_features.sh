#!/bin/bash

# DT-RAG Frontend Features Test Script

echo "======================================"
echo "DT-RAG Frontend Features Test"
echo "======================================"
echo ""

ADMIN_KEY="admin_WLYyK1OiTfjKF3vdb1mXyvsDog-3jMe_MtX69_uA-ed9b"
BASE_URL="http://localhost:8000"

echo "1. Testing Health Endpoint..."
response=$(curl -s -o /dev/null -w '%{http_code}' $BASE_URL/health)
if [ "$response" == "200" ]; then
    echo "✅ Health endpoint working"
else
    echo "❌ Health endpoint failed (Status: $response)"
fi
echo ""

echo "2. Testing Monitoring Health..."
response=$(curl -s -o /dev/null -w '%{http_code}' $BASE_URL/api/v1/monitoring/health)
if [ "$response" == "200" ]; then
    echo "✅ Monitoring health working"
else
    echo "❌ Monitoring health failed (Status: $response)"
fi
echo ""

echo "3. Testing Search Endpoint..."
response=$(curl -s -o /dev/null -w '%{http_code}' \
  -X POST $BASE_URL/api/v1/search/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ADMIN_KEY" \
  -d '{"q":"test","final_topk":3}')
if [ "$response" == "200" ]; then
    echo "✅ Search endpoint working"
else
    echo "❌ Search endpoint failed (Status: $response)"
fi
echo ""

echo "4. Testing Taxonomy Tree..."
response=$(curl -s -o /dev/null -w '%{http_code}' \
  -H "X-API-Key: $ADMIN_KEY" \
  $BASE_URL/api/v1/taxonomy/latest/tree)
if [ "$response" == "200" ] || [ "$response" == "404" ]; then
    echo "✅ Taxonomy endpoint accessible (Status: $response)"
else
    echo "❌ Taxonomy endpoint failed (Status: $response)"
fi
echo ""

echo "5. Testing Document Upload (with sample file)..."
if [ -f "sample_docs/rag_overview.txt" ]; then
    response=$(curl -s -X POST $BASE_URL/ingestion/upload \
      -H "X-API-Key: $ADMIN_KEY" \
      -F "file=@sample_docs/rag_overview.txt" 2>&1 | head -c 100)

    if echo "$response" | grep -q "job_id\|document_id\|202"; then
        echo "✅ Document upload working"
    else
        echo "⚠️  Document upload response: $response"
    fi
else
    echo "⚠️  Sample file not found, skipping upload test"
fi
echo ""

echo "6. Testing Embeddings Endpoint..."
response=$(curl -s -o /dev/null -w '%{http_code}' \
  -X POST $BASE_URL/api/v1/embeddings/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ADMIN_KEY" \
  -d '{"texts":["test"]}')
if [ "$response" == "200" ]; then
    echo "✅ Embeddings endpoint working"
else
    echo "⚠️  Embeddings endpoint (Status: $response)"
fi
echo ""

echo "7. Testing Classification Endpoint..."
response=$(curl -s -o /dev/null -w '%{http_code}' \
  -X POST $BASE_URL/api/v1/classify/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ADMIN_KEY" \
  -d '{"chunk_id":"test","text":"test text"}')
if [ "$response" == "200" ]; then
    echo "✅ Classification endpoint working"
else
    echo "⚠️  Classification endpoint (Status: $response)"
fi
echo ""

echo "8. Checking Redis Connection..."
redis_errors=$(docker logs dt_rag_api --since 60s 2>&1 | grep "Connection refused" | wc -l)
if [ "$redis_errors" -eq "0" ]; then
    echo "✅ No Redis connection errors"
else
    echo "⚠️  Found $redis_errors Redis connection errors in logs"
fi
echo ""

echo "======================================"
echo "Frontend Access Information"
echo "======================================"
echo ""
echo "🌐 Frontend URL: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🔑 Admin API Key: $ADMIN_KEY"
echo ""
echo "📁 Sample documents location:"
echo "   C:\\MYCLAUDE_PROJECT\\sonheungmin\\Unmanned\\dt-rag\\sample_docs\\"
echo ""
echo "======================================"
echo "Test Complete!"
echo "======================================"
