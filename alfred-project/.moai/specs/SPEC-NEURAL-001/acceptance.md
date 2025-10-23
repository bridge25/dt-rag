# Acceptance Criteria: SPEC-NEURAL-001

@SPEC:NEURAL-001 @VERSION:0.1.0 @ACCEPTANCE

---

## Given-When-Then 시나리오

### Scenario 1: Neural Search Activation

**Given**:
- 환경 변수: `FEATURE_NEURAL_CASE_SELECTOR=true`
- CaseBank 데이터:
  - Case 1: query="What is RAG?", query_vector=[0.1, 0.2, ..., 0.5] (1536 dims)
  - Case 2: query="Explain vector search", query_vector=[0.3, 0.4, ..., 0.6]
  - Case 3: query="Machine learning basics", query_vector=[0.2, 0.1, ..., 0.3]
- pgvector extension 설치 완료

**When**:
```bash
curl -X POST "http://localhost:8000/search/neural" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -d '{"q": "vector similarity search", "max_results": 3}'
```

**Then**:
- 응답 상태 코드: 200 OK
- 응답 JSON:
  ```json
  {
    "hits": [
      {"chunk_id": "case-2", "score": 0.89, "text": "Explain vector search", ...},
      {"chunk_id": "case-1", "score": 0.76, "text": "What is RAG?", ...},
      {"chunk_id": "case-3", "score": 0.45, "text": "Machine learning basics", ...}
    ],
    "latency": 0.095,
    "request_id": "uuid-xxx",
    "total_candidates": 3,
    "search_mode": "neural"
  }
  ```
- 검증 항목:
  - ✅ Vector 유사도 기반 정렬 (높은 순)
  - ✅ latency < 150ms
  - ✅ search_mode == "neural"
  - ✅ 상위 3개 케이스 반환

---

### Scenario 2: Hybrid Search with BM25 Fusion

**Given**:
- 환경 변수: `FEATURE_NEURAL_CASE_SELECTOR=true`
- CaseBank 데이터:
  - 10개 케이스 (각각 query_vector 포함)
- BM25 검색 결과: [case-1, case-4, case-7] (스코어: [0.8, 0.6, 0.5])
- Vector 검색 결과: [case-2, case-1, case-5] (스코어: [0.9, 0.7, 0.6])

**When**:
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -d '{"q": "hybrid query test", "max_results": 5}'
```

**Then**:
- 응답 상태 코드: 200 OK
- 하이브리드 스코어 계산:
  - Case-1: 0.7 * 0.7 + 0.3 * 0.8 = 0.73
  - Case-2: 0.7 * 0.9 + 0.3 * 0.0 = 0.63
  - Case-4: 0.7 * 0.0 + 0.3 * 0.6 = 0.18
  - Case-5: 0.7 * 0.6 + 0.3 * 0.0 = 0.42
  - Case-7: 0.7 * 0.0 + 0.3 * 0.5 = 0.15
- 정렬 순서: [case-1, case-2, case-5, case-4, case-7]
- 응답 JSON:
  ```json
  {
    "hits": [
      {"chunk_id": "case-1", "score": 0.73, ...},
      {"chunk_id": "case-2", "score": 0.63, ...},
      {"chunk_id": "case-5", "score": 0.42, ...},
      {"chunk_id": "case-4", "score": 0.18, ...},
      {"chunk_id": "case-7", "score": 0.15, ...}
    ],
    "search_mode": "hybrid",
    ...
  }
  ```
- 검증 항목:
  - ✅ 하이브리드 스코어 정확도 (가중치 0.7:0.3)
  - ✅ 중복 케이스 병합 (case-1은 하이브리드 스코어로 병합)
  - ✅ search_mode == "hybrid"
  - ✅ 상위 5개 결과 반환

---

### Scenario 3: Feature Flag OFF (BM25 Only)

**Given**:
- 환경 변수: `FEATURE_NEURAL_CASE_SELECTOR=false` (또는 미설정)
- CaseBank 데이터: 5개 케이스

**When**:
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -d '{"q": "test query", "max_results": 5}'
```

**Then**:
- 응답 상태 코드: 200 OK
- Vector 검색 쿼리 실행되지 않음 (로그 확인)
- BM25 검색만 수행됨
- 응답 JSON:
  ```json
  {
    "hits": [...],
    "search_mode": "bm25",
    ...
  }
  ```
- 검증 항목:
  - ✅ search_mode == "bm25"
  - ✅ Vector 검색 로직 건너뜀
  - ✅ 기존 BM25 검색 정상 동작

---

### Scenario 4: Vector Search Timeout Handling

**Given**:
- 환경 변수: `FEATURE_NEURAL_CASE_SELECTOR=true`
- CaseBank 데이터: 10000개 케이스 (대량)
- Vector 검색 타임아웃: 100ms
- Vector 검색 실행 시간: 150ms (시뮬레이션)

**When**:
```bash
curl -X POST "http://localhost:8000/search/neural" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -d '{"q": "complex query", "max_results": 10}'
```

**Then**:
- 응답 상태 코드: 200 OK (에러 없음)
- 로그 출력: `WARNING: Vector search timeout (0.1s)`
- BM25 검색 결과만 반환
- 응답 JSON:
  ```json
  {
    "hits": [...],
    "search_mode": "bm25_fallback",
    ...
  }
  ```
- 검증 항목:
  - ✅ search_mode == "bm25_fallback"
  - ✅ HTTP 200 응답 (500 에러 아님)
  - ✅ BM25 검색 결과 정상 반환
  - ✅ 경고 로그 기록됨

---

### Scenario 5: Embedding Generation Failure

**Given**:
- 환경 변수: `FEATURE_NEURAL_CASE_SELECTOR=true`
- OpenAI API 키: 미설정 또는 잘못된 키
- CaseBank 데이터: 5개 케이스

**When**:
```bash
curl -X POST "http://localhost:8000/search/neural" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -d '{"q": "test query", "max_results": 5}'
```

**Then**:
- 응답 상태 코드: 200 OK
- 로그 출력: `WARNING: Embedding generation failed, fallback to BM25`
- BM25 검색 결과 반환
- 응답 JSON:
  ```json
  {
    "hits": [...],
    "search_mode": "bm25_fallback",
    ...
  }
  ```
- 검증 항목:
  - ✅ search_mode == "bm25_fallback"
  - ✅ HTTP 200 응답 (에러 없음)
  - ✅ BM25 검색 정상 수행
  - ✅ 경고 로그 기록됨

---

### Scenario 6: Feature Flag OFF with Neural Endpoint

**Given**:
- 환경 변수: `FEATURE_NEURAL_CASE_SELECTOR=false`

**When**:
```bash
curl -X POST "http://localhost:8000/search/neural" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-api-key" \
  -d '{"q": "test query", "max_results": 5}'
```

**Then**:
- 응답 상태 코드: 503 Service Unavailable
- 응답 JSON:
  ```json
  {
    "detail": "Neural case selector disabled"
  }
  ```
- 검증 항목:
  - ✅ HTTP 503 응답
  - ✅ 에러 메시지 명확함
  - ✅ Vector 검색 실행되지 않음

---

## 품질 게이트 (Quality Gates)

### 1. 코드 품질

**커버리지 목표**:
- 단위 테스트: 100%
- 통합 테스트: 90% 이상

**테스트 수**:
- 단위 테스트: 12개 이상
  - Vector 검색 (3개)
  - 하이브리드 스코어 (3개)
  - API 엔드포인트 (4개)
  - Fallback 처리 (2개)
- 통합 테스트: 4개 이상
  - 전체 검색 흐름 (2개)
  - Feature Flag 토글 (1개)
  - 성능 벤치마크 (1개)

**Linter 검증**:
- ✅ mypy: 타입 힌트 100% (--strict 모드)
- ✅ black: 포맷팅 통과
- ✅ isort: import 정렬 통과
- ✅ flake8: 스타일 가이드 준수 (max-line-length=100)

### 2. 성능 기준

**응답 시간 목표**:
- Vector 검색 (단독): < 100ms
- 하이브리드 검색: < 200ms
- BM25 검색 (Fallback): < 50ms

**동시성 처리**:
- 동시 요청 10개: 평균 응답 시간 < 300ms
- 동시 요청 50개: 평균 응답 시간 < 500ms

**리소스 사용**:
- 메모리: 추가 사용량 < 100MB (벡터 검색 시)
- CPU: 평균 사용률 < 50%

### 3. 보안 검증

**SQL 인젝션 방지**:
- ✅ 모든 쿼리에 parameterized query 사용
- ✅ text() 함수에 파라미터 바인딩 적용

**API 인증**:
- ✅ 모든 엔드포인트에 API Key 인증 적용
- ✅ Feature Flag OFF 시 403/503 응답

**데이터 검증**:
- ✅ 입력 쿼리 길이 제한 (max 1000자)
- ✅ max_results 범위 검증 (1~100)

### 4. 기능 완성도

**필수 기능**:
- ✅ Vector 검색 활성화 (Feature Flag ON 시)
- ✅ 하이브리드 스코어 계산 (가중치 0.7:0.3)
- ✅ Fallback 처리 (임베딩 실패, 타임아웃)
- ✅ search_mode 응답 필드 추가

**옵션 기능** (향후 확장):
- ⏳ 가중치 동적 조정 (환경 변수)
- ⏳ A/B 테스트 프레임워크
- ⏳ 임베딩 캐싱

---

## 검증 도구 및 방법

### 1. 단위 테스트

**테스트 파일**: `tests/unit/test_neural_selector.py`

**주요 테스트 케이스**:
```python
@pytest.mark.asyncio
async def test_neural_case_search_basic():
    """Vector 검색 기본 동작 검증"""
    session = AsyncSession()
    query = "test query"
    results = await neural_case_search(session, query, topk=5)

    assert len(results) <= 5
    assert all("score" in r for r in results)
    assert all(0 <= r["score"] <= 1 for r in results)

@pytest.mark.asyncio
async def test_hybrid_score_calculation():
    """하이브리드 스코어 계산 정확도 검증"""
    bm25_score = 0.8
    vector_score = 0.9
    expected = 0.7 * 0.9 + 0.3 * 0.8  # 0.87

    result = combine_scores(bm25_score, vector_score)
    assert abs(result - expected) < 0.01

@pytest.mark.asyncio
async def test_vector_search_timeout():
    """타임아웃 처리 검증"""
    session = AsyncSession()
    query = "long query that takes time"

    results = await neural_case_search(session, query, timeout=0.01)
    # 타임아웃 시 빈 리스트 반환
    assert results == []
```

### 2. 통합 테스트

**테스트 파일**: `tests/integration/test_hybrid_search.py`

**주요 테스트 케이스**:
```python
@pytest.mark.asyncio
async def test_hybrid_search_flow():
    """전체 하이브리드 검색 흐름 검증"""
    # Feature Flag 활성화
    os.environ["FEATURE_NEURAL_CASE_SELECTOR"] = "true"

    # 검색 요청
    response = await client.post("/search", json={"q": "test", "max_results": 5})

    assert response.status_code == 200
    data = response.json()
    assert data["search_mode"] == "hybrid"
    assert len(data["hits"]) <= 5

@pytest.mark.asyncio
async def test_feature_flag_toggle():
    """Feature Flag ON/OFF 동작 검증"""
    # Flag OFF
    os.environ["FEATURE_NEURAL_CASE_SELECTOR"] = "false"
    response = await client.post("/search/neural", json={"q": "test"})
    assert response.status_code == 503

    # Flag ON
    os.environ["FEATURE_NEURAL_CASE_SELECTOR"] = "true"
    response = await client.post("/search/neural", json={"q": "test"})
    assert response.status_code == 200
```

### 3. 성능 벤치마크

**벤치마크 스크립트**: `scripts/benchmark_neural_search.py`

```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

async def benchmark_vector_search():
    """Vector 검색 성능 측정"""
    latencies = []

    for _ in range(100):
        start = time.time()
        await neural_case_search(session, "test query", topk=5)
        latencies.append(time.time() - start)

    print(f"평균: {sum(latencies)/len(latencies)*1000:.2f}ms")
    print(f"P95: {sorted(latencies)[95]*1000:.2f}ms")
    print(f"최대: {max(latencies)*1000:.2f}ms")
```

**성능 목표**:
- 평균 latency < 80ms
- P95 latency < 120ms
- 최대 latency < 150ms

---

## Definition of Done (DoD)

### 기능 완성
- [x] Vector 검색 SQL 쿼리 구현 완료
- [x] 하이브리드 스코어 계산 로직 구현 완료
- [x] `/search/neural` 엔드포인트 추가 완료
- [x] Feature Flag 기반 동적 활성화 구현 완료
- [x] Fallback 처리 (임베딩 실패, 타임아웃) 구현 완료

### 테스트 완성
- [x] 단위 테스트 12개 작성 완료 (커버리지 100%)
- [x] 통합 테스트 4개 작성 완료 (커버리지 90% 이상)
- [x] 성능 벤치마크 완료 (목표 달성)
- [x] 모든 Given-When-Then 시나리오 검증 완료

### 코드 품질
- [x] Linter 검증 통과 (mypy, black, isort, flake8)
- [x] 보안 검증 완료 (SQL 인젝션 방지, API 인증)
- [x] 코드 리뷰 완료 (2명 이상 승인)

### 문서화
- [x] spec.md 업데이트 (구현 상세 반영)
- [x] plan.md 업데이트 (실제 구현 내용 반영)
- [x] acceptance.md 업데이트 (검증 결과 반영)
- [x] API 문서 생성 (Swagger UI 업데이트)

### 배포 준비
- [x] pgvector 인덱스 생성 마이그레이션 스크립트 작성
- [x] Feature Flag 기본값 확인 (false)
- [x] 모니터링 메트릭 추가 (검색 모드별 latency)
- [x] 롤백 계획 수립 (Feature Flag OFF로 즉시 복구)

---

**END OF ACCEPTANCE CRITERIA**
