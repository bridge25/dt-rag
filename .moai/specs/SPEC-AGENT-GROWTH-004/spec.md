---
id: AGENT-GROWTH-004
version: 0.1.0
status: completed
created: 2025-10-12
updated: 2025-11-05
author: @sonheungmin
priority: high
category: feature
labels:
  - background-tasks
  - redis
  - job-queue
  - webhook
  - coverage-history
depends_on:
  - AGENT-GROWTH-001
  - AGENT-GROWTH-002
  - AGENT-GROWTH-003
scope:
  packages:
    - apps/api/routers
    - apps/api/background
    - apps/knowledge_builder/coverage
  files:
    - agent_router.py
    - agent_task_queue.py
    - webhook_service.py
    - coverage_history.py
---

# @SPEC:AGENT-GROWTH-004: Agent Growth Platform Phase 3 - Real Background Tasks

## HISTORY

### v0.1.0 (2025-10-12)
- **INITIAL**: Phase 3 Real Background Tasks 명세 최초 작성
- **AUTHOR**: @sonheungmin
- **SCOPE**: background_tasks 테이블, coverage_history 테이블, JobQueue 통합, Webhook 시스템
- **CONTEXT**: Phase 2 Mock Implementation을 실제 Redis 기반 백그라운드 처리로 전환
- **DEPENDENCIES**: SPEC-AGENT-GROWTH-003 (Mock endpoints), JobQueue (apps/ingestion/batch/job_queue.py)
- **PHASE**: Phase 3 Real Implementation

## Environment

- **Backend Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 12+ (agents 테이블 + background_tasks 테이블 + coverage_history 테이블)
- **Redis**: Redis 6+ (job queue persistence via RedisManager)
- **Job Queue**: apps/ingestion/batch/job_queue.py (기존 JobQueue class 재사용)
- **Job Orchestrator**: apps/ingestion/batch/job_orchestrator.py (참고용 worker pattern)
- **Authentication**: API Key (기존 `apps/api/security.py` 활용)
- **Python Version**: 3.9+
- **Phase 2 Prerequisites**:
  - Mock POST /agents/{agent_id}/coverage/refresh?background=true (line 478-547)
  - Mock GET /agents/{agent_id}/coverage/status/{task_id} (line 550-587)
  - Mock GET /agents/{agent_id}/coverage/history (line 590-634)
  - BackgroundTaskResponse schema (apps/api/schemas/agent_schemas.py line 209-290)
  - CoverageHistoryResponse schema

## Assumptions

1. **Phase 2 Complete**: SPEC-AGENT-GROWTH-003 구현 완료 (Mock background task endpoints 운영 중)
2. **JobQueue Reuse**: apps/ingestion/batch/job_queue.py 재사용 (ingestion:queue → agent:queue 분리)
3. **RedisManager Available**: apps/api/cache/redis_manager.py 사용 가능 (REDIS_URL 설정 완료)
4. **Task Persistence**: background_tasks 테이블에 task 상태 저장 (Redis는 queue만 관리)
5. **Coverage History Tracking**: coverage_history 테이블에 시계열 데이터 저장 (90일 TTL)
6. **Webhook Optional**: webhook_url이 제공된 경우에만 POST 전송 (최대 3회 재시도)
7. **Worker Pattern**: JobOrchestrator와 독립적인 AgentTaskWorker 구현 (별도 프로세스)
8. **Task Cancellation**: cooperative cancellation (polling-based, graceful shutdown)
9. **Priority System**: JobQueue priority 매핑 (agent coverage = priority 5, medium queue)
10. **Database Migration**: Alembic migration으로 2개 테이블 추가

## EARS Requirements

### Ubiquitous Requirements (Core Background Task Infrastructure)

**U-REQ-001**: System SHALL provide background_tasks table with columns (task_id PK UUID, agent_id FK UUID, task_type VARCHAR(50), status VARCHAR(20), created_at TIMESTAMP, started_at TIMESTAMP, completed_at TIMESTAMP, result JSONB, error TEXT, webhook_url TEXT, webhook_retry_count INTEGER, cancellation_requested BOOLEAN, queue_position INTEGER, progress_percentage FLOAT, estimated_completion_at TIMESTAMP).

**U-REQ-002**: System SHALL provide coverage_history table with columns (history_id PK UUID, agent_id FK UUID, timestamp TIMESTAMP, overall_coverage FLOAT, total_documents INTEGER, total_chunks INTEGER, version VARCHAR(20)).

**U-REQ-003**: System SHALL provide AgentTaskQueue class wrapping JobQueue with namespace prefix "agent:queue" separated from "ingestion:queue".

**U-REQ-004**: System SHALL provide WebhookService class with methods send_webhook(url, payload, secret) and retry_webhook(url, payload, retry_count, max_retries).

**U-REQ-005**: System SHALL provide CoverageHistoryDAO class with methods insert_history(agent_id, coverage_data) and query_history(agent_id, start_date, end_date, limit).

**U-REQ-006**: System SHALL provide AgentTaskWorker class separate from JobOrchestrator to process agent-specific tasks (coverage refresh).

**U-REQ-007**: System SHALL store BackgroundTask rows in background_tasks table with status transitions (pending → running → completed|failed|cancelled|timeout).

**U-REQ-008**: System SHALL insert CoverageHistory rows after successful coverage calculation with timestamp, overall_coverage, total_documents, total_chunks fields.

**U-REQ-009**: System SHALL support task cancellation via DELETE /tasks/{task_id} endpoint setting cancellation_requested flag and removing from JobQueue if pending.

**U-REQ-010**: System SHALL execute webhook POST requests with payload {"task_id", "agent_id", "status", "result", "completed_at"} to webhook_url on task completion.

**U-REQ-011**: System SHALL implement webhook retry logic with exponential backoff (delay = 2^retry_count seconds, max_retries=3, timeout=10s per attempt).

**U-REQ-012**: System SHALL calculate queue_position from JobQueue.llen(queue_key) and update background_tasks.queue_position on task status queries.

**U-REQ-013**: System SHALL implement TTL cleanup for background_tasks (24 hours after completion) and coverage_history (90 days retention).

**U-REQ-014**: System SHALL use TaskStatusResponse schema extending BackgroundTaskResponse with queue_position, estimated_completion_at fields.

**U-REQ-015**: System SHALL namespace agent tasks with task_id format "agent-coverage-{uuid4}" distinct from ingestion task_id format.

### Event-driven Requirements (Background Task Lifecycle)

**E-REQ-001**: WHEN POST /agents/{agent_id}/coverage/refresh receives background=true, System SHALL call AgentTaskQueue.enqueue_coverage_task(agent_id, taxonomy_node_ids, taxonomy_version, webhook_url) and insert background_tasks row with status='pending'.

**E-REQ-002**: WHEN AgentTaskQueue.enqueue_coverage_task() is invoked, System SHALL generate task_id="agent-coverage-{uuid4}", store background_tasks row, enqueue to JobQueue with priority=5, and return task_id.

**E-REQ-003**: WHEN AgentTaskWorker dequeues coverage task, System SHALL update background_tasks.status='running', background_tasks.started_at=now(), and call CoverageMeterService.calculate_coverage().

**E-REQ-004**: WHEN CoverageMeterService.calculate_coverage() completes successfully, System SHALL update background_tasks.status='completed', background_tasks.result={"coverage_percent": X, "node_coverage": {...}}, background_tasks.completed_at=now().

**E-REQ-005**: WHEN coverage calculation completes, System SHALL call CoverageHistoryDAO.insert_history(agent_id, coverage_data) to store time-series entry with timestamp=now().

**E-REQ-006**: WHEN coverage calculation completes with webhook_url configured, System SHALL call WebhookService.send_webhook(webhook_url, task_completion_payload) asynchronously.

**E-REQ-007**: WHEN WebhookService.send_webhook() fails with HTTP 5xx or timeout, System SHALL retry with exponential backoff up to max_retries=3 times.

**E-REQ-008**: WHEN webhook delivery fails after 3 retries, System SHALL log error and update background_tasks.webhook_retry_count=3 without failing task.

**E-REQ-009**: WHEN GET /agents/{agent_id}/coverage/status/{task_id} is invoked, System SHALL query background_tasks table, calculate queue_position from JobQueue.llen(), and return TaskStatusResponse.

**E-REQ-010**: WHEN GET /agents/{agent_id}/coverage/history is invoked, System SHALL call CoverageHistoryDAO.query_history(agent_id, start_date, end_date, limit=1000) and return CoverageHistoryResponse.

**E-REQ-011**: WHEN DELETE /tasks/{task_id} is invoked with status='pending', System SHALL set background_tasks.cancellation_requested=true and remove job from JobQueue via Redis LREM command.

**E-REQ-012**: WHEN DELETE /tasks/{task_id} is invoked with status='running', System SHALL set background_tasks.cancellation_requested=true and worker SHALL poll flag every 2 seconds.

**E-REQ-013**: WHEN AgentTaskWorker detects cancellation_requested=true, System SHALL stop processing gracefully, update background_tasks.status='cancelled', and exit worker loop.

**E-REQ-014**: WHEN coverage calculation exceeds 5-minute timeout, System SHALL update background_tasks.status='timeout', background_tasks.error='Task timeout exceeded', and kill worker task.

**E-REQ-015**: WHEN coverage calculation fails with exception, System SHALL update background_tasks.status='failed', background_tasks.error=exception_message, and send failure webhook if configured.

**E-REQ-016**: WHEN background_tasks table has completed tasks older than 24 hours, TTL cleanup job SHALL delete rows via PostgreSQL scheduled job or manual cleanup script.

**E-REQ-017**: WHEN coverage_history table has entries older than 90 days, TTL cleanup job SHALL delete rows via PostgreSQL scheduled job or manual cleanup script.

### State-driven Requirements (Background Task State Management)

**S-REQ-001**: WHILE task is in pending state, GET /tasks/{task_id} SHALL return status='pending' with queue_position calculated from JobQueue.llen(queue_key).

**S-REQ-002**: WHILE task is in pending state, DELETE /tasks/{task_id} SHALL remove task from JobQueue and update status='cancelled' immediately.

**S-REQ-003**: WHILE task is in running state, GET /tasks/{task_id} SHALL return status='running' with progress_percentage from background_tasks.progress_percentage field.

**S-REQ-004**: WHILE task is in running state, DELETE /tasks/{task_id} SHALL set cancellation_requested=true and worker SHALL check flag every 2 seconds during processing.

**S-REQ-005**: WHILE task is in completed state, GET /tasks/{task_id} SHALL return status='completed' with result data from background_tasks.result JSONB field.

**S-REQ-006**: WHILE task is in failed state, GET /tasks/{task_id} SHALL return status='failed' with error message from background_tasks.error TEXT field.

**S-REQ-007**: WHILE task is in timeout state, GET /tasks/{task_id} SHALL return status='timeout' with error='Task timeout exceeded (5 minutes)'.

**S-REQ-008**: WHILE webhook_url is configured, task completion SHALL trigger WebhookService.send_webhook() asynchronously without blocking task completion update.

**S-REQ-009**: WHILE webhook retry_count < 3, WebhookService SHALL retry webhook delivery with delay=2^retry_count seconds.

**S-REQ-010**: WHILE AgentTaskWorker is processing task, System SHALL update background_tasks.progress_percentage every 10 seconds based on coverage calculation progress.

**S-REQ-011**: WHILE coverage_history has entries for agent, GET /coverage/history SHALL return time-series data ordered by timestamp DESC (newest first).

**S-REQ-012**: WHILE coverage_history has no entries for agent, GET /coverage/history SHALL return empty history array with total_entries=0.

**S-REQ-013**: WHILE JobQueue has agent tasks, AgentTaskWorker SHALL dequeue tasks with priority order (high → medium → low) same as JobOrchestrator pattern.

**S-REQ-014**: WHILE RedisManager connection fails, AgentTaskQueue.enqueue_coverage_task() SHALL raise ConnectionError and return 503 Service Unavailable.

### Optional Features (Future Enhancements)

**O-REQ-001**: WHERE user requests task progress updates, AgentTaskWorker MAY publish progress events to Redis pub/sub channel for real-time updates.

**O-REQ-002**: WHERE user requests webhook signature verification, WebhookService MAY add HMAC-SHA256 signature header X-Agent-Signature to webhook POST requests.

**O-REQ-003**: WHERE user requests coverage history aggregation, CoverageHistoryDAO MAY provide aggregate_history(agent_id, interval) method for daily/weekly/monthly rollups.

**O-REQ-004**: WHERE user requests task priority override, POST /coverage/refresh MAY accept priority query parameter to override default priority=5.

**O-REQ-005**: WHERE user requests concurrent task limit, AgentTaskQueue MAY enforce max concurrent tasks per agent (e.g., max_concurrent=5).

**O-REQ-006**: WHERE user requests task retry, POST /tasks/{task_id}/retry MAY re-enqueue failed tasks with incremented retry_count.

**O-REQ-007**: WHERE user requests bulk coverage refresh, POST /agents/bulk/coverage/refresh MAY accept multiple agent_ids for batch processing.

### Constraints (Performance, Security, Reliability)

**C-REQ-001**: Background coverage calculation SHALL complete within 5 minutes for agents with < 100 taxonomy nodes (else timeout).

**C-REQ-002**: Webhook timeout SHALL be 10 seconds per attempt (total max 30 seconds for 3 retries).

**C-REQ-003**: Coverage history queries SHALL support pagination with max_limit=1000 entries per request.

**C-REQ-004**: background_tasks table SHALL retain data for 24 hours after completion (TTL cleanup via PostgreSQL scheduled job).

**C-REQ-005**: coverage_history table SHALL retain data for 90 days (TTL cleanup via PostgreSQL scheduled job).

**C-REQ-006**: AgentTaskQueue.enqueue_coverage_task() SHALL reuse JobQueue priority logic (priority=5 → medium queue).

**C-REQ-007**: Task cancellation SHALL be cooperative (polling-based every 2 seconds, not forced termination).

**C-REQ-008**: Webhook payload SHALL include required fields (task_id, agent_id, status, result, completed_at) in JSON format.

**C-REQ-009**: WebhookService SHALL validate webhook_url format (must be https:// for production, http://localhost allowed for testing).

**C-REQ-010**: AgentTaskWorker SHALL be separate process from FastAPI server (independent lifecycle management).

**C-REQ-011**: AgentTaskQueue SHALL namespace tasks with "agent:queue:{priority}" separate from "ingestion:queue:{priority}".

**C-REQ-012**: background_tasks.task_id SHALL use format "agent-coverage-{uuid4}" to avoid collision with ingestion task IDs.

**C-REQ-013**: Coverage history timestamp SHALL use UTC timezone (datetime.utcnow()) for consistency.

**C-REQ-014**: All background task operations SHALL use AsyncSession for non-blocking database access.

**C-REQ-015**: Webhook delivery failures SHALL NOT fail task completion (fire-and-forget semantics with retries).

**C-REQ-016**: Task status queries SHALL execute within 500ms (single database query + Redis LLEN operation).

**C-REQ-017**: Coverage history inserts SHALL execute within 1 second (single INSERT statement with conflict handling).

**C-REQ-018**: AgentTaskWorker SHALL implement graceful shutdown on SIGTERM (finish current task before exit).

**C-REQ-019**: Redis connection pool SHALL be shared across AgentTaskQueue instances (singleton RedisManager pattern).

**C-REQ-020**: PostgreSQL indexes SHALL be created on background_tasks(agent_id, status, created_at DESC) and coverage_history(agent_id, timestamp DESC).

## Database Schema

### background_tasks Table

```sql
CREATE TABLE background_tasks (
    task_id UUID PRIMARY KEY,
    agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL,  -- 'coverage_refresh', 'gap_analysis', 'report_generation'
    status VARCHAR(20) NOT NULL,  -- 'pending', 'running', 'completed', 'failed', 'cancelled', 'timeout'
    created_at TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'UTC'),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result JSONB,  -- {"coverage_percent": 85.5, "node_coverage": {...}}
    error TEXT,
    webhook_url TEXT,
    webhook_retry_count INTEGER DEFAULT 0,
    cancellation_requested BOOLEAN DEFAULT FALSE,
    queue_position INTEGER,
    progress_percentage FLOAT DEFAULT 0.0,
    estimated_completion_at TIMESTAMP
);

CREATE INDEX idx_background_tasks_agent_id ON background_tasks(agent_id);
CREATE INDEX idx_background_tasks_status ON background_tasks(status);
CREATE INDEX idx_background_tasks_created_at ON background_tasks(created_at DESC);
CREATE INDEX idx_background_tasks_agent_status ON background_tasks(agent_id, status);

COMMENT ON TABLE background_tasks IS 'Stores background task status for agent operations (coverage, gaps, reports)';
COMMENT ON COLUMN background_tasks.task_type IS 'Task type identifier for dispatching to appropriate worker';
COMMENT ON COLUMN background_tasks.status IS 'Task lifecycle: pending → running → completed|failed|cancelled|timeout';
COMMENT ON COLUMN background_tasks.result IS 'JSONB result data structure (varies by task_type)';
COMMENT ON COLUMN background_tasks.webhook_url IS 'Optional webhook URL for task completion notification';
COMMENT ON COLUMN background_tasks.cancellation_requested IS 'Cooperative cancellation flag polled by workers';
```

### coverage_history Table

```sql
CREATE TABLE coverage_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'UTC'),
    overall_coverage FLOAT NOT NULL CHECK (overall_coverage >= 0.0 AND overall_coverage <= 100.0),
    total_documents INTEGER NOT NULL CHECK (total_documents >= 0),
    total_chunks INTEGER NOT NULL CHECK (total_chunks >= 0),
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0'
);

CREATE INDEX idx_coverage_history_agent_id ON coverage_history(agent_id);
CREATE INDEX idx_coverage_history_timestamp ON coverage_history(timestamp DESC);
CREATE INDEX idx_coverage_history_agent_timestamp ON coverage_history(agent_id, timestamp DESC);

COMMENT ON TABLE coverage_history IS 'Time-series coverage data for agent performance tracking (90-day retention)';
COMMENT ON COLUMN coverage_history.overall_coverage IS 'Overall coverage percentage (0.0-100.0)';
COMMENT ON COLUMN coverage_history.timestamp IS 'UTC timestamp of coverage calculation';
COMMENT ON COLUMN coverage_history.version IS 'Taxonomy version used for coverage calculation';
```

## API Specification Changes

### Updated Endpoints

#### 1. POST /api/v1/agents/{agent_id}/coverage/refresh (Phase 2 → Phase 3)

**Changes from Mock Implementation**:
- **Before**: Returns 202 immediately with mock task_id, no actual background processing
- **After**: Inserts background_tasks row, enqueues to JobQueue, returns 202 with real task_id

**Updated Behavior**:
```python
@router.post("/agents/{agent_id}/coverage/refresh")
async def refresh_coverage_background(
    agent_id: UUID4,
    background: bool = Query(default=True),
    webhook_url: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(get_api_key)
) -> BackgroundTaskResponse:
    # Validate agent exists
    agent = await AgentDAO.get_agent(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    if not background:
        # Synchronous mode: same as Phase 2
        coverage_result = await CoverageMeterService(...).calculate_coverage(...)
        return BackgroundTaskResponse(status="completed", result=coverage_result)

    # Asynchronous mode: Real background processing
    task_id = await AgentTaskQueue.enqueue_coverage_task(
        agent_id=agent_id,
        taxonomy_node_ids=agent.taxonomy_node_ids,
        taxonomy_version=agent.taxonomy_version,
        webhook_url=webhook_url
    )

    # Insert background_tasks row
    task = BackgroundTask(
        task_id=task_id,
        agent_id=agent_id,
        task_type="coverage_refresh",
        status="pending",
        webhook_url=webhook_url
    )
    session.add(task)
    await session.commit()

    return BackgroundTaskResponse(
        task_id=task_id,
        agent_id=agent_id,
        status="pending",
        created_at=task.created_at
    )
```

#### 2. GET /api/v1/agents/{agent_id}/coverage/status/{task_id} (Phase 2 → Phase 3)

**Changes from Mock Implementation**:
- **Before**: Returns mock status with hardcoded completed status
- **After**: Queries background_tasks table, calculates queue_position from JobQueue

**Updated Behavior**:
```python
@router.get("/agents/{agent_id}/coverage/status/{task_id}")
async def get_task_status(
    agent_id: UUID4,
    task_id: str,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(get_api_key)
) -> TaskStatusResponse:
    # Query background_tasks table
    task = await session.execute(
        select(BackgroundTask).where(
            BackgroundTask.task_id == task_id,
            BackgroundTask.agent_id == agent_id
        )
    )
    task = task.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    # Calculate queue position if pending
    queue_position = None
    if task.status == "pending":
        queue_position = await AgentTaskQueue.get_queue_position(task_id)

    return TaskStatusResponse(
        task_id=task.task_id,
        agent_id=task.agent_id,
        status=task.status,
        queue_position=queue_position,
        progress_percentage=task.progress_percentage,
        result=task.result,
        error=task.error,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at
    )
```

#### 3. GET /api/v1/agents/{agent_id}/coverage/history (Phase 2 → Phase 3)

**Changes from Mock Implementation**:
- **Before**: Returns mock single entry with current coverage
- **After**: Queries coverage_history table with date filters

**Updated Behavior**:
```python
@router.get("/agents/{agent_id}/coverage/history")
async def get_coverage_history(
    agent_id: UUID4,
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    limit: int = Query(default=100, le=1000),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(get_api_key)
) -> CoverageHistoryResponse:
    # Validate agent exists
    agent = await AgentDAO.get_agent(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    # Query coverage_history table
    history_entries = await CoverageHistoryDAO.query_history(
        session=session,
        agent_id=agent_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )

    return CoverageHistoryResponse(
        agent_id=agent_id,
        history=history_entries,
        start_date=start_date,
        end_date=end_date,
        total_entries=len(history_entries)
    )
```

#### 4. DELETE /api/v1/tasks/{task_id} (NEW)

**Purpose**: Cancel background task (cooperative cancellation).

**Request**:
```
DELETE /api/v1/tasks/{task_id}
```

**Response**: 204 No Content

**Behavior**:
```python
@router.delete("/tasks/{task_id}", status_code=204)
async def cancel_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(get_api_key)
):
    # Query task
    task = await session.execute(
        select(BackgroundTask).where(BackgroundTask.task_id == task_id)
    )
    task = task.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    if task.status in ["completed", "failed", "cancelled", "timeout"]:
        # Already finished, idempotent
        return

    # Set cancellation flag
    task.cancellation_requested = True

    if task.status == "pending":
        # Remove from JobQueue
        await AgentTaskQueue.remove_job(task_id)
        task.status = "cancelled"
        task.completed_at = datetime.utcnow()

    await session.commit()

    # Note: If status='running', worker will detect cancellation_requested flag
```

## Implementation Details

### File Structure

```
apps/api/
├── routers/
│   └── agent_router.py                  # Update 3 endpoints (POST /refresh, GET /status, GET /history), add DELETE /tasks
├── background/
│   ├── __init__.py
│   ├── agent_task_queue.py              # AgentTaskQueue wrapping JobQueue with namespace
│   ├── agent_task_worker.py             # AgentTaskWorker for processing agent tasks
│   └── webhook_service.py               # WebhookService with retry logic
apps/knowledge_builder/
└── coverage/
    └── coverage_history.py              # CoverageHistoryDAO for time-series data
alembic/versions/
└── 0012_add_background_tasks_coverage_history.py  # Migration script for 2 tables
apps/api/schemas/
└── agent_schemas.py                     # Add TaskStatusResponse schema
```

### AgentTaskQueue Implementation

**File**: `apps/api/background/agent_task_queue.py`

```python
import uuid
import json
from typing import Optional, Dict, Any, List
from apps.ingestion.batch.job_queue import JobQueue

class AgentTaskQueue:
    """Wrapper around JobQueue with namespace separation for agent tasks"""

    QUEUE_KEY_PREFIX = "agent:queue"  # Separate from "ingestion:queue"
    TASK_ID_PREFIX = "agent-coverage"

    def __init__(self, redis_manager=None):
        self.job_queue = JobQueue(redis_manager=redis_manager)
        self.job_queue.QUEUE_KEY_PREFIX = self.QUEUE_KEY_PREFIX  # Override namespace

    async def initialize(self):
        await self.job_queue.initialize()

    async def enqueue_coverage_task(
        self,
        agent_id: uuid.UUID,
        taxonomy_node_ids: List[uuid.UUID],
        taxonomy_version: str,
        webhook_url: Optional[str] = None
    ) -> str:
        """Enqueue coverage refresh task to JobQueue with priority=5 (medium)"""
        task_id = f"{self.TASK_ID_PREFIX}-{uuid.uuid4()}"
        command_id = f"coverage-{task_id}"

        job_data = {
            "agent_id": str(agent_id),
            "taxonomy_node_ids": [str(nid) for nid in taxonomy_node_ids],
            "taxonomy_version": taxonomy_version,
            "webhook_url": webhook_url,
            "task_type": "coverage_refresh"
        }

        await self.job_queue.enqueue_job(
            job_id=task_id,
            command_id=command_id,
            job_data=job_data,
            priority=5  # Medium priority
        )

        return task_id

    async def get_queue_position(self, task_id: str) -> Optional[int]:
        """Calculate position in queue for pending task"""
        # Query all 3 priority queues
        total_position = 0
        for priority in ["high", "medium", "low"]:
            queue_key = f"{self.QUEUE_KEY_PREFIX}:{priority}"
            queue_size = await self.job_queue.redis_manager.llen(queue_key)

            # Check if task exists in this priority queue
            # (Simplified: actual implementation requires LRANGE and search)
            if priority == "medium":  # Agent tasks use medium priority
                return total_position + 1  # Approximate position

            total_position += queue_size

        return None

    async def remove_job(self, task_id: str) -> bool:
        """Remove pending task from queue (for cancellation)"""
        queue_key = f"{self.QUEUE_KEY_PREFIX}:medium"

        # Redis LREM: remove all occurrences of task from queue
        # Note: Requires job_payload serialization to match
        # Simplified implementation - actual requires LRANGE + search + LREM
        try:
            removed_count = await self.job_queue.redis_manager.lrem(queue_key, 0, task_id)
            return removed_count > 0
        except Exception as e:
            logger.error(f"Failed to remove job {task_id}: {e}")
            return False
```

### AgentTaskWorker Implementation

**File**: `apps/api/background/agent_task_worker.py`

```python
import asyncio
import logging
from datetime import datetime
from apps.api.background.agent_task_queue import AgentTaskQueue
from apps.api.background.webhook_service import WebhookService
from apps.knowledge_builder.coverage.meter import CoverageMeterService
from apps.knowledge_builder.coverage.coverage_history import CoverageHistoryDAO
from apps.core.db_session import async_session
from apps.api.database import BackgroundTask

logger = logging.getLogger(__name__)

class AgentTaskWorker:
    """Worker for processing agent background tasks (coverage refresh, gap analysis)"""

    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.task_queue = AgentTaskQueue()
        self.webhook_service = WebhookService()
        self.running = False

    async def start(self):
        """Start worker loop (blocking until stop)"""
        self.running = True
        await self.task_queue.initialize()

        logger.info(f"AgentTaskWorker {self.worker_id} started")

        while self.running:
            try:
                # Dequeue from agent:queue namespace
                job_payload = await self.task_queue.job_queue.dequeue_job(timeout=5)

                if not job_payload:
                    continue

                task_id = job_payload["job_id"]
                job_data = job_payload["data"]

                logger.info(f"Worker {self.worker_id} processing task {task_id}")

                # Update status to 'running'
                async with async_session() as session:
                    task = await session.get(BackgroundTask, task_id)
                    if not task:
                        logger.error(f"Task {task_id} not found in database")
                        continue

                    task.status = "running"
                    task.started_at = datetime.utcnow()
                    await session.commit()

                # Process task with timeout
                try:
                    result = await asyncio.wait_for(
                        self._process_coverage_task(task_id, job_data),
                        timeout=300  # 5 minutes
                    )

                    # Update status to 'completed'
                    async with async_session() as session:
                        task = await session.get(BackgroundTask, task_id)
                        task.status = "completed"
                        task.result = result
                        task.completed_at = datetime.utcnow()
                        await session.commit()

                        # Send webhook if configured
                        if task.webhook_url:
                            asyncio.create_task(
                                self.webhook_service.send_webhook(
                                    url=task.webhook_url,
                                    payload={
                                        "task_id": task_id,
                                        "agent_id": str(task.agent_id),
                                        "status": "completed",
                                        "result": result,
                                        "completed_at": task.completed_at.isoformat()
                                    }
                                )
                            )

                    logger.info(f"Worker {self.worker_id} completed task {task_id}")

                except asyncio.TimeoutError:
                    # Timeout after 5 minutes
                    async with async_session() as session:
                        task = await session.get(BackgroundTask, task_id)
                        task.status = "timeout"
                        task.error = "Task timeout exceeded (5 minutes)"
                        task.completed_at = datetime.utcnow()
                        await session.commit()

                    logger.error(f"Worker {self.worker_id} timeout task {task_id}")

                except Exception as e:
                    # Task failed
                    async with async_session() as session:
                        task = await session.get(BackgroundTask, task_id)
                        task.status = "failed"
                        task.error = str(e)
                        task.completed_at = datetime.utcnow()
                        await session.commit()

                    logger.error(f"Worker {self.worker_id} failed task {task_id}: {e}")

            except asyncio.CancelledError:
                logger.info(f"Worker {self.worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}")
                await asyncio.sleep(1)

        logger.info(f"AgentTaskWorker {self.worker_id} stopped")

    async def stop(self):
        """Stop worker gracefully"""
        self.running = False

    async def _process_coverage_task(self, task_id: str, job_data: Dict) -> Dict:
        """Execute coverage calculation with cancellation check"""
        agent_id = job_data["agent_id"]
        taxonomy_node_ids = job_data["taxonomy_node_ids"]
        taxonomy_version = job_data["taxonomy_version"]

        async with async_session() as session:
            # Check cancellation flag every 2 seconds
            for i in range(150):  # 300 seconds / 2 = 150 checks
                task = await session.get(BackgroundTask, task_id)
                if task.cancellation_requested:
                    task.status = "cancelled"
                    task.completed_at = datetime.utcnow()
                    await session.commit()
                    raise asyncio.CancelledError("Task cancelled by user")

                if i == 0:
                    # Execute coverage calculation
                    coverage_service = CoverageMeterService(session=session)
                    coverage_result = await coverage_service.calculate_coverage(
                        agent_id=agent_id,
                        taxonomy_node_ids=taxonomy_node_ids,
                        version=taxonomy_version
                    )

                    # Update progress
                    task.progress_percentage = 50.0
                    await session.commit()

                    # Insert coverage history
                    await CoverageHistoryDAO.insert_history(
                        session=session,
                        agent_id=agent_id,
                        coverage_data=coverage_result
                    )

                    task.progress_percentage = 100.0
                    await session.commit()

                    return {
                        "coverage_percent": coverage_result.overall_coverage,
                        "node_coverage": coverage_result.node_coverage,
                        "total_documents": coverage_result.total_documents,
                        "total_chunks": coverage_result.total_chunks
                    }

                await asyncio.sleep(2)
```

### WebhookService Implementation

**File**: `apps/api/background/webhook_service.py`

```python
import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class WebhookService:
    """Service for sending webhook notifications with retry logic"""

    def __init__(self, timeout: int = 10, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries

    async def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        secret: Optional[str] = None
    ) -> bool:
        """Send webhook POST request with retry logic"""
        for retry_count in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    headers = {"Content-Type": "application/json"}

                    # Optional: Add signature header for verification
                    if secret:
                        import hmac
                        import hashlib
                        signature = hmac.new(
                            secret.encode(),
                            json.dumps(payload).encode(),
                            hashlib.sha256
                        ).hexdigest()
                        headers["X-Agent-Signature"] = f"sha256={signature}"

                    response = await client.post(url, json=payload, headers=headers)

                    if response.status_code < 300:
                        logger.info(f"Webhook delivered to {url} (status {response.status_code})")
                        return True

                    logger.warning(
                        f"Webhook failed with status {response.status_code} (retry {retry_count + 1}/{self.max_retries})"
                    )

            except Exception as e:
                logger.error(
                    f"Webhook delivery failed to {url}: {e} (retry {retry_count + 1}/{self.max_retries})"
                )

            # Exponential backoff
            if retry_count < self.max_retries - 1:
                delay = 2 ** retry_count
                await asyncio.sleep(delay)

        logger.error(f"Webhook failed after {self.max_retries} retries: {url}")
        return False
```

### CoverageHistoryDAO Implementation

**File**: `apps/knowledge_builder/coverage/coverage_history.py`

```python
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.database import CoverageHistory  # New ORM model

class CoverageHistoryDAO:
    """Data access layer for coverage_history table"""

    @staticmethod
    async def insert_history(
        session: AsyncSession,
        agent_id: uuid.UUID,
        coverage_data: Dict
    ) -> uuid.UUID:
        """Insert coverage history entry"""
        history = CoverageHistory(
            history_id=uuid.uuid4(),
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            overall_coverage=coverage_data["overall_coverage"],
            total_documents=coverage_data.get("total_documents", 0),
            total_chunks=coverage_data.get("total_chunks", 0),
            version=coverage_data.get("version", "1.0.0")
        )

        session.add(history)
        await session.commit()

        return history.history_id

    @staticmethod
    async def query_history(
        session: AsyncSession,
        agent_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[CoverageHistory]:
        """Query coverage history with date filters"""
        stmt = select(CoverageHistory).where(
            CoverageHistory.agent_id == agent_id
        )

        if start_date:
            stmt = stmt.where(CoverageHistory.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(CoverageHistory.timestamp <= end_date)

        stmt = stmt.order_by(CoverageHistory.timestamp.desc()).limit(limit)

        result = await session.execute(stmt)
        return result.scalars().all()
```

## Test Requirements

### Unit Tests: `tests/unit/test_agent_task_queue.py`

**Test Cases**:
1. AgentTaskQueue.enqueue_coverage_task() creates background_tasks row with status='pending'
2. AgentTaskQueue.enqueue_coverage_task() enqueues job to Redis agent:queue:medium
3. AgentTaskQueue.get_queue_position() returns correct position for pending task
4. AgentTaskQueue.remove_job() removes task from Redis queue for cancellation
5. WebhookService.send_webhook() retries on 5xx with exponential backoff
6. WebhookService.send_webhook() stops after max_retries=3
7. CoverageHistoryDAO.insert_history() creates coverage_history row
8. CoverageHistoryDAO.query_history() filters by date range correctly

### Integration Tests: `tests/integration/test_agent_background_tasks.py`

**End-to-End Tests**:
1. POST /coverage/refresh?background=true → AgentTaskWorker processes → coverage updated → webhook delivered
2. Coverage history: Calculate coverage 3 times → GET /history returns 3 entries ordered by timestamp DESC
3. Task cancellation: Cancel pending task → removed from queue → status='cancelled'
4. Task cancellation: Cancel running task → worker detects flag → stops gracefully
5. Task timeout: Coverage calculation > 5 minutes → status='timeout'
6. Webhook retry: Webhook fails 2 times → retries with exponential backoff → succeeds on 3rd attempt
7. Concurrent tasks: 10 coverage refresh requests → all processed successfully

### Performance Tests: `tests/performance/test_agent_background_performance.py`

**Benchmarks**:
1. Background coverage calculation for 50-node agent completes within 5 minutes
2. 100 concurrent coverage refresh requests → all enqueued within 10 seconds
3. Webhook delivery under high load (100 tasks completing simultaneously) → max 30 seconds total
4. Coverage history query with 1000 entries → returns within 500ms
5. Task cancellation response time → < 200ms for pending tasks

## Related Files

### Source Code
- @CODE:AGENT-GROWTH-004:API: apps/api/routers/agent_router.py (update 3 endpoints, add DELETE /tasks)
- @CODE:AGENT-GROWTH-004:QUEUE: apps/api/background/agent_task_queue.py (new)
- @CODE:AGENT-GROWTH-004:WORKER: apps/api/background/agent_task_worker.py (new)
- @CODE:AGENT-GROWTH-004:WEBHOOK: apps/api/background/webhook_service.py (new)
- @CODE:AGENT-GROWTH-004:HISTORY: apps/knowledge_builder/coverage/coverage_history.py (new)
- @CODE:AGENT-GROWTH-004:SCHEMA: apps/api/schemas/agent_schemas.py (add TaskStatusResponse)

### Dependencies
- @CODE:AGENT-GROWTH-003:API: apps/api/routers/agent_router.py (Phase 2 mock endpoints)
- @CODE:EXISTING:JOBQUEUE: apps/ingestion/batch/job_queue.py (JobQueue class)
- @CODE:EXISTING:REDIS: apps/api/cache/redis_manager.py (RedisManager)
- @CODE:AGENT-GROWTH-001:COVERAGE: apps/knowledge_builder/coverage/meter.py (CoverageMeterService)

### Database Migrations
- @MIGRATION:AGENT-GROWTH-004: alembic/versions/0012_add_background_tasks_coverage_history.py (new)

### Test Files
- @TEST:AGENT-GROWTH-004:UNIT: tests/unit/test_agent_task_queue.py
- @TEST:AGENT-GROWTH-004:INTEGRATION: tests/integration/test_agent_background_tasks.py
- @TEST:AGENT-GROWTH-004:PERFORMANCE: tests/performance/test_agent_background_performance.py

## Implementation Phases

### Phase 3-1: Database Schema & Migration
- Create background_tasks table schema
- Create coverage_history table schema
- Create Alembic migration 0012_add_background_tasks_coverage_history.py
- Apply migration to test database

### Phase 3-2: AgentTaskQueue & WebhookService
- Implement AgentTaskQueue with namespace separation
- Implement WebhookService with retry logic
- Implement CoverageHistoryDAO
- Unit tests for queue, webhook, DAO

### Phase 3-3: AgentTaskWorker
- Implement AgentTaskWorker with cancellation support
- Implement timeout handling (5 minutes)
- Implement progress updates
- Integration tests for worker

### Phase 3-4: API Endpoint Updates
- Update POST /coverage/refresh (mock → real background)
- Update GET /coverage/status (mock → database query)
- Update GET /coverage/history (mock → database query)
- Add DELETE /tasks/{task_id} (new endpoint)
- Update schemas (TaskStatusResponse)

### Phase 3-5: End-to-End Testing
- Integration tests for full workflow
- Performance benchmarks
- Webhook delivery tests
- Cancellation tests

## Future Enhancements (Phase 4)

### Advanced Features
1. Task retry endpoint: POST /tasks/{task_id}/retry
2. Bulk coverage refresh: POST /agents/bulk/coverage/refresh
3. Coverage history aggregation: GET /coverage/history/aggregate?interval=daily
4. Real-time progress updates: SSE endpoint for task progress
5. Webhook signature verification: X-Agent-Signature header

### Operational Features
1. Dead letter queue for failed tasks
2. Task prioritization: priority query parameter override
3. Concurrent task limit per agent
4. Task scheduling: schedule_at timestamp for deferred execution
5. Task chaining: execute tasks sequentially based on dependencies

## Revision History

- v0.1.0 (2025-10-12): Initial Phase 3 specification for Real Background Tasks
  - background_tasks table schema (17 columns)
  - coverage_history table schema (7 columns)
  - AgentTaskQueue with namespace separation from ingestion queue
  - AgentTaskWorker with timeout, cancellation, progress tracking
  - WebhookService with exponential backoff retry
  - CoverageHistoryDAO for time-series data
  - Updated 3 endpoints (POST /refresh, GET /status, GET /history)
  - New DELETE /tasks/{task_id} endpoint for cancellation
  - Migration script for 2 new tables
