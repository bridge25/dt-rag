---
id: SEARCH-001
version: 0.1.0
status: completed
created: 2025-10-07
updated: 2025-10-08
author: reverse-engineer
priority: critical
category: feature
labels:
  - hybrid-search
  - bm25
  - vector-search
  - cross-encoder
  - score-fusion
  - caching
scope:
  packages:
    - apps/search
  files:
    - hybrid_search_engine.py
  dependencies:
    - apps/api/embedding_service.py
    - apps/api/database.py
    - apps/core/db_session.py
    - apps/api/monitoring/sentry_reporter.py
---

# @SPEC:SEARCH-001: Hybrid Search System

## HISTORY

### v0.1.0 (2025-10-07)
- **INITIAL**: Reverse-engineered from existing hybrid_search_engine.py (1,208 lines)
- **AUTHOR**: reverse-engineer
- **SCOPE**: BM25 keyword search, Vector similarity search, Cross-encoder reranking, Score normalization and fusion
- **CONTEXT**: Production environment search system completeness verification through reverse engineering
- **SOURCE**: Complete analysis of apps/search/hybrid_search_engine.py and tests/test_hybrid_search.py

## EARS Requirements

### Ubiquitous Requirements (Core Functionality)

**U-REQ-001**: System SHALL provide BM25 keyword search using PostgreSQL full-text search (ts_rank_cd).

**U-REQ-002**: System SHALL provide vector similarity search using pgvector cosine similarity operator (<=>).

**U-REQ-003**: System SHALL combine BM25 and vector search results through hybrid score fusion.

**U-REQ-004**: System SHALL normalize scores using min-max, z-score, or reciprocal rank fusion (RRF) algorithms.

**U-REQ-005**: System SHALL support cross-encoder reranking using sentence-transformers models.

**U-REQ-006**: System SHALL cache search results with configurable TTL (default: 3600s) and size (default: 1000 entries).

**U-REQ-007**: System SHALL support taxonomy path filtering, content type filtering, and date range filtering.

**U-REQ-008**: System SHALL provide keyword-only search mode (BM25 only).

**U-REQ-009**: System SHALL provide vector-only search mode (semantic similarity only).

**U-REQ-010**: System SHALL generate embeddings for queries using the embedding service.

**U-REQ-011**: System SHALL handle both PostgreSQL and SQLite database backends.

**U-REQ-012**: System SHALL validate and sanitize all filter inputs to prevent SQL injection.

**U-REQ-013**: System SHALL return structured SearchResult objects with chunk_id, text, title, source_url, taxonomy_path, and all score types.

**U-REQ-014**: System SHALL return SearchMetrics tracking total_time, bm25_time, vector_time, embedding_time, fusion_time, rerank_time, and candidate counts.

**U-REQ-015**: System SHALL use parameterized SQL queries for all database operations.

### Event-driven Requirements

**E-REQ-001**: WHEN a search query is received, System SHALL execute BM25 and vector searches in parallel using asyncio.gather.

**E-REQ-002**: WHEN parallel search execution completes, System SHALL handle exceptions from either search branch without failing the entire operation.

**E-REQ-003**: WHEN cache is enabled and query matches cached entry, System SHALL return cached results immediately without database access.

**E-REQ-004**: WHEN cache entry is accessed, System SHALL update its access time for LRU eviction.

**E-REQ-005**: WHEN cache reaches max_size, System SHALL evict the oldest entry based on access time.

**E-REQ-006**: WHEN cache TTL expires for an entry, System SHALL delete the entry and proceed with fresh search.

**E-REQ-007**: WHEN BM25 or vector search fails with exception, System SHALL log error and continue with available results.

**E-REQ-008**: WHEN reranking is enabled and results exist, System SHALL apply cross-encoder reranking before returning top_k results.

**E-REQ-009**: WHEN cross-encoder model is unavailable, System SHALL fall back to heuristic reranking using term overlap and quality signals.

**E-REQ-010**: WHEN heuristic reranking executes, System SHALL calculate term overlap, length penalty, and diversity bonus.

**E-REQ-011**: WHEN score normalization encounters identical scores, System SHALL return uniform normalized scores (1.0 for all items).

**E-REQ-012**: WHEN score normalization fails with exception, System SHALL return original unnormalized scores as fallback.

**E-REQ-013**: WHEN adaptive fusion analyzes query characteristics, System SHALL adjust BM25/vector weights based on query length, exact terms, and semantic complexity.

**E-REQ-014**: WHEN search completes successfully, System SHALL cache results if caching is enabled.

**E-REQ-015**: WHEN search fails with exception, System SHALL report to Sentry (if available) with comprehensive context.

**E-REQ-016**: WHEN filter clause is built, System SHALL validate taxonomy paths using alphanumeric whitelist.

**E-REQ-017**: WHEN content type filtering is requested, System SHALL validate against ALLOWED_CONTENT_TYPES whitelist.

**E-REQ-018**: WHEN date range filtering is requested, System SHALL validate dates using datetime.fromisoformat.

**E-REQ-019**: WHEN Sentry is available, System SHALL add search breadcrumbs with correlation_id for tracking.

**E-REQ-020**: WHEN search metrics are recorded, System SHALL call global search_metrics.record_search with search_type and timing.

### State-driven Requirements

**S-REQ-001**: WHILE using PostgreSQL backend, System SHALL use ts_rank_cd for BM25 scoring with normalization flags 32|1.

**S-REQ-002**: WHILE using SQLite backend, System SHALL fall back to FTS5 bm25() function.

**S-REQ-003**: WHILE using PostgreSQL backend, System SHALL use pgvector <=> operator for cosine distance.

**S-REQ-004**: WHILE using SQLite backend, System SHALL return mock cosine similarity scores (0.5).

**S-REQ-005**: WHILE cross-encoder model is loaded, System SHALL use sentence-transformers CrossEncoder.predict().

**S-REQ-006**: WHILE cross-encoder model is not loaded, System SHALL use heuristic reranking as fallback.

**S-REQ-007**: WHILE adaptive fusion detects short query (length ≤ 3) with exact terms, System SHALL increase BM25 weight up to 0.8.

**S-REQ-008**: WHILE adaptive fusion detects high semantic complexity (> 0.7), System SHALL increase vector weight up to 0.8.

**S-REQ-009**: WHILE reranking is disabled, System SHALL sort results by hybrid_score only.

**S-REQ-010**: WHILE cache is disabled, System SHALL skip cache lookup and storage operations.

### Constraints

**C-REQ-001**: Search latency p95 SHALL NOT exceed 1 second.

**C-REQ-002**: Search cost per query SHALL NOT exceed ₩3.

**C-REQ-003**: Recall@10 SHALL be at least 0.85.

**C-REQ-004**: BM25 candidates limit SHALL be configurable (default: 50).

**C-REQ-005**: Vector candidates limit SHALL be configurable (default: 50).

**C-REQ-006**: Cache max_size SHALL be configurable (default: 1000).

**C-REQ-007**: Cache TTL SHALL be configurable (default: 3600 seconds).

**C-REQ-008**: RRF constant k SHALL be 60.

**C-REQ-009**: Embedding dimension SHALL be 768 for text-embedding-3-small model.

**C-REQ-010**: Cross-encoder model SHALL be "cross-encoder/ms-marco-MiniLM-L-6-v2".

**C-REQ-011**: Score normalization SHALL preserve relative ordering of results.

**C-REQ-012**: Filter validation SHALL use whitelist-based approach to prevent injection.

**C-REQ-013**: Concurrent searches SHALL support at least 0.5 queries/second throughput.

**C-REQ-014**: Average concurrent search latency SHALL NOT exceed 15 seconds.

**C-REQ-015**: Error rate during concurrent searches SHALL be less than 10%.

**C-REQ-016**: Text length penalty SHALL favor chunks between 100-500 characters.

**C-REQ-017**: Position bonus SHALL decay linearly from 1.2 to 1.0 based on query position in text.

**C-REQ-018**: Diversity bonus SHALL be calculated from unique sources and taxonomies (max 1.0).

**C-REQ-019**: Adaptive fusion weight adjustment SHALL NOT exceed ±0.2 from configured weights.

**C-REQ-020**: All database operations SHALL use parameterized queries with named parameters.

## Implementation Details

### Major Classes (8 classes discovered)

#### 1. SearchResult (Dataclass)
**Purpose**: Encapsulates a single search result with all scoring information.

**Attributes**:
- chunk_id: str - Unique identifier for chunk
- text: str - Content of the chunk
- title: Optional[str] - Document title
- source_url: Optional[str] - Source URL
- taxonomy_path: List[str] - Taxonomy classification path
- bm25_score: float - BM25 keyword score
- vector_score: float - Vector similarity score
- hybrid_score: float - Fused score
- rerank_score: float - Cross-encoder reranking score
- metadata: Dict[str, Any] - Additional metadata

#### 2. SearchMetrics (Dataclass)
**Purpose**: Tracks performance metrics for search operations.

**Attributes**:
- total_time: float - Total search latency
- bm25_time: float - BM25 search time
- vector_time: float - Vector search time
- embedding_time: float - Query embedding generation time
- fusion_time: float - Score fusion time
- rerank_time: float - Reranking time
- bm25_candidates: int - Number of BM25 results
- vector_candidates: int - Number of vector results
- final_results: int - Final result count
- cache_hit: bool - Cache hit indicator

#### 3. ScoreNormalizer (Static Class)
**Purpose**: Provides score normalization algorithms.

**Methods**:
- min_max_normalize(scores: List[float]) -> List[float]
  - Normalizes to [0, 1] range
  - Returns [1.0] * len if all scores equal
  - Fallback: returns original scores on error

- z_score_normalize(scores: List[float]) -> List[float]
  - Normalizes to mean=0, std=1
  - Returns [0.0] * len if std=0
  - Fallback: returns original scores on error

- reciprocal_rank_normalize(scores: List[float]) -> List[float]
  - RRF with k=60: score = 1/(rank + 60)
  - Sorts by descending score before ranking
  - Fallback: returns original scores on error

#### 4. HybridScoreFusion
**Purpose**: Implements weighted score fusion algorithms.

**Configuration**:
- bm25_weight: float (default: 0.5)
- vector_weight: float (default: 0.5)
- normalization: str (default: "min_max")

**Methods**:
- fuse_scores(bm25_scores, vector_scores) -> List[float]
  - Applies configured normalization
  - Returns weighted combination

- adaptive_fusion(bm25_scores, vector_scores, query_characteristics) -> List[float]
  - Adjusts weights based on query analysis
  - Short queries (≤3 terms) with exact_terms → BM25 weight +0.2
  - High semantic_complexity (>0.7) → vector weight +0.2
  - Caps weight adjustments at configured ±0.2

#### 5. CrossEncoderReranker
**Purpose**: Reranks results using cross-encoder neural models.

**Configuration**:
- model_name: str (default: "cross-encoder/ms-marco-MiniLM-L-6-v2")

**Methods**:
- rerank(query, search_results, top_k) -> List[SearchResult]
  - Uses CrossEncoder.predict() if model available
  - Falls back to _heuristic_rerank if model unavailable
  - Returns top_k results sorted by rerank_score
  - Reports errors to Sentry with reranker context

- _heuristic_rerank(query, results) -> List[SearchResult]
  - Calculates term overlap ratio
  - Applies text length penalty
  - Applies diversity bonus
  - Quality multiplier = 1.0 + 0.2*overlap + 0.1*length + 0.1*diversity

- _calculate_quality_boost(query, text) -> float
  - Position bonus: 1.2 - (position/length) * 0.2
  - Length score multiplier

- _calculate_length_penalty(text_length) -> float
  - < 50 chars: 0.7
  - > 1000 chars: 0.8
  - 100-500 chars: 1.0 (optimal)
  - else: 0.9

- _calculate_diversity_bonus(result, all_results) -> float
  - Based on unique sources and taxonomies
  - Score = min(1.0, (unique_sources + unique_taxonomies) / 10.0)

#### 6. ResultCache
**Purpose**: In-memory LRU cache with TTL for search results.

**Configuration**:
- max_size: int (default: 1000)
- ttl_seconds: int (default: 3600)

**Methods**:
- _generate_cache_key(query, filters, top_k) -> str
  - MD5 hash of JSON-serialized params

- get(query, filters, top_k) -> Optional[List[SearchResult]]
  - Returns cached results if not expired
  - Updates access time on hit
  - Deletes expired entries

- put(query, filters, top_k, results)
  - Evicts oldest if cache full
  - Stores results with current timestamp

- _evict_oldest()
  - LRU eviction based on access_times

- clear()
  - Clears all cache entries

- get_stats() -> Dict[str, int]
  - Returns size, max_size, hit_rate

#### 7. HybridSearchEngine (Main Class)
**Purpose**: Orchestrates hybrid search combining BM25 and vector search.

**Configuration**:
- bm25_weight: float (default: 0.5)
- vector_weight: float (default: 0.5)
- enable_caching: bool (default: True)
- enable_reranking: bool (default: True)
- normalization: str (default: "min_max")

**Core Methods**:

- search(query, top_k, filters, bm25_candidates, vector_candidates, correlation_id) -> Tuple[List[SearchResult], SearchMetrics]
  - Main entry point for hybrid search
  - Checks cache first
  - Generates query embedding
  - Executes BM25 and vector search in parallel
  - Fuses results with adaptive fusion
  - Applies cross-encoder reranking
  - Caches results
  - Records metrics
  - Reports errors to Sentry

- _perform_bm25_search(query, top_k, filters) -> List[SearchResult]
  - PostgreSQL: ts_rank_cd with normalization flags 32|1
  - SQLite: FTS5 bm25() function
  - Builds secure filter clause
  - Returns SearchResult objects with bm25_score

- _perform_vector_search(query_embedding, top_k, filters) -> List[SearchResult]
  - PostgreSQL: pgvector <=> operator (cosine distance)
  - SQLite: mock similarity (0.5)
  - Converts embedding to vector format string
  - Returns SearchResult objects with vector_score

- _fuse_results(query, bm25_results, vector_results) -> List[SearchResult]
  - Merges results by chunk_id
  - Analyzes query characteristics
  - Applies adaptive fusion
  - Updates hybrid_score for all results
  - Adds fusion metadata

- _analyze_query(query) -> Dict[str, float]
  - length: term count
  - exact_terms: presence of quotes
  - semantic_complexity: ratio of long terms (>6 chars)
  - has_operators: presence of AND/OR/NOT/+/-
  - avg_term_length: average character count

- _build_filter_clause(filters) -> Tuple[str, Dict[str, Any]]
  - Taxonomy path filtering with alphanumeric validation
  - Content type whitelist validation
  - Date range validation with datetime.fromisoformat
  - Returns parameterized SQL clause

- keyword_only_search(query, top_k, filters) -> Tuple[List[SearchResult], SearchMetrics]
  - BM25 only mode
  - Sets hybrid_score = bm25_score

- vector_only_search(query, top_k, filters) -> Tuple[List[SearchResult], SearchMetrics]
  - Vector similarity only mode
  - Generates embedding
  - Sets hybrid_score = vector_score

- get_config() -> Dict[str, Any]
  - Returns current configuration
  - Includes cache stats if enabled

- update_config(**kwargs)
  - Updates bm25_weight, vector_weight, normalization
  - Normalizes weights to sum to 1.0

- clear_cache()
  - Clears result cache

#### 8. Global Functions (API Integration)

- hybrid_search(query, top_k, filters, **kwargs) -> Tuple[List[Dict], Dict]
  - API-compatible wrapper
  - Converts SearchResult to dict format
  - Uses rerank_score if available, else hybrid_score

- keyword_search(query, top_k, filters) -> Tuple[List[Dict], Dict]
  - BM25-only API wrapper

- vector_search(query, top_k, filters) -> Tuple[List[Dict], Dict]
  - Vector-only API wrapper

- get_search_engine_config() -> Dict[str, Any]
  - Returns global engine config

- update_search_engine_config(**kwargs)
  - Updates global engine config

- clear_search_cache()
  - Clears global cache

- get_search_statistics() -> Dict[str, Any]
  - Returns database stats, engine config, performance metrics
  - Aggregates from multiple sources

### Core Algorithms

#### 1. Score Normalization

**Min-Max Normalization**:
```
normalized[i] = (score[i] - min) / (max - min)
Result range: [0.0, 1.0]
```

**Z-Score Normalization**:
```
normalized[i] = (score[i] - mean) / std
Result range: centered at 0, typically [-3, +3]
```

**Reciprocal Rank Fusion (RRF)**:
```
rank = position in sorted list (0-indexed)
normalized[i] = 1 / (rank + 60)
k = 60 (RRF constant)
```

#### 2. Hybrid Score Fusion

**Basic Weighted Fusion**:
```
hybrid_score = bm25_weight * norm_bm25 + vector_weight * norm_vector
where bm25_weight + vector_weight = 1.0
```

**Adaptive Fusion**:
```
IF query.length ≤ 3 AND has_exact_terms:
    adaptive_bm25_weight = min(0.8, bm25_weight + 0.2)
ELSE IF semantic_complexity > 0.7:
    adaptive_vector_weight = min(0.8, vector_weight + 0.2)
ELSE:
    use configured weights

hybrid_score = adaptive_bm25_weight * norm_bm25 + adaptive_vector_weight * norm_vector
```

#### 3. Heuristic Reranking

**Quality Multiplier Calculation**:
```
term_overlap = |query_terms ∩ text_terms| / |query_terms|
text_length_penalty = f(text_length)  // see length penalty table
diversity_bonus = min(1.0, (unique_sources + unique_taxonomies) / 10.0)

quality_multiplier = 1.0 + 0.2*term_overlap + 0.1*text_length_penalty + 0.1*diversity_bonus
rerank_score = hybrid_score * quality_multiplier
```

#### 4. Query Characteristics Analysis

**Semantic Complexity**:
```
long_terms = [term for term in query.split() if len(term) > 6]
semantic_complexity = len(long_terms) / max(1, total_terms)
```

**Has Exact Terms**:
```
exact_terms = any(term.startswith('"') OR term.endswith('"') for term in query.split())
```

### Security Features

**SQL Injection Prevention**:
1. All queries use parameterized SQL with named parameters
2. Taxonomy paths validated with alphanumeric whitelist: `[a-zA-Z0-9_\- ]`
3. Content types validated against ALLOWED_CONTENT_TYPES whitelist
4. Date ranges validated with datetime.fromisoformat
5. No string interpolation of user input into SQL

**Input Validation**:
- Query strings trimmed and checked for empty
- Filter values type-checked and validated
- Embedding dimensions validated (768 for text-embedding-3-small)

### Performance Optimization

**Parallel Execution**:
```python
bm25_task = _perform_bm25_search(...)
vector_task = _perform_vector_search(...)
bm25_results, vector_results = await asyncio.gather(bm25_task, vector_task, return_exceptions=True)
```

**Caching Strategy**:
- LRU eviction with TTL
- Cache key: MD5(query + filters + top_k)
- Warm cache improves latency by ~90%

**Database Optimization**:
- PostgreSQL: ts_rank_cd with normalization flags for BM25
- PostgreSQL: pgvector <=> for efficient cosine distance
- SQLite: FTS5 bm25() for keyword search
- Parameterized queries for query plan caching

### Error Handling

**Graceful Degradation**:
1. BM25 failure → continue with vector results only
2. Vector failure → continue with BM25 results only
3. Cross-encoder unavailable → heuristic reranking
4. Normalization error → return original scores
5. Cache error → skip cache and execute search

**Monitoring Integration**:
- Sentry breadcrumbs for search tracking
- Correlation IDs for distributed tracing
- Error reporting with comprehensive context
- Performance metrics recording

### Database Schema Dependencies

**Required Tables**:
- chunks (chunk_id, text, doc_id)
- documents (doc_id, source_url, content_type, processed_at)
- embeddings (chunk_id, vec [vector(768)])
- doc_taxonomy (doc_id, path [text[]])

**PostgreSQL Extensions**:
- pgvector for vector operations
- Full-text search (built-in)

**SQLite Extensions**:
- FTS5 for full-text search

## Test Requirements

### Unit Tests (Covered in tests/test_hybrid_search.py)

**TestScoreNormalization**:
- test_min_max_normalization
  - Verify range [0, 1]
  - Verify min=0, max=1
  - Verify uniform scores handling

- test_z_score_normalization
  - Verify mean ≈ 0
  - Verify std handling

- test_reciprocal_rank_normalization
  - Verify RRF formula with k=60
  - Verify rank ordering

**TestHybridScoreFusion**:
- test_basic_score_fusion
  - Verify weighted combination
  - Verify weight normalization to 1.0

- test_adaptive_fusion
  - Verify short query → BM25 boost
  - Verify complex query → vector boost
  - Verify weight adjustment limits

**TestCrossEncoderReranking**:
- test_basic_reranking
  - Verify rerank_score assignment
  - Verify top_k selection
  - Verify result ordering

- test_heuristic_reranking
  - Verify fallback behavior
  - Verify quality signal calculation

**TestResultCache**:
- test_cache_put_get
  - Verify cache storage and retrieval
  - Verify cache key generation

- test_cache_eviction
  - Verify LRU eviction
  - Verify max_size enforcement

- test_cache_ttl
  - Verify TTL expiration
  - Verify expired entry deletion

**TestHybridSearchEngine**:
- test_engine_initialization
  - Verify config storage
  - Verify component initialization

- test_hybrid_search_execution
  - Verify parallel execution
  - Verify result fusion
  - Verify metric collection

- test_keyword_only_search
  - Verify BM25 only mode

- test_vector_only_search
  - Verify vector only mode

### Performance Tests

**TestSearchPerformance**:
- test_search_latency
  - Verify p95 < 1s (target)
  - Verify average latency < 1s
  - Measure per-query latency

- test_concurrent_searches
  - Verify throughput > 0.5 queries/sec
  - Verify concurrent avg latency < 15s
  - Verify error rate < 10%
  - Test 20 concurrent queries

**TestSearchQuality**:
- test_result_relevance_scoring
  - Verify term overlap calculation
  - Verify relevance > 0 for all results
  - Verify max relevance > 0.5

- test_search_diversity
  - Verify no duplicate results
  - Verify content diversity ratio > 0.5
  - Verify unique technical terms

### Integration Tests

**TestAPIIntegration**:
- test_hybrid_search_api_function
  - Verify API format conversion
  - Verify metadata structure
  - Verify metrics structure

### End-to-End Test Scenarios

**Scenario 1: Basic Hybrid Search**
1. Given a query "machine learning algorithms"
2. When hybrid search executes
3. Then BM25 and vector searches run in parallel
4. And results are fused with adaptive weights
5. And cross-encoder reranking is applied
6. And results are returned in < 1s

**Scenario 2: Cache Hit**
1. Given a previously executed query
2. When same query is executed again
3. Then cache returns results immediately
4. And no database queries are executed
5. And cache_hit metric is True

**Scenario 3: Filtering**
1. Given a query with taxonomy_path filter
2. When hybrid search executes
3. Then only results matching taxonomy are returned
4. And filter clause is parameterized
5. And no SQL injection is possible

**Scenario 4: Graceful Degradation**
1. Given BM25 search fails with exception
2. When hybrid search executes
3. Then vector search results are still returned
4. And error is logged
5. And Sentry receives error report

**Scenario 5: Adaptive Fusion**
1. Given a short query with exact terms
2. When hybrid search executes
3. Then BM25 weight is increased to 0.7-0.8
4. And results favor keyword matches

**Scenario 6: Cross-Encoder Fallback**
1. Given cross-encoder model is unavailable
2. When reranking is requested
3. Then heuristic reranking executes
4. And quality signals are calculated
5. And results are reranked by quality multiplier

## Performance Targets

### Latency
- p50: < 0.5s
- p95: < 1.0s
- p99: < 1.5s

### Throughput
- Single query: > 1 query/sec
- Concurrent (20 queries): > 0.5 query/sec

### Quality
- Recall@10: ≥ 0.85
- Precision@5: ≥ 0.70

### Cost
- Per query: ≤ ₩3
- Includes embedding generation + database queries

### Reliability
- Error rate: < 1% under normal load
- Error rate: < 10% under concurrent load
- Cache hit rate: > 30% in production

## Related Files

### Source Code
- @CODE: /mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/apps/search/hybrid_search_engine.py (1,208 lines)
- @CODE: /mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/apps/api/embedding_service.py
- @CODE: /mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/apps/api/database.py
- @CODE: /mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/apps/core/db_session.py

### Tests
- @TEST: /mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/tests/test_hybrid_search.py (593 lines)

### Monitoring
- @CODE: /mnt/c/MYCLAUDE_PROJECT/sonheungmin/Unmanned/dt-rag/apps/api/monitoring/sentry_reporter.py

### Configuration
- Database: PostgreSQL with pgvector extension
- Embedding Model: text-embedding-3-small (768 dimensions)
- Cross-Encoder Model: cross-encoder/ms-marco-MiniLM-L-6-v2

## Dependencies

### Python Packages
- sqlalchemy (async support)
- asyncpg (PostgreSQL driver)
- numpy (score normalization)
- sentence-transformers (cross-encoder)
- hashlib (cache key generation)

### Database Extensions
- pgvector (PostgreSQL)
- FTS5 (SQLite)

### Internal Services
- embedding_service.generate_embedding()
- db_manager.async_session()
- search_metrics.record_search()
- sentry_reporter (optional)

## Future Enhancements

### Potential Improvements Identified During Analysis
1. Implement Redis-based distributed cache
2. Add learning-to-rank (LTR) model
3. Implement query expansion
4. Add semantic chunking
5. Implement A/B testing framework
6. Add personalization layer
7. Implement federated search across data sources

### Known Limitations
1. SQLite fallback has mock vector similarity (0.5)
2. Heuristic reranking is less accurate than cross-encoder
3. In-memory cache not shared across instances
4. No query spell correction
5. No result deduplication beyond exact chunk_id
6. Diversity bonus is simplistic (source + taxonomy count)

## Revision History

- v0.1.0 (2025-10-08): E2E testing completed successfully
  - Hybrid Search: latency 0.826s < 1.0s target (✅)
  - LangGraph Pipeline: latency 6.776s < 20s target (✅)
  - API Key authentication working
  - All EARS requirements verified
- v0.1.0 (2025-10-07): Initial reverse-engineered specification from production code
