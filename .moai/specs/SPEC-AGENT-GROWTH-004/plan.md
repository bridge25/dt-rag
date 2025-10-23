# Implementation Plan: AGENT-GROWTH-004
# Phase 3 - Real Background Tasks Implementation

## Overview

본 문서는 SPEC-AGENT-GROWTH-004 (Phase 3 Real Background Tasks)의 구현 계획을 명세합니다.

**목표**: Phase 2 Mock background task endpoints를 실제 Redis 기반 JobQueue와 PostgreSQL background_tasks/coverage_history 테이블로 전환하여 프로덕션 수준의 비동기 작업 처리 시스템 구축.

## Prerequisites

### Phase 0-2 Completion Status
- ✅ **Phase 0 (AGENT-GROWTH-001)**: AgentDAO, CoverageMeterService, agents 테이블 구현 완료
- ✅ **Phase 1 (AGENT-GROWTH-002)**: 6개 기본 REST API 엔드포인트 구현 완료
- ✅ **Phase 2 (AGENT-GROWTH-003)**: 7개 고급 API 엔드포인트 구현 완료 (Mock background processing)

### Infrastructure Dependencies
- ✅ **Redis**: RedisManager (apps/api/cache/redis_manager.py) 운영 중
- ✅ **JobQueue**: apps/ingestion/batch/job_queue.py 운영 중 (ingestion 파이프라인)
- ✅ **JobOrchestrator**: apps/ingestion/batch/job_orchestrator.py 운영 중 (worker pattern 참조용)
- ✅ **PostgreSQL**: AsyncSession 기반 비동기 DB 접근 가능

### Required Validations Before Start
```bash
# 1. Redis 연결 확인
python -c "import asyncio; from apps.api.cache.redis_manager import get_redis_manager; asyncio.run(get_redis_manager())"

# 2. JobQueue 초기화 확인
python -c "import asyncio; from apps.ingestion.batch.job_queue import JobQueue; q = JobQueue(); asyncio.run(q.initialize())"

# 3. PostgreSQL agents 테이블 확인
psql -d dt_rag -c "SELECT COUNT(*) FROM agents;"

# 4. Alembic migration 최신 상태 확인
alembic current
```

## Implementation Phases

### Phase 3-1: Database Schema & Migration (1차 목표)

**Objective**: background_tasks 및 coverage_history 테이블 스키마 정의 및 Alembic migration 생성.

**Tasks**:
1. **ORM Model 정의**:
   - `apps/api/database.py`에 BackgroundTask 모델 추가
   - `apps/api/database.py`에 CoverageHistory 모델 추가
   - Foreign Key: agent_id → agents.agent_id (ON DELETE CASCADE)
   - Check constraints: overall_coverage (0.0-100.0), total_documents >= 0

2. **Alembic Migration 생성**:
   ```bash
   alembic revision -m "Add background_tasks and coverage_history tables"
   # File: alembic/versions/0012_add_background_tasks_coverage_history.py
   ```

3. **Migration Script 작성**:
   - background_tasks 테이블 생성 (17 columns)
   - coverage_history 테이블 생성 (7 columns)
   - 5개 Index 생성 (agent_id, status, timestamp 기반)
   - COMMENT 추가 (테이블 및 컬럼 설명)

4. **Migration 적용 및 검증**:
   ```bash
   # Dev database 적용
   alembic upgrade head

   # 테이블 존재 확인
   psql -d dt_rag -c "\d background_tasks"
   psql -d dt_rag -c "\d coverage_history"

   # Index 확인
   psql -d dt_rag -c "\di *background_tasks*"
   psql -d dt_rag -c "\di *coverage_history*"
   ```

**Acceptance Criteria**:
- ✅ BackgroundTask ORM model이 SQLAlchemy 모델로 정의됨
- ✅ CoverageHistory ORM model이 SQLAlchemy 모델로 정의됨
- ✅ Alembic migration 0012 파일 생성됨
- ✅ `alembic upgrade head` 실행 성공
- ✅ background_tasks 테이블이 5개 index와 함께 생성됨
- ✅ coverage_history 테이블이 3개 index와 함께 생성됨

**Files Created/Modified**:
- `apps/api/database.py` (BackgroundTask, CoverageHistory 모델 추가)
- `alembic/versions/0012_add_background_tasks_coverage_history.py` (새 파일)

---

### Phase 3-2: AgentTaskQueue & WebhookService (2차 목표)

**Objective**: JobQueue wrapper 및 Webhook 전송 서비스 구현.

**Tasks**:

1. **AgentTaskQueue 구현** (`apps/api/background/agent_task_queue.py`):
   - JobQueue 인스턴스 래핑
   - Namespace 분리: `agent:queue:{priority}` (ingestion과 독립)
   - `enqueue_coverage_task()`: task_id 생성 및 큐 등록
   - `get_queue_position()`: Redis LLEN 기반 위치 계산
   - `remove_job()`: Redis LREM으로 취소 처리

2. **WebhookService 구현** (`apps/api/background/webhook_service.py`):
   - `send_webhook()`: httpx POST 요청
   - Retry logic: exponential backoff (2^retry_count seconds)
   - Max retries: 3회
   - Timeout: 10초 per attempt
   - Optional: HMAC-SHA256 signature 헤더 (X-Agent-Signature)

3. **CoverageHistoryDAO 구현** (`apps/knowledge_builder/coverage/coverage_history.py`):
   - `insert_history()`: coverage_history 테이블 INSERT
   - `query_history()`: date filter 및 pagination 지원
   - ORDER BY timestamp DESC (최신순)

**Unit Tests** (`tests/unit/test_agent_task_queue.py`):
```python
async def test_enqueue_coverage_task_creates_job():
    """enqueue_coverage_task()가 Redis에 job을 등록하는지 확인"""
    queue = AgentTaskQueue()
    await queue.initialize()

    task_id = await queue.enqueue_coverage_task(
        agent_id=uuid4(),
        taxonomy_node_ids=[uuid4()],
        taxonomy_version="1.0.0",
        webhook_url="https://example.com/webhook"
    )

    assert task_id.startswith("agent-coverage-")

    # Redis queue 확인
    queue_size = await queue.job_queue.get_queue_size("medium")
    assert queue_size > 0

async def test_webhook_service_retries_on_failure():
    """WebhookService가 5xx 에러 시 재시도하는지 확인"""
    service = WebhookService(max_retries=3)

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.side_effect = [
            Mock(status_code=503),  # 1st attempt
            Mock(status_code=503),  # 2nd attempt
            Mock(status_code=200),  # 3rd attempt success
        ]

        result = await service.send_webhook(
            url="https://example.com/webhook",
            payload={"task_id": "123"}
        )

        assert result is True
        assert mock_post.call_count == 3

async def test_coverage_history_query_filters_by_date():
    """CoverageHistoryDAO가 date filter를 올바르게 적용하는지 확인"""
    async with async_session() as session:
        agent_id = uuid4()

        # Insert 3 history entries with different timestamps
        for i in range(3):
            await CoverageHistoryDAO.insert_history(
                session=session,
                agent_id=agent_id,
                coverage_data={
                    "overall_coverage": 80.0 + i,
                    "total_documents": 100 + i,
                    "total_chunks": 500 + i,
                    "version": "1.0.0"
                }
            )

        # Query with date filter
        start_date = datetime.utcnow() - timedelta(hours=1)
        history = await CoverageHistoryDAO.query_history(
            session=session,
            agent_id=agent_id,
            start_date=start_date,
            limit=10
        )

        assert len(history) == 3
        assert history[0].overall_coverage > history[1].overall_coverage  # DESC order
```

**Acceptance Criteria**:
- ✅ AgentTaskQueue.enqueue_coverage_task() 가 Redis agent:queue:medium에 job 등록
- ✅ AgentTaskQueue.get_queue_position() 가 Redis LLEN 기반 위치 반환
- ✅ WebhookService.send_webhook() 가 3회 재시도 후 실패 로깅
- ✅ CoverageHistoryDAO.insert_history() 가 coverage_history 테이블에 row 생성
- ✅ CoverageHistoryDAO.query_history() 가 date filter 및 정렬 올바름
- ✅ Unit tests 5개 이상 작성 및 통과

**Files Created/Modified**:
- `apps/api/background/__init__.py` (새 파일)
- `apps/api/background/agent_task_queue.py` (새 파일)
- `apps/api/background/webhook_service.py` (새 파일)
- `apps/knowledge_builder/coverage/coverage_history.py` (새 파일)
- `tests/unit/test_agent_task_queue.py` (새 파일)

---

### Phase 3-3: AgentTaskWorker Implementation (3차 목표)

**Objective**: 백그라운드 작업 처리 워커 구현 (JobOrchestrator 패턴 참조).

**Tasks**:

1. **AgentTaskWorker 클래스 구현** (`apps/api/background/agent_task_worker.py`):
   - `start()`: Worker loop 시작 (blocking)
   - `stop()`: Graceful shutdown (SIGTERM 처리)
   - `_process_coverage_task()`: Coverage 계산 로직
   - Cancellation check: background_tasks.cancellation_requested 2초마다 polling
   - Timeout handling: asyncio.wait_for(timeout=300)
   - Progress updates: background_tasks.progress_percentage 업데이트

2. **Task Status Transitions 구현**:
   ```
   pending → running (worker dequeue 시)
   running → completed (success)
   running → failed (exception)
   running → cancelled (cancellation_requested=true)
   running → timeout (5분 초과)
   ```

3. **Coverage History Integration**:
   - Coverage 계산 완료 후 CoverageHistoryDAO.insert_history() 호출
   - Timestamp: datetime.utcnow()
   - Version: agent.taxonomy_version

4. **Webhook Integration**:
   - Task 완료 후 WebhookService.send_webhook() 비동기 호출
   - Payload: {"task_id", "agent_id", "status", "result", "completed_at"}

**Integration Tests** (`tests/integration/test_agent_background_tasks.py`):
```python
async def test_end_to_end_coverage_refresh():
    """
    Given: Agent exists with taxonomy scope
    When: POST /coverage/refresh?background=true
    Then: Task created → Worker processes → Coverage updated → Webhook sent
    """
    # 1. Create agent
    agent = await AgentDAO.create_agent(...)

    # 2. Enqueue coverage refresh
    response = await client.post(
        f"/api/v1/agents/{agent.agent_id}/coverage/refresh?background=true",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 202
    task_id = response.json()["task_id"]

    # 3. Start worker
    worker = AgentTaskWorker(worker_id=0)
    worker_task = asyncio.create_task(worker.start())

    # 4. Wait for completion (max 10 seconds)
    await asyncio.sleep(10)
    worker.stop()
    await worker_task

    # 5. Check task status
    async with async_session() as session:
        task = await session.get(BackgroundTask, task_id)
        assert task.status == "completed"
        assert task.result["coverage_percent"] > 0

    # 6. Check coverage history
    history = await CoverageHistoryDAO.query_history(session, agent.agent_id)
    assert len(history) == 1

async def test_task_cancellation_pending():
    """
    Given: Task in pending status
    When: DELETE /tasks/{task_id}
    Then: Task removed from queue, status='cancelled'
    """
    # Enqueue task
    task_id = await AgentTaskQueue().enqueue_coverage_task(...)

    # Cancel task
    response = await client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 204

    # Check status
    async with async_session() as session:
        task = await session.get(BackgroundTask, task_id)
        assert task.status == "cancelled"

    # Verify removed from queue
    queue_size = await AgentTaskQueue().job_queue.get_queue_size("medium")
    assert queue_size == 0

async def test_task_timeout():
    """
    Given: Coverage calculation > 5 minutes
    When: Worker processes task
    Then: Status='timeout', error message set
    """
    # Mock CoverageMeterService.calculate_coverage() to sleep 6 minutes
    with patch("apps.knowledge_builder.coverage.meter.CoverageMeterService.calculate_coverage") as mock:
        mock.side_effect = lambda *args, **kwargs: asyncio.sleep(360)

        task_id = await AgentTaskQueue().enqueue_coverage_task(...)

        worker = AgentTaskWorker(worker_id=0)
        await worker.start()

        # Check timeout status
        async with async_session() as session:
            task = await session.get(BackgroundTask, task_id)
            assert task.status == "timeout"
            assert "timeout" in task.error.lower()
```

**Acceptance Criteria**:
- ✅ AgentTaskWorker.start() 가 Redis에서 job을 dequeue하여 처리
- ✅ Coverage 계산 성공 시 background_tasks.status='completed' 및 result 저장
- ✅ Coverage 계산 성공 시 coverage_history 테이블에 entry 생성
- ✅ Webhook 설정 시 WebhookService.send_webhook() 호출됨
- ✅ Cancellation flag 감지 시 작업 중단 및 status='cancelled'
- ✅ 5분 초과 시 timeout 처리 및 error message 저장
- ✅ Integration tests 3개 이상 작성 및 통과

**Files Created/Modified**:
- `apps/api/background/agent_task_worker.py` (새 파일)
- `tests/integration/test_agent_background_tasks.py` (새 파일)

---

### Phase 3-4: API Endpoint Updates (4차 목표)

**Objective**: Phase 2 Mock endpoints를 실제 background task 처리로 전환.

**Tasks**:

1. **POST /agents/{agent_id}/coverage/refresh 업데이트** (line 478-547):
   - Mock task_id 생성 제거
   - AgentTaskQueue.enqueue_coverage_task() 호출
   - background_tasks 테이블에 row 생성 (status='pending')
   - BackgroundTaskResponse 반환 (202 Accepted)

2. **GET /agents/{agent_id}/coverage/status/{task_id} 업데이트** (line 550-587):
   - Mock status 반환 제거
   - background_tasks 테이블 쿼리
   - Redis LLEN으로 queue_position 계산 (status='pending'인 경우)
   - TaskStatusResponse 반환 (200 OK)

3. **GET /agents/{agent_id}/coverage/history 업데이트** (line 590-634):
   - Mock single entry 반환 제거
   - CoverageHistoryDAO.query_history() 호출
   - Date filters (start_date, end_date) 적용
   - CoverageHistoryResponse 반환 (200 OK)

4. **DELETE /tasks/{task_id} 신규 엔드포인트 추가**:
   - background_tasks 테이블 쿼리
   - status='pending' → Redis LREM + status='cancelled'
   - status='running' → cancellation_requested=true 설정
   - 204 No Content 반환

5. **TaskStatusResponse Schema 추가** (`apps/api/schemas/agent_schemas.py`):
   ```python
   class TaskStatusResponse(BackgroundTaskResponse):
       queue_position: Optional[int] = None
       estimated_completion_at: Optional[datetime] = None
   ```

**Integration Tests** (`tests/integration/test_agent_api_phase3.py`):
```python
async def test_refresh_coverage_background_real():
    """POST /refresh?background=true creates real background task"""
    agent = await AgentDAO.create_agent(...)

    response = await client.post(
        f"/api/v1/agents/{agent.agent_id}/coverage/refresh?background=true"
    )

    assert response.status_code == 202
    data = response.json()
    assert data["task_id"].startswith("agent-coverage-")
    assert data["status"] == "pending"

    # Verify background_tasks row
    async with async_session() as session:
        task = await session.get(BackgroundTask, data["task_id"])
        assert task is not None
        assert task.agent_id == agent.agent_id

async def test_get_task_status_real():
    """GET /status/{task_id} returns real task status from database"""
    task_id = await AgentTaskQueue().enqueue_coverage_task(...)

    response = await client.get(f"/api/v1/agents/{agent_id}/coverage/status/{task_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] in ["pending", "running", "completed"]
    assert "queue_position" in data  # Only for pending tasks

async def test_get_coverage_history_real():
    """GET /history returns real time-series data from database"""
    # Insert 3 history entries
    for i in range(3):
        await CoverageHistoryDAO.insert_history(...)

    response = await client.get(f"/api/v1/agents/{agent_id}/coverage/history")

    assert response.status_code == 200
    data = response.json()
    assert len(data["history"]) == 3
    assert data["history"][0]["timestamp"] > data["history"][1]["timestamp"]  # DESC

async def test_cancel_task_pending():
    """DELETE /tasks/{task_id} cancels pending task"""
    task_id = await AgentTaskQueue().enqueue_coverage_task(...)

    response = await client.delete(f"/api/v1/tasks/{task_id}")

    assert response.status_code == 204

    # Verify status
    async with async_session() as session:
        task = await session.get(BackgroundTask, task_id)
        assert task.status == "cancelled"
```

**Acceptance Criteria**:
- ✅ POST /refresh?background=true 가 background_tasks row 생성 및 JobQueue 등록
- ✅ GET /status/{task_id} 가 database에서 실제 status 조회
- ✅ GET /history 가 coverage_history 테이블에서 time-series data 반환
- ✅ DELETE /tasks/{task_id} 가 취소 처리 (pending → cancelled, running → flag 설정)
- ✅ TaskStatusResponse schema에 queue_position 필드 추가됨
- ✅ Integration tests 4개 이상 작성 및 통과
- ✅ OpenAPI /docs에 DELETE /tasks 엔드포인트 문서화됨

**Files Modified**:
- `apps/api/routers/agent_router.py` (3개 endpoint 업데이트, 1개 endpoint 추가)
- `apps/api/schemas/agent_schemas.py` (TaskStatusResponse 추가)
- `tests/integration/test_agent_api_phase3.py` (새 파일)

---

### Phase 3-5: End-to-End Testing & Documentation (최종 목표)

**Objective**: 전체 워크플로우 검증 및 문서화.

**Tasks**:

1. **Performance Benchmarks** (`tests/performance/test_agent_background_performance.py`):
   ```python
   async def test_background_coverage_50_nodes():
       """50-node agent coverage calculation completes within 5 minutes"""
       start = time.time()

       task_id = await enqueue_coverage_task(50_nodes_agent)
       await wait_for_completion(task_id, max_wait=300)

       duration = time.time() - start
       assert duration < 300  # 5 minutes

   async def test_concurrent_coverage_requests():
       """100 concurrent coverage refresh requests"""
       tasks = []
       for i in range(100):
           task = enqueue_coverage_task(agent_ids[i])
           tasks.append(task)

       await asyncio.gather(*tasks)

       # Verify all tasks enqueued
       queue_size = await AgentTaskQueue().job_queue.get_queue_size()
       assert queue_size == 100
   ```

2. **Webhook Delivery Tests** (`tests/integration/test_webhook_delivery.py`):
   ```python
   async def test_webhook_delivery_success():
       """Webhook delivered successfully after task completion"""
       webhook_received = False

       # Mock webhook server
       @app.post("/webhook")
       async def webhook_handler(request: Request):
           nonlocal webhook_received
           webhook_received = True
           return {"status": "ok"}

       # Enqueue task with webhook
       task_id = await enqueue_coverage_task(
           webhook_url="http://localhost:8001/webhook"
       )

       # Process task
       await worker.process_task(task_id)

       await asyncio.sleep(1)
       assert webhook_received is True
   ```

3. **Documentation Updates**:
   - README.md: AgentTaskWorker 실행 방법 추가
   - API documentation (/docs): DELETE /tasks 엔드포인트 예제
   - Architecture diagram: Background task flow 추가

4. **Operational Validation**:
   ```bash
   # 1. Start AgentTaskWorker
   python -m apps.api.background.agent_task_worker

   # 2. Enqueue task via API
   curl -X POST "http://localhost:8000/api/v1/agents/{agent_id}/coverage/refresh?background=true" \
     -H "X-API-Key: test-key"

   # 3. Check task status
   curl "http://localhost:8000/api/v1/agents/{agent_id}/coverage/status/{task_id}" \
     -H "X-API-Key: test-key"

   # 4. Check coverage history
   curl "http://localhost:8000/api/v1/agents/{agent_id}/coverage/history" \
     -H "X-API-Key: test-key"
   ```

**Acceptance Criteria**:
- ✅ 50-node agent coverage calculation 5분 이내 완료
- ✅ 100 concurrent requests 10초 이내 enqueue 완료
- ✅ Webhook delivery 성공률 > 95% (3회 재시도 포함)
- ✅ Performance tests 2개 이상 작성 및 통과
- ✅ Webhook tests 2개 이상 작성 및 통과
- ✅ README.md 업데이트 (AgentTaskWorker 실행 가이드)
- ✅ OpenAPI /docs 문서화 완료 (DELETE /tasks 포함)

**Files Created/Modified**:
- `tests/performance/test_agent_background_performance.py` (새 파일)
- `tests/integration/test_webhook_delivery.py` (새 파일)
- `README.md` (AgentTaskWorker 섹션 추가)
- `.moai/specs/SPEC-AGENT-GROWTH-004/implementation-report.md` (새 파일)

---

## Technical Decisions

### Design Choices

1. **Namespace Separation (agent:queue vs ingestion:queue)**:
   - **Rationale**: Agent background tasks와 ingestion jobs는 lifecycle이 다름 (agent: 5분, ingestion: 30분+)
   - **Benefit**: Priority queue 충돌 방지, 독립적인 scaling 가능
   - **Trade-off**: Redis key 증가, 관리 복잡도 상승

2. **Cooperative Cancellation (Polling-based)**:
   - **Rationale**: Python asyncio는 forced termination 지원하지 않음 (안전성 문제)
   - **Benefit**: Graceful shutdown, 리소스 정리 보장
   - **Trade-off**: 2초 polling delay, 즉각 취소 불가

3. **Task Persistence (PostgreSQL + Redis)**:
   - **Rationale**: Redis는 queue만, PostgreSQL은 task status + history
   - **Benefit**: Redis 장애 시에도 task status 조회 가능
   - **Trade-off**: 2개 storage 동기화 필요

4. **Webhook Fire-and-Forget**:
   - **Rationale**: Webhook 실패로 task 완료가 block되면 안 됨
   - **Benefit**: Task completion과 webhook delivery 독립적
   - **Trade-off**: Webhook 실패 시 재시도 제한 (max 3회)

5. **TTL Cleanup (24 hours / 90 days)**:
   - **Rationale**: background_tasks는 단기 상태 추적, coverage_history는 장기 추세 분석
   - **Benefit**: 테이블 크기 제어, 쿼리 성능 유지
   - **Trade-off**: 수동 cleanup 필요 (PostgreSQL scheduled job 또는 cron)

### Alternative Approaches Considered

1. **Celery vs Custom Worker**:
   - **Rejected**: Celery는 무겁고 Redis 의존성 중복, JobQueue 재사용 불가
   - **Chosen**: Custom AgentTaskWorker로 JobQueue 패턴 일관성 유지

2. **WebSocket vs SSE for Progress Updates**:
   - **Deferred to Phase 4**: 현재 polling으로 충분, real-time 필요 시 SSE 추가

3. **Single Table vs Separate Tables (background_tasks + coverage_history)**:
   - **Chosen**: Separate tables로 TTL 정책 독립 관리, 쿼리 성능 최적화

## Risk Mitigation

### High Priority Risks

1. **Risk**: Redis 장애 시 task queue 손실
   - **Mitigation**: background_tasks 테이블에 status='pending' 유지, Redis 복구 후 재enqueue 가능
   - **Fallback**: Synchronous mode (background=false) 사용

2. **Risk**: Worker crash 시 task 상태 불일치
   - **Mitigation**: Worker restart 시 status='running' tasks를 'failed'로 전환
   - **Monitoring**: background_tasks.status='running' + (now() - started_at > 10 minutes) 알림

3. **Risk**: Coverage calculation > 5분 시 timeout
   - **Mitigation**: Large taxonomy scope agent는 synchronous mode 권장
   - **Optimization**: Coverage calculation batch size 튜닝

4. **Risk**: Webhook delivery 실패 (endpoint down)
   - **Mitigation**: 3회 재시도 + exponential backoff
   - **Logging**: Webhook 실패 로그 집계, 알림 발송

### Medium Priority Risks

1. **Risk**: Concurrent task limit 초과 (resource exhaustion)
   - **Deferred to Phase 4**: max_concurrent per agent 제한 구현 필요
   - **Temporary**: Worker 수 제한 (max_workers=10)

2. **Risk**: Coverage history 테이블 무한 증가
   - **Mitigation**: 90일 TTL cleanup (PostgreSQL scheduled job)
   - **Monitoring**: Table size weekly 체크

## Testing Strategy

### Unit Test Coverage
- AgentTaskQueue: 4 tests (enqueue, position, remove, namespace)
- WebhookService: 3 tests (success, retry, timeout)
- CoverageHistoryDAO: 3 tests (insert, query, date filter)
- **Target**: 90% code coverage

### Integration Test Coverage
- End-to-end workflow: 3 tests (success, cancellation, timeout)
- API endpoints: 4 tests (refresh, status, history, cancel)
- Webhook delivery: 2 tests (success, retry)
- **Target**: All critical paths covered

### Performance Test Coverage
- Background calculation: 1 test (50-node agent < 5 minutes)
- Concurrent requests: 1 test (100 requests < 10 seconds)
- Webhook delivery: 1 test (100 tasks < 30 seconds total)
- **Target**: All latency requirements validated

## Monitoring & Observability

### Metrics to Track
1. **Task Metrics**:
   - Task enqueue rate (tasks/second)
   - Task completion rate (tasks/second)
   - Task failure rate (%)
   - Task average duration (seconds)

2. **Queue Metrics**:
   - Queue size by priority (high/medium/low)
   - Queue wait time (seconds)
   - Worker utilization (%)

3. **Webhook Metrics**:
   - Webhook delivery success rate (%)
   - Webhook retry count distribution
   - Webhook latency (milliseconds)

### Logging Strategy
```python
# Task lifecycle events
logger.info("Task enqueued", extra={"task_id": task_id, "agent_id": agent_id})
logger.info("Task started", extra={"task_id": task_id, "worker_id": worker_id})
logger.info("Task completed", extra={"task_id": task_id, "duration_ms": duration})
logger.error("Task failed", extra={"task_id": task_id, "error": str(e)})

# Webhook events
logger.info("Webhook delivered", extra={"url": webhook_url, "task_id": task_id})
logger.warning("Webhook retry", extra={"url": webhook_url, "retry_count": retry_count})
logger.error("Webhook failed", extra={"url": webhook_url, "max_retries": max_retries})
```

### Alerting Thresholds
- Task failure rate > 10% (1 hour window)
- Queue size > 1000 tasks (any priority)
- Webhook failure rate > 20% (1 hour window)
- Worker crash count > 3 (10 minute window)

## Deployment Considerations

### Prerequisites for Production Deployment
1. Redis cluster with persistence enabled (AOF or RDB)
2. PostgreSQL scheduled job for TTL cleanup (background_tasks, coverage_history)
3. Worker process manager (systemd, supervisor, or Kubernetes)
4. Webhook URL validation (https:// required, localhost blocked)

### Deployment Sequence
1. Apply Alembic migration 0012 (background_tasks, coverage_history tables)
2. Deploy updated API server (new endpoints)
3. Deploy AgentTaskWorker as separate process
4. Enable background task API (feature flag)
5. Monitor logs and metrics for 24 hours

### Rollback Plan
1. Disable background task API (feature flag off)
2. Stop AgentTaskWorker processes
3. Revert API server to Phase 2 version (mock endpoints)
4. (Optional) Rollback Alembic migration if necessary

## Maintenance

### Weekly Tasks
- Review background_tasks table size (manual cleanup if > 100MB)
- Review coverage_history table size (TTL validation)
- Check webhook failure logs

### Monthly Tasks
- Performance benchmark validation (regression testing)
- Redis queue metrics analysis
- Worker resource usage optimization

## Success Criteria

### Functional Completeness
- ✅ All 5 implementation phases completed
- ✅ background_tasks 및 coverage_history 테이블 운영 중
- ✅ AgentTaskWorker가 Redis queue에서 task 처리
- ✅ Webhook delivery 3회 재시도 동작 확인
- ✅ Coverage history time-series data 조회 가능

### Quality Gates
- ✅ Unit test coverage > 90%
- ✅ Integration test coverage: all critical paths
- ✅ Performance tests: all latency requirements met
- ✅ OpenAPI /docs 문서화 완료

### Operational Readiness
- ✅ AgentTaskWorker systemd service 설정
- ✅ Monitoring dashboards 구성 (Grafana/Prometheus)
- ✅ Alert rules 설정
- ✅ Runbook 작성 (troubleshooting guide)

## Related Specifications

- **Phase 0**: @SPEC:AGENT-GROWTH-001 (AgentDAO, CoverageMeterService)
- **Phase 1**: @SPEC:AGENT-GROWTH-002 (6 basic REST APIs)
- **Phase 2**: @SPEC:AGENT-GROWTH-003 (7 advanced APIs with mock background)
- **Dependencies**: JobQueue (apps/ingestion/batch/job_queue.py), RedisManager (apps/api/cache/redis_manager.py)

## Notes

- **시간 예측 금지**: 우선순위 기반 마일스톤만 명시 (1차 목표, 2차 목표, ...)
- **Context Engineering**: Phase 3-4 진행 중 Phase 0-2 문서 참조 최소화 (필요 시 JIT 로딩)
- **Compaction**: Phase 3-5 완료 후 `/clear` 또는 `/new` 권장
