#!/usr/bin/env bash
set -euo pipefail

: "${STAGING_API_BASE:?STAGING_API_BASE missing}"
: "${API_KEY:?API_KEY missing}"

H() { curl -fsS -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" "$@"; }
has_jq() { command -v jq >/dev/null 2>&1; }

echo "🔥 Starting Bridge Pack Smoke Tests..."
echo "📍 Base URL: $STAGING_API_BASE"
echo ""

echo "[1/4] health check"
resp_health=$(H "$STAGING_API_BASE/healthz")
if has_jq; then 
    echo "$resp_health" | jq '.status,.version' >/dev/null
    status=$(echo "$resp_health" | jq -r '.status')
    version=$(echo "$resp_health" | jq -r '.version')
    echo "✔ health ok (status: $status, version: $version)"
else
    echo "✔ health ok (raw response received)"
fi
echo ""

echo "[2/4] taxonomy tree"
resp1=$(H "$STAGING_API_BASE/taxonomy/1.8.1/tree")
if has_jq; then 
    echo "$resp1" | jq '.[0] | {label,version:"1.8.1"}' >/dev/null
    label=$(echo "$resp1" | jq -r '.[0].label')
    echo "✔ tree ok (root label: $label)"
else
    echo "✔ tree ok (raw response received)"
fi
echo ""

echo "[3/4] classify"
resp2=$(H -X POST "$STAGING_API_BASE/classify" \
  --data '{"text":"RAG taxonomy spec example"}')
if has_jq; then 
    echo "$resp2" | jq '.request_id,.confidence' >/dev/null
    request_id=$(echo "$resp2" | jq -r '.request_id')
    confidence=$(echo "$resp2" | jq -r '.confidence')
    hitl=$(echo "$resp2" | jq -r '.hitl')
    echo "✔ classify ok (request_id: $request_id, confidence: $confidence, hitl: $hitl)"
else
    echo "✔ classify ok (raw response received)"
fi
echo ""

echo "[4/4] search"
resp3=$(H -X POST "$STAGING_API_BASE/search" --data '{
  "q":"taxonomy tree",
  "filters":{"canonical_in":[["AI","RAG"]]},
  "bm25_topk":12, "vector_topk":12, "rerank_candidates":50, "final_topk":5
}')
if has_jq; then 
    echo "$resp3" | jq '.hits|length,.request_id' >/dev/null
    hits_count=$(echo "$resp3" | jq -r '.hits|length')
    search_request_id=$(echo "$resp3" | jq -r '.request_id')
    latency=$(echo "$resp3" | jq -r '.latency')
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