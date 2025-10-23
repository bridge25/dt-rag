# Acceptance Criteria: AGENT-GROWTH-004
# Phase 3 - Real Background Tasks Acceptance Tests

## Overview

본 문서는 SPEC-AGENT-GROWTH-004 (Phase 3 Real Background Tasks)의 수락 기준을 Given-When-Then 형식으로 정의합니다.

**검증 범위**:
- background_tasks 테이블 및 coverage_history 테이블 운영
- AgentTaskQueue 및 JobQueue 통합
- AgentTaskWorker 백그라운드 처리
- WebhookService retry 로직
- API 엔드포인트 (POST /refresh, GET /status, GET /history, DELETE /tasks)

## Acceptance Test Scenarios

### AC-1: Background Coverage Refresh (Async Mode)

**Given**: Agent exists with taxonomy scope (50 nodes)
**When**: Client calls POST /agents/{agent_id}/coverage/refresh?background=true
**Then**:
1. API returns 202 Accepted with BackgroundTaskResponse
2. background_tasks table has row with status='pending'
3. Redis agent:queue:medium has job payload
4. task_id format is "agent-coverage-{uuid4}"

**Test Steps**:
```python
async def test_ac1_background_coverage_refresh():
    # Given: Create agent with 50 nodes
    agent = await AgentDAO.create_agent(
        session=session,
        name="Test Agent",
        taxonomy_node_ids=[uuid4() for _ in range(50)],
        taxonomy_version="1.0.0"
    )

    # When: POST /coverage/refresh?background=true
    response = await client.post(
        f"/api/v1/agents/{agent.agent_id}/coverage/refresh?background=true",
        headers={"X-API-Key": "test-key"}
    )

    # Then: 202 Accepted
    assert response.status_code == 202
    data = response.json()

    # Then: task_id format
    assert data["task_id"].startswith("agent-coverage-")
    assert data["status"] == "pending"
    assert data["agent_id"] == str(agent.agent_id)

    # Then: background_tasks row exists
    async with async_session() as session:
        task = await session.get(BackgroundTask, data["task_id"])
        assert task is not None
        assert task.status == "pending"
        assert task.agent_id == agent.agent_id

    # Then: Redis queue has job
    queue_size = await AgentTaskQueue().job_queue.get_queue_size("medium")
    assert queue_size > 0
```

**Pass Criteria**:
- ✅ 202 Accepted 응답
- ✅ background_tasks 테이블에 row 생성됨
- ✅ Redis agent:queue:medium에 job 등록됨
- ✅ task_id가 올바른 형식

---

### AC-2: Background Task Processing (Worker)

**Given**: background_tasks row with status='pending' and job in Redis queue
**When**: AgentTaskWorker dequeues and processes task
**Then**:
1. background_tasks.status transitions: pending → running → completed
2. background_tasks.started_at is set when status='running'
3. background_tasks.completed_at is set when status='completed'
4. background_tasks.result contains coverage data (JSON)
5. coverage_history table has new row with timestamp

**Test Steps**:
```python
async def test_ac2_background_task_processing():
    # Given: Enqueue coverage task
    agent = await AgentDAO.create_agent(...)
    task_id = await AgentTaskQueue().enqueue_coverage_task(
        agent_id=agent.agent_id,
        taxonomy_node_ids=agent.taxonomy_node_ids,
        taxonomy_version=agent.taxonomy_version
    )

    # Given: background_tasks row exists
    async with async_session() as session:
        task = await session.get(BackgroundTask, task_id)
        assert task.status == "pending"

    # When: Worker processes task
    worker = AgentTaskWorker(worker_id=0)
    worker_task = asyncio.create_task(worker.start())

    # Wait for processing (max 10 seconds)
    await asyncio.sleep(10)
    worker.stop()
    await worker_task

    # Then: Status transitions
    async with async_session() as session:
        task = await session.get(BackgroundTask, task_id)
        assert task.status == "completed"
        assert task.started_at is not None
        assert task.completed_at is not None
        assert task.result is not None
        assert "coverage_percent" in task.result

    # Then: coverage_history row created
    history = await CoverageHistoryDAO.query_history(session, agent.agent_id)
    assert len(history) >= 1
    assert history[0].overall_coverage == task.result["coverage_percent"]
```

**Pass Criteria**:
- ✅ Status 전환: pending → running → completed
- ✅ started_at 및 completed_at 타임스탬프 설정됨
- ✅ result JSONB 필드에 coverage 데이터 저장됨
- ✅ coverage_history 테이블에 row 생성됨

---

### AC-3: Task Status Query (Real-time)

**Given**: background_tasks row with status='pending'
**When**: Client calls GET /agents/{agent_id}/coverage/status/{task_id}
**Then**:
1. API returns 200 OK with TaskStatusResponse
2. Response includes queue_position (calculated from Redis LLEN)
3. Response includes progress_percentage (0.0 for pending)

**Test Steps**:
```python
async def test_ac3_task_status_query():
    # Given: Enqueue task (pending)
    task_id = await AgentTaskQueue().enqueue_coverage_task(...)

    # When: GET /status/{task_id}
    response = await client.get(
        f"/api/v1/agents/{agent_id}/coverage/status/{task_id}",
        headers={"X-API-Key": "test-key"}
    )

    # Then: 200 OK
    assert response.status_code == 200
    data = response.json()

    # Then: Response fields
    assert data["task_id"] == task_id
    assert data["status"] == "pending"
    assert data["queue_position"] is not None  # Redis LLEN result
    assert data["progress_percentage"] == 0.0
    assert data["created_at"] is not None

    # Given: Task transitions to running
    async with async_session() as session:
        task = await session.get(BackgroundTask, task_id)
        task.status = "running"
        task.started_at = datetime.utcnow()
        task.progress_percentage = 50.0
        await session.commit()

    # When: GET /status/{task_id} again
    response = await client.get(
        f"/api/v1/agents/{agent_id}/coverage/status/{task_id}",
        headers={"X-API-Key": "test-key"}
    )

    # Then: Status updated
    data = response.json()
    assert data["status"] == "running"
    assert data["queue_position"] is None  # Only for pending
    assert data["progress_percentage"] == 50.0
    assert data["started_at"] is not None
```

**Pass Criteria**:
- ✅ 200 OK 응답
- ✅ status='pending' 시 queue_position 반환
- ✅ status='running' 시 progress_percentage 반환
- ✅ Database query 기반 실시간 상태 반영

---

### AC-4: Coverage History Query (Time-series)

**Given**: coverage_history table has 3 entries for agent (different timestamps)
**When**: Client calls GET /agents/{agent_id}/coverage/history
**Then**:
1. API returns 200 OK with CoverageHistoryResponse
2. Response includes 3 history entries ordered by timestamp DESC
3. Each entry has overall_coverage, total_documents, total_chunks, timestamp fields

**Test Steps**:
```python
async def test_ac4_coverage_history_query():
    # Given: Insert 3 history entries
    agent_id = uuid4()
    for i in range(3):
        await CoverageHistoryDAO.insert_history(
            session=session,
            agent_id=agent_id,
            coverage_data={
                "overall_coverage": 80.0 + i,
                "total_documents": 100 + i * 10,
                "total_chunks": 500 + i * 50,
                "version": "1.0.0"
            }
        )
        await asyncio.sleep(0.1)  # Ensure different timestamps

    # When: GET /coverage/history
    response = await client.get(
        f"/api/v1/agents/{agent_id}/coverage/history",
        headers={"X-API-Key": "test-key"}
    )

    # Then: 200 OK
    assert response.status_code == 200
    data = response.json()

    # Then: 3 entries
    assert len(data["history"]) == 3
    assert data["total_entries"] == 3
    assert data["agent_id"] == str(agent_id)

    # Then: DESC order (newest first)
    assert data["history"][0]["overall_coverage"] == 82.0  # Latest
    assert data["history"][1]["overall_coverage"] == 81.0
    assert data["history"][2]["overall_coverage"] == 80.0  # Oldest

    # Then: All required fields present
    for entry in data["history"]:
        assert "timestamp" in entry
        assert "overall_coverage" in entry
        assert "total_documents" in entry
        assert "total_chunks" in entry
```

**Pass Criteria**:
- ✅ 200 OK 응답
- ✅ 3개 history entries 반환
- ✅ timestamp DESC 정렬 (최신순)
- ✅ 모든 필수 필드 포함

---

### AC-5: Coverage History with Date Filters

**Given**: coverage_history table has 5 entries spanning 7 days
**When**: Client calls GET /agents/{agent_id}/coverage/history?start_date={3_days_ago}
**Then**:
1. API returns only entries with timestamp >= start_date
2. Response includes filtered count (not all 5 entries)

**Test Steps**:
```python
async def test_ac5_coverage_history_date_filters():
    # Given: Insert 5 entries (7 days span)
    agent_id = uuid4()
    now = datetime.utcnow()

    for i in range(5):
        timestamp = now - timedelta(days=i * 2)  # Day 0, 2, 4, 6, 8
        await CoverageHistoryDAO.insert_history(
            session=session,
            agent_id=agent_id,
            coverage_data={
                "overall_coverage": 80.0 + i,
                "timestamp": timestamp,  # Override timestamp
                ...
            }
        )

    # When: GET /history with start_date filter (3 days ago)
    start_date = (now - timedelta(days=3)).isoformat()
    response = await client.get(
        f"/api/v1/agents/{agent_id}/coverage/history?start_date={start_date}",
        headers={"X-API-Key": "test-key"}
    )

    # Then: Filtered results (only entries within 3 days)
    data = response.json()
    assert len(data["history"]) == 2  # Day 0, Day 2
    assert data["start_date"] == start_date

    # Verify timestamps
    for entry in data["history"]:
        entry_timestamp = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
        assert entry_timestamp >= datetime.fromisoformat(start_date)
```

**Pass Criteria**:
- ✅ start_date filter 적용됨
- ✅ 필터링된 결과만 반환
- ✅ 모든 반환된 entry의 timestamp >= start_date

---

### AC-6: Task Cancellation (Pending Task)

**Given**: background_tasks row with status='pending' in Redis queue
**When**: Client calls DELETE /tasks/{task_id}
**Then**:
1. API returns 204 No Content
2. background_tasks.status updated to 'cancelled'
3. background_tasks.completed_at is set
4. Job removed from Redis queue (LREM)

**Test Steps**:
```python
async def test_ac6_task_cancellation_pending():
    # Given: Enqueue task (pending)
    task_id = await AgentTaskQueue().enqueue_coverage_task(...)

    # Given: Verify queue size
    queue_size_before = await AgentTaskQueue().job_queue.get_queue_size("medium")
    assert queue_size_before > 0

    # When: DELETE /tasks/{task_id}
    response = await client.delete(
        f"/api/v1/tasks/{task_id}",
        headers={"X-API-Key": "test-key"}
    )

    # Then: 204 No Content
    assert response.status_code == 204

    # Then: Status updated
    async with async_session() as session:
        task = await session.get(BackgroundTask, task_id)
        assert task.status == "cancelled"
        assert task.completed_at is not None

    # Then: Removed from queue
    queue_size_after = await AgentTaskQueue().job_queue.get_queue_size("medium")
    assert queue_size_after == queue_size_before - 1
```

**Pass Criteria**:
- ✅ 204 No Content 응답
- ✅ background_tasks.status='cancelled'
- ✅ completed_at 타임스탬프 설정됨
- ✅ Redis queue에서 제거됨

---

### AC-7: Task Cancellation (Running Task)

**Given**: background_tasks row with status='running' (worker processing)
**When**: Client calls DELETE /tasks/{task_id}
**Then**:
1. API returns 204 No Content
2. background_tasks.cancellation_requested set to true
3. Worker detects flag and stops processing gracefully
4. background_tasks.status updated to 'cancelled'

**Test Steps**:
```python
async def test_ac7_task_cancellation_running():
    # Given: Start worker and enqueue long-running task
    task_id = await AgentTaskQueue().enqueue_coverage_task(...)

    worker = AgentTaskWorker(worker_id=0)
    worker_task = asyncio.create_task(worker.start())

    # Wait for task to start processing
    await asyncio.sleep(2)

    async with async_session() as session:
        task = await session.get(BackgroundTask, task_id)
        assert task.status == "running"

    # When: DELETE /tasks/{task_id}
    response = await client.delete(
        f"/api/v1/tasks/{task_id}",
        headers={"X-API-Key": "test-key"}
    )

    # Then: 204 No Content
    assert response.status_code == 204

    # Then: cancellation_requested flag set
    async with async_session() as session:
        task = await session.get(BackgroundTask, task_id)
        assert task.cancellation_requested is True

    # Wait for worker to detect flag (2 seconds polling)
    await asyncio.sleep(3)

    # Then: Status updated to cancelled
    async with async_session() as session:
        task = await session.get(BackgroundTask, task_id)
        assert task.status == "cancelled"

    # Cleanup
    worker.stop()
    await worker_task
```

**Pass Criteria**:
- ✅ 204 No Content 응답
- ✅ cancellation_requested 플래그 설정됨
- ✅ Worker가 플래그 감지 (2초 이내)
- ✅ Status='cancelled'로 전환됨

---

### AC-8: Task Timeout (5 Minutes)

**Given**: Coverage calculation takes longer than 5 minutes
**When**: AgentTaskWorker processes task
**Then**:
1. background_tasks.status updated to 'timeout'
2. background_tasks.error contains "Task timeout exceeded"
3. background_tasks.completed_at is set

**Test Steps**:
```python
async def test_ac8_task_timeout():
    # Given: Mock coverage calculation to sleep 6 minutes
    with patch("apps.knowledge_builder.coverage.meter.CoverageMeterService.calculate_coverage") as mock:
        mock.side_effect = lambda *args, **kwargs: asyncio.sleep(360)  # 6 minutes

        # Given: Enqueue task
        task_id = await AgentTaskQueue().enqueue_coverage_task(...)

        # When: Worker processes task (with 5-minute timeout)
        worker = AgentTaskWorker(worker_id=0)
        worker_task = asyncio.create_task(worker.start())

        # Wait for timeout (5 minutes + buffer)
        await asyncio.sleep(310)

        # Then: Status updated to timeout
        async with async_session() as session:
            task = await session.get(BackgroundTask, task_id)
            assert task.status == "timeout"
            assert "timeout" in task.error.lower()
            assert task.completed_at is not None

        # Cleanup
        worker.stop()
        await worker_task
```

**Pass Criteria**:
- ✅ Status='timeout' 전환됨
- ✅ error 필드에 "timeout" 메시지 포함
- ✅ completed_at 타임스탬프 설정됨

---

### AC-9: Webhook Delivery (Success)

**Given**: Task completes successfully with webhook_url configured
**When**: AgentTaskWorker finishes task
**Then**:
1. WebhookService.send_webhook() is called
2. POST request sent to webhook_url with payload
3. background_tasks.webhook_retry_count remains 0

**Test Steps**:
```python
async def test_ac9_webhook_delivery_success():
    # Given: Mock webhook server
    webhook_received = False
    webhook_payload = None

    @app.post("/test-webhook")
    async def webhook_handler(request: Request):
        nonlocal webhook_received, webhook_payload
        webhook_received = True
        webhook_payload = await request.json()
        return {"status": "ok"}

    # Given: Enqueue task with webhook_url
    task_id = await AgentTaskQueue().enqueue_coverage_task(
        agent_id=agent.agent_id,
        taxonomy_node_ids=agent.taxonomy_node_ids,
        taxonomy_version=agent.taxonomy_version,
        webhook_url="http://localhost:8001/test-webhook"
    )

    # When: Worker processes task
    worker = AgentTaskWorker(worker_id=0)
    worker_task = asyncio.create_task(worker.start())

    await asyncio.sleep(10)
    worker.stop()
    await worker_task

    # Then: Webhook received
    assert webhook_received is True
    assert webhook_payload["task_id"] == task_id
    assert webhook_payload["status"] == "completed"
    assert "result" in webhook_payload

    # Then: webhook_retry_count = 0
    async with async_session() as session:
        task = await session.get(BackgroundTask, task_id)
        assert task.webhook_retry_count == 0
```

**Pass Criteria**:
- ✅ Webhook POST 요청 전송됨
- ✅ Payload에 task_id, status, result 포함
- ✅ webhook_retry_count=0 유지됨

---

### AC-10: Webhook Retry (Exponential Backoff)

**Given**: Webhook endpoint returns 503 Service Unavailable twice, then 200 OK
**When**: WebhookService.send_webhook() is called
**Then**:
1. 3 attempts total (initial + 2 retries)
2. Retry delays: 1 second, 2 seconds
3. Final attempt succeeds (200 OK)
4. background_tasks.webhook_retry_count = 2

**Test Steps**:
```python
async def test_ac10_webhook_retry_exponential_backoff():
    # Given: Mock webhook endpoint with failures
    attempt_count = 0

    @app.post("/test-webhook")
    async def webhook_handler(request: Request):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count <= 2:
            return JSONResponse(status_code=503, content={"error": "Service unavailable"})
        return {"status": "ok"}

    # Given: Enqueue task with webhook_url
    task_id = await AgentTaskQueue().enqueue_coverage_task(
        webhook_url="http://localhost:8001/test-webhook",
        ...
    )

    # When: Worker processes task
    start_time = time.time()
    worker = AgentTaskWorker(worker_id=0)
    worker_task = asyncio.create_task(worker.start())

    await asyncio.sleep(15)  # Wait for retries
    worker.stop()
    await worker_task

    # Then: 3 attempts made
    assert attempt_count == 3

    # Then: Total time includes backoff delays (1s + 2s = 3s minimum)
    elapsed = time.time() - start_time
    assert elapsed >= 3.0

    # Then: webhook_retry_count = 2
    async with async_session() as session:
        task = await session.get(BackgroundTask, task_id)
        assert task.webhook_retry_count == 2
```

**Pass Criteria**:
- ✅ 3회 시도 (1 initial + 2 retries)
- ✅ Exponential backoff 적용됨 (1s, 2s)
- ✅ 최종 시도 성공
- ✅ webhook_retry_count=2 기록됨

---

### AC-11: Webhook Failure (Max Retries)

**Given**: Webhook endpoint returns 503 Service Unavailable 3 times
**When**: WebhookService.send_webhook() is called
**Then**:
1. 3 attempts total (all fail)
2. WebhookService logs error "Webhook failed after 3 retries"
3. Task status remains 'completed' (webhook failure doesn't fail task)
4. background_tasks.webhook_retry_count = 3

**Test Steps**:
```python
async def test_ac11_webhook_failure_max_retries():
    # Given: Mock webhook endpoint always fails
    @app.post("/test-webhook")
    async def webhook_handler(request: Request):
        return JSONResponse(status_code=503, content={"error": "Service unavailable"})

    # Given: Enqueue task with webhook_url
    task_id = await AgentTaskQueue().enqueue_coverage_task(
        webhook_url="http://localhost:8001/test-webhook",
        ...
    )

    # When: Worker processes task (with logging capture)
    with capture_logs() as logs:
        worker = AgentTaskWorker(worker_id=0)
        worker_task = asyncio.create_task(worker.start())

        await asyncio.sleep(15)
        worker.stop()
        await worker_task

    # Then: Error logged
    assert any("Webhook failed after 3 retries" in log for log in logs)

    # Then: Task status = completed (webhook failure ignored)
    async with async_session() as session:
        task = await session.get(BackgroundTask, task_id)
        assert task.status == "completed"
        assert task.webhook_retry_count == 3
```

**Pass Criteria**:
- ✅ 3회 시도 모두 실패
- ✅ Error log 기록됨
- ✅ Task status='completed' 유지 (fire-and-forget)
- ✅ webhook_retry_count=3 기록됨

---

### AC-12: Performance - 50-Node Coverage < 5 Minutes

**Given**: Agent with 50 taxonomy nodes and 1000 documents
**When**: Background coverage refresh is triggered
**Then**:
1. Task completes within 5 minutes (300 seconds)
2. background_tasks.status='completed'
3. Coverage result accuracy validated

**Test Steps**:
```python
async def test_ac12_performance_50_node_coverage():
    # Given: Agent with 50 nodes, 1000 documents
    agent = await AgentDAO.create_agent(
        name="Large Agent",
        taxonomy_node_ids=[uuid4() for _ in range(50)],
        ...
    )

    # Insert 1000 documents across 50 nodes
    for i in range(1000):
        await insert_test_document(node_id=agent.taxonomy_node_ids[i % 50])

    # When: Background coverage refresh
    start_time = time.time()
    task_id = await AgentTaskQueue().enqueue_coverage_task(...)

    worker = AgentTaskWorker(worker_id=0)
    worker_task = asyncio.create_task(worker.start())

    # Wait for completion (max 5 minutes)
    await wait_for_task_completion(task_id, max_wait=300)

    worker.stop()
    await worker_task

    # Then: Completed within 5 minutes
    elapsed = time.time() - start_time
    assert elapsed < 300  # 5 minutes

    # Then: Status = completed
    async with async_session() as session:
        task = await session.get(BackgroundTask, task_id)
        assert task.status == "completed"
        assert task.result["coverage_percent"] > 0
```

**Pass Criteria**:
- ✅ 50-node agent coverage < 5분
- ✅ Status='completed' 확인
- ✅ Coverage 계산 정확성 검증

---

### AC-13: Performance - 100 Concurrent Requests

**Given**: 100 agents exist in database
**When**: 100 concurrent POST /coverage/refresh?background=true requests
**Then**:
1. All 100 requests return 202 Accepted within 10 seconds
2. All 100 tasks enqueued to Redis
3. background_tasks table has 100 rows with status='pending'

**Test Steps**:
```python
async def test_ac13_performance_concurrent_requests():
    # Given: Create 100 agents
    agents = []
    for i in range(100):
        agent = await AgentDAO.create_agent(name=f"Agent-{i}", ...)
        agents.append(agent)

    # When: 100 concurrent requests
    start_time = time.time()

    tasks = []
    for agent in agents:
        task = client.post(
            f"/api/v1/agents/{agent.agent_id}/coverage/refresh?background=true",
            headers={"X-API-Key": "test-key"}
        )
        tasks.append(task)

    responses = await asyncio.gather(*tasks)

    elapsed = time.time() - start_time

    # Then: All within 10 seconds
    assert elapsed < 10.0

    # Then: All 202 Accepted
    for response in responses:
        assert response.status_code == 202

    # Then: Redis queue size = 100
    queue_size = await AgentTaskQueue().job_queue.get_queue_size("medium")
    assert queue_size == 100

    # Then: background_tasks table has 100 rows
    async with async_session() as session:
        count = await session.execute(
            select(func.count()).select_from(BackgroundTask).where(
                BackgroundTask.status == "pending"
            )
        )
        assert count.scalar() == 100
```

**Pass Criteria**:
- ✅ 100 requests < 10초
- ✅ 모든 요청 202 Accepted
- ✅ Redis queue size=100
- ✅ background_tasks 테이블 100 rows

---

## Summary of Acceptance Criteria

### Functional Requirements (AC-1 to AC-11)
- ✅ **AC-1**: Background coverage refresh (async mode)
- ✅ **AC-2**: Background task processing (worker)
- ✅ **AC-3**: Task status query (real-time)
- ✅ **AC-4**: Coverage history query (time-series)
- ✅ **AC-5**: Coverage history with date filters
- ✅ **AC-6**: Task cancellation (pending task)
- ✅ **AC-7**: Task cancellation (running task)
- ✅ **AC-8**: Task timeout (5 minutes)
- ✅ **AC-9**: Webhook delivery (success)
- ✅ **AC-10**: Webhook retry (exponential backoff)
- ✅ **AC-11**: Webhook failure (max retries)

### Performance Requirements (AC-12 to AC-13)
- ✅ **AC-12**: 50-node coverage < 5 minutes
- ✅ **AC-13**: 100 concurrent requests < 10 seconds

### Quality Gates

**Coverage**:
- Unit test coverage: > 90%
- Integration test coverage: All critical paths
- Acceptance test coverage: 13 scenarios

**Latency**:
- POST /refresh: < 500ms (enqueue only)
- GET /status: < 500ms (database + Redis LLEN)
- GET /history: < 500ms (database query with limit 1000)
- DELETE /tasks: < 200ms (database update)

**Reliability**:
- Task success rate: > 95% (excluding user errors)
- Webhook delivery success rate: > 95% (with 3 retries)
- Worker crash recovery: < 5 minutes (systemd restart)

## Testing Checklist

### Pre-Deployment Validation
- [ ] All 13 acceptance tests pass
- [ ] Unit test coverage > 90%
- [ ] Integration test coverage: all critical paths
- [ ] Performance benchmarks validated
- [ ] OpenAPI /docs documentation complete

### Operational Readiness
- [ ] Redis cluster with persistence enabled
- [ ] PostgreSQL scheduled job for TTL cleanup
- [ ] AgentTaskWorker systemd service configured
- [ ] Monitoring dashboards created (Grafana/Prometheus)
- [ ] Alert rules configured
- [ ] Runbook written (troubleshooting guide)

### Rollback Plan
- [ ] Feature flag for background task API
- [ ] Rollback procedure documented
- [ ] Rollback tested in staging environment

## Notes

- **Given-When-Then 형식**: 모든 acceptance test는 BDD 스타일로 작성됨
- **Database 상태 검증**: 각 test는 database 및 Redis 상태를 직접 확인
- **Time-sensitive tests**: Timeout 및 performance tests는 환경에 따라 threshold 조정 필요
- **Mock vs Real**: Unit tests는 mock 사용, Integration tests는 실제 database/Redis 사용
