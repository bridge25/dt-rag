# ACCESS CARD — Staging

## 📍 Environment Configuration

### 🏠 Local Development
- **BASE URL**: `http://localhost:8000`
- **Use Case**: Local development and testing
- **Setup**:
  ```bash
  export STAGING_API_BASE=http://localhost:8000
  export API_KEY=***   # ❗️키는 커밋 금지, 별도 채널로 배포
  ```

### 🌐 Remote Staging  
- **BASE URL**: `https://api.staging.example.com` 
- **Use Case**: Remote integration and CI/CD
- **Setup**: Use Repository Variables and Secrets
  ```bash
  export STAGING_API_BASE="${{ vars.STAGING_API_BASE }}"    # Repository Variable
  export API_KEY="${{ secrets.STAGING_API_KEY }}"          # Repository Secret
  ```
- **GitHub Settings**: 
  - Variable: `STAGING_API_BASE` = `https://api.staging.example.com`
  - Secret: `STAGING_API_KEY` = `<actual_api_key>`

## 📋 Common Specifications
- **SPEC**: OpenAPI v1.8.1 · Schemas 0.1.3  
- **Health**: `GET /healthz` → 200
- **Auth**: Header `X-API-Key: <PROVIDED_OUT_OF_BAND>`
- **Timeouts**: 10s
- **Rate limits**: 10 r/s (per-user), 100 r/s (per-IP)
- **Required headers**: `Content-Type: application/json`

### API Endpoints

#### 1. Health Check
```bash
curl -X GET "${STAGING_API_BASE}/healthz" \
  -H "X-API-Key: ${API_KEY}"
```

#### 2. Taxonomy Tree
```bash
curl -X GET "${STAGING_API_BASE}/taxonomy/1.8.1/tree" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json"
```

#### 3. Classify Document
```bash
curl -X POST "${STAGING_API_BASE}/classify" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text":"RAG taxonomy spec example"}'
```

#### 4. Search Documents
```bash
curl -X POST "${STAGING_API_BASE}/search" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "q":"taxonomy tree",
    "filters":{"canonical_in":[["AI","RAG"]]},
    "bm25_topk":12, "vector_topk":12, "rerank_candidates":50, "final_topk":5
  }'
```

### Expected Responses

#### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2025-09-05T14:45:00Z",
  "version": "1.8.1"
}
```

#### Classify Response
```json
{
  "canonical": ["AI", "RAG"],
  "candidates": [
    {
      "node_id": "ai_rag_001",
      "label": "RAG Systems",
      "canonical_path": ["AI", "RAG"],
      "version": "1.8.1",
      "confidence": 0.85
    }
  ],
  "hitl": false,
  "confidence": 0.85,
  "reasoning": ["High confidence match for RAG taxonomy", "Clear AI domain classification"],
  "request_id": "req_12345"
}
```

#### Search Response
```json
{
  "hits": [
    {
      "chunk_id": "chunk_001",
      "score": 0.95,
      "text": "RAG taxonomy specification...",
      "taxonomy_path": ["AI", "RAG"]
    }
  ],
  "latency": 0.25,
  "request_id": "search_12345",
  "total_candidates": 50,
  "sources_count": 1,
  "taxonomy_version": "1.8.1"
}
```

### Troubleshooting

#### Common Issues
1. **401 Unauthorized**: Check API_KEY is set correctly
2. **429 Rate Limit**: Wait and retry, respect rate limits
3. **404 Not Found**: Verify BASE URL and endpoint paths
4. **Timeout**: Check network connectivity and server status

#### Debug Mode
Add `-v` flag to curl commands for verbose output:
```bash
curl -v -X GET "${STAGING_API_BASE}/healthz" \
  -H "X-API-Key: ${API_KEY}"
```

## How to set env

### Environment Variables Setup

**Required Environment Variables:**
- `STAGING_API_BASE`: The base URL for the staging API
- `API_KEY`: Authentication key for API access

**For Local Development:**
```bash
export STAGING_API_BASE=http://localhost:8000
export API_KEY=your_local_api_key_here
```

**For CI/CD (GitHub Actions):**
```bash
export STAGING_API_BASE="${{ vars.STAGING_API_BASE }}"
export API_KEY="${{ secrets.STAGING_API_KEY }}"
```

**For Docker Environment:**
```bash
docker run -e STAGING_API_BASE=http://localhost:8000 -e API_KEY=your_key your_image
```

**Verification:**
```bash
echo "API Base: $STAGING_API_BASE"
echo "API Key: ${API_KEY:0:8}..." # Show only first 8 characters
```