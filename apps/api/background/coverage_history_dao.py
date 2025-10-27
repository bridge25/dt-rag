"""
@CODE:AGENT-GROWTH-004:DAO - CoverageHistoryDAO

Data access object for coverage_history table.
Provides time-series coverage tracking for agents.
"""

from typing import List, Optional
from uuid import UUID
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.database import CoverageHistory
import logging

logger = logging.getLogger(__name__)


class CoverageHistoryDAO:
    @staticmethod
    async def insert_history(
        session: AsyncSession,
        agent_id: UUID,
        overall_coverage: float,
        total_documents: int,
        total_chunks: int,
        version: str = "1.0.0",
    ) -> UUID:
        """
        Insert coverage history record

        Args:
            session: AsyncSession
            agent_id: Agent UUID
            overall_coverage: Coverage percentage (0.0 - 100.0)
            total_documents: Total document count
            total_chunks: Total chunk count
            version: Taxonomy version

        Returns:
            history_id: UUID of inserted record

        Raises:
            ValueError: If overall_coverage is out of range
        """
        if not (0.0 <= overall_coverage <= 100.0):
            raise ValueError("overall_coverage must be between 0.0 and 100.0")

        history_id = uuid.uuid4()

        history = CoverageHistory(
            history_id=history_id,
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            overall_coverage=overall_coverage,
            total_documents=total_documents,
            total_chunks=total_chunks,
            version=version,
        )

        session.add(history)
        await session.commit()

        logger.info(
            f"Coverage history inserted: agent_id={agent_id}, "
            f"coverage={overall_coverage:.2f}%, history_id={history_id}"
        )

        return history_id

    @staticmethod
    async def query_history(
        session: AsyncSession,
        agent_id: UUID,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[CoverageHistory]:
        """
        Query coverage history for agent

        Args:
            session: AsyncSession
            agent_id: Agent UUID
            from_date: Optional start date filter (inclusive)
            to_date: Optional end date filter (inclusive)
            limit: Optional maximum number of records

        Returns:
            List of CoverageHistory objects, sorted by timestamp DESC (newest first)
        """
        query = select(CoverageHistory).where(CoverageHistory.agent_id == agent_id)

        if from_date is not None:
            query = query.where(CoverageHistory.timestamp >= from_date)

        if to_date is not None:
            query = query.where(CoverageHistory.timestamp <= to_date)

        query = query.order_by(CoverageHistory.timestamp.desc())

        if limit is not None:
            query = query.limit(limit)

        result = await session.execute(query)
        histories = result.scalars().all()

        logger.debug(
            f"Coverage history query: agent_id={agent_id}, "
            f"from_date={from_date}, to_date={to_date}, "
            f"limit={limit}, results={len(histories)}"
        )

        return list(histories)
