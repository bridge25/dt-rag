---
id: NEURAL-001
version: 0.2.0
status: completed
created: 2025-10-09
updated: 2025-10-09
author: @claude
priority: high
category: feature
labels:
  - neural-cbr
  - vector-search
  - casebank
  - phase-2a
depends_on:
  - FOUNDATION-001
blocks: []
related_specs:
  - PLANNER-001
  - SEARCH-001
  - DATABASE-001
scope:
  packages:
    - apps/api
  files:
    - apps/api/database.py
    - apps/api/routers/search_router.py
    - apps/api/env_manager.py
  tests:
    - tests/unit/test_neural_selector.py
    - tests/integration/test_hybrid_search.py
---

# SPEC-NEURAL-001: Neural Case Selector 구현

@SPEC:NEURAL-001 @VERSION:0.2.0 @STATUS:completed

## HISTORY

### v0.2.0 (2025-10-09)
- **COMPLETED**: Neural Case Selector 구현 완료
- **AUTHOR**: @claude + code-builder
- **SCOPE**:
  - pgvector 기반 Vector 유사도 검색 (cosine distance)
  - 하이브리드 스코어 결합 (Vector 70% + BM25 30%)
  - 스코어 정규화 (Min-Max Scaling)
  - Feature Flag 기반 활성화/비활성화
- **TESTS**: 23개 신규 테스트 (단위 14개 + 통합 9개, 100% 통과)
- **PERFORMANCE**: Vector 검색 < 100ms, 하이브리드 < 200ms
- **TAG 체인**: @SPEC:NEURAL-001 → @IMPL:0.1/0.2/0.3/0.4 (4개) → @TEST:0.1/0.2 (23개)
- **FILES**:
  - 신규: apps/api/neural_selector.py
  - 신규: tests/unit/test_neural_selector.py
  - 신규: tests/integration/test_hybrid_search.py
  - 신규: db/migrations/001_add_vector_index.sql
  - 수정: packages/common_schemas/common_schemas/models.py (SearchRequest.use_neural, SearchResponse.mode)
  - 수정: apps/api/routers/search_router.py (Neural 검색 통합)
- **NEXT**: Phase 2B (MCP Tools) 또는 Phase 3 (Soft-Q/Bandit + Debate)

### v0.1.0 (2025-10-09)
- **INITIAL**: Neural Case Selector SPEC 최초 작성
- **AUTHOR**: @claude
- **SCOPE**: CaseBank vector 검색 활성화, 하이브리드 검색 (BM25 + Vector)
- **CONTEXT**: PRD 1.5P Neural CBR 구현 (Phase 2A)
- **BASELINE**: FOUNDATION-001 완료 (CaseBank query_vector 필드, generate_case_embedding() 메서드)

---

## 1. 개요

### 목적
CaseBank의 Vector 검색 기능을 활성화하여 Neural Case-Based Reasoning (CBR)을 구현합니다. 기존 BM25 기반 검색에 Vector 유사도를 결합한 하이브리드 검색 전략을 통해 검색 품질을 향상시킵니다.

### 범위
- **Phase 0 기반**: FOUNDATION-001에서 구현된 CaseBank query_vector 필드 및 임베딩 생성 메서드 활용
- **Feature Flag**: env_manager.py의 `neural_case_selector` 플래그로 동적 활성화/비활성화
- **하이브리드 검색**: Vector 유사도 (70%) + BM25 스코어 (30%) 가중치 결합
- **성능 목표**: Vector 검색 응답 시간 < 100ms

---

## 2. Environment (환경)

### 기술 스택
- **Database**: PostgreSQL 15+ with pgvector extension
- **Vector 타입**: VECTOR(1536) - OpenAI text-embedding-ada-002 차원
- **ORM**: SQLAlchemy 2.0+ (AsyncSession)
- **검색 연산자**: pgvector 코사인 유사도 (`<=>`)

### 기존 구현 상태
- **CaseBank 모델** (database.py:192-204):
  - `query_vector: Mapped[List[float]]` 필드 활성화 완료
  - `generate_case_embedding()` 메서드 구현 완료
- **Feature Flag** (env_manager.py:136):
  - `neural_case_selector: False` (기본값)
  - 환경 변수 `FEATURE_NEURAL_CASE_SELECTOR=true`로 활성화 가능
- **BM25 검색** (search_router.py:568-641):
  - PostgreSQL full-text search 구현 완료
  - ts_rank_cd 기반 스코어링

### 제약사항
- pgvector extension 설치 필수 (database.py:221에서 자동 설치)
- CaseBank에 최소 1개 이상의 케이스 및 임베딩 필요
- 임베딩 생성 실패 시 BM25 검색으로 Fallback

---

## 3. Assumptions (가정)

### 데이터 가정
1. CaseBank 테이블에 케이스가 최소 1개 이상 존재
2. 각 케이스의 query_vector 필드가 NULL이 아닌 유효한 1536차원 임베딩
3. pgvector extension이 데이터베이스에 설치되어 있음 (init_database()에서 자동 설치)

### 성능 가정
1. Vector 검색 시간: < 100ms (인덱스 최적화 가정)
2. 임베딩 생성 시간: < 500ms (OpenAI API 응답 시간)
3. 하이브리드 검색 총 시간: < 200ms

### 아키텍처 가정
1. Feature Flag를 통한 동적 활성화/비활성화 지원
2. Vector 검색 실패 시 BM25 검색으로 안전하게 Fallback
3. 기존 search_router.py의 하이브리드 검색 로직 재사용 가능

---

## 4. Requirements (요구사항)

### Ubiquitous Requirements

**@REQ:NEURAL-001.1** Vector Similarity Calculation
- 시스템은 쿼리 임베딩과 CaseBank query_vector 간 코사인 유사도를 계산해야 한다
- 유사도는 0~1 범위로 정규화되어야 한다
- pgvector의 `<=>` 연산자를 사용해야 한다

**@REQ:NEURAL-001.2** Hybrid Score Fusion
- 시스템은 BM25 스코어와 Vector 유사도를 결합하여 최종 스코어를 산출해야 한다
- 기본 가중치: Vector 0.7, BM25 0.3
- 최종 스코어 = 0.7 * vector_score + 0.3 * bm25_score

**@REQ:NEURAL-001.3** Performance Constraint
- Vector 검색 쿼리 실행 시간은 100ms를 초과하지 않아야 한다
- 타임아웃 발생 시 경고 로그를 기록해야 한다

### Event-driven Requirements

**@REQ:NEURAL-001.4** WHEN Feature Flag ON
- WHEN neural_case_selector flag가 True이면, 시스템은 Vector 검색을 활성화해야 한다
- WHEN 검색 요청이 들어오면, 시스템은 쿼리 임베딩을 생성하고 유사한 케이스를 검색해야 한다

**@REQ:NEURAL-001.5** WHEN Query Input
- WHEN 사용자가 검색 쿼리를 입력하면, 시스템은 query_vector를 생성해야 한다
- WHEN 임베딩 생성에 실패하면, 시스템은 BM25 검색만 수행해야 한다

**@REQ:NEURAL-001.6** WHEN Hybrid Search
- WHEN Vector 검색 결과와 BM25 결과를 결합할 때, 시스템은 가중치를 적용해야 한다
- WHEN 중복 케이스가 발견되면, 시스템은 하이브리드 스코어로 병합해야 한다

### State-driven Requirements

**@REQ:NEURAL-001.7** WHILE Flag Active
- WHILE neural_case_selector가 활성화된 상태일 때, 시스템은 하이브리드 검색을 수행해야 한다
- WHILE 하이브리드 검색 중, 응답에 검색 모드(neural, bm25, hybrid)를 포함해야 한다

**@REQ:NEURAL-001.8** WHILE Flag Inactive
- WHILE neural_case_selector가 비활성화된 상태일 때, 시스템은 기존 BM25 검색만 수행해야 한다
- WHILE BM25 검색 중, 응답에 mode="bm25"를 명시해야 한다

### Constraints

**@REQ:NEURAL-001.9** Fallback Strategy
- IF Vector 검색 실패 시, 시스템은 BM25 검색 결과만 반환해야 한다
- IF 임베딩 생성 실패 시, 시스템은 경고 로그를 기록하고 BM25로 Fallback해야 한다

**@REQ:NEURAL-001.10** Timeout Handling
- Vector 검색 타임아웃은 100ms로 설정되어야 한다
- asyncio.wait_for()를 사용하여 타임아웃을 강제해야 한다

---

## 5. Specifications (상세 구현 명세)

### IMPL 0.1: Vector Similarity Search

**@IMPL:NEURAL-001.0.1** SQL Query Implementation
```sql
SELECT
    case_id,
    query,
    response_text,
    category_path,
    1.0 - (query_vector <=> :query_embedding::vector) AS vector_score
FROM case_bank
WHERE query_vector IS NOT NULL
ORDER BY query_vector <=> :query_embedding::vector
LIMIT :topk
```

**@IMPL:NEURAL-001.0.2** Python Implementation
```python
async def neural_case_search(
    session: AsyncSession,
    query: str,
    topk: int = 5,
    timeout: float = 0.1
) -> List[Dict[str, Any]]:
    # 1. 쿼리 임베딩 생성
    query_embedding = await EmbeddingService.generate_embedding(query)

    # 2. Vector 검색 (타임아웃 적용)
    vector_query = text("""
        SELECT case_id, query, response_text, category_path,
               1.0 - (query_vector <=> :query_vector::vector) AS vector_score
        FROM case_bank
        WHERE query_vector IS NOT NULL
        ORDER BY query_vector <=> :query_vector::vector
        LIMIT :topk
    """)

    vector_str = '[' + ','.join(map(str, query_embedding)) + ']'

    try:
        result = await asyncio.wait_for(
            session.execute(vector_query, {"query_vector": vector_str, "topk": topk}),
            timeout=timeout
        )
        rows = result.fetchall()
        return [{"case_id": r[0], "query": r[1], "response_text": r[2],
                 "category_path": r[3], "score": float(r[4])} for r in rows]
    except asyncio.TimeoutError:
        logger.warning(f"Vector search timeout ({timeout}s)")
        return []
```

### IMPL 0.2: Hybrid Search Strategy

**@IMPL:NEURAL-001.0.2.1** Score Normalization
- BM25 스코어: Min-Max Scaling (0~1)
- Vector 스코어: 코사인 유사도 (이미 0~1)

**@IMPL:NEURAL-001.0.2.2** Score Fusion
```python
def combine_scores(bm25_score: float, vector_score: float,
                   bm25_weight: float = 0.3, vector_weight: float = 0.7) -> float:
    return vector_weight * vector_score + bm25_weight * bm25_score
```

**@IMPL:NEURAL-001.0.2.3** Duplicate Handling
- case_id 기준으로 중복 제거
- 중복 케이스는 하이브리드 스코어로 병합

### IMPL 0.3: API Endpoint Extension

**@IMPL:NEURAL-001.0.3.1** New Endpoint: `/search/neural`
```python
@search_router.post("/neural", response_model=SearchResponse)
async def neural_case_search_endpoint(
    request: Request,
    search_request: SearchRequest,
    service: SearchService = Depends(get_search_service),
    api_key: APIKeyInfo = Depends(verify_api_key)
):
    # Feature flag 확인
    env_manager = get_env_manager()
    if not env_manager.get_feature_flags().get("neural_case_selector"):
        raise HTTPException(status_code=503, detail="Neural case selector disabled")

    # Neural 검색 수행
    result = await service.neural_search(search_request)
    return result
```

**@IMPL:NEURAL-001.0.3.2** Response Schema Extension
```python
class SearchResponse(BaseModel):
    hits: List[SearchHit]
    latency: float
    request_id: str
    total_candidates: int
    sources_count: int
    taxonomy_version: str
    search_mode: str  # NEW: "neural", "bm25", "hybrid"
```

---

## 6. Acceptance Criteria (수락 기준)

### Scenario 1: Neural Search Activation

**Given**:
- neural_case_selector=True
- CaseBank에 케이스 3개 존재 (각각 query_vector 임베딩 포함)
- pgvector extension 활성화

**When**:
- POST `/search/neural?q=test query&use_neural=true`

**Then**:
- Vector 유사도 기반 검색 결과 반환
- 응답에 `search_mode: "neural"` 포함
- latency < 150ms
- 상위 3개 케이스 정렬 (vector_score 내림차순)

### Scenario 2: Hybrid Search

**Given**:
- neural_case_selector=True
- CaseBank에 케이스 10개 존재

**When**:
- POST `/search?q=test query&max_results=5`

**Then**:
- Vector + BM25 하이브리드 스코어로 정렬
- 가중치 적용: 0.7 * vector_score + 0.3 * bm25_score
- 응답에 `search_mode: "hybrid"` 포함
- 중복 케이스 제거 완료
- 상위 5개 결과 반환

### Scenario 3: Flag OFF (BM25 Only)

**Given**:
- neural_case_selector=False

**When**:
- POST `/search?q=test query`

**Then**:
- BM25 검색만 수행
- 응답에 `search_mode: "bm25"` 포함
- Vector 검색 쿼리 실행되지 않음
- 기존 search_router.py 로직 사용

### Scenario 4: Vector Search Timeout

**Given**:
- neural_case_selector=True
- Vector 검색 타임아웃 100ms 설정
- 대량 케이스 (10000개) 존재

**When**:
- POST `/search/neural?q=complex query`
- Vector 검색이 100ms 초과

**Then**:
- BM25 검색 결과만 반환
- 경고 로그 기록: "Vector search timeout (0.1s)"
- 응답에 `search_mode: "bm25_fallback"` 포함
- HTTP 500 대신 200 응답 (Fallback 성공)

### Scenario 5: Embedding Generation Failure

**Given**:
- neural_case_selector=True
- OpenAI API 키 미설정 또는 네트워크 오류

**When**:
- POST `/search/neural?q=test query`

**Then**:
- BM25 검색으로 Fallback
- 경고 로그: "Embedding generation failed, fallback to BM25"
- 응답에 `search_mode: "bm25_fallback"` 포함
- 정상 응답 반환 (에러 없음)

---

## 7. Traceability (추적성)

### 상위 SPEC 의존성
- **@SPEC:FOUNDATION-001**: CaseBank query_vector 필드, generate_case_embedding() 메서드
- **@SPEC:DATABASE-001**: PostgreSQL 스키마, pgvector extension
- **@SPEC:SEARCH-001**: 기존 BM25 검색 로직

### 관련 SPEC
- **@SPEC:PLANNER-001**: Meta-Planner의 Neural CBR 통합 (향후)
- **@SPEC:EVAL-001**: Neural 검색 품질 평가 메트릭

### 향후 확장
- Phase 2B: Soft Q-learning Bandit 통합
- Phase 3: Debate Mode에서 Neural CBR 활용
- Phase 4: Tools Policy와 Neural CBR 연계

---

## 8. 검증 방법

### 단위 테스트
- `test_neural_case_search()`: Vector 검색 SQL 쿼리 검증
- `test_score_fusion()`: 하이브리드 스코어 계산 검증
- `test_timeout_handling()`: 타임아웃 처리 검증
- `test_embedding_fallback()`: 임베딩 실패 시 Fallback 검증

### 통합 테스트
- `test_hybrid_search_flow()`: 전체 하이브리드 검색 흐름 검증
- `test_feature_flag_toggle()`: Feature Flag ON/OFF 시 동작 검증
- `test_pgvector_integration()`: pgvector 연산 정확도 검증

### 성능 테스트
- Vector 검색 시간 < 100ms (케이스 1000개 기준)
- 하이브리드 검색 시간 < 200ms
- 동시 요청 10개 처리 시 응답 시간 < 300ms

---

**END OF SPEC**
