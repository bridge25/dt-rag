"""
@TEST:AGENT-GROWTH-004:UNIT - CoverageHistoryDAO Unit Tests

RED Phase: Unit tests for CoverageHistoryDAO service
Tests coverage history insertion, querying with date filters, timestamp DESC ordering
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession


class TestCoverageHistoryDAO:
    """Unit tests for CoverageHistoryDAO service"""

    @pytest.mark.asyncio
    async def test_coverage_history_dao_insert_history(self):
        """
        RED Test: Verify insert_history() inserts coverage_history record

        Expected:
        - session.add() called with CoverageHistory instance
        - session.commit() called
        - Returns history_id UUID
        """
        from apps.api.background.coverage_history_dao import CoverageHistoryDAO

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        agent_id = uuid.uuid4()
        overall_coverage = 75.5
        total_documents = 100
        total_chunks = 500
        version = "1.0.0"

        history_id = await CoverageHistoryDAO.insert_history(
            session=mock_session,
            agent_id=agent_id,
            overall_coverage=overall_coverage,
            total_documents=total_documents,
            total_chunks=total_chunks,
            version=version
        )

        assert history_id is not None, "insert_history should return history_id"
        assert isinstance(history_id, uuid.UUID), "history_id should be UUID type"

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        added_instance = mock_session.add.call_args.args[0]
        assert added_instance.agent_id == agent_id, "agent_id should match"
        assert added_instance.overall_coverage == overall_coverage, "overall_coverage should match"
        assert added_instance.total_documents == total_documents, "total_documents should match"
        assert added_instance.total_chunks == total_chunks, "total_chunks should match"
        assert added_instance.version == version, "version should match"

    @pytest.mark.asyncio
    async def test_coverage_history_dao_query_history_basic(self):
        """
        RED Test: Verify query_history() returns all history records for agent

        Expected:
        - SELECT query executed with agent_id filter
        - timestamp DESC ordering
        - Returns list of CoverageHistory objects
        """
        from apps.api.background.coverage_history_dao import CoverageHistoryDAO
        from apps.api.database import CoverageHistory

        mock_session = AsyncMock(spec=AsyncSession)

        agent_id = uuid.uuid4()

        mock_history_1 = CoverageHistory(
            history_id=uuid.uuid4(),
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            overall_coverage=80.0,
            total_documents=100,
            total_chunks=500,
            version="1.0.0"
        )
        mock_history_2 = CoverageHistory(
            history_id=uuid.uuid4(),
            agent_id=agent_id,
            timestamp=datetime.utcnow() - timedelta(hours=1),
            overall_coverage=75.0,
            total_documents=90,
            total_chunks=450,
            version="1.0.0"
        )

        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_history_1, mock_history_2])))
        mock_session.execute = AsyncMock(return_value=mock_result)

        histories = await CoverageHistoryDAO.query_history(
            session=mock_session,
            agent_id=agent_id
        )

        assert len(histories) == 2, "Should return 2 history records"
        assert histories[0].overall_coverage == 80.0, "First record should be most recent"
        assert histories[1].overall_coverage == 75.0, "Second record should be older"

        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_coverage_history_dao_query_history_with_date_filter(self):
        """
        RED Test: Verify query_history() filters by date range (from_date, to_date)

        Expected:
        - WHERE clause includes timestamp >= from_date AND timestamp <= to_date
        - Returns only records within date range
        """
        from apps.api.background.coverage_history_dao import CoverageHistoryDAO
        from apps.api.database import CoverageHistory

        mock_session = AsyncMock(spec=AsyncSession)

        agent_id = uuid.uuid4()
        from_date = datetime.utcnow() - timedelta(days=7)
        to_date = datetime.utcnow()

        mock_history = CoverageHistory(
            history_id=uuid.uuid4(),
            agent_id=agent_id,
            timestamp=datetime.utcnow() - timedelta(days=3),
            overall_coverage=78.0,
            total_documents=95,
            total_chunks=475,
            version="1.0.0"
        )

        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_history])))
        mock_session.execute = AsyncMock(return_value=mock_result)

        histories = await CoverageHistoryDAO.query_history(
            session=mock_session,
            agent_id=agent_id,
            from_date=from_date,
            to_date=to_date
        )

        assert len(histories) == 1, "Should return 1 filtered record"
        assert from_date <= histories[0].timestamp <= to_date, "Record should be within date range"

        mock_session.execute.assert_called_once()

        call_args = mock_session.execute.call_args
        query = call_args.args[0]

        query_str = str(query.compile(compile_kwargs={"literal_binds": True}))
        assert "timestamp >=" in query_str or "timestamp <=" in query_str, "Query should include date filters"

    @pytest.mark.asyncio
    async def test_coverage_history_dao_query_history_sorted_by_timestamp_desc(self):
        """
        RED Test: Verify query_history() returns records sorted by timestamp DESC (newest first)

        Expected:
        - ORDER BY timestamp DESC
        - Most recent record first in list
        """
        from apps.api.background.coverage_history_dao import CoverageHistoryDAO
        from apps.api.database import CoverageHistory

        mock_session = AsyncMock(spec=AsyncSession)

        agent_id = uuid.uuid4()

        now = datetime.utcnow()
        mock_history_1 = CoverageHistory(
            history_id=uuid.uuid4(),
            agent_id=agent_id,
            timestamp=now,
            overall_coverage=85.0,
            total_documents=110,
            total_chunks=550,
            version="1.0.0"
        )
        mock_history_2 = CoverageHistory(
            history_id=uuid.uuid4(),
            agent_id=agent_id,
            timestamp=now - timedelta(hours=2),
            overall_coverage=82.0,
            total_documents=105,
            total_chunks=525,
            version="1.0.0"
        )
        mock_history_3 = CoverageHistory(
            history_id=uuid.uuid4(),
            agent_id=agent_id,
            timestamp=now - timedelta(hours=4),
            overall_coverage=80.0,
            total_documents=100,
            total_chunks=500,
            version="1.0.0"
        )

        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_history_1, mock_history_2, mock_history_3])))
        mock_session.execute = AsyncMock(return_value=mock_result)

        histories = await CoverageHistoryDAO.query_history(
            session=mock_session,
            agent_id=agent_id
        )

        assert len(histories) == 3, "Should return 3 records"
        assert histories[0].timestamp > histories[1].timestamp, "First should be newer than second"
        assert histories[1].timestamp > histories[2].timestamp, "Second should be newer than third"

        for i in range(len(histories) - 1):
            assert histories[i].timestamp >= histories[i + 1].timestamp, f"Record {i} should be newer than {i+1}"

    @pytest.mark.asyncio
    async def test_coverage_history_dao_query_history_with_limit(self):
        """
        RED Test: Verify query_history() respects limit parameter

        Expected:
        - LIMIT clause applied to query
        - Returns at most 'limit' records
        """
        from apps.api.background.coverage_history_dao import CoverageHistoryDAO
        from apps.api.database import CoverageHistory

        mock_session = AsyncMock(spec=AsyncSession)

        agent_id = uuid.uuid4()
        limit = 2

        mock_histories = [
            CoverageHistory(
                history_id=uuid.uuid4(),
                agent_id=agent_id,
                timestamp=datetime.utcnow() - timedelta(hours=i),
                overall_coverage=80.0 + i,
                total_documents=100,
                total_chunks=500,
                version="1.0.0"
            ) for i in range(5)
        ]

        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=mock_histories[:limit])))
        mock_session.execute = AsyncMock(return_value=mock_result)

        histories = await CoverageHistoryDAO.query_history(
            session=mock_session,
            agent_id=agent_id,
            limit=limit
        )

        assert len(histories) == limit, f"Should return at most {limit} records"

        mock_session.execute.assert_called_once()

        call_args = mock_session.execute.call_args
        query = call_args.args[0]

        query_str = str(query.compile(compile_kwargs={"literal_binds": True}))
        assert "LIMIT" in query_str or "limit" in query_str.lower(), "Query should include LIMIT clause"

    @pytest.mark.asyncio
    async def test_coverage_history_dao_validates_coverage_range(self):
        """
        RED Test: Verify insert_history() validates overall_coverage range (0.0 - 100.0)

        Expected:
        - Raises ValueError if coverage < 0.0 or > 100.0
        - Database CHECK constraint enforces range
        """
        from apps.api.background.coverage_history_dao import CoverageHistoryDAO

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add = MagicMock()

        agent_id = uuid.uuid4()

        with pytest.raises(ValueError, match="overall_coverage must be between 0.0 and 100.0"):
            await CoverageHistoryDAO.insert_history(
                session=mock_session,
                agent_id=agent_id,
                overall_coverage=-5.0,
                total_documents=100,
                total_chunks=500,
                version="1.0.0"
            )

        with pytest.raises(ValueError, match="overall_coverage must be between 0.0 and 100.0"):
            await CoverageHistoryDAO.insert_history(
                session=mock_session,
                agent_id=agent_id,
                overall_coverage=105.0,
                total_documents=100,
                total_chunks=500,
                version="1.0.0"
            )

        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_coverage_history_dao_handles_nonexistent_agent(self):
        """
        RED Test: Verify query_history() returns empty list for nonexistent agent_id

        Expected:
        - Returns [] when no records found
        - No exception raised
        """
        from apps.api.background.coverage_history_dao import CoverageHistoryDAO

        mock_session = AsyncMock(spec=AsyncSession)

        nonexistent_agent_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        mock_session.execute = AsyncMock(return_value=mock_result)

        histories = await CoverageHistoryDAO.query_history(
            session=mock_session,
            agent_id=nonexistent_agent_id
        )

        assert histories == [], "Should return empty list for nonexistent agent"
        assert isinstance(histories, list), "Should return list type"

        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_coverage_history_dao_uses_utc_timestamp(self):
        """
        RED Test: Verify insert_history() uses UTC timezone for timestamp

        Expected:
        - timestamp field populated with datetime.utcnow()
        - No timezone offset (naive datetime in UTC)
        """
        from apps.api.background.coverage_history_dao import CoverageHistoryDAO

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        agent_id = uuid.uuid4()

        before_insert = datetime.utcnow()

        history_id = await CoverageHistoryDAO.insert_history(
            session=mock_session,
            agent_id=agent_id,
            overall_coverage=80.0,
            total_documents=100,
            total_chunks=500,
            version="1.0.0"
        )

        after_insert = datetime.utcnow()

        added_instance = mock_session.add.call_args.args[0]
        assert added_instance.timestamp is not None, "timestamp should be set"
        assert before_insert <= added_instance.timestamp <= after_insert, "timestamp should be within insert window"
        assert added_instance.timestamp.tzinfo is None, "timestamp should be naive datetime (UTC)"
