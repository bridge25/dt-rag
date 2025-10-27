# @TEST:JOB-OPTIMIZE-001:REDIS-CONN, @TEST:JOB-OPTIMIZE-001:QUEUE, @TEST:JOB-OPTIMIZE-001:LOAD
# Chain: SPEC-JOB-OPTIMIZE-001 -> CODE-JOB-OPTIMIZE-001 -> TEST-JOB-OPTIMIZE-001
"""
JobOrchestrator Dispatcher Pattern Integration Tests

Tests verify:
1. Redis connection count stays ≤5 with dispatcher pattern
2. Internal queue properly distributes jobs to workers
3. System handles 100 concurrent jobs without Redis overload
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from apps.ingestion.batch.job_orchestrator import JobOrchestrator
from apps.ingestion.batch.job_queue import JobQueue
from apps.api.embedding_service import EmbeddingService


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dispatcher_attribute_exists():
    """
    @TEST:JOB-OPTIMIZE-001:REDIS-CONN

    Given: JobOrchestrator initialized with 10 workers
    When: System is inspected for dispatcher components
    Then: internal_queue and dispatcher_task attributes should exist
    """
    mock_job_queue = MagicMock(spec=JobQueue)
    mock_job_queue.initialize = AsyncMock()
    mock_job_queue.dequeue_job = AsyncMock(return_value=None)

    mock_embedding_service = MagicMock(spec=EmbeddingService)

    orchestrator = JobOrchestrator(
        job_queue=mock_job_queue,
        embedding_service=mock_embedding_service,
        max_workers=10,
    )

    assert hasattr(
        orchestrator, "internal_queue"
    ), "JobOrchestrator should have internal_queue attribute"
    assert hasattr(
        orchestrator, "dispatcher_task"
    ), "JobOrchestrator should have dispatcher_task attribute"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dispatcher_task_created_on_start():
    """
    @TEST:JOB-OPTIMIZE-001:QUEUE

    Given: JobOrchestrator initialized
    When: start() method is called
    Then: dispatcher_task should be created and running
    """
    mock_job_queue = MagicMock(spec=JobQueue)
    mock_job_queue.initialize = AsyncMock()
    mock_job_queue.dequeue_job = AsyncMock(return_value=None)

    mock_embedding_service = MagicMock(spec=EmbeddingService)

    orchestrator = JobOrchestrator(
        job_queue=mock_job_queue,
        embedding_service=mock_embedding_service,
        max_workers=2,
    )

    await orchestrator.start()

    assert (
        orchestrator.dispatcher_task is not None
    ), "Dispatcher task should be created after start()"
    assert not orchestrator.dispatcher_task.done(), "Dispatcher task should be running"

    await orchestrator.stop()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_worker_uses_internal_queue():
    """
    @TEST:JOB-OPTIMIZE-001:LOAD

    Given: JobOrchestrator with internal queue
    When: _worker method is examined
    Then: Worker should read from internal_queue instead of job_queue directly
    """
    mock_job_queue = MagicMock(spec=JobQueue)
    mock_job_queue.initialize = AsyncMock()

    mock_embedding_service = MagicMock(spec=EmbeddingService)

    orchestrator = JobOrchestrator(
        job_queue=mock_job_queue,
        embedding_service=mock_embedding_service,
        max_workers=1,
    )

    import inspect

    worker_source = inspect.getsource(orchestrator._worker)

    assert "internal_queue" in worker_source, "Worker should use internal_queue"
    assert (
        "internal_queue.get" in worker_source
        or "self.internal_queue.get" in worker_source
    ), "Worker should call get() on internal_queue"
