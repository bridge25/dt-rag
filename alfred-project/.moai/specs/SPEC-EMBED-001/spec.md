---
id: EMBED-001
version: 0.1.0
status: completed
created: 2025-10-07
updated: 2025-10-08
author: @Alfred
priority: high

category: feature
labels:
  - embedding
  - openai
  - vector
  - pgvector

scope:
  packages:
    - apps/api/embedding_service.py
    - apps/api/routers/embedding_router.py
  files:
    - embedding_service.py
    - embedding_router.py

related_specs:
  - SEARCH-001
---

# @SPEC:EMBED-001: OpenAI 기반 벡터 임베딩 서비스

## HISTORY

### v0.1.0 (2025-10-08)
- **COMPLETED**: E2E 테스트 완료 및 검증
  - OpenAI text-embedding-3-large 정상 작동 확인 (1536차원)
  - 폴백 메커니즘 (Sentence Transformers) 준비 완료
  - 캐싱 기능 정상 작동 (cache_size: 2)
  - API 응답 시간: 즉시 (캐시 히트)
  - Phase 6 Hybrid Search에서 벡터 검색 검증 완료

### v0.1.0 (2025-10-07)
- **INITIAL**: OpenAI text-embedding-3-large 기반 임베딩 서비스 명세 작성
- **AUTHOR**: @Alfred
- **SCOPE**: 임베딩 생성, 배치 처리, 캐싱, 문서 임베딩 업데이트
- **CONTEXT**: dt-rag v1.8.1 프로젝트의 핵심 벡터 임베딩 시스템 역공학

---

## 개요

DT-RAG 프로젝트의 벡터 임베딩 서비스는 OpenAI의 text-embedding-3-large 모델을 사용하여 텍스트를 1536차원 벡터로 변환한다. PostgreSQL pgvector와 통합되어 하이브리드 검색 시스템의 의미론적 검색을 지원한다.

### 핵심 기능

1. **OpenAI 기반 임베딩 생성**: text-embedding-3-large (1536차원)
2. **폴백 메커니즘**: Sentence Transformers (all-mpnet-base-v2, 768차원 → 1536차원 패딩)
3. **배치 처리**: 대량 문서 임베딩 생성 최적화
4. **인메모리 캐싱**: MD5 해시 기반 중복 임베딩 방지
5. **문서 임베딩 관리**: 데이터베이스 동기화 및 업데이트
6. **Langfuse 통합**: LLM 비용 추적 및 모니터링

---

## EARS 요구사항

### Ubiquitous Requirements (기본 요구사항)

- 시스템은 텍스트를 1536차원 벡터로 변환하는 임베딩 생성 기능을 제공해야 한다
- 시스템은 OpenAI text-embedding-3-large 모델을 기본 임베딩 엔진으로 사용해야 한다
- 시스템은 PostgreSQL pgvector와 호환되는 벡터 형식을 생성해야 한다
- 시스템은 단일 텍스트 및 배치 텍스트 임베딩을 모두 지원해야 한다
- 시스템은 임베딩 간 코사인 유사도 계산 기능을 제공해야 한다

### Event-driven Requirements (이벤트 기반)

- WHEN OpenAI API 키가 없거나 OpenAI 클라이언트 초기화 실패 시, 시스템은 Sentence Transformers 폴백 모델로 전환해야 한다
- WHEN 빈 텍스트 또는 공백 문자만 포함된 텍스트 입력 시, 시스템은 1536차원 제로 벡터를 반환해야 한다
- WHEN 임베딩 생성 중 예외 발생 시, 시스템은 텍스트 기반 시드 더미 임베딩을 생성해야 한다
- WHEN 캐싱이 활성화되고 동일 텍스트 요청 시, 시스템은 캐시된 임베딩을 반환해야 한다
- WHEN 캐시 크기가 1000개 항목을 초과하면, 시스템은 가장 오래된 항목을 제거해야 한다
- WHEN 배치 임베딩 생성 중 특정 배치 실패 시, 시스템은 해당 배치의 각 텍스트에 대해 더미 임베딩을 생성해야 한다

### State-driven Requirements (상태 기반)

- WHILE OpenAI 클라이언트가 활성화된 상태일 때, 시스템은 OpenAI API를 사용하여 임베딩을 생성해야 한다
- WHILE 폴백 모드일 때, 시스템은 Sentence Transformers 모델을 로드하고 768차원 벡터를 1536차원으로 패딩해야 한다
- WHILE Langfuse가 활성화된 상태일 때, 시스템은 모든 임베딩 생성 작업을 추적하고 비용을 기록해야 한다
- WHILE 문서 임베딩 업데이트 진행 중일 때, 시스템은 배치 단위로 진행 상황을 로깅해야 한다

### Optional Features (선택적 기능)

- WHERE 캐싱이 활성화되면, 시스템은 MD5 해시 기반 캐시 키로 임베딩을 저장할 수 있다
- WHERE 배치 처리 시, 시스템은 진행 상황 표시(show_progress)를 제공할 수 있다
- WHERE 문서 임베딩 업데이트 시, 시스템은 특정 문서 ID 목록 또는 전체 문서를 대상으로 선택할 수 있다

### Constraints (제약사항)

- IF 텍스트 길이가 8000자를 초과하면, 시스템은 텍스트를 8000자로 잘라야 한다
- IF 폴백 모델 벡터 차원이 1536이 아니면, 시스템은 패딩 또는 절단으로 1536차원으로 맞춰야 한다
- IF 유사도 계산 시 벡터 차원이 불일치하면, 시스템은 0.0을 반환해야 한다
- IF 벡터의 L2 norm이 0이면, 시스템은 정규화를 건너뛰어야 한다
- 배치 크기는 최대 100개를 초과할 수 없어야 한다
- 단일 요청으로 처리할 수 있는 텍스트 개수는 최대 1000개를 초과할 수 없어야 한다

---

## 아키텍처

### 시스템 구성요소

```
┌─────────────────────────────────────────────────────────────┐
│                    Embedding Service Layer                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  EmbeddingService                                            │
│  ├── OpenAI Client (text-embedding-3-large)                 │
│  ├── Sentence Transformers (all-mpnet-base-v2) [Fallback]  │
│  ├── Cache Manager (MD5-based, LRU, max 1000)              │
│  └── Langfuse Observer (@observe decorator)                 │
│                                                               │
│  DocumentEmbeddingService                                    │
│  ├── Database Integration (PostgreSQL pgvector)            │
│  └── Batch Update Manager                                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Router Layer                    │
├─────────────────────────────────────────────────────────────┤
│  /embeddings/health        - 헬스체크                       │
│  /embeddings/info          - 서비스 정보                    │
│  /embeddings/status        - DB 상태                        │
│  /embeddings/generate      - 단일 임베딩 생성               │
│  /embeddings/generate/batch - 배치 임베딩 생성             │
│  /embeddings/similarity    - 유사도 계산                    │
│  /embeddings/documents/update - 문서 임베딩 업데이트       │
│  /embeddings/cache/clear   - 캐시 클리어                    │
│  /embeddings/models        - 지원 모델 목록                 │
│  /embeddings/analytics     - 분석 정보                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL + pgvector                      │
├─────────────────────────────────────────────────────────────┤
│  embeddings 테이블:                                         │
│    - embedding_id (UUID PK)                                 │
│    - chunk_id (UUID FK → chunks)                            │
│    - vec (vector(1536))                                     │
│    - model_name (TEXT)                                      │
│    - created_at (TIMESTAMP)                                 │
└─────────────────────────────────────────────────────────────┘
```

### 데이터 흐름

#### 단일 임베딩 생성
```
텍스트 입력
  ↓
텍스트 전처리 (최대 8000자)
  ↓
캐시 확인 (MD5 해시)
  ↓ (캐시 미스)
OpenAI API 호출 / Sentence Transformers 실행
  ↓
L2 정규화
  ↓
캐시 저장 (LRU, max 1000)
  ↓
1536차원 벡터 반환
```

#### 배치 임베딩 생성
```
텍스트 목록 (최대 1000개)
  ↓
배치 분할 (기본 100개씩)
  ↓
각 배치:
  - 텍스트 전처리
  - OpenAI 배치 API 호출 / Sentence Transformers 배치 실행
  - L2 정규화
  - 0.01초 대기 (Rate limiting)
  ↓
전체 벡터 목록 반환
```

#### 문서 임베딩 업데이트
```
문서 ID 목록 (선택적)
  ↓
DB 조회: 임베딩 없는 청크 조회
  ↓
배치 처리 (기본 100개씩):
  - 배치 임베딩 생성
  - DB INSERT (UPSERT)
  - COMMIT
  - 진행 로깅
  ↓
업데이트 결과 반환
```

---

## 모델 사양

### 지원 모델

| 모델명 | 차원 | 비용 (USD/1K tokens) | 설명 |
|--------|------|---------------------|------|
| text-embedding-3-large | 1536 | $0.00013 | OpenAI 최고 성능 임베딩 모델 (기본) |
| text-embedding-3-small | 1536 | $0.00002 | OpenAI 효율적 임베딩 모델 |
| text-embedding-ada-002 | 1536 | $0.0001 | OpenAI 레거시 임베딩 모델 |
| all-mpnet-base-v2 | 768 → 1536 | $0 (로컬) | Sentence Transformers 폴백 모델 |

### 폴백 메커니즘

1. **우선순위 1**: OpenAI API (OPENAI_API_KEY 필요)
2. **우선순위 2**: Sentence Transformers (로컬 모델)
   - 768차원 벡터 생성
   - 제로 패딩으로 1536차원 확장
   - `[0:768] = 실제 벡터, [768:1536] = 0.0`
3. **우선순위 3**: 더미 임베딩 (모든 방법 실패 시)
   - MD5 해시 기반 시드
   - 정규분포 난수 생성 (mean=0, std=0.1)
   - L2 정규화

---

## 구현 세부사항

### EmbeddingService 클래스

#### 주요 속성
```python
SUPPORTED_MODELS: Dict[str, Dict]  # 모델 설정 딕셔너리
TARGET_DIMENSIONS: int = 1536      # 목표 벡터 차원
model_name: str                     # 현재 사용 모델명
model_config: Dict                  # 현재 모델 설정
embedding_cache: Dict[str, List[float]]  # MD5 → 벡터 캐시
_openai_client: AsyncOpenAI         # OpenAI 비동기 클라이언트
_sentence_transformer: SentenceTransformer  # 폴백 모델
```

#### 핵심 메서드

**generate_embedding(text: str, use_cache: bool = True) -> List[float]**
- 데코레이터: `@observe(name="generate_embedding", as_type="embedding")`
- 단일 텍스트 임베딩 생성
- 캐싱 지원
- Langfuse 비용 추적

**batch_generate_embeddings(texts: List[str], batch_size: int = 100, show_progress: bool = True) -> List[List[float]]**
- 데코레이터: `@observe(name="batch_generate_embeddings", as_type="embedding")`
- 배치 임베딩 생성
- 배치 크기 조정 가능
- 진행 상황 로깅

**calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float**
- 코사인 유사도 계산
- 범위: [-1.0, 1.0]
- 차원 불일치 시 0.0 반환

**health_check() -> Dict[str, Any]**
- 서비스 상태 확인
- 상태: healthy, degraded, unhealthy
- OpenAI/폴백 모드 표시

**clear_cache() -> int**
- 캐시 클리어
- 제거된 항목 수 반환

#### 내부 메서드

**_preprocess_text(text: str) -> str**
- 공백 제거 (strip)
- 최대 8000자 제한

**_get_cache_key(text: str) -> str**
- MD5 해시 생성
- UTF-8 인코딩

**_normalize_vector(vector: List[float]) -> List[float]**
- L2 정규화
- norm이 0이면 원본 반환

**_pad_or_truncate_vector(vector: np.ndarray) -> List[float]**
- 768차원 → 1536차원: 제로 패딩
- 1536차원 초과 → 1536차원: 절단
- 1536차원: 그대로 반환

**_generate_openai_embedding(text: str) -> List[float]**
- OpenAI embeddings.create() 호출
- encoding_format="float"
- dimensions=1536

**_generate_sentence_transformer_embedding(text: str) -> List[float]**
- Sentence Transformers encode() 호출
- asyncio.run_in_executor로 비동기 실행
- 768차원 → 1536차원 패딩

**_generate_dummy_embedding(text: str) -> List[float]**
- MD5 해시 기반 시드
- 정규분포 난수 (mean=0, std=0.1)
- L2 정규화

**_generate_zero_vector() -> List[float]**
- 1536차원 제로 벡터 반환

**_load_sentence_transformer() -> Optional[SentenceTransformer]**
- 폴백 모델 지연 로드
- 싱글톤 패턴

### DocumentEmbeddingService 클래스

#### 주요 메서드

**update_document_embeddings(document_ids: Optional[List[str]] = None, batch_size: int = 100) -> Dict[str, Any]**
- 임베딩 없는 청크 조회 (LEFT JOIN)
- 배치 단위 임베딩 생성
- DB UPSERT (ON CONFLICT chunk_id DO UPDATE)
- 진행 상황 로깅

**get_embedding_status() -> Dict[str, Any]**
- 통계 조회:
  - total_chunks: 전체 청크 수
  - embedded_chunks: 임베딩 존재 청크 수
  - missing_embeddings: 임베딩 없는 청크 수
- 모델 분포: 모델별 임베딩 수
- 커버리지: (embedded_chunks / total_chunks) * 100

---

## API 엔드포인트

### GET /embeddings/health
헬스체크

**응답**:
```json
{
  "timestamp": "2025-10-07T12:00:00Z",
  "service": "embedding_service",
  "status": "healthy",
  "model_name": "text-embedding-3-large",
  "model_loaded": true,
  "target_dimensions": 1536,
  "openai_available": true,
  "cache_size": 42
}
```

### GET /embeddings/info
서비스 정보

**응답**:
```json
{
  "timestamp": "2025-10-07T12:00:00Z",
  "service": "embedding_service",
  "model_name": "text-embedding-3-large",
  "model_config": {
    "name": "text-embedding-3-large",
    "dimensions": 1536,
    "description": "OpenAI's most capable embedding model",
    "cost_per_1k_tokens": 0.00013
  },
  "target_dimensions": 1536,
  "model_loaded": false,
  "cache_size": 42,
  "openai_available": true,
  "sentence_transformers_available": true
}
```

### GET /embeddings/status
데이터베이스 임베딩 상태

**응답**:
```json
{
  "timestamp": "2025-10-07T12:00:00Z",
  "service": "document_embedding_service",
  "statistics": {
    "total_chunks": 1000,
    "embedded_chunks": 950,
    "missing_embeddings": 50
  },
  "model_distribution": {
    "text-embedding-3-large": 900,
    "text-embedding-ada-002": 50
  },
  "embedding_coverage_percent": 95.0,
  "current_model": "text-embedding-3-large",
  "target_dimensions": 1536,
  "service_status": { ... }
}
```

### POST /embeddings/generate
단일 임베딩 생성

**요청**:
```json
{
  "text": "DT-RAG 시스템의 핵심 기능은 무엇인가?",
  "use_cache": true
}
```

**응답**:
```json
{
  "text": "DT-RAG 시스템의 핵심 기능은 무엇인가?",
  "embedding": [0.023, -0.041, 0.015, ...],
  "dimensions": 1536,
  "model": "text-embedding-3-large",
  "cached": true,
  "timestamp": "2025-10-07T12:00:00Z"
}
```

### POST /embeddings/generate/batch
배치 임베딩 생성

**요청**:
```json
{
  "texts": [
    "첫 번째 텍스트",
    "두 번째 텍스트",
    "세 번째 텍스트"
  ],
  "batch_size": 32
}
```

**응답**:
```json
{
  "total_texts": 3,
  "valid_texts": 3,
  "embeddings": [
    [0.023, -0.041, ...],
    [0.015, 0.032, ...],
    [-0.009, 0.021, ...]
  ],
  "dimensions": 1536,
  "model": "text-embedding-3-large",
  "batch_size": 32,
  "timestamp": "2025-10-07T12:00:00Z"
}
```

### POST /embeddings/similarity
유사도 계산

**요청**:
```json
{
  "embedding1": [0.023, -0.041, 0.015, ...],
  "embedding2": [0.019, -0.038, 0.012, ...]
}
```

**응답**:
```json
{
  "similarity": 0.9234,
  "embedding1_dimensions": 1536,
  "embedding2_dimensions": 1536,
  "timestamp": "2025-10-07T12:00:00Z"
}
```

### POST /embeddings/documents/update
문서 임베딩 업데이트

**요청**:
```json
{
  "document_ids": ["uuid-1", "uuid-2"],
  "batch_size": 10,
  "run_in_background": false
}
```

**응답 (동기)**:
```json
{
  "completed_at": "2025-10-07T12:05:00Z",
  "success": true,
  "message": "임베딩 업데이트 완료",
  "updated_count": 150,
  "total_chunks": 150,
  "model_name": "text-embedding-3-large"
}
```

**응답 (백그라운드)**:
```json
{
  "message": "임베딩 업데이트가 백그라운드에서 시작되었습니다",
  "document_ids": ["uuid-1", "uuid-2"],
  "batch_size": 10,
  "started_at": "2025-10-07T12:00:00Z"
}
```

### POST /embeddings/cache/clear
캐시 클리어

**응답**:
```json
{
  "message": "임베딩 캐시가 클리어되었습니다",
  "cleared_items": 42,
  "timestamp": "2025-10-07T12:00:00Z"
}
```

### GET /embeddings/models
지원 모델 목록

**응답**:
```json
{
  "supported_models": {
    "text-embedding-3-large": { ... },
    "text-embedding-3-small": { ... },
    "text-embedding-ada-002": { ... },
    "all-mpnet-base-v2": { ... }
  },
  "current_model": "text-embedding-3-large",
  "target_dimensions": 1536,
  "timestamp": "2025-10-07T12:00:00Z"
}
```

### GET /embeddings/analytics
분석 정보

**응답**:
```json
{
  "timestamp": "2025-10-07T12:00:00Z",
  "service_health": { ... },
  "service_info": { ... },
  "database_status": { ... },
  "recommendations": [
    "임베딩 커버리지가 95.0%입니다. 문서 임베딩 업데이트를 실행하세요"
  ]
}
```

---

## 데이터베이스 스키마

### embeddings 테이블

```sql
CREATE TABLE IF NOT EXISTS embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    vec vector(1536),  -- pgvector extension
    model_name TEXT DEFAULT 'text-embedding-3-large',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**제약사항**:
- `chunk_id`는 `chunks` 테이블의 FK
- CASCADE DELETE: 청크 삭제 시 임베딩도 삭제
- UPSERT 지원: `ON CONFLICT (chunk_id) DO UPDATE`

### 인덱스 (권장)

```sql
CREATE INDEX idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX idx_embeddings_model_name ON embeddings(model_name);
```

---

## 캐싱 전략

### 캐시 키 생성
```python
cache_key = hashlib.md5(text.encode('utf-8')).hexdigest()
```

### 캐시 정책
- **타입**: 인메모리 딕셔너리
- **최대 크기**: 1000개 항목
- **퇴출 정책**: FIFO (Oldest First)
- **캐시 히트**: O(1) 조회
- **캐시 미스**: OpenAI API 호출 또는 폴백

### 캐시 관리
```python
if use_cache:
    cache_key = self._get_cache_key(text)
    if cache_key in self.embedding_cache:
        return self.embedding_cache[cache_key]

# 캐시 미스: 임베딩 생성
embedding = await self._generate_openai_embedding(processed_text)

if use_cache:
    self.embedding_cache[cache_key] = final_embedding
    if len(self.embedding_cache) > 1000:
        oldest_key = next(iter(self.embedding_cache))
        del self.embedding_cache[oldest_key]
```

---

## Langfuse 통합

### 데코레이터 적용
```python
@observe(name="generate_embedding", as_type="embedding")
async def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
    ...

@observe(name="batch_generate_embeddings", as_type="embedding")
async def batch_generate_embeddings(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
    ...
```

### 비용 추적
- **모델**: text-embedding-3-large
- **비용**: $0.00013 per 1K tokens
- **추적 항목**:
  - 입력 토큰 수
  - 총 비용 (USD)
  - 모델명
  - 타임스탬프

### 폴백 시 Langfuse
- Langfuse 미설치 시: no-op 데코레이터 사용
- 서비스 중단 없이 계속 작동

---

## 에러 처리

### 임베딩 생성 실패
```python
try:
    embedding = await self._generate_openai_embedding(processed_text)
except Exception as e:
    logger.error(f"임베딩 생성 실패: {e}")
    return await self._generate_dummy_embedding(text)
```

### 배치 처리 실패
```python
try:
    batch_embeddings = await self._openai_client.embeddings.create(...)
except Exception as e:
    logger.error(f"배치 {batch_num} 처리 실패: {e}")
    for text in batch_texts:
        dummy_emb = await self._generate_dummy_embedding(text)
        embeddings.append(dummy_emb)
```

### 유사도 계산 실패
```python
if len(vec1) != len(vec2):
    logger.warning(f"벡터 크기 불일치: {len(vec1)} vs {len(vec2)}")
    return 0.0

if norm1 == 0 or norm2 == 0:
    return 0.0
```

---

## 성능 최적화

### 배치 처리
- **기본 배치 크기**: 100
- **최대 배치 크기**: 100 (API 제약)
- **배치 간 대기**: 0.01초 (Rate limiting)

### 비동기 처리
- **OpenAI API**: 네이티브 비동기 클라이언트
- **Sentence Transformers**: asyncio.run_in_executor

### 캐싱
- **캐시 히트율**: 동일 텍스트 반복 시 100%
- **메모리 사용량**: 약 6MB per 1000 벡터

### 텍스트 전처리
- **최대 길이**: 8000자 (조기 절단)
- **공백 제거**: strip()

---

## 테스트 요구사항

### 단위 테스트

#### EmbeddingService
```python
@TEST:EMBED-001:01 - OpenAI 임베딩 생성 테스트
def test_generate_embedding_with_openai():
    service = EmbeddingService(model_name="text-embedding-3-large")
    embedding = await service.generate_embedding("테스트 텍스트")
    assert len(embedding) == 1536
    assert isinstance(embedding, list)
    assert all(isinstance(x, float) for x in embedding)

@TEST:EMBED-001:02 - 캐싱 테스트
def test_embedding_caching():
    service = EmbeddingService()
    embedding1 = await service.generate_embedding("same text", use_cache=True)
    embedding2 = await service.generate_embedding("same text", use_cache=True)
    assert embedding1 == embedding2
    assert service.embedding_cache[service._get_cache_key("same text")] == embedding1

@TEST:EMBED-001:03 - 폴백 테스트
def test_fallback_to_sentence_transformers():
    service = EmbeddingService(model_name="all-mpnet-base-v2")
    service._openai_client = None
    embedding = await service.generate_embedding("테스트")
    assert len(embedding) == 1536
    assert embedding[768:] == [0.0] * 768  # 패딩 확인

@TEST:EMBED-001:04 - 더미 임베딩 테스트
def test_generate_dummy_embedding():
    service = EmbeddingService()
    dummy = await service._generate_dummy_embedding("test")
    assert len(dummy) == 1536
    assert abs(np.linalg.norm(np.array(dummy)) - 1.0) < 1e-6  # L2 정규화 확인

@TEST:EMBED-001:05 - 빈 텍스트 테스트
def test_empty_text_zero_vector():
    service = EmbeddingService()
    zero_vec = await service.generate_embedding("")
    assert zero_vec == [0.0] * 1536

@TEST:EMBED-001:06 - 긴 텍스트 절단 테스트
def test_long_text_truncation():
    service = EmbeddingService()
    long_text = "a" * 10000
    processed = service._preprocess_text(long_text)
    assert len(processed) == 8000

@TEST:EMBED-001:07 - 배치 임베딩 테스트
def test_batch_generate_embeddings():
    service = EmbeddingService()
    texts = ["text1", "text2", "text3"]
    embeddings = await service.batch_generate_embeddings(texts, batch_size=2)
    assert len(embeddings) == 3
    assert all(len(emb) == 1536 for emb in embeddings)

@TEST:EMBED-001:08 - 유사도 계산 테스트
def test_calculate_similarity():
    service = EmbeddingService()
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    similarity = service.calculate_similarity(vec1, vec2)
    assert similarity == 1.0

@TEST:EMBED-001:09 - 캐시 LRU 테스트
def test_cache_lru_eviction():
    service = EmbeddingService()
    for i in range(1001):
        await service.generate_embedding(f"text{i}", use_cache=True)
    assert len(service.embedding_cache) == 1000
    assert service._get_cache_key("text0") not in service.embedding_cache

@TEST:EMBED-001:10 - 헬스체크 테스트
def test_health_check():
    service = EmbeddingService()
    health = service.health_check()
    assert health["status"] in ["healthy", "degraded", "unhealthy"]
    assert "target_dimensions" in health
    assert health["target_dimensions"] == 1536
```

#### DocumentEmbeddingService
```python
@TEST:EMBED-001:11 - 문서 임베딩 업데이트 테스트
async def test_update_document_embeddings():
    service = DocumentEmbeddingService(embedding_service)
    result = await service.update_document_embeddings(
        document_ids=["test-doc-1"],
        batch_size=10
    )
    assert result["success"] == True
    assert result["updated_count"] >= 0

@TEST:EMBED-001:12 - 임베딩 상태 조회 테스트
async def test_get_embedding_status():
    service = DocumentEmbeddingService(embedding_service)
    status = await service.get_embedding_status()
    assert "statistics" in status
    assert "embedding_coverage_percent" in status
    assert status["embedding_coverage_percent"] >= 0
    assert status["embedding_coverage_percent"] <= 100
```

### 통합 테스트

```python
@TEST:EMBED-001:20 - API 엔드포인트 통합 테스트
async def test_embedding_router_integration():
    response = await client.post(
        "/embeddings/generate",
        json={"text": "테스트 텍스트", "use_cache": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["embedding"]) == 1536
    assert data["model"] == "text-embedding-3-large"

@TEST:EMBED-001:21 - 배치 API 통합 테스트
async def test_batch_embedding_router():
    response = await client.post(
        "/embeddings/generate/batch",
        json={"texts": ["text1", "text2"], "batch_size": 32}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_texts"] == 2
    assert len(data["embeddings"]) == 2

@TEST:EMBED-001:22 - DB 통합 테스트
async def test_database_embedding_integration(db_session):
    # 청크 생성
    chunk = Chunk(text="테스트 청크", doc_id=test_doc_id)
    db_session.add(chunk)
    await db_session.commit()

    # 임베딩 업데이트
    result = await update_document_embeddings([test_doc_id], batch_size=10)

    # 확인
    embedding = await db_session.execute(
        select(Embedding).where(Embedding.chunk_id == chunk.chunk_id)
    )
    assert embedding.scalar_one_or_none() is not None
```

### 성능 테스트

```python
@TEST:EMBED-001:30 - 단일 임베딩 성능 테스트
async def test_single_embedding_performance():
    service = EmbeddingService()
    start = time.time()
    await service.generate_embedding("테스트 텍스트")
    duration = time.time() - start
    assert duration < 1.0  # 1초 이내

@TEST:EMBED-001:31 - 배치 임베딩 성능 테스트
async def test_batch_embedding_performance():
    service = EmbeddingService()
    texts = ["text"] * 100
    start = time.time()
    await service.batch_generate_embeddings(texts, batch_size=100)
    duration = time.time() - start
    assert duration < 5.0  # 5초 이내

@TEST:EMBED-001:32 - 캐시 성능 테스트
async def test_cache_performance():
    service = EmbeddingService()
    text = "반복 텍스트"

    # 첫 호출 (캐시 미스)
    start = time.time()
    await service.generate_embedding(text, use_cache=True)
    miss_duration = time.time() - start

    # 두 번째 호출 (캐시 히트)
    start = time.time()
    await service.generate_embedding(text, use_cache=True)
    hit_duration = time.time() - start

    assert hit_duration < miss_duration / 10  # 캐시는 최소 10배 빠름
```

### 에러 처리 테스트

```python
@TEST:EMBED-001:40 - OpenAI API 실패 시 폴백 테스트
async def test_openai_failure_fallback():
    service = EmbeddingService()
    service._openai_client.embeddings.create = AsyncMock(side_effect=Exception("API Error"))

    embedding = await service.generate_embedding("테스트")
    assert len(embedding) == 1536  # 더미 임베딩 생성 확인

@TEST:EMBED-001:41 - 빈 텍스트 리스트 에러 테스트
async def test_empty_texts_error():
    response = await client.post(
        "/embeddings/generate/batch",
        json={"texts": [], "batch_size": 32}
    )
    assert response.status_code == 400

@TEST:EMBED-001:42 - 차원 불일치 유사도 테스트
def test_dimension_mismatch_similarity():
    service = EmbeddingService()
    vec1 = [1.0] * 1536
    vec2 = [1.0] * 768
    similarity = service.calculate_similarity(vec1, vec2)
    assert similarity == 0.0
```

---

## 배포 및 운영

### 환경 변수

```bash
# OpenAI 설정
OPENAI_API_KEY=sk-...                # OpenAI API 키 (필수)

# Langfuse 설정 (선택)
LANGFUSE_ENABLED=true                # Langfuse 활성화
LANGFUSE_PUBLIC_KEY=pk-...           # Langfuse Public Key
LANGFUSE_SECRET_KEY=sk-...           # Langfuse Secret Key
LANGFUSE_HOST=https://cloud.langfuse.com  # Langfuse 호스트
```

### 의존성

```txt
openai>=1.0.0              # OpenAI API 클라이언트
sentence-transformers      # 폴백 모델
numpy                      # 벡터 연산
langfuse>=3.6.0           # LLM 비용 추적 (선택)
asyncpg                    # PostgreSQL 비동기 드라이버
sqlalchemy[asyncio]        # ORM
fastapi                    # API 프레임워크
```

### 모니터링

#### 헬스체크
```bash
curl http://localhost:8000/embeddings/health
```

#### 상태 확인
```bash
curl http://localhost:8000/embeddings/status
```

#### 분석 정보
```bash
curl http://localhost:8000/embeddings/analytics
```

### 로깅

```python
logger.info(f"OpenAI 클라이언트 초기화: {self.model_name} ({self.model_config['dimensions']}차원)")
logger.warning("OPENAI_API_KEY 없음, Sentence Transformers 폴백 사용")
logger.error(f"임베딩 생성 실패: {e}")
logger.debug(f"캐시에서 임베딩 반환: {text[:50]}...")
```

### 성능 메트릭

- **임베딩 생성 시간**: 평균 < 500ms (단일)
- **배치 처리 시간**: 평균 < 3초 (100개)
- **캐시 히트율**: > 30% (실사용 환경)
- **임베딩 커버리지**: > 95%

---

## 보안 고려사항

### API 키 보안
- OpenAI API 키는 환경 변수로 관리
- 코드나 로그에 노출 금지
- 키 로테이션 정책 수립

### 입력 검증
- 텍스트 최대 길이 제한 (8000자)
- 배치 크기 제한 (최대 100)
- 총 텍스트 개수 제한 (최대 1000)

### Rate Limiting
- 배치 간 0.01초 대기
- OpenAI API 할당량 모니터링

### 데이터 프라이버시
- 임베딩 캐시는 메모리에만 존재 (재시작 시 삭제)
- 개인정보 포함 텍스트 처리 시 주의

---

## 향후 개선사항

### 성능 최적화
- [ ] Redis 기반 분산 캐싱
- [ ] 임베딩 벡터 양자화 (차원 축소)
- [ ] GPU 가속 Sentence Transformers

### 기능 확장
- [ ] 다국어 모델 지원
- [ ] 커스텀 임베딩 모델 통합
- [ ] 임베딩 버전 관리

### 모니터링 강화
- [ ] Prometheus 메트릭 노출
- [ ] 임베딩 품질 평가 메트릭
- [ ] 비용 알림 시스템

### 운영 개선
- [ ] 임베딩 재생성 스케줄링
- [ ] A/B 테스트 프레임워크
- [ ] 자동 폴백 전환 로직

---

## 참조

### 외부 문서
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
- [Sentence Transformers Documentation](https://www.sbert.net/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [Langfuse Documentation](https://langfuse.com/docs)

### 내부 문서
- `.moai/specs/SPEC-SEARCH-001/spec.md` - 하이브리드 검색 시스템
- `apps/api/monitoring/langfuse_client.py` - Langfuse 통합
- `apps/search/hybrid_search_engine.py` - 검색 엔진 통합

### 관련 파일
- `apps/api/embedding_service.py` - 임베딩 서비스 구현
- `apps/api/routers/embedding_router.py` - API 라우터
- `init.sql` - 데이터베이스 스키마
- `apps/api/monitoring/langfuse_client.py` - 비용 추적

---

**문서 버전**: v0.1.0
**최종 업데이트**: 2025-10-07
**작성자**: @Alfred
**상태**: Active
