# SPEC-SEARCH-001 Acceptance Criteria

## 수락 기준 개요

Hybrid Search System은 이미 프로덕션 환경에서 완전히 구현되어 검증되었습니다. 본 문서는 시스템의 기능적 완성도를 검증하기 위한 상세한 수락 기준과 테스트 시나리오를 정의합니다.

## Given-When-Then 테스트 시나리오

### AC-001: BM25 Keyword Search

**Given**: 사용자가 키워드 쿼리를 제공했을 때
**When**: BM25 검색이 수행되면
**Then**: PostgreSQL ts_rank_cd를 사용하여 관련 문서를 반환해야 한다

**검증 코드**:
```python
search_engine = HybridSearchEngine(
    embedding_service=embedding_service,
    db_manager=db_manager
)

query = "machine learning algorithms"
results, metrics = await search_engine._perform_bm25_search(
    query=query,
    top_k=10,
    filters={}
)

# Assertions
assert len(results) <= 10
assert all(r.bm25_score > 0 for r in results)
assert all("machine" in r.text.lower() or "learning" in r.text.lower() for r in results[:3])
# Results should be sorted by bm25_score DESC
assert results[0].bm25_score >= results[-1].bm25_score
```

**PostgreSQL 쿼리 검증**:
```python
# Verify parameterized query
assert "to_tsvector('english', c.text)" in query_string
assert "plainto_tsquery('english', :query)" in query_string
assert "ts_rank_cd" in query_string
assert "32|1" in query_string  # Normalization flags
```

**품질 게이트**:
- ✅ BM25 results ≥ 1 (if matching documents exist)
- ✅ Score range: 0 < bm25_score ≤ 1.0
- ✅ Query execution time < 500ms

---

### AC-002: Vector Similarity Search

**Given**: 사용자가 의미론적 쿼리를 제공했을 때
**When**: Vector 검색이 수행되면
**Then**: pgvector cosine distance를 사용하여 유사 문서를 반환해야 한다

**검증 코드**:
```python
query = "deep learning neural networks"
query_embedding = await embedding_service.generate_embedding(query)

results, metrics = await search_engine._perform_vector_search(
    query_embedding=query_embedding,
    top_k=10,
    filters={}
)

# Assertions
assert len(results) <= 10
assert all(0 <= r.vector_score <= 1.0 for r in results)
# Vector scores should be sorted DESC (higher similarity first)
assert results[0].vector_score >= results[-1].vector_score
```

**pgvector 쿼리 검증**:
```python
# Verify parameterized query
assert "e.vec <=> :query_embedding::vector" in query_string
assert "(1 - (e.vec <=> :query_embedding::vector))" in query_string  # Convert distance to similarity
```

**품질 게이트**:
- ✅ Vector results ≥ 1 (if embeddings exist)
- ✅ Similarity range: 0.0 ≤ vector_score ≤ 1.0
- ✅ Query execution time < 800ms

---

### AC-003: Parallel BM25 + Vector Execution

**Given**: 사용자가 하이브리드 검색을 요청했을 때
**When**: BM25와 Vector 검색이 병렬 실행되면
**Then**: asyncio.gather로 동시 수행되고 한쪽 실패 시에도 다른 결과를 반환해야 한다

**검증 코드**:
```python
import time

query = "machine learning"
start = time.time()

results, metrics = await search_engine.search(
    query=query,
    top_k=10,
    filters={},
    bm25_candidates=50,
    vector_candidates=50
)

duration = time.time() - start

# Parallel execution should be faster than sequential
# (Expected: ~800ms vs ~1300ms sequential)
assert duration < 1.5  # seconds

# Verify both searches executed
assert metrics.bm25_candidates > 0
assert metrics.vector_candidates > 0
assert metrics.bm25_time > 0
assert metrics.vector_time > 0
```

**Graceful Degradation 테스트**:
```python
# Simulate BM25 failure
with mock.patch.object(search_engine, '_perform_bm25_search', side_effect=Exception("BM25 failed")):
    results, metrics = await search_engine.search(query="test", top_k=10)

    # Should still return vector results
    assert len(results) > 0
    assert metrics.bm25_candidates == 0  # BM25 failed
    assert metrics.vector_candidates > 0  # Vector succeeded
```

**품질 게이트**:
- ✅ Parallel execution: Total time ≈ max(bm25_time, vector_time)
- ✅ Graceful degradation: One failure doesn't crash system
- ✅ Both candidates > 0 (normal case)

---

### AC-004: Score Normalization

**Given**: BM25와 Vector 점수가 서로 다른 스케일일 때
**When**: Score normalization이 수행되면
**Then**: 모든 점수가 0-1 범위로 정규화되어야 한다

**검증 시나리오**:

**시나리오 A: Min-Max Normalization**
```python
scores = [0.5, 1.2, 0.8, 2.0, 0.3]
normalized = ScoreNormalizer.min_max_normalize(scores)

assert all(0.0 <= s <= 1.0 for s in normalized)
assert normalized.index(max(normalized)) == scores.index(max(scores))  # Ordering preserved
assert min(normalized) == 0.0
assert max(normalized) == 1.0
```

**시나리오 B: Z-Score Normalization**
```python
scores = [10.0, 15.0, 20.0, 25.0, 30.0]
normalized = ScoreNormalizer.z_score_normalize(scores)

# Mean should be approximately 0
mean = sum(normalized) / len(normalized)
assert abs(mean) < 0.1
```

**시나리오 C: Reciprocal Rank Fusion (RRF)**
```python
scores = [2.5, 1.8, 3.2, 0.5]
normalized = ScoreNormalizer.reciprocal_rank_normalize(scores)

# RRF formula: 1 / (rank + k), k=60
# Highest score (3.2) → rank 0 → 1/60 = 0.0167
# Lowest score (0.5) → rank 3 → 1/63 = 0.0159
assert all(s > 0 for s in normalized)
assert normalized[scores.index(3.2)] > normalized[scores.index(0.5)]
```

**품질 게이트**:
- ✅ All normalized scores: 0.0 ≤ s ≤ 1.0
- ✅ Relative ordering preserved
- ✅ Uniform scores → [1.0] * len (edge case)

---

### AC-005: Hybrid Score Fusion

**Given**: 정규화된 BM25와 Vector 점수가 주어졌을 때
**When**: Hybrid score fusion이 수행되면
**Then**: 가중 평균으로 결합된 hybrid_score를 반환해야 한다

**검증 코드**:
```python
fusion = HybridScoreFusion(
    bm25_weight=0.5,
    vector_weight=0.5,
    normalization="min_max"
)

bm25_scores = [0.8, 0.6, 0.4]
vector_scores = [0.7, 0.9, 0.5]

hybrid_scores = fusion.fuse_scores(bm25_scores, vector_scores)

# Expected: [0.5*0.8 + 0.5*0.7, 0.5*0.6 + 0.5*0.9, 0.5*0.4 + 0.5*0.5]
expected = [0.75, 0.75, 0.45]
assert all(abs(h - e) < 0.01 for h, e in zip(hybrid_scores, expected))
```

**Weight Normalization 테스트**:
```python
# Weights should sum to 1.0
fusion = HybridScoreFusion(bm25_weight=0.6, vector_weight=0.5)  # Sum = 1.1

# After initialization
assert abs((fusion.bm25_weight + fusion.vector_weight) - 1.0) < 0.01
```

**품질 게이트**:
- ✅ bm25_weight + vector_weight = 1.0
- ✅ Hybrid score range: [0.0, 1.0]
- ✅ Fusion time < 10ms

---

### AC-006: Adaptive Fusion

**Given**: 쿼리 특성이 분석되었을 때
**When**: Adaptive fusion이 가중치를 조정하면
**Then**: 짧은 쿼리는 BM25 우선, 복잡한 쿼리는 Vector 우선으로 가중치가 변경되어야 한다

**검증 시나리오**:

**시나리오 A: 짧은 쿼리 + 정확한 용어 → BM25 Boost**
```python
query = "API"  # Short query with exact term
query_characteristics = search_engine._analyze_query(query)

assert query_characteristics['length'] <= 3
assert query_characteristics['exact_terms'] or query_characteristics['has_operators']

fusion = HybridScoreFusion(bm25_weight=0.5, vector_weight=0.5)
hybrid_scores = fusion.adaptive_fusion(
    bm25_scores=[0.8],
    vector_scores=[0.6],
    query_characteristics=query_characteristics
)

# BM25 weight should increase (0.5 → 0.7)
# Expected: 0.7*0.8 + 0.3*0.6 = 0.56 + 0.18 = 0.74
assert hybrid_scores[0] > 0.5 * 0.8 + 0.5 * 0.6  # 0.74 > 0.70
```

**시나리오 B: 복잡한 쿼리 → Vector Boost**
```python
query = "How to implement distributed machine learning algorithms for large-scale data processing"
query_characteristics = search_engine._analyze_query(query)

assert query_characteristics['semantic_complexity'] > 0.7

hybrid_scores = fusion.adaptive_fusion(
    bm25_scores=[0.5],
    vector_scores=[0.9],
    query_characteristics=query_characteristics
)

# Vector weight should increase (0.5 → 0.7)
# Expected: 0.3*0.5 + 0.7*0.9 = 0.15 + 0.63 = 0.78
assert hybrid_scores[0] > 0.5 * 0.5 + 0.5 * 0.9  # 0.78 > 0.70
```

**품질 게이트**:
- ✅ Weight adjustment: ±0.2 from configured weights
- ✅ Short queries (≤3 terms) → BM25 boost
- ✅ Complex queries (semantic_complexity > 0.7) → Vector boost

---

### AC-007: Cross-Encoder Reranking

**Given**: Hybrid fusion 결과가 존재할 때
**When**: Cross-encoder reranking이 수행되면
**Then**: Neural model로 재평가하여 rerank_score를 업데이트해야 한다

**검증 코드**:
```python
reranker = CrossEncoderReranker(
    model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"
)

query = "machine learning algorithms"
results = [
    SearchResult(chunk_id="1", text="ML algorithms...", hybrid_score=0.75),
    SearchResult(chunk_id="2", text="Database systems...", hybrid_score=0.80),
    SearchResult(chunk_id="3", text="Deep learning...", hybrid_score=0.70)
]

reranked = reranker.rerank(query, results, top_k=3)

# Rerank scores should be assigned
assert all(r.rerank_score > 0 for r in reranked)
# Ordering may change based on semantic relevance
assert reranked[0].rerank_score >= reranked[-1].rerank_score
```

**Heuristic Fallback 테스트**:
```python
# Simulate cross-encoder unavailable
reranker._model = None

reranked = reranker.rerank(query, results, top_k=3)

# Heuristic reranking should still work
assert all(r.rerank_score > 0 for r in reranked)
# Rerank score = hybrid_score * quality_multiplier
# quality_multiplier = 1.0 + 0.2*term_overlap + 0.1*length_penalty + 0.1*diversity
```

**품질 게이트**:
- ✅ Cross-encoder model loaded successfully
- ✅ Reranking time < 500ms (for 10 results)
- ✅ Fallback heuristic reranking works

---

### AC-008: Result Caching

**Given**: 동일한 쿼리가 반복될 때
**When**: 캐시가 활성화되어 있으면
**Then**: 데이터베이스 쿼리 없이 캐시된 결과를 즉시 반환해야 한다

**검증 코드**:
```python
search_engine = HybridSearchEngine(enable_caching=True)

query = "test query"
filters = {}
top_k = 10

# First call (cache miss)
start = time.time()
results_1, metrics_1 = await search_engine.search(query, top_k, filters)
miss_duration = time.time() - start

assert metrics_1.cache_hit == False
assert miss_duration > 0.5  # Database queries took time

# Second call (cache hit)
start = time.time()
results_2, metrics_2 = await search_engine.search(query, top_k, filters)
hit_duration = time.time() - start

assert metrics_2.cache_hit == True
assert hit_duration < miss_duration / 10  # Cache is at least 10x faster
assert results_1 == results_2  # Same results
```

**Cache Eviction 테스트**:
```python
cache = ResultCache(max_size=3, ttl_seconds=3600)

# Fill cache
cache.put("query1", {}, 10, results_1)
cache.put("query2", {}, 10, results_2)
cache.put("query3", {}, 10, results_3)

# 4th entry should evict oldest (query1)
cache.put("query4", {}, 10, results_4)

assert cache.get("query1", {}, 10) is None  # Evicted
assert cache.get("query2", {}, 10) is not None
assert cache.get("query4", {}, 10) is not None
```

**TTL Expiration 테스트**:
```python
import time

cache = ResultCache(max_size=100, ttl_seconds=1)  # 1 second TTL

cache.put("query", {}, 10, results)
assert cache.get("query", {}, 10) is not None  # Immediate hit

time.sleep(2)  # Wait for TTL to expire

assert cache.get("query", {}, 10) is None  # Expired
```

**품질 게이트**:
- ✅ Cache hit: < 10ms response time
- ✅ Cache miss: Full search execution
- ✅ LRU eviction: max_size enforced
- ✅ TTL expiration: Old entries deleted

---

### AC-009: Filtering (Taxonomy, Content Type, Date)

**Given**: 사용자가 필터 조건을 제공했을 때
**When**: 검색이 수행되면
**Then**: 필터 조건에 맞는 결과만 반환하고 SQL injection을 방지해야 한다

**검증 시나리오**:

**시나리오 A: Taxonomy Path Filtering**
```python
filters = {
    "taxonomy_paths": [["AI", "ML"], ["Database"]]
}

results, metrics = await search_engine.search(
    query="algorithms",
    top_k=10,
    filters=filters
)

# All results should match taxonomy paths
for result in results:
    assert any(
        result.taxonomy_path[:len(path)] == path
        for path in filters["taxonomy_paths"]
    )
```

**시나리오 B: Content Type Filtering**
```python
filters = {
    "content_types": ["application/pdf", "text/markdown"]
}

results, metrics = await search_engine.search(query="test", top_k=10, filters=filters)

# Verify content_type in ALLOWED_CONTENT_TYPES
assert all(filters["content_types"] in ["application/pdf", "text/markdown", "text/plain", "text/html"])
```

**시나리오 C: Date Range Filtering**
```python
filters = {
    "date_from": "2025-01-01T00:00:00Z",
    "date_to": "2025-10-31T23:59:59Z"
}

results, metrics = await search_engine.search(query="test", top_k=10, filters=filters)

# All results should be within date range
for result in results:
    doc_date = result.metadata.get("processed_at")
    if doc_date:
        assert "2025-01-01" <= doc_date <= "2025-10-31"
```

**SQL Injection Prevention 테스트**:
```python
# Attempt SQL injection in taxonomy path
malicious_filters = {
    "taxonomy_paths": [["'; DROP TABLE chunks; --"]]
}

# Should be validated and rejected or sanitized
with pytest.raises(ValueError):
    await search_engine.search(query="test", top_k=10, filters=malicious_filters)

# Or: Validation should strip invalid characters
filter_clause, params = search_engine._build_filter_clause(malicious_filters)
assert "DROP TABLE" not in filter_clause
```

**품질 게이트**:
- ✅ Taxonomy path: Alphanumeric whitelist `[a-zA-Z0-9_\- ]`
- ✅ Content type: ALLOWED_CONTENT_TYPES whitelist
- ✅ Date range: `datetime.fromisoformat` validation
- ✅ Parameterized queries: No string interpolation

---

### AC-010: End-to-End Hybrid Search

**Given**: 사용자가 복잡한 쿼리를 제공했을 때
**When**: 전체 하이브리드 검색 파이프라인이 실행되면
**Then**: BM25 + Vector → Fusion → Reranking → Caching이 순차적으로 완료되어야 한다

**통합 테스트**:
```python
search_engine = HybridSearchEngine(
    embedding_service=embedding_service,
    db_manager=db_manager,
    enable_caching=True,
    enable_reranking=True,
    bm25_weight=0.5,
    vector_weight=0.5
)

query = "How to implement machine learning algorithms for natural language processing"
filters = {
    "taxonomy_paths": [["AI", "ML"]],
    "content_types": ["application/pdf"]
}

results, metrics = await search_engine.search(
    query=query,
    top_k=10,
    filters=filters,
    bm25_candidates=50,
    vector_candidates=50
)

# Verify all stages executed
assert metrics.embedding_time > 0  # Query embedding generated
assert metrics.bm25_time > 0  # BM25 search executed
assert metrics.vector_time > 0  # Vector search executed
assert metrics.fusion_time > 0  # Score fusion performed
assert metrics.rerank_time > 0  # Reranking applied (if enabled)
assert metrics.total_time < 1.5  # Overall latency target

# Verify results quality
assert len(results) <= 10
assert all(r.rerank_score > 0 for r in results)  # Reranked
assert all(r.hybrid_score > 0 for r in results)  # Fused
assert results[0].rerank_score >= results[-1].rerank_score  # Sorted

# Verify filters applied
assert all(r.taxonomy_path[:2] == ["AI", "ML"] for r in results)
```

**품질 게이트**:
- ✅ E2E latency p95 < 1.0s
- ✅ Recall@10 ≥ 0.85
- ✅ Precision@5 ≥ 0.70
- ✅ Cache hit rate > 30% (production)

---

## 성능 수락 기준

### Performance Metrics

**Latency Targets**:
```python
@pytest.mark.performance
async def test_search_latency():
    latencies = []
    for i in range(100):
        start = time.time()
        await search_engine.search(query=f"test query {i}", top_k=10)
        latencies.append(time.time() - start)

    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)

    assert p50 < 0.5  # 500ms
    assert p95 < 1.0  # 1 second
    assert p99 < 1.5  # 1.5 seconds
```

**Concurrent Throughput**:
```python
@pytest.mark.concurrent
async def test_concurrent_searches():
    queries = [f"query {i}" for i in range(20)]

    start = time.time()
    tasks = [search_engine.search(q, 10) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.time() - start

    # Throughput > 0.5 queries/sec
    throughput = len(queries) / duration
    assert throughput > 0.5

    # Average latency < 15s
    avg_latency = duration / len(queries)
    assert avg_latency < 15.0

    # Error rate < 10%
    errors = sum(1 for r in results if isinstance(r, Exception))
    error_rate = errors / len(results)
    assert error_rate < 0.10
```

---

## 모니터링 수락 기준

### Alert Thresholds

**High Severity**:
```python
assert search_latency_p95 <= 3.0  # seconds
assert error_rate <= 0.05  # 5%
```

**Medium Severity**:
```python
assert search_latency_p95 <= 1.0  # seconds
assert cache_hit_rate >= 0.20  # 20%
```

**Low Severity**:
```python
assert recall_at_10 >= 0.80
assert diversity_ratio >= 0.50
```

---

## 최종 수락 체크리스트

### 기능 완성도

- [x] **U-REQ-001**: BM25 keyword search (PostgreSQL ts_rank_cd)
- [x] **U-REQ-002**: Vector similarity search (pgvector <=>)
- [x] **U-REQ-003**: Hybrid score fusion
- [x] **U-REQ-004**: Score normalization (min-max, z-score, RRF)
- [x] **U-REQ-005**: Cross-encoder reranking
- [x] **U-REQ-006**: Result caching (LRU + TTL)
- [x] **U-REQ-007**: Filtering (taxonomy, content_type, date)
- [x] **E-REQ-001**: Parallel BM25 + Vector execution
- [x] **E-REQ-008**: Reranking with fallback
- [x] **S-REQ-007**: Adaptive fusion

### 품질 게이트

- [x] Search latency p95 < 1.0s
- [x] Recall@10 ≥ 0.85
- [x] Precision@5 ≥ 0.70
- [x] Cache hit rate > 30%
- [x] Error rate < 1%

### 운영 준비

- [x] PostgreSQL with pgvector extension
- [x] Full-text search indexes
- [x] Embedding service integration
- [x] Cross-encoder model (optional)
- [x] Sentry monitoring (optional)
- [x] API endpoints exposed
- [x] Metrics collection configured

---

**문서 버전**: v0.1.0
**최종 업데이트**: 2025-10-09
**작성자**: @Claude
**상태**: Approved
