"""
@TEST:AGENT-GROWTH-004:UNIT - AgentTaskWorker Unit Tests

RED Phase: Unit tests for AgentTaskWorker
Tests worker lifecycle, task processing, timeout, cancellation, progress tracking
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from apps.api.background.agent_task_worker import AgentTaskWorker


class TestAgentTaskWorker:
    """Unit tests for AgentTaskWorker"""

    @pytest.mark.asyncio
    async def test_worker_lifecycle_start_and_stop(self):
        """
        RED Test: Verify worker start() and stop() lifecycle

        Expected:
        - start() sets running=True and creates worker task
        - stop() sets running=False and cancels worker task
        - Graceful shutdown without errors
        """
        worker = AgentTaskWorker(worker_id=0)

        with patch.object(worker, '_worker_loop', new_callable=AsyncMock) as mock_loop:
            mock_loop.side_effect = asyncio.CancelledError()

            worker_task = asyncio.create_task(worker.start())

            await asyncio.sleep(0.1)

            assert worker.running is True, "Worker should be running after start()"

            await worker.stop()

            assert worker.running is False, "Worker should stop after stop()"

            with pytest.raises((asyncio.CancelledError, Exception)):
                await worker_task

    @pytest.mark.asyncio
    async def test_worker_dequeues_task_from_redis(self):
        """
        RED Test: Verify worker dequeues task from AgentTaskQueue

        Expected:
        - Calls AgentTaskQueue.job_queue.dequeue_job()
        - Processes task with correct job_id
        """
        worker = AgentTaskWorker(worker_id=0)

        mock_job_payload = {
            "job_id": "agent-coverage-test-123",
            "command_id": "agent-coverage-test-123",
            "data": {
                "task_id": "agent-coverage-test-123",
                "agent_id": str(uuid.uuid4()),
                "taxonomy_node_ids": [str(uuid.uuid4())],
                "taxonomy_version": "1.0.0",
                "task_type": "coverage_refresh"
            },
            "priority": 5
        }

        with patch.object(worker.task_queue.job_queue, 'dequeue_job', new_callable=AsyncMock) as mock_dequeue:
            mock_dequeue.side_effect = [mock_job_payload, None]  # Return job once, then None

            with patch.object(worker, '_process_coverage_task', new_callable=AsyncMock) as mock_process:
                worker_task = asyncio.create_task(worker._worker_loop())

                await asyncio.sleep(0.2)

                await worker.stop()
                worker_task.cancel()

                try:
                    await worker_task
                except asyncio.CancelledError:
                    pass

                mock_dequeue.assert_called()
                mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_coverage_task_updates_status(self):
        """
        RED Test: Verify _process_coverage_task() updates background_tasks status

        Expected:
        - status: pending → running → completed
        - started_at and completed_at timestamps set
        - result JSON contains coverage data
        """
        worker = AgentTaskWorker(worker_id=0)

        task_id = "agent-coverage-test-456"
        agent_id = uuid.uuid4()
        job_data = {
            "task_id": task_id,
            "agent_id": str(agent_id),
            "taxonomy_node_ids": [str(uuid.uuid4())],
            "taxonomy_version": "1.0.0",
            "task_type": "coverage_refresh"
        }

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        mock_task = MagicMock()
        mock_task.task_id = task_id
        mock_task.agent_id = agent_id
        mock_task.status = "pending"
        mock_task.cancellation_requested = False

        mock_session.get = AsyncMock(return_value=mock_task)
        mock_session.commit = AsyncMock()

        mock_agent = MagicMock()
        mock_agent.agent_id = agent_id
        mock_agent.taxonomy_node_ids = [uuid.uuid4()]
        mock_agent.taxonomy_version = "1.0.0"

        mock_coverage_result = MagicMock()
        mock_coverage_result.coverage_percent = 85.5
        mock_coverage_result.total_documents = 100
        mock_coverage_result.total_chunks = 500

        with patch('apps.api.background.agent_task_worker.async_session', return_value=mock_session):
            with patch('apps.api.background.agent_task_worker.AgentDAO.get_agent', new_callable=AsyncMock) as mock_get_agent:
                mock_get_agent.return_value = mock_agent

                with patch('apps.api.background.agent_task_worker.CoverageMeterService.calculate_coverage', new_callable=AsyncMock) as mock_calculate:
                    mock_calculate.return_value = mock_coverage_result

                    await worker._process_coverage_task(task_id, job_data)

                    assert mock_task.status == "completed", "Task status should be 'completed'"
                    assert mock_task.started_at is not None, "started_at should be set"
                    assert mock_task.completed_at is not None, "completed_at should be set"
                    assert mock_task.result is not None, "result should contain coverage data"

                    mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_process_coverage_task_handles_timeout(self):
        """
        RED Test: Verify _process_coverage_task() handles timeout (>5 minutes)

        Expected:
        - asyncio.TimeoutError caught
        - status set to 'timeout'
        - error message contains 'timeout'
        """
        worker = AgentTaskWorker(worker_id=0, timeout=1)  # 1 second timeout for testing

        task_id = "agent-coverage-test-789"
        agent_id = uuid.uuid4()
        job_data = {
            "task_id": task_id,
            "agent_id": str(agent_id),
            "taxonomy_node_ids": [str(uuid.uuid4())],
            "taxonomy_version": "1.0.0",
            "task_type": "coverage_refresh"
        }

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        mock_task = MagicMock()
        mock_task.task_id = task_id
        mock_task.status = "running"
        mock_task.cancellation_requested = False

        mock_session.get = AsyncMock(return_value=mock_task)
        mock_session.commit = AsyncMock()

        mock_agent = MagicMock()
        mock_agent.agent_id = agent_id

        async def slow_calculation(*args, **kwargs):
            await asyncio.sleep(10)  # Exceed timeout

        with patch('apps.api.background.agent_task_worker.async_session', return_value=mock_session):
            with patch('apps.api.background.agent_task_worker.AgentDAO.get_agent', new_callable=AsyncMock) as mock_get_agent:
                mock_get_agent.return_value = mock_agent

                with patch('apps.api.background.agent_task_worker.CoverageMeterService.calculate_coverage', new_callable=AsyncMock) as mock_calculate:
                    mock_calculate.side_effect = slow_calculation

                    await worker._process_coverage_task(task_id, job_data)

                    assert mock_task.status == "timeout", "Task status should be 'timeout'"
                    assert "timeout" in mock_task.error.lower(), "Error message should mention timeout"
                    mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_process_coverage_task_checks_cancellation(self):
        """
        RED Test: Verify _process_coverage_task() checks cancellation_requested flag

        Expected:
        - Polls cancellation_requested every 2 seconds
        - When flag=True, sets status='cancelled' and exits
        """
        worker = AgentTaskWorker(worker_id=0)

        task_id = "agent-coverage-test-cancel"
        agent_id = uuid.uuid4()
        job_data = {
            "task_id": task_id,
            "agent_id": str(agent_id),
            "taxonomy_node_ids": [str(uuid.uuid4())],
            "taxonomy_version": "1.0.0",
            "task_type": "coverage_refresh"
        }

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        mock_task = MagicMock()
        mock_task.task_id = task_id
        mock_task.status = "running"
        mock_task.cancellation_requested = True  # Set to True immediately

        mock_session.get = AsyncMock(return_value=mock_task)
        mock_session.commit = AsyncMock()

        with patch('apps.api.background.agent_task_worker.async_session', return_value=mock_session):
            await worker._process_coverage_task(task_id, job_data)

            assert mock_task.status == "cancelled", "Task status should be 'cancelled'"
            mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_process_coverage_task_updates_progress(self):
        """
        RED Test: Verify _process_coverage_task() updates progress_percentage

        Expected:
        - progress_percentage starts at 0.0
        - progress_percentage updates during calculation (e.g., 50.0)
        - progress_percentage reaches 100.0 on completion
        """
        worker = AgentTaskWorker(worker_id=0)

        task_id = "agent-coverage-test-progress"
        agent_id = uuid.uuid4()
        job_data = {
            "task_id": task_id,
            "agent_id": str(agent_id),
            "taxonomy_node_ids": [str(uuid.uuid4())],
            "taxonomy_version": "1.0.0",
            "task_type": "coverage_refresh"
        }

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        mock_task = MagicMock()
        mock_task.task_id = task_id
        mock_task.status = "running"
        mock_task.cancellation_requested = False
        mock_task.progress_percentage = 0.0

        progress_values = []

        def track_progress():
            progress_values.append(mock_task.progress_percentage)

        mock_session.get = AsyncMock(return_value=mock_task)

        original_commit = AsyncMock()
        async def commit_with_tracking(*args, **kwargs):
            track_progress()
            return await original_commit(*args, **kwargs)

        mock_session.commit = commit_with_tracking

        mock_agent = MagicMock()
        mock_agent.agent_id = agent_id
        mock_agent.taxonomy_node_ids = [uuid.uuid4()]
        mock_agent.taxonomy_version = "1.0.0"

        mock_coverage_result = MagicMock()
        mock_coverage_result.coverage_percent = 80.0
        mock_coverage_result.total_documents = 100
        mock_coverage_result.total_chunks = 500

        with patch('apps.api.background.agent_task_worker.async_session', return_value=mock_session):
            with patch('apps.api.background.agent_task_worker.AgentDAO.get_agent', new_callable=AsyncMock) as mock_get_agent:
                mock_get_agent.return_value = mock_agent

                with patch('apps.api.background.agent_task_worker.CoverageMeterService.calculate_coverage', new_callable=AsyncMock) as mock_calculate:
                    mock_calculate.return_value = mock_coverage_result

                    await worker._process_coverage_task(task_id, job_data)

                    assert len(progress_values) > 0, "Progress should be tracked"
                    assert any(p > 0.0 for p in progress_values), "Progress should increase"

    @pytest.mark.asyncio
    async def test_process_coverage_task_inserts_coverage_history(self):
        """
        RED Test: Verify _process_coverage_task() inserts coverage_history record

        Expected:
        - CoverageHistoryDAO.insert_history() called after successful coverage calculation
        - Parameters: agent_id, overall_coverage, total_documents, total_chunks, version
        """
        worker = AgentTaskWorker(worker_id=0)

        task_id = "agent-coverage-test-history"
        agent_id = uuid.uuid4()
        job_data = {
            "task_id": task_id,
            "agent_id": str(agent_id),
            "taxonomy_node_ids": [str(uuid.uuid4())],
            "taxonomy_version": "1.0.0",
            "task_type": "coverage_refresh"
        }

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        mock_task = MagicMock()
        mock_task.task_id = task_id
        mock_task.status = "running"
        mock_task.cancellation_requested = False

        mock_session.get = AsyncMock(return_value=mock_task)
        mock_session.commit = AsyncMock()

        mock_agent = MagicMock()
        mock_agent.agent_id = agent_id
        mock_agent.taxonomy_node_ids = [uuid.uuid4()]
        mock_agent.taxonomy_version = "1.0.0"

        mock_coverage_result = MagicMock()
        mock_coverage_result.coverage_percent = 75.0
        mock_coverage_result.total_documents = 90
        mock_coverage_result.total_chunks = 450

        with patch('apps.api.background.agent_task_worker.async_session', return_value=mock_session):
            with patch('apps.api.background.agent_task_worker.AgentDAO.get_agent', new_callable=AsyncMock) as mock_get_agent:
                mock_get_agent.return_value = mock_agent

                with patch('apps.api.background.agent_task_worker.CoverageMeterService.calculate_coverage', new_callable=AsyncMock) as mock_calculate:
                    mock_calculate.return_value = mock_coverage_result

                    with patch('apps.api.background.agent_task_worker.CoverageHistoryDAO.insert_history', new_callable=AsyncMock) as mock_insert:
                        await worker._process_coverage_task(task_id, job_data)

                        mock_insert.assert_called_once()

                        call_args = mock_insert.call_args
                        assert call_args.kwargs['agent_id'] == agent_id, "agent_id should match"
                        assert call_args.kwargs['overall_coverage'] == 75.0, "overall_coverage should match"
                        assert call_args.kwargs['total_documents'] == 90, "total_documents should match"
                        assert call_args.kwargs['total_chunks'] == 450, "total_chunks should match"
                        assert call_args.kwargs['version'] == "1.0.0", "version should match"

    @pytest.mark.asyncio
    async def test_process_coverage_task_sends_webhook(self):
        """
        RED Test: Verify _process_coverage_task() sends webhook on completion

        Expected:
        - WebhookService.send_webhook() called with task result
        - Payload includes: task_id, agent_id, status, result, completed_at
        - Webhook failure doesn't fail task completion
        """
        worker = AgentTaskWorker(worker_id=0)

        task_id = "agent-coverage-test-webhook"
        agent_id = uuid.uuid4()
        webhook_url = "https://example.com/webhook"
        job_data = {
            "task_id": task_id,
            "agent_id": str(agent_id),
            "taxonomy_node_ids": [str(uuid.uuid4())],
            "taxonomy_version": "1.0.0",
            "task_type": "coverage_refresh",
            "webhook_url": webhook_url
        }

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        mock_task = MagicMock()
        mock_task.task_id = task_id
        mock_task.status = "running"
        mock_task.cancellation_requested = False
        mock_task.webhook_url = webhook_url

        mock_session.get = AsyncMock(return_value=mock_task)
        mock_session.commit = AsyncMock()

        mock_agent = MagicMock()
        mock_agent.agent_id = agent_id
        mock_agent.taxonomy_node_ids = [uuid.uuid4()]
        mock_agent.taxonomy_version = "1.0.0"

        mock_coverage_result = MagicMock()
        mock_coverage_result.coverage_percent = 82.0
        mock_coverage_result.total_documents = 110
        mock_coverage_result.total_chunks = 550

        with patch('apps.api.background.agent_task_worker.async_session', return_value=mock_session):
            with patch('apps.api.background.agent_task_worker.AgentDAO.get_agent', new_callable=AsyncMock) as mock_get_agent:
                mock_get_agent.return_value = mock_agent

                with patch('apps.api.background.agent_task_worker.CoverageMeterService.calculate_coverage', new_callable=AsyncMock) as mock_calculate:
                    mock_calculate.return_value = mock_coverage_result

                    with patch('apps.api.background.agent_task_worker.WebhookService.send_webhook', new_callable=AsyncMock) as mock_webhook:
                        mock_webhook.return_value = True

                        await worker._process_coverage_task(task_id, job_data)

                        mock_webhook.assert_called_once()

                        call_args = mock_webhook.call_args
                        assert call_args.args[0] == webhook_url, "URL should match"

                        payload = call_args.args[1]
                        assert payload['task_id'] == task_id, "Payload should include task_id"
                        assert payload['agent_id'] == str(agent_id), "Payload should include agent_id"
                        assert payload['status'] == "completed", "Payload should include status"
                        assert 'result' in payload, "Payload should include result"
                        assert 'completed_at' in payload, "Payload should include completed_at"
