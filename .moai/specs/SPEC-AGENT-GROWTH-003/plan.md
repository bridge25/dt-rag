# Implementation Plan - SPEC-AGENT-GROWTH-003

> **Status**: Implementation Completed
> **Base**: SPEC-AGENT-GROWTH-002 (Phase 1 - 6 endpoints)
> **Extension**: Phase 2 - 7 advanced endpoints

---

## 우선순위 1차 목표: Management Endpoints (완료)

### 작업 범위
에이전트 운영 관리를 위한 핵심 CRUD 확장 (PATCH, DELETE, Search)

### 구현 완료 사항

#### ✅ PATCH /agents/{agent_id}
- **파일**: `apps/api/routers/agent_router.py` (line 367-406)
- **스키마**: `AgentUpdateRequest` (apps/api/schemas/agent_schemas.py line 209-224)
- **기능**:
  - 부분 업데이트 지원 (Pydantic model_dump(exclude_unset=True))
  - 업데이트 가능 필드: name, scope_description, retrieval_config, features_config
  - 불변 필드: agent_id, taxonomy_node_ids, taxonomy_version, created_at
  - 404 처리: 존재하지 않는 agent_id
  - 200 OK 응답: 업데이트된 AgentResponse

#### ✅ DELETE /agents/{agent_id}
- **파일**: `apps/api/routers/agent_router.py` (line 409-437)
- **기능**:
  - 영구 삭제 (AgentDAO.delete_agent)
  - 204 No Content 응답
  - 404 처리: 존재하지 않는 agent_id
  - 멱등성 보장 (삭제 후 재호출 시 404)

#### ✅ GET /agents/search
- **파일**: `apps/api/routers/agent_router.py` (line 440-475)
- **DAO**: `AgentDAO.search_agents()` (apps/api/agent_dao.py)
- **기능**:
  - 쿼리 파라미터: q (검색어), max_results (기본 50, 최대 100)
  - SQL ILIKE 연산자 사용 (대소문자 무시)
  - 빈 쿼리 시 전체 에이전트 반환
  - AgentListResponse 응답 (agents, total, filters_applied)

### 의존성
- **Phase 1**: GET /agents/{agent_id}, POST /agents/from-taxonomy
- **DAO**: AgentDAO.update_agent(), delete_agent(), search_agents()

### 검증 기준
- ✅ PATCH 엔드포인트 부분 업데이트 동작 확인
- ✅ DELETE 엔드포인트 멱등성 확인
- ✅ Search 엔드포인트 대소문자 무시 검색 확인

---

## 우선순위 2차 목표: Background Processing (완료)

### 작업 범위
대규모 커버리지 계산을 비동기로 처리 (200+ nodes 대응)

### 구현 완료 사항

#### ✅ POST /agents/{agent_id}/coverage/refresh
- **파일**: `apps/api/routers/agent_router.py` (line 478-547)
- **스키마**: `BackgroundTaskResponse` (apps/api/schemas/agent_schemas.py line 227-252)
- **기능**:
  - 쿼리 파라미터: background (기본 true)
  - background=true: 202 Accepted 즉시 반환, task_id 생성
  - background=false: 동기 실행, 200 OK + 결과 포함
  - Task ID 형식: "task-{uuid4}"
  - Mock 구현: 실제 비동기 처리 없음 (향후 Celery/RQ 통합)

#### ✅ GET /agents/{agent_id}/coverage/status/{task_id}
- **파일**: `apps/api/routers/agent_router.py` (line 550-587)
- **기능**:
  - 작업 상태 조회: pending, running, completed, failed
  - Mock 구현: 항상 completed 상태 반환 (agent.coverage_percent 포함)
  - 향후: background_tasks 테이블 조회 필요

### 의존성
- **Phase 1**: GET /agents/{agent_id}/coverage (동기 커버리지 계산)
- **Service**: CoverageMeterService.calculate_coverage()

### 검증 기준
- ✅ background=true 시 202 Accepted 즉시 반환 확인
- ✅ background=false 시 동기 실행 확인
- ✅ Task ID 고유성 확인

### 향후 개선 (Phase 3)
```sql
CREATE TABLE background_tasks (
    task_id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(agent_id),
    task_type VARCHAR(50),  -- 'coverage_refresh'
    status VARCHAR(20),     -- 'pending'|'running'|'completed'|'failed'
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result JSONB,
    error TEXT
);
```

---

## 우선순위 3차 목표: Coverage History (완료)

### 작업 범위
시간 경과에 따른 커버리지 추적 및 트렌드 분석

### 구현 완료 사항

#### ✅ GET /agents/{agent_id}/coverage/history
- **파일**: `apps/api/routers/agent_router.py` (line 590-634)
- **스키마**:
  - `CoverageHistoryItem` (line 255-270)
  - `CoverageHistoryResponse` (line 273-290)
- **기능**:
  - 쿼리 파라미터: start_date, end_date (옵셔널)
  - Mock 구현: 단일 엔트리 반환 (agent.last_coverage_update 기준)
  - 향후: coverage_history 테이블 조회 필요

### 의존성
- **Agent 필드**: last_coverage_update, coverage_percent, total_documents, total_chunks

### 검증 기준
- ✅ History 엔드포인트 응답 구조 확인
- ✅ 빈 히스토리 처리 (total_entries=0)

### 향후 개선 (Phase 3)
```sql
CREATE TABLE coverage_history (
    history_id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(agent_id),
    timestamp TIMESTAMP NOT NULL,
    overall_coverage FLOAT,
    total_documents INT,
    total_chunks INT,
    node_coverage JSONB,  -- {node_id: percentage}
    INDEX idx_agent_timestamp (agent_id, timestamp DESC)
);
```

**자동 히스토리 추적**:
- GET /coverage 호출 시 coverage_history 테이블 INSERT
- 트렌드 분석 API 추가 (주간/월간 변화율)

---

## 우선순위 4차 목표: Streaming Query (완료)

### 작업 범위
실시간 결과 스트리밍으로 UX 개선 (50+ results 대응)

### 구현 완료 사항

#### ✅ POST /agents/{agent_id}/query/stream
- **파일**: `apps/api/routers/agent_router.py` (line 637-722)
- **프로토콜**: Server-Sent Events (SSE)
- **기능**:
  - Request: QueryRequest (Phase 1과 동일)
  - Response: text/event-stream
  - 헤더: Cache-Control=no-cache, Connection=keep-alive, X-Accel-Buffering=no
  - 이벤트 흐름:
    1. status=started 이벤트
    2. 개별 결과 이벤트 (50ms 딜레이)
    3. status=completed 이벤트

**SSE 이벤트 형식**:
```
data: {"status": "started", "agent_id": "123e4567-..."}

data: {"index": 0, "doc_id": "...", "content": "...", "score": 0.95}

data: {"status": "completed", "total_results": 10, "query_time_ms": 1250.5}
```

### 의존성
- **Phase 1**: POST /agents/{agent_id}/query (동기 쿼리)
- **Service**: SearchDAO.hybrid_search()

### 검증 기준
- ✅ SSE 스트림 응답 확인
- ✅ 이벤트 순서 확인 (started → results → completed)
- ✅ 에러 처리 (404 이벤트 전송)

### 클라이언트 예제 (JavaScript)
```javascript
const eventSource = new EventSource('/api/v1/agents/123e4567-e89b-12d3-a456-426614174000/query/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.status === 'started') {
    console.log('Query started');
  } else if (data.status === 'completed') {
    console.log(`Completed: ${data.total_results} results in ${data.query_time_ms}ms`);
    eventSource.close();
  } else {
    console.log(`Result ${data.index}: ${data.content}`);
  }
};

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  eventSource.close();
};
```

---

## 테스트 전략

### Unit Tests (완료)
- **파일**: `tests/unit/test_agent_router_phase2.py`
- **Mock 대상**:
  - AgentDAO.update_agent(), delete_agent(), search_agents()
  - CoverageMeterService.calculate_coverage()
  - SearchDAO.hybrid_search()
  - verify_api_key()
- **커버리지**: 모든 Phase 2 엔드포인트 (7개)

### Integration Tests (필요)
- **파일**: `tests/integration/test_agent_api_phase2.py`
- **테스트 케이스**:
  1. PATCH → DB 업데이트 확인
  2. DELETE → DB 삭제 확인
  3. Search → ILIKE 쿼리 동작 확인
  4. Background refresh → coverage_percent 업데이트 확인
  5. Streaming query → SSE 이벤트 수신 확인

### API Tests (필요)
- **파일**: `tests/api/test_agent_openapi_phase2.py`
- **검증 항목**:
  - /docs에 Phase 2 엔드포인트 표시 여부
  - Request/Response 스키마 정확성
  - SSE 스트리밍 문서화

### Performance Tests (필요)
- **파일**: `tests/performance/test_agent_api_phase2_performance.py`
- **벤치마크**:
  - PATCH /agents/{agent_id} < 1초
  - DELETE /agents/{agent_id} < 2초
  - GET /agents/search < 1초 (1000 agents)
  - POST /coverage/refresh (background=true) < 500ms
  - POST /query/stream 첫 이벤트 < 1초

---

## 기술적 접근 방법

### 1. Partial Update (PATCH)
```python
# Pydantic exclude_unset로 제공된 필드만 추출
update_fields = request.model_dump(exclude_unset=True)

if update_fields:
    await AgentDAO.update_agent(
        session=session,
        agent_id=agent_id,
        **update_fields  # name=..., scope_description=...
    )
```

### 2. Case-Insensitive Search
```python
# SQLAlchemy ILIKE 연산자
stmt = select(Agent)
if query:
    stmt = stmt.where(Agent.name.ilike(f"%{query}%"))
stmt = stmt.limit(max_results)
```

### 3. SSE Streaming
```python
async def event_generator():
    # 1. Validate
    agent = await AgentDAO.get_agent(session, agent_id)

    # 2. Start event
    yield f"data: {json.dumps({'status': 'started'})}\n\n"

    # 3. Stream results
    for result in search_results:
        yield f"data: {json.dumps(result)}\n\n"
        await asyncio.sleep(0.05)  # 50ms delay

    # 4. Complete event
    yield f"data: {json.dumps({'status': 'completed'})}\n\n"

return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 4. Background Task Mock
```python
# Mock implementation (in-memory)
task_id = f"task-{uuid4()}"
return BackgroundTaskResponse(
    task_id=task_id,
    status="pending",
    created_at=datetime.utcnow(),
    ...
)

# Future: Celery task
@celery_app.task
def calculate_coverage_task(agent_id: str):
    ...
```

---

## 리스크 및 대응 방안

### 1. Background Task 미구현
- **현황**: Mock 구현 (항상 completed 상태)
- **리스크**: 실제 비동기 처리 불가
- **대응**: Phase 3에서 Celery/RQ 통합, background_tasks 테이블 추가

### 2. Coverage History 미구현
- **현황**: 단일 엔트리 반환 (mock)
- **리스크**: 트렌드 분석 불가
- **대응**: Phase 3에서 coverage_history 테이블 추가, 자동 히스토리 추적

### 3. SSE Proxy Buffering
- **리스크**: Nginx/Load Balancer가 SSE 버퍼링 → 스트리밍 지연
- **대응**: X-Accel-Buffering: no 헤더 설정 완료

### 4. DELETE Cascade
- **리스크**: 연관 데이터 미삭제 (background_tasks, coverage_history)
- **대응**: Phase 3에서 ON DELETE CASCADE 또는 명시적 cascade 로직 추가

---

## 완료 조건 (Definition of Done)

### Phase 2-1: Management Endpoints
- ✅ PATCH /agents/{agent_id} 구현 완료
- ✅ DELETE /agents/{agent_id} 구현 완료
- ✅ GET /agents/search 구현 완료
- ✅ AgentUpdateRequest 스키마 추가
- ✅ AgentDAO.search_agents() 메서드 추가

### Phase 2-2: Background Processing
- ✅ POST /coverage/refresh 구현 완료 (mock)
- ✅ GET /coverage/status/{task_id} 구현 완료 (mock)
- ✅ BackgroundTaskResponse 스키마 추가

### Phase 2-3: Coverage History
- ✅ GET /coverage/history 구현 완료 (mock)
- ✅ CoverageHistoryItem, CoverageHistoryResponse 스키마 추가

### Phase 2-4: Streaming Query
- ✅ POST /query/stream 구현 완료
- ✅ SSE 이벤트 생성기 구현
- ✅ StreamingResponse 헤더 설정

### 공통
- ✅ OpenAPI 문서 자동 생성 (/docs)
- ✅ API Key 인증 통합 (verify_api_key)
- ✅ 에러 처리 (404, 422, 500, 503)
- ✅ Unit Tests (완료: 15/15 passed - 2025-10-12)
- ⚠️ Integration Tests (필요)
- ⚠️ Performance Tests (필요)

---

## 다음 단계 (Phase 3 방향)

### 1. 영속적 Background Task
- background_tasks 테이블 생성
- Celery/RQ 통합
- 작업 진행률 업데이트 (0-100%)
- 작업 취소 엔드포인트

### 2. 실시간 Coverage History
- coverage_history 테이블 생성
- 자동 히스토리 추적 (GET /coverage 호출 시)
- 트렌드 분석 API (주간/월간 변화율)
- 커버리지 변화 알림

### 3. Bulk Operations
- PATCH /agents/bulk (여러 에이전트 일괄 업데이트)
- DELETE /agents/bulk (여러 에이전트 일괄 삭제)

### 4. Advanced Features
- POST /agents/{agent_id}/clone (에이전트 복제)
- WebSocket 스트리밍 (SSE 대안)
- Webhook 알림 (background task 완료 시)
