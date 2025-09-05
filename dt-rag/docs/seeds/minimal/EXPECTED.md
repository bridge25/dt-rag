# Expected Results (Minimal Seeds)

## 📋 Test Baseline Configuration
- **Taxonomy Version**: **1.8.1** (스모크/시드 기준선)
- **OpenAPI Spec**: v1.8.1
- **Common Schemas**: v0.1.3
- **Test Environment**: Staging
- **Last Updated**: 2025-09-05

## API Endpoint Expectations

### 1. GET /taxonomy/1.8.1/tree
**Expected Response:**
- Status: 200 OK
- Format: JSON array
- Content: 배열[0]에 루트 노드 존재
- Root node must have `label` field
- **Version field: "1.8.1"** (strictly enforced)
- **Version Validation**: Smoke test will fail if version != "1.8.1"

**Example:**
```json
[
  {
    "node_id": "root",
    "label": "Root Node",
    "canonical_path": [],
    "version": "1.8.1",
    "confidence": 1.0
  }
]
```

### 2. POST /classify {"text":"RAG taxonomy spec example"}
**Expected Response:**
- Status: 200 OK
- Required fields: `request_id`, `confidence`
- `confidence` range: 0.0 ~ 1.0
- `confidence < 0.70` → HITL 큐 자동 적재 (정상 동작)
- `canonical` path should include ["AI", "RAG"] or similar
- `reasoning` array should have ≥ 2 items

**Example:**
```json
{
  "canonical": ["AI", "RAG"],
  "candidates": [...],
  "hitl": false,
  "confidence": 0.85,
  "reasoning": ["Clear RAG reference", "AI domain classification"],
  "request_id": "req_abc123"
}
```

### 3. POST /search {...}
**Expected Response:**
- Status: 200 OK
- `hits.length ≥ 1` (seed 규모 기준)
- Each hit should have: `chunk_id`, `score`, `text`
- `request_id` field present
- `latency` field > 0.0
- `taxonomy_version` should be "1.8.1"

**Example:**
```json
{
  "hits": [
    {
      "chunk_id": "chunk_001", 
      "score": 0.95,
      "text": "taxonomy tree content...",
      "taxonomy_path": ["AI", "RAG"]
    }
  ],
  "latency": 0.25,
  "request_id": "search_xyz789",
  "total_candidates": 50,
  "sources_count": 3,
  "taxonomy_version": "1.8.1"
}
```

### 4. GET /healthz
**Expected Response:**
- Status: 200 OK
- `status` field: "healthy" (exactly this value)
- **`version` field: "1.8.1"** (version consistency check)
- Response time < 1000ms
- **Health Validation**: Smoke test will fail if status != "healthy"

## Document Processing Expectations

### sample.md (Markdown)
- **Ingestion**: Should parse frontmatter and content
- **Chunking**: ~3-4 chunks (500 chars each, 128 overlap)
- **Classification**: ["AI", "RAG"] with confidence > 0.80
- **Search**: Should return high relevance for "RAG taxonomy" queries

### sample.html (HTML) 
- **Parsing**: Extract text from HTML tags, ignore markup
- **Content**: Clear RAG and taxonomy references
- **Classification**: ["AI", "RAG"] with confidence > 0.75
- **Metadata**: Should preserve title and structure info

### sample.pdf (PDF)
- **Text Extraction**: PyMuPDF should extract readable text
- **Processing**: No OCR required (text-based PDF)
- **Classification**: ["AI", "RAG"] with confidence > 0.80
- **Size**: Generated PDF should be 1-10KB

## Error Handling Expectations

### Authentication Errors
- **Missing API Key**: 401 Unauthorized
- **Invalid API Key**: 401 Unauthorized 
- **Rate Limiting**: 429 Too Many Requests

### Validation Errors
- **Malformed JSON**: 400 Bad Request
- **Missing required fields**: 422 Unprocessable Entity
- **Invalid taxonomy version**: 404 Not Found

### Server Errors
- **Service unavailable**: 503 Service Unavailable
- **Internal errors**: 500 Internal Server Error
- **Timeout**: 504 Gateway Timeout

## Performance Benchmarks

### Response Times (95th percentile)
- Health check: < 100ms
- Taxonomy tree: < 500ms  
- Single classify: < 1000ms
- Search (5 results): < 2000ms

### Throughput Limits
- 10 requests/second per user
- 100 requests/second per IP
- Burst capacity: 2x rate limit for 10 seconds

## Quality Thresholds

### Classification Confidence
- **High confidence**: ≥ 0.80 (auto-accept)
- **Medium confidence**: 0.70 - 0.79 (auto-accept with flag)
- **Low confidence**: < 0.70 (HITL queue)

### Search Relevance
- **Relevant results**: score ≥ 0.70
- **Minimum results**: ≥ 1 for basic queries
- **Maximum results**: Respects `final_topk` parameter

## Integration Success Criteria

### B-team Integration Success
- [ ] All 4 endpoints return expected status codes
- [ ] Response schemas match common-schemas
- [ ] Error handling works for auth/validation failures
- [ ] Performance meets SLA requirements
- [ ] Rate limiting enforced correctly

### Smoke Test Success  
- [ ] `smoke.sh` runs without errors
- [ ] All 4 endpoint checks pass
- [ ] JSON parsing works (if jq available)
- [ ] "ALL GREEN ✅" message displayed
- [ ] No authentication errors with valid API key