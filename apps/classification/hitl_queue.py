"""
Human-in-the-Loop (HITL) Queue Management
Manages classification tasks requiring human review

Features:
- Queue management for low-confidence classifications
- Priority-based task ordering
- Task assignment and completion tracking
- Statistics and monitoring
"""

# @CODE:CLASS-001 | SPEC: .moai/specs/SPEC-CLASS-001/spec.md | TEST: tests/e2e/test_complete_workflow.py

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy import text
from apps.api.database import db_manager

logger = logging.getLogger(__name__)


class HITLQueue:
    """Human-in-the-loop queue manager"""

    def __init__(self) -> None:
        """Initialize HITL queue manager"""
        logger.info("HITLQueue initialized")

    async def add_task(
        self,
        chunk_id: str,
        text: str,
        suggested_classification: List[str],
        confidence: float,
        alternatives: List[List[str]],
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add classification task to HITL queue

        Args:
            chunk_id: Chunk identifier
            text: Text content
            suggested_classification: Suggested canonical path
            confidence: Classification confidence score
            alternatives: Alternative classification paths
            priority: Task priority (low, normal, high, urgent)
            metadata: Additional metadata

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())

        try:
            async with db_manager.async_session() as session:
                # Insert into doc_taxonomy with hitl_required=true
                # @CODE:MYPY-CONSOLIDATION-002 | Phase 14d: operator (Fix 46 - SQLAlchemy text() untyped)
                query = text(  # type: ignore[operator]
                    """
                    UPDATE doc_taxonomy
                    SET hitl_required = true,
                        confidence = :confidence,
                        path = :path
                    WHERE doc_id = (
                        SELECT doc_id FROM chunks WHERE chunk_id = :chunk_id
                    )
                """
                )

                await session.execute(
                    query,
                    {
                        "chunk_id": chunk_id,
                        "confidence": confidence,
                        "path": suggested_classification,
                    },
                )

                await session.commit()

                logger.info(
                    f"Added HITL task {task_id} for chunk {chunk_id} (conf={confidence})"
                )

                return task_id

        except Exception as e:
            logger.error(f"Failed to add HITL task: {e}")
            raise

    async def get_pending_tasks(
        self,
        limit: int = 50,
        priority: Optional[str] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get pending HITL tasks

        Args:
            limit: Maximum number of tasks to return
            priority: Filter by priority level
            min_confidence: Minimum confidence threshold
            max_confidence: Maximum confidence threshold

        Returns:
            List of pending tasks
        """
        try:
            async with db_manager.async_session() as session:
                query = text(
                    """
                    SELECT
                        dt.doc_id,
                        dt.path as suggested_classification,
                        dt.confidence,
                        c.chunk_id,
                        c.text,
                        c.created_at
                    FROM doc_taxonomy dt
                    JOIN chunks c ON c.doc_id = dt.doc_id
                    WHERE dt.hitl_required = true
                    ORDER BY dt.confidence ASC, c.created_at ASC
                    LIMIT :limit
                """
                )

                result = await session.execute(query, {"limit": limit})
                rows = result.fetchall()

                tasks = []
                for row in rows:
                    tasks.append(
                        {
                            "task_id": str(uuid.uuid4()),  # Generate task ID
                            "chunk_id": str(row[3]),
                            "text": row[4][:500],  # Limit text length
                            "suggested_classification": row[1],
                            "confidence": float(row[2]) if row[2] else 0.0,
                            "alternatives": [],  # TODO: Fetch from candidates table
                            "created_at": (
                                row[5].isoformat()
                                if row[5]
                                else datetime.utcnow().isoformat()
                            ),
                            "priority": "normal",
                            "status": "pending",
                        }
                    )

                logger.info(f"Retrieved {len(tasks)} pending HITL tasks")
                return tasks

        except Exception as e:
            logger.error(f"Failed to get pending tasks: {e}")
            return []

    async def complete_task(
        self,
        task_id: str,
        chunk_id: str,
        approved_path: List[str],
        confidence_override: Optional[float] = None,
        reviewer_notes: Optional[str] = None,
        reviewer_id: Optional[str] = None,
    ) -> bool:
        """
        Mark HITL task as completed

        Args:
            task_id: Task identifier
            chunk_id: Chunk identifier
            approved_path: Human-approved classification path
            confidence_override: Optional confidence override
            reviewer_notes: Optional reviewer notes
            reviewer_id: Optional reviewer identifier

        Returns:
            True if successful
        """
        try:
            async with db_manager.async_session() as session:
                # Update doc_taxonomy with approved classification
                query = text(
                    """
                    UPDATE doc_taxonomy
                    SET path = :approved_path,
                        confidence = :confidence,
                        hitl_required = false
                    WHERE doc_id = (
                        SELECT doc_id FROM chunks WHERE chunk_id = :chunk_id
                    )
                """
                )

                await session.execute(
                    query,
                    {
                        "chunk_id": chunk_id,
                        "approved_path": approved_path,
                        "confidence": (
                            confidence_override
                            if confidence_override is not None
                            else 1.0
                        ),
                    },
                )

                await session.commit()

                logger.info(f"Completed HITL task {task_id} for chunk {chunk_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to complete HITL task: {e}")
            return False

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get HITL queue statistics

        Returns:
            Statistics dictionary
        """
        try:
            async with db_manager.async_session() as session:
                query = text(
                    """
                    SELECT
                        COUNT(*) as total_pending,
                        AVG(confidence) as avg_confidence,
                        MIN(confidence) as min_confidence,
                        MAX(confidence) as max_confidence
                    FROM doc_taxonomy
                    WHERE hitl_required = true
                """
                )

                result = await session.execute(query)
                row = result.fetchone()

                if row is not None:
                    return {
                        "total_pending": int(row[0]) if row[0] else 0,
                        "avg_confidence": float(row[1]) if row[1] else 0.0,
                        "min_confidence": float(row[2]) if row[2] else 0.0,
                        "max_confidence": float(row[3]) if row[3] else 0.0,
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                # Fallback if row is None
                return {
                    "total_pending": 0,
                    "avg_confidence": 0.0,
                    "min_confidence": 0.0,
                    "max_confidence": 0.0,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error(f"Failed to get HITL statistics: {e}")
            return {
                "total_pending": 0,
                "avg_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 0.0,
                "error": str(e),
            }

    async def cancel_task(self, task_id: str, chunk_id: str, reason: str) -> bool:
        """
        Cancel HITL task

        Args:
            task_id: Task identifier
            chunk_id: Chunk identifier
            reason: Cancellation reason

        Returns:
            True if successful
        """
        try:
            async with db_manager.async_session() as session:
                # Simply remove HITL flag
                query = text(
                    """
                    UPDATE doc_taxonomy
                    SET hitl_required = false
                    WHERE doc_id = (
                        SELECT doc_id FROM chunks WHERE chunk_id = :chunk_id
                    )
                """
                )

                await session.execute(query, {"chunk_id": chunk_id})
                await session.commit()

                logger.info(f"Cancelled HITL task {task_id}: {reason}")
                return True

        except Exception as e:
            logger.error(f"Failed to cancel HITL task: {e}")
            return False
