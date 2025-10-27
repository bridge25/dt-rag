"""
@CODE:AGENT-GROWTH-004:QUEUE - AgentTaskQueue

Agent task queue manager with separate namespace from ingestion queue.
Wraps JobQueue for coverage refresh tasks with priority management.
"""

import json
import uuid
import logging
from typing import List, Optional
from uuid import UUID

from apps.ingestion.batch.job_queue import JobQueue

logger = logging.getLogger(__name__)


class AgentTaskQueue:
    """
    Agent task queue manager

    Features:
    - Separate namespace: agent:queue vs ingestion:queue
    - Task ID format: agent-coverage-{uuid4}
    - Priority: 5 (medium queue)
    - Coverage refresh task type
    """

    QUEUE_KEY_PREFIX = "agent:queue"

    def __init__(self, job_queue: Optional[JobQueue] = None):
        """
        Initialize AgentTaskQueue

        Args:
            job_queue: Optional JobQueue instance for testing
        """
        self.job_queue = job_queue or JobQueue()

    async def initialize(self):
        """Initialize underlying JobQueue"""
        await self.job_queue.initialize()

    def _get_queue_key(self, priority: str) -> str:
        """
        Get queue key with agent namespace

        Args:
            priority: Priority level (high, medium, low)

        Returns:
            Queue key string with agent namespace
        """
        return f"{self.QUEUE_KEY_PREFIX}:{priority}"

    async def enqueue_coverage_task(
        self,
        agent_id: UUID,
        taxonomy_node_ids: List[UUID],
        taxonomy_version: str,
        webhook_url: Optional[str] = None
    ) -> str:
        """
        Enqueue coverage refresh task

        Args:
            agent_id: Agent UUID
            taxonomy_node_ids: List of taxonomy node UUIDs
            taxonomy_version: Taxonomy version string
            webhook_url: Optional webhook URL for completion notification

        Returns:
            task_id: Unique task ID (agent-coverage-{uuid4})
        """
        task_id = f"agent-coverage-{uuid.uuid4()}"

        job_data = {
            "task_id": task_id,
            "agent_id": str(agent_id),
            "taxonomy_node_ids": [str(nid) for nid in taxonomy_node_ids],
            "taxonomy_version": taxonomy_version,
            "task_type": "coverage_refresh",
            "webhook_url": webhook_url
        }

        await self.job_queue.enqueue_job(
            job_id=task_id,
            command_id=task_id,
            job_data=job_data,
            priority=5
        )

        logger.info(
            f"Coverage task enqueued: task_id={task_id}, agent_id={agent_id}, "
            f"taxonomy_version={taxonomy_version}"
        )

        return task_id

    async def get_queue_position(self, task_id: str) -> Optional[int]:
        """
        Get approximate queue position for task

        Args:
            task_id: Task ID to query

        Returns:
            Approximate queue position (1-indexed), or None if not found

        Note:
            Position is approximate: high_queue_size + estimated_medium_position
        """
        high_size = await self.job_queue.get_queue_size("high")
        medium_size = await self.job_queue.get_queue_size("medium")

        if medium_size > 0:
            position = high_size + (medium_size // 2) + 1
            logger.debug(
                f"Queue position estimate: task_id={task_id}, "
                f"high_size={high_size}, medium_size={medium_size}, position={position}"
            )
            return position

        logger.debug(f"Queue position unknown: task_id={task_id}, medium_size=0")
        return None

    async def remove_job(self, task_id: str) -> bool:
        """
        Remove pending task from queue

        Args:
            task_id: Task ID to remove

        Returns:
            True if task was removed, False otherwise
        """
        for priority in ["high", "medium", "low"]:
            queue_key = self._get_queue_key(priority)

            try:
                items = await self.job_queue.redis_manager.lrange(queue_key, 0, -1)

                if not items:
                    continue

                for item in items:
                    try:
                        if isinstance(item, bytes):
                            item_str = item.decode('utf-8')
                        else:
                            item_str = item

                        job_payload = json.loads(item_str)

                        if job_payload.get("job_id") == task_id:
                            removed_count = await self.job_queue.redis_manager.lrem(
                                queue_key, 1, item_str.encode('utf-8') if isinstance(item_str, str) else item
                            )

                            if removed_count > 0:
                                logger.info(f"Task removed: task_id={task_id}, queue={priority}")
                                return True

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse job payload: {e}")
                        continue
                    except Exception as e:
                        logger.warning(f"Error processing item in {priority} queue: {e}")
                        continue

            except Exception as e:
                logger.error(f"Failed to remove job {task_id} from {priority} queue: {e}")
                continue

        logger.warning(f"Task not found in any queue: task_id={task_id}")
        return False
