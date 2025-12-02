"""
Q-Table Data Access Object for reinforcement learning persistence.

@CODE:DATABASE-PKG-016
"""

from __future__ import annotations

import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import select, func

from ..connection import async_session
from ..models.q_table import QTableEntry

logger = logging.getLogger(__name__)

__all__ = ["QTableDAO", "USE_PERSISTENT_QTABLE"]

# Feature Flag for persistent Q-Table (set via environment variable)
USE_PERSISTENT_QTABLE = os.getenv("USE_PERSISTENT_QTABLE", "false").lower() == "true"


class QTableDAO:
    """
    Q-table Data Access Object (Feature Flag support).

    Supports two storage backends:
    - Memory-based (default): Fast, but lost on restart
    - PostgreSQL-based (USE_PERSISTENT_QTABLE=true): Persistent, survives restarts

    The interface remains the same regardless of backend.
    """

    def __init__(self, use_persistent: Optional[bool] = None) -> None:
        """
        Initialize Q-table DAO.

        Args:
            use_persistent: Override for persistent storage. If None, uses env var.
        """
        self._use_persistent = use_persistent if use_persistent is not None else USE_PERSISTENT_QTABLE
        self._memory_storage: Dict[str, List[float]] = {}

        if self._use_persistent:
            logger.info("QTableDAO initialized (PostgreSQL persistent storage)")
        else:
            logger.info("QTableDAO initialized (memory-based storage)")

    async def save_q_table(self, state_hash: str, q_values: List[float]) -> None:
        """
        Save Q-table.

        Args:
            state_hash: State hash string (64-char)
            q_values: Q-values list (6 values)
        """
        if self._use_persistent:
            await self._save_persistent(state_hash, q_values)
        else:
            self._memory_storage[state_hash] = q_values.copy()
            logger.debug(
                f"Saved Q-table (memory): state={state_hash}, q_values={[round(q, 3) for q in q_values]}"
            )

    async def load_q_table(self, state_hash: str) -> Optional[List[float]]:
        """
        Load Q-table.

        Args:
            state_hash: State hash string

        Returns:
            Q-values list (6 values) or None
        """
        if self._use_persistent:
            return await self._load_persistent(state_hash)
        else:
            q_values = self._memory_storage.get(state_hash)
            if q_values:
                logger.debug(f"Loaded Q-table (memory): state={state_hash}")
            return q_values

    async def _save_persistent(self, state_hash: str, q_values: List[float]) -> None:
        """Save Q-table to PostgreSQL."""
        async with async_session() as session:
            try:
                # Check if entry exists
                stmt = select(QTableEntry).where(QTableEntry.state_hash == state_hash)
                result = await session.execute(stmt)
                entry = result.scalar_one_or_none()

                if entry:
                    # Update existing entry
                    entry.q_values = q_values
                    entry.access_count += 1
                    entry.updated_at = datetime.utcnow()
                else:
                    # Create new entry
                    entry = QTableEntry(
                        state_hash=state_hash,
                        q_values=q_values,
                        access_count=0,
                    )
                    session.add(entry)

                await session.commit()
                logger.debug(
                    f"Saved Q-table (PostgreSQL): state={state_hash}, q_values={[round(q, 3) for q in q_values]}"
                )
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to save Q-table: {e}")
                # Fallback to memory storage
                self._memory_storage[state_hash] = q_values.copy()
                logger.warning(f"Fell back to memory storage for state={state_hash}")

    async def _load_persistent(self, state_hash: str) -> Optional[List[float]]:
        """Load Q-table from PostgreSQL."""
        async with async_session() as session:
            try:
                stmt = select(QTableEntry).where(QTableEntry.state_hash == state_hash)
                result = await session.execute(stmt)
                entry = result.scalar_one_or_none()

                if entry:
                    # Increment access count
                    entry.access_count += 1
                    await session.commit()
                    logger.debug(f"Loaded Q-table (PostgreSQL): state={state_hash}")
                    return list(entry.q_values)  # type: ignore[arg-type]
                return None
            except Exception as e:
                logger.error(f"Failed to load Q-table: {e}")
                # Fallback to memory storage
                return self._memory_storage.get(state_hash)

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Return Q-Table storage statistics.

        Returns:
            Dict containing storage statistics
        """
        if self._use_persistent:
            async with async_session() as session:
                try:
                    count_stmt = select(func.count(QTableEntry.id))
                    count_result = await session.execute(count_stmt)
                    total_entries = count_result.scalar() or 0

                    access_stmt = select(func.sum(QTableEntry.access_count))
                    access_result = await session.execute(access_stmt)
                    total_accesses = access_result.scalar() or 0

                    return {
                        "storage_type": "postgresql",
                        "total_entries": total_entries,
                        "total_accesses": total_accesses,
                        "memory_fallback_entries": len(self._memory_storage),
                    }
                except Exception as e:
                    logger.error(f"Failed to get Q-table statistics: {e}")
                    return {
                        "storage_type": "postgresql",
                        "error": str(e),
                        "memory_fallback_entries": len(self._memory_storage),
                    }
        else:
            return {
                "storage_type": "memory",
                "total_entries": len(self._memory_storage),
            }
