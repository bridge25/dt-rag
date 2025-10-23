---
id: ORCHESTRATION-001
version: 1.0.0
status: completed
created: 2025-10-09
updated: 2025-10-09
author: "@claude"
priority: critical
category: system
labels: [orchestration, langgraph, cbr, agent-factory, pipeline]
---

# SPEC-ORCHESTRATION-001: LangGraph 7-Step Orchestration System

## 1. 개요

### 1.1 목적

Dynamic Taxonomy RAG 시스템의 핵심 오케스트레이션 레이어로서, LangGraph 기반 4단계 파이프라인, CBR(Case-Based Reasoning) 시스템, Agent Factory를 통합하여 사용자 쿼리에 대한 정확하고 신뢰할 수 있는 답변을 생성한다.

### 1.2 범위

**포함 사항**:
- LangGraph 4-Step Pipeline (intent, retrieve, compose, respond)
- CBR k-NN 기반 케이스 추천 시스템
- Agent Factory 및 Manifest 생성
- B-O2 Retrieval Filter (Category Path 기반)
- FastAPI 기반 Orchestration Gateway
- 7-Step Pipeline 통합 (4단계로 단순화)

**제외 사항**:
- 실제 Debate 단계 구현 (1.5P Phase reserved)
- MCP Tools 실행 (1.5P Phase reserved)
- Neural Selector 학습 (2P Phase reserved)

### 1.3 이해관계자

- **개발팀**: LangGraph pipeline, CBR system, Agent Factory 구현
- **QA팀**: 파이프라인 품질 검증, CBR 추천 정확도 테스트
- **운영팀**: p95 latency ≤ 4s 모니터링, CBR 시스템 운영
- **보안팀**: Agent Manifest 검증, Filter bypass 방지

---

## 2. 요구사항 (EARS)

### 2.1 기능 요구사항

#### FR-ORCH-001: LangGraph 4-Step Pipeline 실행
**WHERE** 사용자가 chat/run 엔드포인트로 쿼리를 전송할 때,
**WHEN** PipelineRequest가 유효한 경우,
**THEN** 시스템은 다음 4단계를 순차 실행해야 한다:
1. **Step 1 (Intent)**: 쿼리 의도 분석 (question, explanation, search, general)
2. **Step 2 (Retrieve)**: Hybrid search 실행 (BM25 + Vector + Rerank, top 5 chunks)
3. **Step 5 (Compose)**: LLM으로 답변 생성 (Gemini API 사용)
4. **Step 7 (Respond)**: 신뢰도 점수 계산 및 응답 포맷팅

**성능 요구사항**: p95 latency ≤ 4s

#### FR-ORCH-002: Step별 Timeout 강제
**WHERE** 각 파이프라인 단계가 실행 중일 때,
**WHEN** 실측 기반 timeout 제한을 초과하는 경우,
**THEN** 시스템은 TimeoutError를 발생시켜야 한다.

**Timeout 설정** (2025-10-06 실측값 기준):
- Intent: 0.1s (실측 0.056~0.15ms)
- Retrieve: 2.0s (실측 0.37~1.19s)
- Compose: 3.5s (실측 1.29~2.06s, LLM API 변동 고려)
- Respond: 0.1s (실측 0.043~0.05ms)

#### FR-ORCH-003: Confidence Score 계산
**WHERE** Step 7 (Respond) 단계에서,
**WHEN** 검색 결과와 소스 개수를 확인할 때,
**THEN** 시스템은 다음 공식으로 신뢰도를 계산해야 한다:

```
confidence = min(max(top_rerank_score * source_penalty, 0.0), 1.0)
source_penalty = 1.0 if source_count >= 2 else 0.5
```

**정당화**: PRD 요구사항 "≥2 sources" 충족 여부 반영

#### FR-ORCH-004: CBR Case Suggestion
**WHERE** 사용자가 /cbr/suggest 엔드포인트로 요청할 때,
**WHEN** CBR_ENABLED=true 환경변수가 설정된 경우,
**THEN** 시스템은 다음을 수행해야 한다:
1. SQLite 기반 cbr_cases 테이블에서 k개 케이스 검색
2. 유사도 계산 (cosine, euclidean, jaccard 중 선택)
3. quality_score, usage_count 기준 정렬
4. 상호작용 로그 cbr_logs 테이블에 기록

**품질 요구사항**:
- 평균 응답 시간 ≤ 200ms
- 추천 결과 min_quality_score 필터링 지원

#### FR-ORCH-005: Agent Factory - Manifest 생성
**WHERE** 사용자가 /agents/from-category 엔드포인트로 요청할 때,
**WHEN** version, node_paths가 유효한 경우,
**THEN** 시스템은 다음 설정의 AgentManifest를 생성해야 한다:

**검증 강화 항목** (GPT 검토 반영):
- version: Semantic versioning 형식 검증 (`\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?`)
- node_paths: 최대 10개 경로, 각 경로 최대 5레벨 깊이
- 경로 요소: 50자 제한, 안전하지 않은 문자 차단 (`..`, `/`, `\`, `<`, `>`, etc.)
- 중복 경로 제거 및 정규화

**Manifest 기본 설정**:
```json
{
  "retrieval": {
    "bm25_topk": 12,
    "vector_topk": 12,
    "rerank": {"candidates": 50, "final_topk": 5},
    "filter": {"canonical_in": true}
  },
  "features": {
    "debate": false,
    "hitl_below_conf": 0.70,
    "cost_guard": true
  }
}
```

**성능 요구사항**: 입력검증 + 생성 < 100ms

#### FR-ORCH-006: B-O2 Retrieval Filter 적용
**WHERE** /search 엔드포인트로 검색 요청 시,
**WHEN** allowed_category_paths 필터가 제공된 경우,
**THEN** 시스템은 다음을 수행해야 한다:
1. CategoryFilter 생성
2. 필터 우회 시도 탐지 (validate_filter_bypass_attempt)
3. raw_search_results에 필터 적용
4. 허용된 canonical_path만 반환

**보안 요구사항**:
- 필터 우회 시도 시 403 Forbidden 반환
- 필터 처리 latency ≤ 10ms

#### FR-ORCH-007: CBR Case CRUD Operations
**WHERE** CBR 시스템이 활성화된 경우,
**WHEN** 관리자가 케이스를 관리할 때,
**THEN** 시스템은 다음 API를 제공해야 한다:
- **GET** `/cbr/cases/{case_id}`: 케이스 조회
- **PUT** `/cbr/cases/{case_id}`: 케이스 업데이트
- **DELETE** `/cbr/cases/{case_id}`: 케이스 삭제
- **PUT** `/cbr/cases/{case_id}/quality`: 품질 점수 업데이트

**데이터 무결성**:
- case_id 유효성 검증
- 트랜잭션으로 업데이트 수행
- 케이스 삭제 시 관련 로그도 함께 삭제

#### FR-ORCH-008: CBR Feedback 수집
**WHERE** 사용자가 CBR 추천 결과를 사용할 때,
**WHEN** 피드백을 제출하는 경우,
**THEN** 시스템은 다음을 수행해야 한다:
1. FeedbackType 검증 (thumbs_up, thumbs_down, selected, ignored)
2. usage_count 증가
3. quality_score 조정:
   - thumbs_up/selected: +0.1 (최대 1.0)
   - thumbs_down: -0.1 (최소 0.0)
4. cbr_logs 테이블에 피드백 기록

**Neural Selector 준비**:
- 최소 1,000개 상호작용 수집
- 성공률 ≥ 70% 유지

---

### 2.2 비기능 요구사항

#### NFR-ORCH-001: 성능 요구사항
**WHERE** 프로덕션 환경에서,
**WHEN** 정상 부하 조건일 때,
**THEN** 시스템은 다음 성능을 보장해야 한다:

**Pipeline 성능**:
- p50 latency: < 2.0s
- p95 latency: ≤ 4.0s (PRD 요구사항)
- p99 latency: < 6.0s

**CBR 성능**:
- 평균 응답 시간: ≤ 200ms
- k-NN 검색: < 100ms
- 유사도 계산: < 50ms

**Agent Factory 성능**:
- Manifest 생성: < 100ms
- 입력 검증: < 10ms

**Filter 성능**:
- 필터링 latency: ≤ 10ms
- 처리량: > 10,000 docs/sec

#### NFR-ORCH-002: 확장성 요구사항
**WHERE** 시스템 부하가 증가할 때,
**WHEN** 동시 요청 수가 100개를 초과하는 경우,
**THEN** 시스템은 다음을 지원해야 한다:

- 수평 확장 (FastAPI workers)
- CBR SQLite → PostgreSQL 마이그레이션 가능
- Pipeline lazy loading (search_engine, llm_service)

#### NFR-ORCH-003: 가용성 요구사항
**WHERE** 프로덕션 환경에서,
**WHEN** 시스템 운영 중,
**THEN** 시스템은 다음 가용성을 제공해야 한다:

- Uptime: ≥ 99.0%
- Graceful degradation:
  - Embedding 실패 시 BM25-only 검색
  - Cross-encoder 미사용 시 heuristic reranking
  - CBR 비활성화 시 501 응답 (graceful)
- Health check endpoint 제공 (`/health`)

#### NFR-ORCH-004: 보안 요구사항
**WHERE** 외부 요청을 처리할 때,
**WHEN** 보안 위협이 탐지된 경우,
**THEN** 시스템은 다음을 수행해야 한다:

**Agent Factory 입력 검증**:
- Semantic versioning 형식 검증
- Path traversal 방지 (`..`, `/`, `\` 차단)
- XSS 방지 (안전하지 않은 문자 차단)
- SQL Injection 방지 (parameterized queries)

**Filter Bypass 방지**:
- 필터 우회 시도 탐지 (validate_filter_bypass_attempt)
- 403 Forbidden 응답
- 보안 위반 로그 기록

**CORS 설정**:
- Specific origins only (no wildcards)
- Specific methods/headers only

#### NFR-ORCH-005: 관측성 요구사항
**WHERE** 시스템 운영 중,
**WHEN** 모니터링 및 디버깅이 필요할 때,
**THEN** 시스템은 다음을 제공해야 한다:

**Pipeline 메트릭**:
- step_timings (각 단계별 소요 시간)
- total_latency
- confidence_score
- intent 분류 결과

**CBR 메트릭**:
- total_cases, total_interactions
- success_rate (성공한 상호작용 비율)
- average_response_time_ms
- average_quality_score
- category_distribution

**Health Check**:
- Service status (healthy, degraded, unhealthy)
- Feature flags (B-O1, B-O2, B-O3, B-O4)
- Performance targets

---

## 3. 아키텍처 설계

### 3.1 시스템 구성도

```
┌──────────────────────────────────────────────────────────┐
│            Orchestration Gateway (FastAPI)               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │   LangGraph 4-Step Pipeline                      │   │
│  │   ┌────────┐  ┌─────────┐  ┌────────┐  ┌──────┐│   │
│  │   │Intent  │→ │Retrieve │→ │Compose │→ │Respond││   │
│  │   │ (0.1s) │  │ (2.0s)  │  │ (3.5s) │  │(0.1s)││   │
│  │   └────────┘  └─────────┘  └────────┘  └──────┘│   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │   CBR System (SQLite)                            │   │
│  │   ┌──────────────┐  ┌──────────────┐            │   │
│  │   │ cbr_cases    │  │ cbr_logs     │            │   │
│  │   │ - case_id    │  │ - log_id     │            │   │
│  │   │ - query      │  │ - suggested  │            │   │
│  │   │ - category   │  │ - picked     │            │   │
│  │   │ - quality    │  │ - feedback   │            │   │
│  │   └──────────────┘  └──────────────┘            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │   Agent Factory                                  │   │
│  │   - Manifest Builder (< 100ms)                   │   │
│  │   - Input Validation (semantic versioning)       │   │
│  │   - Path Normalization & Deduplication           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │   B-O2 Retrieval Filter                          │   │
│  │   - CategoryFilter (< 10ms)                      │   │
│  │   - Bypass Detection (validate_filter_bypass)    │   │
│  │   - Canonical Path Filtering                     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘
         │                │                 │
         ▼                ▼                 ▼
    [Search API]   [Embedding Service]  [LLM Service]
```

### 3.2 데이터 모델

#### PipelineState (LangGraph State)
```python
class PipelineState(BaseModel):
    query: str
    intent: Optional[str] = None
    retrieved_chunks: List[Dict[str, Any]] = []
    answer: Optional[str] = None
    sources: List[Dict[str, Any]] = []
    confidence: float = 0.0

    # Metadata
    taxonomy_version: str = "1.0.0"
    canonical_filter: Optional[List[List[str]]] = None
    start_time: float
    step_timings: Dict[str, float] = {}
```

#### CBR Case (SQLite)
```sql
CREATE TABLE cbr_cases (
    case_id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    category_path TEXT NOT NULL,  -- JSON array
    content TEXT NOT NULL,
    quality_score REAL DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    metadata TEXT DEFAULT '{}',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

#### CBR Log (SQLite)
```sql
CREATE TABLE cbr_logs (
    log_id TEXT PRIMARY KEY,
    timestamp TEXT,
    query TEXT,
    category_path TEXT,  -- JSON array
    suggested_case_ids TEXT,  -- JSON array
    picked_case_ids TEXT,  -- JSON array
    success_flag INTEGER,
    feedback TEXT,
    execution_time_ms REAL,
    similarity_method TEXT,
    user_id TEXT
)
```

#### Agent Manifest
```python
class AgentManifest(BaseModel):
    name: str
    taxonomy_version: str
    allowed_category_paths: List[List[str]]
    retrieval: Dict[str, Any]  # bm25_topk, vector_topk, rerank
    features: Dict[str, Any]   # debate, hitl_below_conf, cost_guard
    mcp_tools_allowlist: List[str]
```

### 3.3 API 엔드포인트

#### Chat Pipeline
- **POST** `/chat/run`: LangGraph 7-Step 채팅 파이프라인 실행
  - Request: `ChatRequest` (message, conversation_id, context)
  - Response: `ChatResponse` (response, conversation_id, sources)
  - Timeout: p95 ≤ 4s

#### CBR System
- **POST** `/cbr/suggest`: CBR k-NN 케이스 추천
  - Request: `CBRSuggestRequest` (query, category_path, k, similarity_method)
  - Response: `CBRSuggestResponse` (suggestions, execution_time_ms)
  - Performance: ≤ 200ms

- **POST** `/cbr/feedback`: 케이스 피드백 제출
  - Request: `CBRFeedbackRequest` (log_id, case_id, feedback, success)
  - Response: `{status, message}`

- **GET** `/cbr/stats`: CBR 시스템 통계 조회
  - Response: total_cases, total_interactions, success_rate, etc.

- **POST** `/cbr/case`: CBR 케이스 추가
  - Request: `{query, category_path, content, quality_score, metadata}`
  - Response: `{status, case_id, message}`

- **GET** `/cbr/logs`: CBR 상호작용 로그 조회
  - Query: `limit`, `success_only`
  - Response: `{logs, total_count, neural_selector_readiness}`

- **GET** `/cbr/export`: Neural Selector 학습 데이터 내보내기
  - Response: `{training_data, ready_for_neural_selector}`

#### CBR CRUD
- **GET** `/cbr/cases/{case_id}`: 특정 케이스 조회
  - Response: `CBRCaseResponse`

- **PUT** `/cbr/cases/{case_id}`: 케이스 업데이트
  - Request: `CBRUpdateRequest` (query, category_path, content, quality_score, metadata)
  - Response: `{status, case_id, message, updated_fields}`

- **DELETE** `/cbr/cases/{case_id}`: 케이스 삭제
  - Response: `{status, case_id, message}`

- **PUT** `/cbr/cases/{case_id}/quality`: 품질 점수 업데이트
  - Request: `CBRQualityUpdateRequest` (quality_score)
  - Response: `{status, case_id, quality_score, previous_quality_score}`

#### Agent Factory
- **POST** `/agents/from-category`: 노드 경로에서 Agent Manifest 생성
  - Request: `FromCategoryRequest` (version, node_paths, options)
  - Response: `AgentManifest`
  - Performance: < 100ms

#### Search & Filter
- **POST** `/search`: 하이브리드 검색 (B-O2 필터링 적용)
  - Request: `SearchRequest` (query, filters)
  - Response: `SearchResponse` (hits, latency, total_count)
  - Filter latency: ≤ 10ms

#### Filter Management
- **POST** `/filter/validate`: 필터 경로 유효성 검증
  - Request: `{paths: List[List[str]]}`
  - Response: `{valid, paths_count, normalized_paths}`

- **POST** `/filter/test`: 필터 성능 테스트
  - Request: `{allowed_paths, test_documents}`
  - Response: `{performance, filtering_results, filter_stats}`

- **GET** `/metrics/filter`: 필터링 시스템 메트릭 조회
  - Response: `{filter_system, performance_metrics, security_metrics}`

#### Taxonomy
- **GET** `/api/taxonomy/tree/{version}`: Taxonomy API 프록시
  - Response: Taxonomy tree data

#### Health
- **GET** `/health`: 헬스체크
  - Response: `{status, service, version, features, performance}`

---

## 4. 제약사항

### 4.1 기술적 제약사항

1. **LangGraph 단순화**: 7-Step → 4-Step (Debate, Tools, Cite 단계 제외)
2. **CBR Storage**: SQLite 기반 (향후 PostgreSQL 마이그레이션 가능)
3. **Lazy Loading**: search_engine, llm_service는 첫 요청 시 로딩
4. **GitHub Actions 호환**: 더미 파이프라인 fallback 지원

### 4.2 운영 제약사항

1. **CBR 활성화**: `CBR_ENABLED=true` 환경변수 필요
2. **CORS 설정**: 특정 origin만 허용 (no wildcards)
3. **Timeout 강제**: 각 단계별 timeout 초과 시 TimeoutError

### 4.3 보안 제약사항

1. **Input Validation**: Semantic versioning, path traversal 방지
2. **Filter Bypass**: 우회 시도 탐지 및 403 반환
3. **SQL Injection**: Parameterized queries 사용
4. **CORS**: Specific origins/methods/headers only

---

## 5. 테스트 전략

### 5.1 단위 테스트
- [ ] Step 함수별 단위 테스트 (intent, retrieve, compose, respond)
- [ ] Timeout 강제 테스트 (asyncio.TimeoutError)
- [ ] Confidence score 계산 테스트 (source_penalty 검증)
- [ ] CBR 유사도 계산 테스트 (cosine, euclidean, jaccard)
- [ ] Agent Manifest 입력 검증 테스트 (version, paths, unsafe chars)

### 5.2 통합 테스트
- [ ] 전체 Pipeline 실행 테스트 (end-to-end)
- [ ] CBR suggest + feedback 통합 테스트
- [ ] Agent Factory + Filter 통합 테스트
- [ ] Pipeline + CBR + Agent Factory 통합 테스트

### 5.3 성능 테스트
- [ ] Pipeline latency 측정 (p50, p95, p99)
- [ ] CBR 응답 시간 측정 (≤ 200ms)
- [ ] Agent Factory 생성 시간 측정 (< 100ms)
- [ ] Filter 처리 시간 측정 (≤ 10ms)
- [ ] 동시 요청 부하 테스트 (100+ concurrent)

### 5.4 보안 테스트
- [ ] Path traversal 공격 시도 (`..',` `/`, `\`)
- [ ] SQL Injection 시도 (parameterized queries 검증)
- [ ] Filter bypass 시도 (validate_filter_bypass_attempt)
- [ ] XSS 공격 시도 (unsafe chars)

---

## 6. 운영 계획

### 6.1 배포 체크리스트

**환경변수**:
- `CBR_ENABLED`: CBR 시스템 활성화 여부
- `CBR_DATA_DIR`: CBR 데이터 디렉토리 (기본값: `data/cbr`)

**의존성**:
- FastAPI, Pydantic
- SQLite3 (CBR)
- httpx (Taxonomy API proxy)
- LangGraph pipeline 모듈
- Search engine, Embedding service, LLM service

**Database 초기화**:
- cbr_cases 테이블 생성
- cbr_logs 테이블 생성

### 6.2 모니터링 메트릭

**Pipeline 메트릭**:
- `pipeline_latency_p50`, `pipeline_latency_p95`, `pipeline_latency_p99`
- `pipeline_timeout_errors`
- `pipeline_confidence_avg`
- `pipeline_sources_count_avg`

**CBR 메트릭**:
- `cbr_suggestion_latency_avg`
- `cbr_total_cases`, `cbr_total_interactions`
- `cbr_success_rate`
- `cbr_quality_score_avg`

**Agent Factory 메트릭**:
- `agent_creation_latency_p95`
- `agent_validation_errors`
- `agent_manifest_count`

**Filter 메트릭**:
- `filter_latency_p95`
- `filter_bypass_attempts`
- `filter_security_violations`

### 6.3 Alert 조건

- **Critical**: Pipeline p95 > 6s, CBR 비활성화 오류
- **High**: Pipeline p95 > 4s, CBR 평균 응답 > 500ms
- **Medium**: Filter latency > 50ms, Agent 검증 오류 > 10/min
- **Low**: CBR success_rate < 0.7

---

## 7. 참조 문서

- `.moai/specs/SPEC-SEARCH-001/spec.md` - Hybrid Search System
- `.moai/specs/SPEC-EMBED-001/spec.md` - Embedding Service
- `.moai/specs/SPEC-CLASS-001/spec.md` - Classification System
- `apps/orchestration/src/langgraph_pipeline.py` - Pipeline 구현
- `apps/orchestration/src/main.py` - FastAPI Gateway 구현

---

## 8. 변경 이력

| 날짜 | 변경 내용 | 작성자 |
|------|----------|--------|
| 2025-10-09 | 초안 작성 (역공학 기반) | @claude |
