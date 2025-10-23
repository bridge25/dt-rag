"""
@TEST:AGENT-GROWTH-004:UNIT - AgentTaskQueue Unit Tests

RED Phase: Unit tests for AgentTaskQueue service
Tests namespace separation, task enqueueing, queue position calculation
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from apps.api.background.agent_task_queue import AgentTaskQueue


class TestAgentTaskQueue:
    """Unit tests for AgentTaskQueue service"""

    @pytest.fixture
    def mock_redis_manager(self):
        """Mock RedisManager for testing"""
        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock()
        mock_redis.llen = AsyncMock(return_value=5)
        mock_redis.lrange = AsyncMock(return_value=[])
        mock_redis.lrem = AsyncMock(return_value=1)
        return mock_redis

    @pytest.fixture
    def mock_job_queue(self, mock_redis_manager):
        """Mock JobQueue instance"""
        with patch('apps.api.background.agent_task_queue.JobQueue') as MockJobQueue:
            mock_instance = AsyncMock()
            mock_instance.redis_manager = mock_redis_manager
            mock_instance.initialize = AsyncMock()
            mock_instance.enqueue_job = AsyncMock(return_value=True)
            mock_instance.get_queue_size = AsyncMock(return_value=5)
            MockJobQueue.return_value = mock_instance
            yield mock_instance

    @pytest.mark.asyncio
    async def test_agent_task_queue_has_separate_namespace(self, mock_job_queue):
        """
        RED Test: Verify AgentTaskQueue uses 'agent:queue' namespace separate from 'ingestion:queue'

        Expected:
        - AgentTaskQueue.QUEUE_KEY_PREFIX == "agent:queue"
        - Different from ingestion:queue namespace
        """
        task_queue = AgentTaskQueue()

        assert hasattr(task_queue, 'QUEUE_KEY_PREFIX'), "AgentTaskQueue should have QUEUE_KEY_PREFIX"
        assert task_queue.QUEUE_KEY_PREFIX == "agent:queue", (
            f"Expected namespace 'agent:queue', got '{task_queue.QUEUE_KEY_PREFIX}'"
        )

        # Verify it's different from ingestion namespace
        from apps.ingestion.batch.job_queue import JobQueue
        ingestion_prefix = JobQueue.QUEUE_KEY_PREFIX
        assert task_queue.QUEUE_KEY_PREFIX != ingestion_prefix, (
            "Agent queue namespace should be separate from ingestion namespace"
        )

    @pytest.mark.asyncio
    async def test_enqueue_coverage_task_creates_task_with_correct_prefix(self, mock_job_queue):
        """
        RED Test: Verify enqueue_coverage_task() generates task_id with 'agent-coverage-' prefix

        Expected:
        - task_id format: "agent-coverage-{uuid4}"
        - Distinct from ingestion task IDs
        """
        task_queue = AgentTaskQueue()
        task_queue.job_queue = mock_job_queue

        agent_id = uuid.uuid4()
        taxonomy_node_ids = [uuid.uuid4(), uuid.uuid4()]
        taxonomy_version = "1.0.0"

        task_id = await task_queue.enqueue_coverage_task(
            agent_id=agent_id,
            taxonomy_node_ids=taxonomy_node_ids,
            taxonomy_version=taxonomy_version
        )

        assert task_id is not None, "enqueue_coverage_task should return task_id"
        assert task_id.startswith("agent-coverage-"), (
            f"Task ID should start with 'agent-coverage-', got '{task_id}'"
        )

        # Verify UUID format
        uuid_part = task_id.replace("agent-coverage-", "")
        try:
            uuid.UUID(uuid_part)
        except ValueError:
            pytest.fail(f"Task ID should contain valid UUID, got '{uuid_part}'")

    @pytest.mark.asyncio
    async def test_enqueue_coverage_task_calls_job_queue_with_priority_5(self, mock_job_queue):
        """
        RED Test: Verify coverage tasks are enqueued with priority=5 (medium queue)

        Expected:
        - JobQueue.enqueue_job called with priority=5
        - Maps to 'medium' priority queue
        """
        task_queue = AgentTaskQueue()
        task_queue.job_queue = mock_job_queue

        agent_id = uuid.uuid4()
        taxonomy_node_ids = [uuid.uuid4()]
        taxonomy_version = "1.0.0"
        webhook_url = "https://example.com/webhook"

        await task_queue.enqueue_coverage_task(
            agent_id=agent_id,
            taxonomy_node_ids=taxonomy_node_ids,
            taxonomy_version=taxonomy_version,
            webhook_url=webhook_url
        )

        # Verify JobQueue.enqueue_job was called
        mock_job_queue.enqueue_job.assert_called_once()

        # Extract call arguments
        call_args = mock_job_queue.enqueue_job.call_args
        assert call_args is not None, "enqueue_job should be called"

        # Verify priority=5
        assert call_args.kwargs.get('priority') == 5, (
            f"Expected priority=5, got {call_args.kwargs.get('priority')}"
        )

        # Verify job_data contains required fields
        job_data = call_args.kwargs.get('job_data', {})
        assert str(agent_id) in job_data.get('agent_id', ''), "job_data should contain agent_id"
        assert job_data.get('task_type') == 'coverage_refresh', "task_type should be 'coverage_refresh'"
        assert job_data.get('webhook_url') == webhook_url, "job_data should contain webhook_url"

    @pytest.mark.asyncio
    async def test_get_queue_position_calculates_position_from_redis(self, mock_job_queue):
        """
        RED Test: Verify get_queue_position() calculates position from Redis LLEN

        Expected:
        - Returns approximate queue position
        - Based on medium queue size (agent tasks use medium priority)
        """
        task_queue = AgentTaskQueue()
        task_queue.job_queue = mock_job_queue

        # Mock queue sizes: high=2, medium=8, low=3
        async def mock_get_queue_size(priority):
            sizes = {"high": 2, "medium": 8, "low": 3}
            return sizes.get(priority, 0)

        mock_job_queue.get_queue_size = mock_get_queue_size

        task_id = "agent-coverage-test-123"
        position = await task_queue.get_queue_position(task_id)

        assert position is not None, "get_queue_position should return position"
        assert isinstance(position, int), "Position should be integer"
        # Position should be in range [1, total_queue_size]
        # High priority (2) + current position in medium (1-8)
        assert 1 <= position <= 10, f"Position should be between 1 and 10, got {position}"

    @pytest.mark.asyncio
    async def test_remove_job_removes_task_from_redis_queue(self, mock_job_queue):
        """
        RED Test: Verify remove_job() removes pending task from Redis queue

        Expected:
        - Calls Redis LREM to remove task
        - Returns True if task was removed
        """
        import json

        task_queue = AgentTaskQueue()
        task_queue.job_queue = mock_job_queue

        task_id = "agent-coverage-test-456"

        # Create a mock job payload
        job_payload = {
            "job_id": task_id,
            "command_id": task_id,
            "data": {
                "task_id": task_id,
                "agent_id": "test-agent-123",
                "task_type": "coverage_refresh"
            },
            "priority": 5,
            "enqueued_at": "2025-10-12T00:00:00"
        }
        job_payload_str = json.dumps(job_payload)

        # Mock Redis lrange to return the job payload
        mock_redis = mock_job_queue.redis_manager
        mock_redis.lrange = AsyncMock(return_value=[job_payload_str.encode('utf-8')])
        mock_redis.lrem = AsyncMock(return_value=1)  # 1 item removed

        removed = await task_queue.remove_job(task_id)

        assert removed is True, "remove_job should return True when task is removed"

        # Verify Redis lrem was called
        mock_redis.lrem.assert_called_once()
        call_args = mock_redis.lrem.call_args

        # Verify queue key contains agent namespace
        queue_key = call_args.args[0] if call_args.args else call_args.kwargs.get('key')
        assert 'agent:queue' in queue_key, f"Queue key should contain 'agent:queue', got '{queue_key}'"

    @pytest.mark.asyncio
    async def test_enqueue_coverage_task_includes_taxonomy_data(self, mock_job_queue):
        """
        RED Test: Verify job_data includes all required taxonomy fields

        Expected:
        - agent_id (UUID string)
        - taxonomy_node_ids (list of UUID strings)
        - taxonomy_version (string)
        - task_type (string)
        """
        task_queue = AgentTaskQueue()
        task_queue.job_queue = mock_job_queue

        agent_id = uuid.uuid4()
        node_id_1 = uuid.uuid4()
        node_id_2 = uuid.uuid4()
        taxonomy_node_ids = [node_id_1, node_id_2]
        taxonomy_version = "2.0.0"

        await task_queue.enqueue_coverage_task(
            agent_id=agent_id,
            taxonomy_node_ids=taxonomy_node_ids,
            taxonomy_version=taxonomy_version
        )

        # Extract job_data from call
        call_args = mock_job_queue.enqueue_job.call_args
        job_data = call_args.kwargs.get('job_data', {})

        # Verify all fields present
        assert job_data.get('agent_id') == str(agent_id), "agent_id should match"

        taxonomy_ids = job_data.get('taxonomy_node_ids', [])
        assert len(taxonomy_ids) == 2, "Should have 2 taxonomy node IDs"
        assert str(node_id_1) in taxonomy_ids, "Should contain node_id_1"
        assert str(node_id_2) in taxonomy_ids, "Should contain node_id_2"

        assert job_data.get('taxonomy_version') == "2.0.0", "taxonomy_version should match"
        assert job_data.get('task_type') == 'coverage_refresh', "task_type should be coverage_refresh"

    @pytest.mark.asyncio
    async def test_remove_job_returns_false_when_task_not_found(self, mock_job_queue):
        """
        RED Test: Verify remove_job() returns False when task doesn't exist

        Expected:
        - Returns False when Redis LREM returns 0 (no items removed)
        """
        task_queue = AgentTaskQueue()
        task_queue.job_queue = mock_job_queue

        # Mock Redis lrem returning 0 (not found)
        mock_redis = mock_job_queue.redis_manager
        mock_redis.lrem = AsyncMock(return_value=0)

        task_id = "agent-coverage-nonexistent"
        removed = await task_queue.remove_job(task_id)

        assert removed is False, "remove_job should return False when task not found"
