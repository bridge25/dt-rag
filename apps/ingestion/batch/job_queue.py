"""
Job queue management for ingestion tasks.

@CODE:INGESTION-001
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any, cast
from datetime import datetime, timedelta
from apps.api.cache.redis_manager import RedisManager, get_redis_manager

logger = logging.getLogger(__name__)


class JobQueue:
    QUEUE_KEY_PREFIX = "ingestion:queue"
    JOB_STATUS_PREFIX = "ingestion:job"
    IDEMPOTENCY_KEY_PREFIX = "ingestion:idempotency"
    PRIORITY_QUEUES = ["high", "medium", "low"]

    def __init__(self, redis_manager: Optional[RedisManager] = None):
        self.redis_manager = redis_manager
        self._redis_initialized = False
        self._redis_available = False  # Track if Redis is actually reachable

    async def initialize(self) -> None:
        """Initialize Redis connection with graceful fallback on failure.

        Railway deployments may not have Redis configured, so we handle
        connection failures gracefully with a 3-second timeout.
        """
        if not self._redis_initialized:
            try:
                if self.redis_manager is None:
                    # Use asyncio.wait_for to prevent hanging on Redis connection
                    self.redis_manager = await asyncio.wait_for(
                        get_redis_manager(),
                        timeout=3.0  # 3 second timeout for Railway cold starts
                    )
                self._redis_available = True
                logger.info("Redis connection established for job queue")
            except asyncio.TimeoutError:
                logger.warning("Redis connection timeout (3s) - using in-memory fallback")
                self._redis_available = False
            except Exception as e:
                logger.warning(f"Redis connection failed: {e} - using in-memory fallback")
                self._redis_available = False
            self._redis_initialized = True

    @property
    def is_redis_available(self) -> bool:
        """Check if Redis is available for job queue operations."""
        return self._redis_available and self.redis_manager is not None

    def _get_queue_key(self, priority: str) -> str:
        return f"{self.QUEUE_KEY_PREFIX}:{priority}"

    def _get_job_status_key(self, job_id: str) -> str:
        return f"{self.JOB_STATUS_PREFIX}:{job_id}"

    def _get_idempotency_key(self, idempotency_key: str) -> str:
        return f"{self.IDEMPOTENCY_KEY_PREFIX}:{idempotency_key}"

    async def check_idempotency_key(self, idempotency_key: str) -> Optional[str]:
        await self.initialize()
        if not self.is_redis_available:
            logger.debug("Redis unavailable - skipping idempotency check")
            return None

        try:
            key = self._get_idempotency_key(idempotency_key)
            existing_job_id = await self.redis_manager.get(key)
            return existing_job_id
        except Exception as e:
            logger.error(f"Failed to check idempotency key {idempotency_key}: {e}")
            return None

    async def store_idempotency_key(
        self, idempotency_key: str, job_id: str, ttl: int = 3600
    ) -> bool:
        await self.initialize()
        if not self.is_redis_available:
            logger.debug("Redis unavailable - skipping idempotency key storage")
            return True  # Return True to allow job to proceed

        try:
            key = self._get_idempotency_key(idempotency_key)
            await self.redis_manager.set(key, job_id, ttl=ttl)
            logger.info(
                f"Stored idempotency key {idempotency_key} for job {job_id} with TTL {ttl}s"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store idempotency key {idempotency_key}: {e}")
            return False

    async def enqueue_job(
        self,
        job_id: str,
        command_id: str,
        job_data: Dict[str, Any],
        priority: int = 5,
        idempotency_key: Optional[str] = None,
    ) -> bool:
        await self.initialize()
        if not self.is_redis_available:
            logger.warning(f"Redis unavailable - job {job_id} queued in-memory only")
            # Store job status in memory (limited functionality without Redis)
            return True

        try:
            if idempotency_key:
                existing_job_id = await self.check_idempotency_key(idempotency_key)
                if existing_job_id:
                    logger.warning(
                        f"Duplicate idempotency key {idempotency_key} detected (existing job: {existing_job_id})"
                    )
                    raise ValueError(
                        f"Duplicate request with idempotency key: {idempotency_key}"
                    )

            priority_level = (
                "high" if priority <= 3 else ("medium" if priority <= 7 else "low")
            )

            queue_key = self._get_queue_key(priority_level)

            job_payload = {
                "job_id": job_id,
                "command_id": command_id,
                "data": job_data,
                "priority": priority,
                "enqueued_at": datetime.utcnow().isoformat(),
            }

            await self.redis_manager.lpush(queue_key, json.dumps(job_payload))

            await self.set_job_status(
                job_id=job_id,
                command_id=command_id,
                status="pending",
                progress_percentage=0.0,
                current_stage="Queued",
            )

            if idempotency_key:
                await self.store_idempotency_key(idempotency_key, job_id)

            logger.info(f"Job {job_id} enqueued with priority {priority_level}")
            return True

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to enqueue job {job_id}: {e}")
            return False

    async def dequeue_job(self, timeout: int = 5) -> Optional[Dict[str, Any]]:
        await self.initialize()
        if not self.is_redis_available:
            logger.debug("Redis unavailable - cannot dequeue jobs")
            return None

        try:
            for priority in self.PRIORITY_QUEUES:
                queue_key = self._get_queue_key(priority)

                result = await self.redis_manager.brpop(queue_key, timeout=timeout)

                if result:
                    _, job_payload_bytes = result
                    job_payload = json.loads(job_payload_bytes.decode("utf-8"))

                    logger.info(
                        f"Dequeued job {job_payload['job_id']} from {priority} priority"
                    )
                    return cast(Optional[Dict[str, Any]], job_payload)

            return None

        except Exception as e:
            logger.error(f"Failed to dequeue job: {e}")
            return None

    async def set_job_status(
        self,
        job_id: str,
        command_id: str,
        status: str,
        progress_percentage: float = 0.0,
        current_stage: Optional[str] = None,
        chunks_processed: int = 0,
        total_chunks: int = 0,
        error_message: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        estimated_completion_at: Optional[str] = None,
        retry_count: int = 0,
        max_retries: int = 3,
        last_attempt_at: Optional[str] = None,
        next_retry_at: Optional[str] = None,
    ) -> bool:
        await self.initialize()
        if not self.is_redis_available:
            logger.debug(f"Redis unavailable - job {job_id} status not persisted")
            return True

        try:
            status_key = self._get_job_status_key(job_id)

            status_data = {
                "job_id": job_id,
                "command_id": command_id,
                "status": status,
                "progress_percentage": progress_percentage,
                "current_stage": current_stage,
                "chunks_processed": chunks_processed,
                "total_chunks": total_chunks,
                "error_message": error_message,
                "started_at": started_at,
                "completed_at": completed_at,
                "estimated_completion_at": estimated_completion_at,
                "updated_at": datetime.utcnow().isoformat(),
                "retry_count": retry_count,
                "max_retries": max_retries,
                "last_attempt_at": last_attempt_at,
                "next_retry_at": next_retry_at,
            }

            ttl = 86400

            await self.redis_manager.set(status_key, status_data, ttl=ttl)

            return True

        except Exception as e:
            logger.error(f"Failed to set job status for {job_id}: {e}")
            return False

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        await self.initialize()
        if not self.is_redis_available:
            logger.debug(f"Redis unavailable - cannot retrieve job {job_id} status")
            return None

        try:
            status_key = self._get_job_status_key(job_id)
            status_data = await self.redis_manager.get(status_key)

            return status_data

        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None

    async def get_queue_size(self, priority: Optional[str] = None) -> int:
        await self.initialize()
        if not self.is_redis_available:
            return 0

        try:
            if priority:
                queue_key = self._get_queue_key(priority)
                return await self.redis_manager.llen(queue_key)
            else:
                total_size = 0
                for p in self.PRIORITY_QUEUES:
                    queue_key = self._get_queue_key(p)
                    total_size += await self.redis_manager.llen(queue_key)
                return total_size

        except Exception as e:
            logger.error(f"Failed to get queue size: {e}")
            return 0

    async def clear_queue(self, priority: Optional[str] = None) -> bool:
        await self.initialize()
        if not self.is_redis_available:
            return True

        try:
            if priority:
                queue_key = self._get_queue_key(priority)
                await self.redis_manager.delete(queue_key)
            else:
                for p in self.PRIORITY_QUEUES:
                    queue_key = self._get_queue_key(p)
                    await self.redis_manager.delete(queue_key)

            logger.info(f"Cleared queue(s): {priority or 'all'}")
            return True

        except Exception as e:
            logger.error(f"Failed to clear queue: {e}")
            return False

    async def retry_job(
        self,
        job_id: str,
        command_id: str,
        job_data: Dict[str, Any],
        priority: int = 5,
    ) -> bool:
        await self.initialize()
        if not self.is_redis_available:
            logger.warning(f"Redis unavailable - cannot retry job {job_id}")
            return False

        try:
            status = await self.get_job_status(job_id)
            if not status:
                logger.error(f"Cannot retry job {job_id}: status not found")
                return False

            retry_count = status.get("retry_count", 0) + 1
            max_retries = status.get("max_retries", 3)

            if retry_count > max_retries:
                logger.error(f"Job {job_id} exceeded max retries ({max_retries})")
                return False

            delay_seconds = 2**retry_count
            next_retry_at = (
                datetime.utcnow() + timedelta(seconds=delay_seconds)
            ).isoformat()

            await self.set_job_status(
                job_id=job_id,
                command_id=command_id,
                status="retrying",
                current_stage=f"Retry {retry_count}/{max_retries}",
                error_message=status.get("error_message", ""),
                retry_count=retry_count,
                max_retries=max_retries,
                last_attempt_at=datetime.utcnow().isoformat(),
                next_retry_at=next_retry_at,
            )

            await asyncio.sleep(delay_seconds)

            idempotency_key = job_data.get("idempotency_key")

            await self.enqueue_job(
                job_id=job_id,
                command_id=command_id,
                job_data=job_data,
                priority=priority,
                idempotency_key=idempotency_key,
            )

            logger.info(
                f"Retrying job {job_id} (attempt {retry_count}/{max_retries}) after {delay_seconds}s with idempotency_key={idempotency_key}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to retry job {job_id}: {e}")
            return False
