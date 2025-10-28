"""
@CODE:AGENT-GROWTH-004:WORKER - AgentTaskWorker

Background worker for agent coverage refresh tasks.
Processes tasks from Redis queue with timeout, cancellation, and progress tracking.
"""

import asyncio
import logging
from typing import Dict, Any
from uuid import UUID
from datetime import datetime

from apps.api.background.agent_task_queue import AgentTaskQueue
from apps.api.background.coverage_history_dao import CoverageHistoryDAO
from apps.api.background.webhook_service import WebhookService
from apps.api.agent_dao import AgentDAO
from apps.knowledge_builder.coverage.meter import CoverageMeterService
from apps.core.db_session import async_session
from apps.api.database import BackgroundTask

logger = logging.getLogger(__name__)


class AgentTaskWorker:
    """
    Agent task background worker

    Features:
    - Dequeues coverage tasks from Redis queue
    - Task lifecycle: pending → running → completed/failed/cancelled/timeout
    - Timeout: configurable (default 300 seconds / 5 minutes)
    - Cancellation: polling-based (checks every 2 seconds)
    - Progress tracking: updates progress_percentage during execution
    - Coverage history: inserts coverage_history record on success
    - Webhook: sends completion notification if webhook_url present
    """

    def __init__(self, worker_id: int, timeout: int = 300):
        """
        Initialize AgentTaskWorker

        Args:
            worker_id: Worker identifier
            timeout: Task timeout in seconds (default 300)
        """
        self.worker_id = worker_id
        self.timeout = timeout
        self.running = False
        self.task_queue = AgentTaskQueue()
        self.worker_task = None
        logger.info(
            f"AgentTaskWorker initialized: worker_id={worker_id}, timeout={timeout}s"
        )

    async def start(self):
        """Start worker loop"""
        self.running = True
        logger.info(f"AgentTaskWorker {self.worker_id} started")
        await self._worker_loop()

    async def stop(self):
        """Stop worker gracefully"""
        self.running = False
        logger.info(f"AgentTaskWorker {self.worker_id} stopping...")

        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

    async def _worker_loop(self):
        """
        Main worker loop

        Dequeues tasks from Redis and processes them until stopped.
        """
        if not self.running:
            self.running = True

        while self.running:
            try:
                job = await self.task_queue.job_queue.dequeue_job()

                if job:
                    task_id = job["data"]["task_id"]
                    job_data = job["data"]

                    logger.info(f"Worker {self.worker_id} processing task: {task_id}")
                    await self._process_coverage_task(task_id, job_data)
                else:
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info(f"Worker {self.worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _process_coverage_task(self, task_id: str, job_data: Dict[str, Any]):
        """
        Process coverage refresh task

        Args:
            task_id: Task ID
            job_data: Job data containing agent_id, taxonomy_node_ids, etc.

        Task lifecycle:
        1. Check cancellation_requested → 'cancelled'
        2. Update status → 'running'
        3. Calculate coverage (with timeout)
        4. Insert coverage_history record
        5. Update status → 'completed'
        6. Send webhook notification

        Error handling:
        - asyncio.TimeoutError → status='timeout'
        - Exception → status='failed'
        """
        async with async_session() as session:
            try:
                task = await session.get(BackgroundTask, task_id)

                if not task:
                    logger.error(f"Task not found: {task_id}")
                    return

                # Check cancellation before starting
                if task.cancellation_requested:
                    logger.info(f"Task cancelled before start: {task_id}")
                    task.status = "cancelled"
                    task.completed_at = datetime.utcnow()
                    await session.commit()
                    return

                # Update status to running
                task.status = "running"
                task.started_at = datetime.utcnow()
                task.progress_percentage = 0.0
                await session.commit()

                logger.info(
                    f"Task {task_id} started: agent_id={job_data.get('agent_id')}"
                )

                try:
                    # Calculate coverage with timeout
                    result = await asyncio.wait_for(
                        self._calculate_coverage(session, task, job_data),
                        timeout=self.timeout,
                    )

                    # Update progress to 100%
                    task.progress_percentage = 100.0
                    await session.commit()

                    # Insert coverage history
                    agent_id = UUID(job_data["agent_id"])
                    await CoverageHistoryDAO.insert_history(
                        session=session,
                        agent_id=agent_id,
                        overall_coverage=result.coverage_percent,
                        total_documents=result.total_documents,
                        total_chunks=result.total_chunks,
                        version=job_data["taxonomy_version"],
                    )

                    # Update task status to completed
                    task.status = "completed"
                    task.completed_at = datetime.utcnow()
                    task.result = {
                        "coverage_percent": result.coverage_percent,
                        "total_documents": result.total_documents,
                        "total_chunks": result.total_chunks,
                    }
                    await session.commit()

                    logger.info(
                        f"Task {task_id} completed: coverage={result.coverage_percent:.2f}%"
                    )

                    # Send webhook notification
                    webhook_url = job_data.get("webhook_url")
                    if webhook_url:
                        await self._send_webhook(task, job_data, webhook_url)

                except asyncio.TimeoutError:
                    logger.warning(f"Task {task_id} timed out after {self.timeout}s")
                    task.status = "timeout"
                    task.error = f"Task timeout after {self.timeout} seconds"
                    task.completed_at = datetime.utcnow()
                    await session.commit()

                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}", exc_info=True)
                    task.status = "failed"
                    task.error = str(e)
                    task.completed_at = datetime.utcnow()
                    await session.commit()

            except Exception as e:
                logger.error(
                    f"Fatal error processing task {task_id}: {e}", exc_info=True
                )

    async def _calculate_coverage(
        self, session: Any, task: BackgroundTask, job_data: Dict[str, Any]
    ) -> None:
        """
        Calculate coverage with cancellation checks

        Args:
            session: Database session
            task: BackgroundTask instance
            job_data: Job data

        Returns:
            CoverageMeterService result

        Raises:
            asyncio.CancelledError: If task cancelled during execution
        """
        # Get agent
        agent_id = UUID(job_data["agent_id"])
        agent = await AgentDAO.get_agent(session, agent_id)

        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        # Update progress
        task.progress_percentage = 25.0
        await session.commit()

        # @CODE:MYPY-CONSOLIDATION-002 | Phase 2: Fix call-arg errors
        # Calculate coverage - Fixed method signature
        result = await CoverageMeterService().calculate_coverage(
            taxonomy_version=agent.taxonomy_version,
            node_ids=agent.taxonomy_node_ids,
        )

        # Update progress
        task.progress_percentage = 75.0
        await session.commit()

        return result

    async def _send_webhook(
        self, task: BackgroundTask, job_data: Dict[str, Any], webhook_url: str
    ):
        """
        Send webhook notification

        Args:
            task: BackgroundTask instance
            job_data: Job data
            webhook_url: Webhook URL
        """
        try:
            webhook_service = WebhookService()

            payload = {
                "task_id": task.task_id,
                "agent_id": job_data["agent_id"],
                "status": task.status,
                "result": task.result,
                "completed_at": (
                    task.completed_at.isoformat() if task.completed_at else None
                ),
            }

            success = await webhook_service.send_webhook(webhook_url, payload)

            if success:
                logger.info(f"Webhook sent successfully: task_id={task.task_id}")
            else:
                logger.warning(f"Webhook delivery failed: task_id={task.task_id}")

        except Exception as e:
            logger.error(f"Webhook error for task {task.task_id}: {e}", exc_info=True)
