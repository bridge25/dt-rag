# 하이브리드 검색 시스템 최적화 가이드

## 🎯 개요

이 가이드는 BM25 + Vector + Cross-Encoder 하이브리드 검색 시스템의 성능을 최적화하는 방법을 제공합니다.

## 📚 목차

1. [시스템 아키텍처](#시스템-아키텍처)
2. [BM25 최적화](#bm25-최적화)
3. [벡터 검색 최적화](#벡터-검색-최적화)
4. [하이브리드 융합 최적화](#하이브리드-융합-최적화)
5. [Cross-Encoder 리랭킹 최적화](#cross-encoder-리랭킹-최적화)
6. [캐싱 및 성능 최적화](#캐싱-및-성능-최적화)
7. [배포 및 운영 최적화](#배포-및-운영-최적화)

## 🏗️ 시스템 아키텍처

### 전체 워크플로우

```
Query Input
    ↓
Query Optimization ← 캐시 조회
    ↓
┌─────────────┬─────────────┐
│ BM25 Search │ Vector Search│ (병렬 실행)
└─────────────┴─────────────┘
    ↓
Hybrid Score Fusion
    ↓
Cross-Encoder Reranking
    ↓
Final Results → 캐시 저장
```

### 핵심 컴포넌트

- **BM25Engine**: 키워드 기반 검색
- **VectorEngine**: 의미적 유사도 검색
- **HybridFusion**: 점수 융합 및 정규화
- **CrossEncoderReranker**: 정밀 리랭킹
- **SearchCache**: Redis/로컬 캐싱
- **PerformanceMonitor**: 성능 모니터링

## 🔍 BM25 최적화

### 1. 파라미터 튜닝

```python
# 기본 설정 (범용)
BM25_K1 = 1.5  # Term frequency saturation (1.2-2.0)
BM25_B = 0.75   # Document length normalization (0.0-1.0)

# 짧은 문서용 (chunk 기반)
BM25_K1 = 1.8  # 높은 값으로 TF 중요도 증가
BM25_B = 0.6   # 문서 길이 정규화 감소

# 긴 문서용
BM25_K1 = 1.2  # 낮은 값으로 TF saturation 빠르게
BM25_B = 0.9   # 문서 길이 정규화 강화
```

### 2. 인덱스 최적화

#### PostgreSQL with GIN Index

```sql
-- Full-text search 인덱스
CREATE INDEX CONCURRENTLY idx_chunks_text_gin
ON chunks USING gin(to_tsvector('english', text));

-- 복합 인덱스 (필터링 + 검색)
CREATE INDEX CONCURRENTLY idx_chunks_composite
ON chunks(doc_id, to_tsvector('english', text))
WHERE text IS NOT NULL;

-- 인덱스 통계 업데이트
ANALYZE chunks;
```

#### SQLite with FTS5

```sql
-- FTS5 가상 테이블 생성
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    chunk_id,
    text,
    title,
    content='chunks',
    tokenize='porter'
);

-- 데이터 동기화
INSERT INTO chunks_fts(chunk_id, text, title)
SELECT chunk_id, text, title FROM chunks;
```

### 3. 쿼리 최적화

```python
def optimize_bm25_query(query: str) -> str:
    """BM25용 쿼리 최적화"""
    # 1. 불용어 제거 (선택적)
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but'}
    words = [w for w in query.split() if w.lower() not in stopwords]

    # 2. 동의어 확장
    expanded_words = []
    for word in words:
        expanded_words.append(word)
        synonyms = get_synonyms(word)  # 사용자 정의 함수
        expanded_words.extend(synonyms[:2])  # 최대 2개 동의어

    return " ".join(expanded_words)
```

## 🎯 벡터 검색 최적화

### 1. 임베딩 모델 선택

```python
# 성능 vs 품질 트레이드오프
EMBEDDING_MODELS = {
    # 고성능 (빠름, 작은 차원)
    'sentence-transformers/all-MiniLM-L6-v2': {
        'dimensions': 384,
        'speed': 'fast',
        'quality': 'good'
    },

    # 균형
    'text-embedding-ada-002': {
        'dimensions': 1536,
        'speed': 'medium',
        'quality': 'excellent'
    },

    # 고품질 (느림, 큰 차원)
    'sentence-transformers/all-mpnet-base-v2': {
        'dimensions': 768,
        'speed': 'slow',
        'quality': 'excellent'
    }
}
```

### 2. 벡터 인덱스 최적화

#### pgvector with HNSW

```sql
-- HNSW 인덱스 (높은 품질)
CREATE INDEX CONCURRENTLY idx_chunks_embedding_hnsw
ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- IVFFlat 인덱스 (빠른 속도)
CREATE INDEX CONCURRENTLY idx_chunks_embedding_ivfflat
ON chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 런타임 설정
SET hnsw.ef_search = 40;  -- 검색 정확도 vs 속도
SET ivfflat.probes = 10;  -- 탐색할 클러스터 수
```

### 3. 임베딩 캐싱

```python
class EmbeddingCache:
    async def get_or_create_embedding(self, text: str) -> np.ndarray:
        # 1. 텍스트 해시 생성
        text_hash = hashlib.md5(text.encode()).hexdigest()

        # 2. 캐시 조회
        cached = await self.cache.get(f"emb:{text_hash}")
        if cached:
            return np.frombuffer(cached, dtype=np.float32)

        # 3. 임베딩 생성
        embedding = await self.embedding_service.generate(text)

        # 4. 캐시 저장 (24시간)
        await self.cache.setex(
            f"emb:{text_hash}",
            86400,
            embedding.tobytes()
        )

        return embedding
```

### 4. 배치 처리 최적화

```python
async def batch_vector_search(
    self,
    queries: List[str],
    batch_size: int = 10
) -> List[List[Dict]]:
    """벡터 검색 배치 처리"""

    # 1. 임베딩 배치 생성
    embeddings = await self.batch_generate_embeddings(queries)

    # 2. 배치 검색 실행
    results = []
    for i in range(0, len(embeddings), batch_size):
        batch_embeddings = embeddings[i:i + batch_size]
        batch_results = await self.batch_search_vectors(batch_embeddings)
        results.extend(batch_results)

    return results
```

## ⚖️ 하이브리드 융합 최적화

### 1. 점수 정규화 방법 선택

```python
# 상황별 정규화 방법
NORMALIZATION_STRATEGIES = {
    # 점수 범위가 다를 때
    'min_max': MinMaxNormalization,

    # 점수 분포가 정규분포에 가까울 때
    'z_score': ZScoreNormalization,

    # 순위가 중요할 때
    'rank_based': RankBasedNormalization,

    # 상위 결과에 집중할 때
    'reciprocal_rank': ReciprocalRankNormalization
}
```

### 2. 융합 방법 최적화

```python
def select_fusion_method(query_characteristics: Dict) -> FusionMethod:
    """쿼리 특성에 따른 융합 방법 선택"""

    # 짧은 키워드 쿼리 → BM25 우선
    if query_characteristics['word_count'] <= 2:
        return FusionMethod.WEIGHTED_SUM  # BM25 가중치 높게

    # 긴 자연어 쿼리 → Vector 우선
    elif query_characteristics['word_count'] >= 6:
        return FusionMethod.RRF  # Reciprocal Rank Fusion

    # 구문 검색 → BM25 우선
    elif query_characteristics['has_quotes']:
        return FusionMethod.WEIGHTED_SUM  # BM25 가중치 높게

    # 기술 용어 → Vector 우선
    elif query_characteristics['has_technical_terms']:
        return FusionMethod.RRF

    # 기본값
    else:
        return FusionMethod.WEIGHTED_SUM
```

### 3. 가중치 자동 조정

```python
class AdaptiveWeighting:
    def __init__(self):
        self.performance_history = defaultdict(list)

    def adjust_weights(
        self,
        query: str,
        user_feedback: float
    ) -> Tuple[float, float]:
        """사용자 피드백 기반 가중치 조정"""

        query_type = self.classify_query(query)

        # 성능 이력 기반 가중치 계산
        if query_type in self.performance_history:
            # 최근 성능이 좋았던 설정 우선
            recent_performance = self.performance_history[query_type][-10:]
            best_config = max(recent_performance, key=lambda x: x['score'])
            return best_config['bm25_weight'], best_config['vector_weight']

        # 기본 가중치
        return 0.5, 0.5
```

## 🎭 Cross-Encoder 리랭킹 최적화

### 1. 모델 선택

```python
# 성능별 모델 추천
RERANKING_MODELS = {
    # 빠른 속도 (추천)
    'cross-encoder/ms-marco-MiniLM-L-6-v2': {
        'speed': 'fast',
        'quality': 'good',
        'max_length': 512
    },

    # 균형
    'cross-encoder/ms-marco-MiniLM-L-12-v2': {
        'speed': 'medium',
        'quality': 'excellent',
        'max_length': 512
    },

    # 최고 품질
    'cross-encoder/ms-marco-electra-base': {
        'speed': 'slow',
        'quality': 'best',
        'max_length': 512
    }
}
```

### 2. 다단계 리랭킹

```python
async def multi_stage_rerank(
    self,
    query: str,
    candidates: List[Dict],
    final_k: int = 5
) -> List[Dict]:
    """3단계 리랭킹"""

    # Stage 1: 빠른 필터링 (50 → 20)
    stage1 = await self.fast_rerank(query, candidates, 20)

    # Stage 2: Cross-encoder (20 → 10)
    stage2 = await self.cross_encoder_rerank(query, stage1, 10)

    # Stage 3: 다양성 보장 (10 → 5)
    final = self.diversity_rerank(stage2, final_k)

    return final
```

### 3. 배치 처리 최적화

```python
class OptimizedCrossEncoder:
    def __init__(self, batch_size: int = 32):
        self.batch_size = batch_size
        self.model_cache = {}

    async def batch_rerank(
        self,
        query: str,
        candidates: List[Dict]
    ) -> List[Dict]:
        """배치 단위 리랭킹"""

        # 쿼리-문서 쌍 생성
        pairs = [(query, doc['text'][:500]) for doc in candidates]

        # 배치 처리
        scores = []
        for i in range(0, len(pairs), self.batch_size):
            batch = pairs[i:i + self.batch_size]
            batch_scores = await self.model.predict(batch)
            scores.extend(batch_scores)

        # 점수 할당 및 정렬
        for doc, score in zip(candidates, scores):
            doc['rerank_score'] = float(score)

        return sorted(candidates, key=lambda x: x['rerank_score'], reverse=True)
```

## 🚀 캐싱 및 성능 최적화

### 1. Redis 캐싱 설정

```python
# Redis 설정 최적화
REDIS_CONFIG = {
    'decode_responses': True,
    'health_check_interval': 30,
    'socket_keepalive': True,
    'socket_keepalive_options': {},
    'connection_pool_kwargs': {
        'max_connections': 50,
        'retry_on_timeout': True
    }
}

# 캐시 TTL 설정
CACHE_TTL = {
    'search_results': 3600,      # 1시간
    'embeddings': 86400 * 7,     # 1주일
    'query_suggestions': 3600,   # 1시간
    'user_preferences': 86400    # 1일
}
```

### 2. 메모리 최적화

```python
class MemoryOptimizedSearch:
    def __init__(self):
        # 임베딩 양자화 (메모리 50% 절약)
        self.use_quantization = True
        self.quantization_bits = 8

        # 결과 스트리밍
        self.enable_streaming = True
        self.stream_batch_size = 10

    async def quantize_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """임베딩 양자화"""
        if self.use_quantization:
            # Float32 → Int8 변환
            min_val, max_val = embeddings.min(), embeddings.max()
            scale = (max_val - min_val) / 255
            quantized = ((embeddings - min_val) / scale).astype(np.uint8)
            return quantized, scale, min_val
        return embeddings
```

### 3. 비동기 최적화

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncOptimizedEngine:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.semaphore = asyncio.Semaphore(10)  # 동시 요청 제한

    async def search_with_concurrency_limit(
        self,
        session: AsyncSession,
        query: str
    ) -> SearchResponse:
        async with self.semaphore:
            # BM25와 Vector 검색 병렬 실행
            bm25_task = self.bm25_search(session, query)
            vector_task = self.vector_search(session, query)

            bm25_results, vector_results = await asyncio.gather(
                bm25_task, vector_task
            )

            # CPU 집약적 작업은 ThreadPool에서 실행
            fusion_task = asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.fusion_engine.fuse_results,
                bm25_results,
                vector_results
            )

            fused_results = await fusion_task
            return fused_results
```

## 🗄️ 데이터베이스 최적화

### 1. 연결 풀 설정

```python
# SQLAlchemy 연결 풀 최적화
ENGINE_CONFIG = {
    'pool_size': 20,           # 기본 연결 수
    'max_overflow': 30,        # 추가 연결 수
    'pool_timeout': 30,        # 연결 대기 시간
    'pool_recycle': 3600,      # 연결 재사용 시간
    'pool_pre_ping': True,     # 연결 상태 확인
}

# PostgreSQL 전용 설정
POSTGRESQL_CONFIG = {
    'statement_timeout': 30000,    # 30초
    'lock_timeout': 10000,         # 10초
    'idle_in_transaction_session_timeout': 60000,  # 1분
}
```

### 2. 쿼리 최적화

```sql
-- 복합 인덱스 활용
CREATE INDEX CONCURRENTLY idx_chunks_search_optimized
ON chunks(doc_id, LENGTH(text), to_tsvector('english', text))
WHERE text IS NOT NULL AND LENGTH(text) > 50;

-- 파티셔닝 (대용량 데이터)
CREATE TABLE chunks_partitioned (
    LIKE chunks INCLUDING ALL
) PARTITION BY RANGE (doc_id);

-- 통계 최적화
ALTER TABLE chunks ALTER COLUMN text SET STATISTICS 1000;
ANALYZE chunks;
```

### 3. 배치 Insert 최적화

```python
async def bulk_insert_embeddings(
    session: AsyncSession,
    embeddings_data: List[Dict]
) -> None:
    """배치 임베딩 삽입"""

    # 배치 크기 설정
    batch_size = 1000

    for i in range(0, len(embeddings_data), batch_size):
        batch = embeddings_data[i:i + batch_size]

        # PostgreSQL COPY 사용
        if "postgresql" in str(session.bind.url):
            await session.execute(
                text("""
                COPY chunks(chunk_id, text, embedding)
                FROM STDIN WITH CSV
                """),
                batch
            )
        else:
            # SQLite executemany 사용
            await session.execute(
                insert(Chunk),
                batch
            )

        await session.commit()
```

## 📊 모니터링 및 알람

### 1. 성능 메트릭 추적

```python
class SearchMetrics:
    def __init__(self):
        self.metrics = {
            'search_latency_p95': Histogram('search_latency_p95'),
            'search_throughput': Counter('search_requests_total'),
            'cache_hit_rate': Gauge('cache_hit_rate'),
            'error_rate': Gauge('search_error_rate'),
            'result_quality': Histogram('result_quality_score')
        }

    def record_search(
        self,
        latency: float,
        result_count: int,
        cache_hit: bool,
        error: bool = False
    ):
        self.metrics['search_latency_p95'].observe(latency)
        self.metrics['search_throughput'].inc()

        if cache_hit:
            self.metrics['cache_hit_rate'].inc()

        if error:
            self.metrics['error_rate'].inc()
```

### 2. 알람 설정

```python
# 성능 임계치
PERFORMANCE_THRESHOLDS = {
    'p95_latency_ms': 1000,      # 1초
    'error_rate_percent': 5,      # 5%
    'cache_hit_rate_percent': 70, # 70%
    'throughput_qps': 10          # 10 QPS
}

async def check_performance_alerts():
    """성능 알람 확인"""
    metrics = get_current_metrics()

    alerts = []

    if metrics['p95_latency'] > PERFORMANCE_THRESHOLDS['p95_latency_ms']:
        alerts.append(f"High latency: {metrics['p95_latency']}ms")

    if metrics['error_rate'] > PERFORMANCE_THRESHOLDS['error_rate_percent']:
        alerts.append(f"High error rate: {metrics['error_rate']}%")

    if alerts:
        await send_alert_notification(alerts)
```

## 🚀 배포 최적화

### 1. Docker 최적화

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# 애플리케이션 코드
COPY . .

# 환경 변수
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Kubernetes 설정

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hybrid-search
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hybrid-search
  template:
    metadata:
      labels:
        app: hybrid-search
    spec:
      containers:
      - name: hybrid-search
        image: hybrid-search:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: hybrid-search-service
spec:
  selector:
    app: hybrid-search
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. 오토스케일링

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: hybrid-search-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hybrid-search
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 📈 성능 벤치마크

### 목표 성능 지표

| 메트릭 | 목표 값 | 설명 |
|--------|---------|------|
| **Recall@10** | ≥ 0.85 | 상위 10개 결과 중 관련 문서 비율 |
| **P95 Latency** | ≤ 1s | 95%의 쿼리가 1초 내 완료 |
| **Throughput** | ≥ 50 QPS | 초당 50개 쿼리 처리 |
| **Cache Hit Rate** | ≥ 70% | 캐시 적중률 70% 이상 |
| **Error Rate** | ≤ 1% | 오류율 1% 이하 |
| **Cost per Search** | ≤ ₩3 | 검색당 비용 3원 이하 |

### 실제 성능 측정

```bash
# 성능 테스트 실행
python -m pytest tests/test_hybrid_search_performance.py -v

# 벤치마크 실행
python examples/benchmark_search_performance.py \
    --queries 1000 \
    --concurrent-users 10 \
    --duration 300

# 결과 분석
python scripts/analyze_performance_results.py \
    --results-file benchmark_results.json
```

## 🔧 트러블슈팅

### 일반적인 문제들

#### 1. 높은 지연시간
```python
# 원인 분석
async def diagnose_latency():
    # BM25 vs Vector 시간 비교
    # 인덱스 상태 확인
    # 캐시 히트율 확인
    # 데이터베이스 연결 상태 확인
```

#### 2. 낮은 정확도
```python
# 개선 방법
async def improve_accuracy():
    # BM25 파라미터 튜닝
    # 임베딩 모델 변경
    # 융합 가중치 조정
    # 리랭킹 모델 업그레이드
```

#### 3. 메모리 부족
```python
# 메모리 최적화
async def optimize_memory():
    # 임베딩 양자화
    # 배치 크기 축소
    # 캐시 크기 조정
    # 가비지 컬렉션 최적화
```

## 📚 추가 자료

- [BM25 알고리즘 상세 설명](https://en.wikipedia.org/wiki/Okapi_BM25)
- [pgvector 공식 문서](https://github.com/pgvector/pgvector)
- [Sentence Transformers 모델 목록](https://www.sbert.net/docs/pretrained_models.html)
- [Cross-Encoder 모델 허브](https://huggingface.co/cross-encoder)

---

## 🎉 결론

이 가이드를 따라 구현하면 다음과 같은 성능을 달성할 수 있습니다:

- **검색 정확도**: Recall@10 ≥ 85%
- **검색 속도**: P95 ≤ 1초
- **처리량**: 50+ QPS
- **비용 효율성**: ≤ ₩3/검색

지속적인 모니터링과 최적화를 통해 더욱 향상된 성능을 달성할 수 있습니다.