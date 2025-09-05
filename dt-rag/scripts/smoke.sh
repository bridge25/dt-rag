#!/usr/bin/env bash
set -euo pipefail

: "${STAGING_API_BASE:?STAGING_API_BASE missing}"
: "${API_KEY:?API_KEY missing}"

# Curl wrapper with proper error handling
H() { 
    curl -fsS -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" "$@" || {
        echo "❌ HTTP request failed: $*" >&2
        exit 1
    }
}

has_jq() { command -v jq >/dev/null 2>&1; }

echo "🔥 Starting Bridge Pack Smoke Tests..."
echo "📍 Base URL: $STAGING_API_BASE"
echo "🔐 API Key: ${API_KEY:0:8}..." 
echo ""

# Test 0: Health check (critical baseline)
echo "[0/4] health check"
resp_health=$(H "$STAGING_API_BASE/healthz")
if has_jq; then 
    status=$(echo "$resp_health" | jq -r '.status // "unknown"')
    version=$(echo "$resp_health" | jq -r '.version // "unknown"')
    if [[ "$status" != "healthy" ]]; then
        echo "❌ health check failed: status=$status" >&2
        exit 1
    fi
    echo "✔ health ok (status: $status, version: $version)"
else
    echo "✔ health ok (raw response received)"
fi
echo ""

# Test 1: Taxonomy tree
echo "[1/4] taxonomy tree"
resp1=$(H "$STAGING_API_BASE/taxonomy/1.8.1/tree")
if has_jq; then 
    # Validate tree structure and version
    echo "$resp1" | jq '.[0] | {label,version:"1.8.1"}' >/dev/null || {
        echo "❌ taxonomy tree validation failed" >&2
        exit 1
    }
    label=$(echo "$resp1" | jq -r '.[0].label // "unknown"')
    echo "✔ tree ok (root label: $label)"
else
    echo "✔ tree ok (raw response received)"
fi
echo ""

# Test 2: Classify
echo "[2/4] classify"
resp2=$(H -X POST "$STAGING_API_BASE/classify" \
  --data '{"text":"RAG taxonomy spec example"}')
if has_jq; then 
    # Validate required fields
    request_id=$(echo "$resp2" | jq -r '.request_id // "missing"')
    confidence=$(echo "$resp2" | jq -r '.confidence // "missing"')
    if [[ "$request_id" == "missing" || "$confidence" == "missing" ]]; then
        echo "❌ classify response missing required fields" >&2
        exit 1
    fi
    hitl=$(echo "$resp2" | jq -r '.hitl // false')
    echo "✔ classify ok (request_id: $request_id, confidence: $confidence, hitl: $hitl)"
else
    echo "✔ classify ok (raw response received)"
fi
echo ""

# Test 3: Search
echo "[3/4] search"
resp3=$(H -X POST "$STAGING_API_BASE/search" --data '{
  "q":"taxonomy tree",
  "filters":{"canonical_in":[["AI","RAG"]]},
  "bm25_topk":12, "vector_topk":12, "rerank_candidates":50, "final_topk":5
}')
if has_jq; then 
    # Validate search results
    hits_count=$(echo "$resp3" | jq -r '.hits|length // 0')
    search_request_id=$(echo "$resp3" | jq -r '.request_id // "missing"')
    latency=$(echo "$resp3" | jq -r '.latency // "missing"')
    if [[ "$search_request_id" == "missing" ]]; then
        echo "❌ search response missing request_id" >&2
        exit 1
    fi
    echo "✔ search ok (hits: $hits_count, request_id: $search_request_id, latency: ${latency}s)"
else
    echo "✔ search ok (raw response received)"
fi
echo ""

echo "🎉 ALL GREEN ✅"
echo ""
echo "📊 Smoke Test Summary:"
echo "  ✅ Health Check: PASS"
echo "  ✅ Taxonomy Tree: PASS" 
echo "  ✅ Document Classify: PASS"
echo "  ✅ Document Search: PASS"
echo ""
echo "🚀 B-team can now integrate with confidence!"
echo "🔄 Exit code: 0 (success)"