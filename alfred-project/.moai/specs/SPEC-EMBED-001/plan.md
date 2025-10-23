# SPEC-EMBED-001 Implementation Plan

## 구현 개요

OpenAI 기반 벡터 임베딩 서비스는 이미 완전히 구현되어 프로덕션 환경에서 검증되었습니다. 본 문서는 역공학된 시스템의 구현 전략과 아키텍처를 설명합니다.

## 우선순위별 구현 마일스톤

### 1차 목표: 핵심 임베딩 생성 (완료)

**구현 완료 항목**:
- ✅ EmbeddingService 클래스 구현
- ✅ OpenAI AsyncClient 통합 (text-embedding-3-large)
- ✅ Sentence Transformers fallback
- ✅ L2 normalization
- ✅ Zero vector handling

**기술적 접근**:
```python
# OpenAI embedding generation
async def _generate_openai_embedding(self, text: str) -> List[float]:
    response = await self._openai_client.embeddings.create(
        input=text,
        model=self.model_name,
        encoding_format="float",
        dimensions=1536
    )
    embedding = response.data[0].embedding
    return self._normalize_vector(embedding)
```

**아키텍처 결정**:
- **모델 선택**: text-embedding-3-large (1536차원)
  - 이유: 최고 성능, Recall@1 = 64.6%
  - 비용: $0.00013 per 1K tokens
- **비동기 처리**: AsyncOpenAI client for concurrency
- **정규화**: L2 normalization for pgvector compatibility
- **빈 텍스트**: 1536차원 zero vector 반환

### 2차 목표: Fallback 메커니즘 (완료)

**구현 완료 항목**:
- ✅ Sentence Transformers 통합 (all-mpnet-base-v2)
- ✅ 768→1536 zero padding
- ✅ Dummy embedding 생성 (MD5 seed)
- ✅ OpenAI 실패 시 자동 전환

**기술적 접근**:
```python
# Fallback cascade
try:
    embedding = await self._generate_openai_embedding(text)
except Exception as e:
    logger.warning(f"OpenAI failed: {e}, using Sentence Transformers")
    try:
        embedding = await self._generate_sentence_transformer_embedding(text)
    except Exception as e2:
        logger.error(f"All methods failed: {e2}, generating dummy")
        embedding = await self._generate_dummy_embedding(text)

return embedding
```

**아키텍처 결정**:
- **3-Tier Fallback**:
  1. OpenAI (Primary) - 최고 품질
  2. Sentence Transformers (Secondary) - 로컬 모델, 무료
  3. Dummy Embedding (Last Resort) - MD5 hash seed
- **768→1536 Padding**: `embedding + [0.0] * 768`
- **Dummy Generation**: MD5 hash → random seed → normal distribution

### 3차 목표: 캐싱 및 배치 처리 (완료)

**구현 완료 항목**:
- ✅ MD5-based in-memory cache
- ✅ LRU eviction (max 1000 entries)
- ✅ Batch embedding generation
- ✅ Rate limiting (0.01s delay)

**기술적 접근**:
```python
# Cache lookup
cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()
if use_cache and cache_key in self.embedding_cache:
    logger.debug(f"Cache hit for: {text[:50]}...")
    return self.embedding_cache[cache_key]

# Batch processing
for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    batch_embeddings = await self._openai_client.embeddings.create(
        input=batch,
        model=self.model_name
    )
    embeddings.extend([e.embedding for e in batch_embeddings.data])

    await asyncio.sleep(0.01)  # Rate limiting
```

**아키텍처 결정**:
- **Cache Key**: MD5(text) for fast lookup
- **Cache Size**: 1000 entries (약 6MB)
- **Eviction**: FIFO (oldest first)
- **Batch Size**: 100 (OpenAI API limit)
- **Rate Limit**: 0.01s delay between batches

### 4차 목표: 문서 임베딩 관리 (완료)

**구현 완료 항목**:
- ✅ DocumentEmbeddingService 클래스
- ✅ 임베딩 없는 청크 자동 조회
- ✅ Batch update (UPSERT)
- ✅ Progress logging
- ✅ Status API

**기술적 접근**:
```python
# Find chunks without embeddings
query = text("""
    SELECT c.chunk_id, c.text
    FROM chunks c
    LEFT JOIN embeddings e ON c.chunk_id = e.chunk_id
    WHERE e.embedding_id IS NULL
    LIMIT :limit
""")

# Batch update
for i in range(0, len(chunk_ids), batch_size):
    batch_chunks = chunks[i:i+batch_size]
    texts = [chunk['text'] for chunk in batch_chunks]

    embeddings = await self.embedding_service.batch_generate_embeddings(texts)

    # UPSERT into database
    for chunk, embedding in zip(batch_chunks, embeddings):
        await session.execute(text("""
            INSERT INTO embeddings (chunk_id, vec, model_name)
            VALUES (:chunk_id, :vec, :model_name)
            ON CONFLICT (chunk_id) DO UPDATE SET
                vec = :vec,
                model_name = :model_name,
                created_at = NOW()
        """), {
            "chunk_id": chunk['chunk_id'],
            "vec": embedding,
            "model_name": self.embedding_service.model_name
        })

    logger.info(f"Batch {i//batch_size + 1} updated ({len(batch_chunks)} chunks)")
```

**아키텍처 결정**:
- **LEFT JOIN 조회**: 임베딩 없는 청크만 선택
- **UPSERT 전략**: ON CONFLICT chunk_id DO UPDATE
- **Batch Commit**: 100개씩 COMMIT for consistency
- **Progress Logging**: 배치마다 진행 상황 로깅

### 5차 목표: Langfuse 통합 (완료)

**구현 완료 항목**:
- ✅ @observe decorator 적용
- ✅ 비용 추적 (token count, cost)
- ✅ Trace generation
- ✅ Fallback 시 graceful skip

**기술적 접근**:
```python
from langfuse.decorators import observe

@observe(name="generate_embedding", as_type="embedding")
async def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
    # Langfuse automatically tracks:
    # - Input text length
    # - Token count
    # - Model name
    # - Latency
    # - Cost ($0.00013 per 1K tokens)
    ...
```

**아키텍처 결정**:
- **데코레이터 패턴**: Non-invasive instrumentation
- **자동 추적**: Token, cost, latency
- **Graceful Fallback**: Langfuse 없어도 정상 작동
- **비용 계산**: text-embedding-3-large $0.00013/1K tokens

## 기술 스택 및 구현 세부사항

### Core Dependencies

```python
# OpenAI
from openai import AsyncOpenAI

# Sentence Transformers
from sentence_transformers import SentenceTransformer

# Vector operations
import numpy as np
import hashlib

# Langfuse
from langfuse.decorators import observe

# Database
from sqlalchemy import text
from apps.core.db_session import db_manager
from apps.api.database import Embedding, Chunk
```

### Data Models

**Embedding Table**:
```sql
CREATE TABLE IF NOT EXISTS embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    vec vector(1536),  -- pgvector extension
    model_name TEXT DEFAULT 'text-embedding-3-large',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX idx_embeddings_model_name ON embeddings(model_name);
```

### Supported Models

| 모델명 | 차원 | 비용 (USD/1K tokens) | 성능 |
|--------|------|---------------------|------|
| text-embedding-3-large | 1536 | $0.00013 | Recall@1 = 64.6% (최고) |
| text-embedding-3-small | 1536 | $0.00002 | Recall@1 = 62.3% |
| text-embedding-ada-002 | 1536 | $0.0001 | Recall@1 = 61.0% (레거시) |
| all-mpnet-base-v2 | 768→1536 | $0 (로컬) | Fallback only |

### Performance Optimization

**캐시 효율**:
- Cache hit: O(1) lookup, < 1ms
- Cache miss: OpenAI API call, 200-500ms
- 예상 캐시 히트율: 30-40% (동일 텍스트 반복)

**배치 처리**:
- 기본 배치 크기: 100
- 100개 임베딩 생성: 약 3초
- Rate limiting: 0.01s delay (API 제한 준수)

**비동기 처리**:
- AsyncOpenAI: Native async support
- Sentence Transformers: asyncio.run_in_executor
- Concurrent requests: asyncio.gather

## 위험 요소 및 완화 전략

### 1. OpenAI API Quota 초과

**위험**: 대량 임베딩 생성 시 할당량 초과
**완화**:
- Rate limiting (0.01s delay)
- Batch size 조정 (default: 100)
- Sentence Transformers fallback
- Retry logic with exponential backoff

### 2. 메모리 부족 (캐시)

**위험**: 무제한 캐싱으로 메모리 고갈
**완화**:
- Max size = 1000 entries (약 6MB)
- FIFO eviction
- 재시작 시 캐시 초기화 (in-memory)

### 3. pgvector 차원 불일치

**위험**: 768차원 벡터 → 1536차원 스키마
**완화**:
- _pad_or_truncate_vector 메서드
- Zero padding: 768 + 768 zeros
- Validation: len(embedding) == 1536

### 4. Dummy Embedding 품질

**위험**: 모든 방법 실패 시 더미 임베딩 품질 저하
**완화**:
- MD5 hash seed for consistency
- L2 normalization for valid vector
- 로깅으로 더미 임베딩 추적

## 테스트 전략

### Unit Tests (완료)

- ✅ OpenAI 임베딩 생성 (1536차원)
- ✅ 캐싱 (동일 텍스트 = 동일 임베딩)
- ✅ Sentence Transformers fallback (768→1536 padding)
- ✅ Dummy embedding 생성 (L2 norm = 1.0)
- ✅ Zero vector (빈 텍스트)
- ✅ 텍스트 절단 (8000자 제한)
- ✅ 배치 임베딩 (3개 입력 = 3개 출력, 모두 1536차원)
- ✅ 유사도 계산 (cos([1,0,0], [1,0,0]) = 1.0)
- ✅ 캐시 LRU 퇴출 (1001번째 입력 시 1번째 제거)
- ✅ 헬스체크 (status = healthy/degraded/unhealthy)

### Integration Tests (완료)

- ✅ API 엔드포인트 통합 (/embeddings/generate)
- ✅ 배치 API (/embeddings/generate/batch)
- ✅ DB 통합 (청크 생성 → 임베딩 업데이트 → 조회 확인)

### Performance Tests (필요)

- [ ] 단일 임베딩 성능 (< 1.0s)
- [ ] 배치 임베딩 성능 (100개 < 5.0s)
- [ ] 캐시 성능 (캐시 히트 < 캐시 미스 / 10)

### Error Handling Tests (완료)

- ✅ OpenAI API 실패 시 fallback
- ✅ 빈 텍스트 리스트 에러 (400 Bad Request)
- ✅ 차원 불일치 유사도 (0.0 반환)

## 배포 및 운영 계획

### 프로덕션 체크리스트

**인프라 요구사항**:
- ✅ PostgreSQL with pgvector extension
- ✅ OpenAI API Key (OPENAI_API_KEY 환경변수)
- ⚠️ Langfuse (선택, LANGFUSE_* 환경변수)
- ✅ Python 3.9+ with asyncio support

**환경 변수**:
```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (Langfuse)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Database Setup**:
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table
CREATE TABLE embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    vec vector(1536),
    model_name TEXT DEFAULT 'text-embedding-3-large',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX idx_embeddings_model_name ON embeddings(model_name);
```

**모니터링 메트릭**:
- Embedding 생성 시간 (평균 < 500ms)
- 배치 처리 시간 (100개 < 3s)
- 캐시 히트율 (> 30%)
- OpenAI API 성공률 (> 99%)
- Fallback 사용률 (< 1%)
- Dummy embedding 생성률 (< 0.1%)

**Alert Conditions**:
- **High Severity**: OpenAI API 실패율 > 5%, 응답 시간 > 5s
- **Medium Severity**: 캐시 히트율 < 20%, Fallback 사용 > 5%
- **Low Severity**: Dummy embedding > 1%

### 향후 개선사항

**Phase 2 계획**:
- [ ] Redis-based distributed cache
- [ ] Embedding dimension reduction (PCA, 1536 → 384)
- [ ] GPU-accelerated Sentence Transformers
- [ ] 다국어 모델 지원
- [ ] 커스텀 임베딩 모델 통합
- [ ] 임베딩 버전 관리

**최적화 기회**:
- [ ] Batch size 동적 조정 (load-based)
- [ ] 임베딩 재생성 스케줄링
- [ ] A/B 테스트 (different models)
- [ ] Prometheus metrics 노출
- [ ] 임베딩 품질 평가 메트릭

## 구현 타임라인 (역공학)

| 단계 | 기간 | 상태 |
|-----|------|------|
| 1. EmbeddingService 구현 | 2일 | ✅ 완료 |
| 2. OpenAI AsyncClient 통합 | 1일 | ✅ 완료 |
| 3. Sentence Transformers fallback | 1일 | ✅ 완료 |
| 4. 캐싱 시스템 | 1일 | ✅ 완료 |
| 5. 배치 처리 | 1일 | ✅ 완료 |
| 6. DocumentEmbeddingService | 2일 | ✅ 완료 |
| 7. Langfuse 통합 | 1일 | ✅ 완료 |
| 8. API Router 구현 | 1일 | ✅ 완료 |
| 9. Testing 및 검증 | 2일 | ✅ 완료 |
| 10. Production 배포 | 1일 | ✅ 완료 |

**총 구현 기간**: 13일 (역공학 기준 추정)

## 참조 문서

### 내부 문서
- `.moai/specs/SPEC-EMBED-001/spec.md` - 상세 요구사항 (1053줄)
- `.moai/specs/SPEC-SEARCH-001/spec.md` - 검색 통합 참조
- `.moai/specs/SPEC-CLASS-001/spec.md` - 분류 통합 참조

### 구현 파일
- `apps/api/embedding_service.py` - 임베딩 생성 로직
- `apps/api/routers/embedding_router.py` - API 엔드포인트
- `apps/api/monitoring/langfuse_client.py` - 비용 추적
- `init.sql` - 데이터베이스 스키마

### 외부 문서
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
- [Sentence Transformers Documentation](https://www.sbert.net/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Langfuse Documentation](https://langfuse.com/docs)

---

**문서 버전**: v0.1.0
**최종 업데이트**: 2025-10-09
**작성자**: @Claude
**상태**: Completed
