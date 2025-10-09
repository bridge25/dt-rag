# SPEC-EMBED-001 Acceptance Criteria

## 수락 기준 개요

OpenAI 기반 벡터 임베딩 서비스는 이미 프로덕션 환경에서 완전히 구현되어 검증되었습니다. 본 문서는 시스템의 기능적 완성도를 검증하기 위한 상세한 수락 기준과 테스트 시나리오를 정의합니다.

## Given-When-Then 테스트 시나리오

### AC-001: OpenAI Embedding Generation

**Given**: 사용자가 텍스트를 제공했을 때
**When**: OpenAI 임베딩 생성이 수행되면
**Then**: 1536차원 벡터를 반환하고 L2 정규화되어야 한다

**검증 코드**:
```python
embedding_service = EmbeddingService(model_name="text-embedding-3-large")

text = "Machine learning is a subset of artificial intelligence"
embedding = await embedding_service.generate_embedding(text, use_cache=False)

# Assertions
assert isinstance(embedding, list)
assert len(embedding) == 1536
assert all(isinstance(x, float) for x in embedding)

# Verify L2 normalization (norm should be 1.0)
import numpy as np
norm = np.linalg.norm(np.array(embedding))
assert abs(norm - 1.0) < 1e-6
```

**OpenAI API 검증**:
```python
# Verify API call parameters
mock_openai_client.embeddings.create.assert_called_with(
    input=text,
    model="text-embedding-3-large",
    encoding_format="float",
    dimensions=1536
)
```

**품질 게이트**:
- ✅ Vector dimensions: 1536
- ✅ L2 norm: ≈ 1.0
- ✅ Response time < 500ms (single embedding)

---

### AC-002: Caching Mechanism

**Given**: 동일한 텍스트가 반복 요청될 때
**When**: 캐싱이 활성화되어 있으면
**Then**: 두 번째 요청부터는 캐시된 임베딩을 즉시 반환해야 한다

**검증 코드**:
```python
embedding_service = EmbeddingService()

text = "Same text for caching test"

# First call (cache miss)
start = time.time()
embedding_1 = await embedding_service.generate_embedding(text, use_cache=True)
miss_duration = time.time() - start

assert embedding_service._get_cache_key(text) in embedding_service.embedding_cache

# Second call (cache hit)
start = time.time()
embedding_2 = await embedding_service.generate_embedding(text, use_cache=True)
hit_duration = time.time() - start

assert embedding_1 == embedding_2  # Same embedding
assert hit_duration < miss_duration / 10  # Cache is at least 10x faster
assert hit_duration < 0.001  # < 1ms
```

**Cache Key Generation**:
```python
# MD5 hash test
cache_key = embedding_service._get_cache_key(text)
expected_key = hashlib.md5(text.encode('utf-8')).hexdigest()
assert cache_key == expected_key
```

**품질 게이트**:
- ✅ Cache hit time < 1ms
- ✅ Cache miss time = Full embedding generation
- ✅ MD5 hash consistency

---

### AC-003: LRU Cache Eviction

**Given**: 캐시 크기가 최대치(1000)를 초과할 때
**When**: 새로운 임베딩이 추가되면
**Then**: 가장 오래된 항목이 제거되어야 한다

**검증 코드**:
```python
embedding_service = EmbeddingService()

# Fill cache to max (1000 entries)
for i in range(1000):
    await embedding_service.generate_embedding(f"text {i}", use_cache=True)

assert len(embedding_service.embedding_cache) == 1000

# Verify first entry is in cache
first_key = embedding_service._get_cache_key("text 0")
assert first_key in embedding_service.embedding_cache

# Add 1001th entry
await embedding_service.generate_embedding("text 1000", use_cache=True)

# First entry should be evicted
assert len(embedding_service.embedding_cache) == 1000
assert first_key not in embedding_service.embedding_cache

# Last entry should exist
last_key = embedding_service._get_cache_key("text 1000")
assert last_key in embedding_service.embedding_cache
```

**품질 게이트**:
- ✅ Cache size ≤ 1000 at all times
- ✅ FIFO eviction: Oldest first
- ✅ Memory usage: ~6MB for 1000 entries

---

### AC-004: Sentence Transformers Fallback

**Given**: OpenAI API가 실패했을 때
**When**: Sentence Transformers fallback이 실행되면
**Then**: 768차원 벡터를 생성하고 1536차원으로 zero padding해야 한다

**검증 코드**:
```python
embedding_service = EmbeddingService()

# Simulate OpenAI failure
with mock.patch.object(
    embedding_service,
    '_generate_openai_embedding',
    side_effect=Exception("OpenAI API error")
):
    text = "Fallback test text"
    embedding = await embedding_service.generate_embedding(text)

    # Assertions
    assert len(embedding) == 1536
    # First 768: real embeddings, last 768: zeros
    assert all(e != 0.0 for e in embedding[:768])  # Real values
    assert all(e == 0.0 for e in embedding[768:])  # Zero padding
```

**Padding Logic Verification**:
```python
# Test _pad_or_truncate_vector
import numpy as np

# 768 → 1536 (zero padding)
vec_768 = np.random.rand(768)
padded = embedding_service._pad_or_truncate_vector(vec_768)
assert len(padded) == 1536
assert all(padded[i] == vec_768[i] for i in range(768))
assert all(padded[i] == 0.0 for i in range(768, 1536))

# 1536 → 1536 (no change)
vec_1536 = np.random.rand(1536)
result = embedding_service._pad_or_truncate_vector(vec_1536)
assert len(result) == 1536
assert all(result[i] == vec_1536[i] for i in range(1536))

# 2048 → 1536 (truncate)
vec_2048 = np.random.rand(2048)
truncated = embedding_service._pad_or_truncate_vector(vec_2048)
assert len(truncated) == 1536
assert all(truncated[i] == vec_2048[i] for i in range(1536))
```

**품질 게이트**:
- ✅ Fallback success rate: 100%
- ✅ Zero padding: embedding[768:] == [0.0] * 768
- ✅ Semantic quality: Acceptable (though lower than OpenAI)

---

### AC-005: Dummy Embedding Generation

**Given**: OpenAI와 Sentence Transformers 모두 실패했을 때
**When**: Dummy embedding이 생성되면
**Then**: MD5 hash 기반 시드로 정규분포 난수를 생성하고 L2 정규화해야 한다

**검증 코드**:
```python
embedding_service = EmbeddingService()

# Simulate all methods failing
with mock.patch.object(embedding_service, '_generate_openai_embedding', side_effect=Exception):
    with mock.patch.object(embedding_service, '_generate_sentence_transformer_embedding', side_effect=Exception):
        text = "Dummy test"
        embedding = await embedding_service.generate_embedding(text)

        # Assertions
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)

        # Verify L2 normalization
        norm = np.linalg.norm(np.array(embedding))
        assert abs(norm - 1.0) < 1e-6

        # Verify determinism (same text = same dummy embedding)
        embedding_2 = await embedding_service._generate_dummy_embedding(text)
        assert embedding == embedding_2
```

**MD5 Seed Verification**:
```python
# Test seeded random generation
text = "test"
seed = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16) % (2**32)

np.random.seed(seed)
expected_vec = np.random.normal(0, 0.1, 1536)
expected_vec = expected_vec / np.linalg.norm(expected_vec)

dummy = await embedding_service._generate_dummy_embedding(text)
assert all(abs(d - e) < 1e-6 for d, e in zip(dummy, expected_vec))
```

**품질 게이트**:
- ✅ Dummy generation rate < 0.1% (production)
- ✅ Deterministic: Same text = same dummy
- ✅ L2 normalized: norm ≈ 1.0

---

### AC-006: Zero Vector for Empty Text

**Given**: 빈 텍스트 또는 공백만 포함된 텍스트가 입력될 때
**When**: 임베딩 생성이 수행되면
**Then**: 1536차원 zero vector를 반환해야 한다

**검증 코드**:
```python
embedding_service = EmbeddingService()

# Empty string
embedding_1 = await embedding_service.generate_embedding("")
assert embedding_1 == [0.0] * 1536

# Whitespace only
embedding_2 = await embedding_service.generate_embedding("   \n\t   ")
assert embedding_2 == [0.0] * 1536

# Verify preprocessing
assert embedding_service._preprocess_text("") == ""
assert embedding_service._preprocess_text("   ") == ""
```

**품질 게이트**:
- ✅ Empty text → zero vector
- ✅ Whitespace text → zero vector
- ✅ No API call for empty text

---

### AC-007: Text Preprocessing

**Given**: 긴 텍스트가 입력될 때
**When**: Preprocessing이 수행되면
**Then**: 8000자로 제한되고 앞뒤 공백이 제거되어야 한다

**검증 코드**:
```python
embedding_service = EmbeddingService()

# Long text (10000 characters)
long_text = "a" * 10000
processed = embedding_service._preprocess_text(long_text)
assert len(processed) == 8000

# Whitespace removal
text_with_whitespace = "   Hello World   \n"
processed = embedding_service._preprocess_text(text_with_whitespace)
assert processed == "Hello World"

# Empty after strip
processed = embedding_service._preprocess_text("   ")
assert processed == ""
```

**품질 게이트**:
- ✅ Max length: 8000 characters
- ✅ Strip whitespace: True
- ✅ Preserve content integrity

---

### AC-008: Batch Embedding Generation

**Given**: 여러 텍스트가 배치로 제공될 때
**When**: Batch embedding generation이 수행되면
**Then**: 배치 크기만큼 나누어 처리하고 0.01초 delay를 적용해야 한다

**검증 코드**:
```python
embedding_service = EmbeddingService()

texts = [f"Text {i}" for i in range(250)]  # 250 texts
batch_size = 100

start = time.time()
embeddings = await embedding_service.batch_generate_embeddings(
    texts=texts,
    batch_size=batch_size,
    show_progress=True
)
duration = time.time() - start

# Assertions
assert len(embeddings) == 250
assert all(len(emb) == 1536 for emb in embeddings)

# 3 batches: 100, 100, 50
# Expected time: ~3 seconds (3 batches) + 2 * 0.01s (2 delays)
assert duration > 0.02  # At least 2 delays (0.01s each)
```

**Batch Processing Verification**:
```python
# Verify batching logic
texts = ["text"] * 105
batch_size = 50

# Mock OpenAI API
with mock.patch.object(embedding_service._openai_client.embeddings, 'create') as mock_create:
    mock_create.return_value = mock_response(batch_size)

    await embedding_service.batch_generate_embeddings(texts, batch_size)

    # Should be called 3 times: 50, 50, 5
    assert mock_create.call_count == 3
```

**품질 게이트**:
- ✅ Batch size: default 100, max 100
- ✅ Rate limiting: 0.01s delay between batches
- ✅ Progress logging: Enabled by default

---

### AC-009: Cosine Similarity Calculation

**Given**: 두 개의 임베딩 벡터가 제공될 때
**When**: Cosine similarity가 계산되면
**Then**: -1.0 ~ 1.0 범위의 유사도를 반환해야 한다

**검증 코드**:
```python
embedding_service = EmbeddingService()

# Identical vectors (similarity = 1.0)
vec1 = [1.0, 0.0, 0.0]
vec2 = [1.0, 0.0, 0.0]
similarity = embedding_service.calculate_similarity(vec1, vec2)
assert abs(similarity - 1.0) < 1e-6

# Orthogonal vectors (similarity = 0.0)
vec3 = [1.0, 0.0, 0.0]
vec4 = [0.0, 1.0, 0.0]
similarity = embedding_service.calculate_similarity(vec3, vec4)
assert abs(similarity - 0.0) < 1e-6

# Opposite vectors (similarity = -1.0)
vec5 = [1.0, 0.0, 0.0]
vec6 = [-1.0, 0.0, 0.0]
similarity = embedding_service.calculate_similarity(vec5, vec6)
assert abs(similarity - (-1.0)) < 1e-6
```

**Dimension Mismatch Handling**:
```python
# Different dimensions → return 0.0
vec1 = [1.0] * 1536
vec2 = [1.0] * 768
similarity = embedding_service.calculate_similarity(vec1, vec2)
assert similarity == 0.0
```

**품질 게이트**:
- ✅ Similarity range: [-1.0, 1.0]
- ✅ Dimension mismatch → 0.0
- ✅ Zero vectors → 0.0

---

### AC-010: Document Embedding Update

**Given**: 데이터베이스에 임베딩 없는 청크가 존재할 때
**When**: Document embedding update가 수행되면
**Then**: 배치 단위로 임베딩을 생성하고 UPSERT로 저장해야 한다

**검증 코드**:
```python
doc_embedding_service = DocumentEmbeddingService(embedding_service)

# Add chunks without embeddings
async with db_manager.async_session() as session:
    chunks = [
        Chunk(chunk_id=f"chunk-{i}", text=f"Text {i}", doc_id="test-doc")
        for i in range(150)
    ]
    session.add_all(chunks)
    await session.commit()

# Update embeddings
result = await doc_embedding_service.update_document_embeddings(
    document_ids=["test-doc"],
    batch_size=50
)

# Assertions
assert result["success"] == True
assert result["updated_count"] == 150
assert result["model_name"] == "text-embedding-3-large"

# Verify database records
async with db_manager.async_session() as session:
    query = text("""
        SELECT COUNT(*) FROM embeddings
        WHERE chunk_id IN (
            SELECT chunk_id FROM chunks WHERE doc_id = :doc_id
        )
    """)
    result = await session.execute(query, {"doc_id": "test-doc"})
    count = result.scalar()
    assert count == 150
```

**UPSERT Logic Verification**:
```python
# Update existing embedding
chunk_id = "chunk-1"
new_embedding = [0.1] * 1536

async with db_manager.async_session() as session:
    # First insert
    await session.execute(text("""
        INSERT INTO embeddings (chunk_id, vec, model_name)
        VALUES (:chunk_id, :vec, :model_name)
    """), {"chunk_id": chunk_id, "vec": new_embedding, "model_name": "test-model"})

    # UPSERT (update)
    await session.execute(text("""
        INSERT INTO embeddings (chunk_id, vec, model_name)
        VALUES (:chunk_id, :vec, :model_name)
        ON CONFLICT (chunk_id) DO UPDATE SET
            vec = EXCLUDED.vec,
            model_name = EXCLUDED.model_name,
            created_at = NOW()
    """), {"chunk_id": chunk_id, "vec": new_embedding, "model_name": "new-model"})

    # Verify only one record exists
    result = await session.execute(text("SELECT COUNT(*) FROM embeddings WHERE chunk_id = :chunk_id"), {"chunk_id": chunk_id})
    assert result.scalar() == 1
```

**품질 게이트**:
- ✅ Batch update: 100 chunks per batch
- ✅ UPSERT: ON CONFLICT chunk_id DO UPDATE
- ✅ Progress logging: Every batch

---

### AC-011: Embedding Status API

**Given**: 데이터베이스에 청크와 임베딩이 존재할 때
**When**: Embedding status가 조회되면
**Then**: 전체 청크 수, 임베딩 수, 커버리지를 반환해야 한다

**검증 코드**:
```python
doc_embedding_service = DocumentEmbeddingService(embedding_service)

status = await doc_embedding_service.get_embedding_status()

# Assertions
assert "statistics" in status
assert "total_chunks" in status["statistics"]
assert "embedded_chunks" in status["statistics"]
assert "missing_embeddings" in status["statistics"]
assert "embedding_coverage_percent" in status
assert 0.0 <= status["embedding_coverage_percent"] <= 100.0

# Model distribution
assert "model_distribution" in status
assert isinstance(status["model_distribution"], dict)
```

**Coverage Calculation**:
```python
# Test coverage formula
total_chunks = 1000
embedded_chunks = 950

coverage = (embedded_chunks / total_chunks) * 100
assert coverage == 95.0

# Edge case: No chunks
total_chunks = 0
coverage = (0 / max(1, total_chunks)) * 100
assert coverage == 0.0
```

**품질 게이트**:
- ✅ Coverage calculation: (embedded / total) * 100
- ✅ Model distribution: Count by model_name
- ✅ Response time < 100ms

---

## 성능 수락 기준

### Performance Metrics

**Single Embedding Latency**:
```python
@pytest.mark.performance
async def test_single_embedding_performance():
    embedding_service = EmbeddingService()

    latencies = []
    for i in range(100):
        start = time.time()
        await embedding_service.generate_embedding(f"Performance test {i}")
        latencies.append(time.time() - start)

    avg_latency = sum(latencies) / len(latencies)
    p95_latency = np.percentile(latencies, 95)

    assert avg_latency < 0.5  # 500ms average
    assert p95_latency < 1.0  # 1 second p95
```

**Batch Embedding Throughput**:
```python
@pytest.mark.performance
async def test_batch_embedding_performance():
    embedding_service = EmbeddingService()

    texts = ["text"] * 100
    start = time.time()
    await embedding_service.batch_generate_embeddings(texts, batch_size=100)
    duration = time.time() - start

    assert duration < 5.0  # 5 seconds for 100 embeddings
    throughput = len(texts) / duration
    assert throughput > 20  # At least 20 embeddings per second
```

**Cache Performance**:
```python
@pytest.mark.performance
async def test_cache_performance():
    embedding_service = EmbeddingService()

    text = "Cached text"

    # Cache miss
    start = time.time()
    await embedding_service.generate_embedding(text, use_cache=True)
    miss_latency = time.time() - start

    # Cache hit
    start = time.time()
    await embedding_service.generate_embedding(text, use_cache=True)
    hit_latency = time.time() - start

    assert hit_latency < 0.001  # < 1ms
    assert hit_latency < miss_latency / 10  # At least 10x faster
```

---

## 모니터링 수락 기준

### Alert Thresholds

**High Severity**:
```python
assert openai_api_success_rate >= 0.95  # 95%
assert embedding_generation_time_p95 <= 5.0  # 5 seconds
```

**Medium Severity**:
```python
assert cache_hit_rate >= 0.20  # 20%
assert fallback_usage_rate <= 0.05  # 5%
```

**Low Severity**:
```python
assert dummy_embedding_rate <= 0.01  # 1%
assert embedding_coverage >= 0.95  # 95%
```

---

## 최종 수락 체크리스트

### 기능 완성도

- [x] OpenAI embedding generation (1536 dims)
- [x] Sentence Transformers fallback (768→1536 padding)
- [x] Dummy embedding generation (MD5 seed)
- [x] Zero vector for empty text
- [x] Text preprocessing (8000 char limit)
- [x] MD5-based caching
- [x] LRU cache eviction (max 1000)
- [x] Batch embedding generation
- [x] Rate limiting (0.01s delay)
- [x] Cosine similarity calculation
- [x] Document embedding update (UPSERT)
- [x] Embedding status API
- [x] Langfuse integration (optional)

### 품질 게이트

- [x] Vector dimensions: 1536
- [x] L2 normalization: norm ≈ 1.0
- [x] Cache hit time < 1ms
- [x] Single embedding < 1.0s p95
- [x] Batch (100) < 5.0s

### 운영 준비

- [x] PostgreSQL with pgvector extension
- [x] OpenAI API key configured
- [x] Langfuse configured (optional)
- [x] Database indexes created
- [x] API endpoints exposed
- [x] Monitoring metrics defined

---

**문서 버전**: v0.1.0
**최종 업데이트**: 2025-10-09
**작성자**: @Claude
**상태**: Approved
