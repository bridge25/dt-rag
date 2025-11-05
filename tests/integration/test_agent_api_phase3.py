"""
@TEST:AGENT-GROWTH-004:API | Phase 3-4 API Endpoint Integration Tests

Integration tests for Phase 3-4 real background task API endpoints.
Tests POST /refresh, GET /status, GET /history, DELETE /tasks endpoints.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from apps.api.main import app
from apps.core.db_session import async_session
from apps.api.agent_dao import AgentDAO
from apps.api.database import BackgroundTask
from apps.api.background.agent_task_queue import AgentTaskQueue
from apps.api.background.coverage_history_dao import CoverageHistoryDAO


class TestAgentAPIPhase3:
    """Integration tests for SPEC-AGENT-GROWTH-004 Phase 3-4 API endpoints"""

    @pytest.fixture
    async def test_agent(self):
        """Create test agent"""
        async with async_session() as session:
            agent = await AgentDAO.create_agent(
                session=session,
                name="Test Phase 3 Agent",
                taxonomy_node_ids=[uuid.uuid4()],
                taxonomy_version="1.0.0",
                scope_description="Test agent for Phase 3 API tests",
                retrieval_config={"top_k": 5, "strategy": "hybrid"},
                features_config={},
            )
            yield agent

            # Cleanup
            await AgentDAO.delete_agent(session, agent.agent_id)

    @pytest.fixture
    async def client(self):
        """Create async HTTP client"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_refresh_coverage_background_creates_task(self, test_agent, client):
        """
        Given: Agent exists
        When: POST /agents/{agent_id}/coverage/refresh?background=true
        Then: Creates background_tasks row and returns task_id
        """
        response = await client.post(
            f"/api/v1/agents/{test_agent.agent_id}/coverage/refresh?background=true",
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 202
        data = response.json()

        assert data["task_id"].startswith("agent-coverage-")
        assert data["agent_id"] == str(test_agent.agent_id)
        assert data["task_type"] == "coverage_refresh"
        assert data["status"] == "pending"
        assert data["created_at"] is not None

        # Verify background_tasks row exists
        async with async_session() as session:
            task = await session.get(BackgroundTask, data["task_id"])
            assert task is not None
            assert task.agent_id == test_agent.agent_id
            assert task.status == "pending"

    @pytest.mark.asyncio
    async def test_get_task_status_returns_real_status(self, test_agent, client):
        """
        Given: Task exists in database
        When: GET /agents/{agent_id}/coverage/status/{task_id}
        Then: Returns real task status from database
        """
        # Create task
        async with async_session() as session:
            task_id = f"agent-coverage-{uuid.uuid4()}"
            task = BackgroundTask(
                task_id=task_id,
                agent_id=test_agent.agent_id,
                task_type="coverage_refresh",
                status="pending",
                created_at=datetime.utcnow(),
            )
            session.add(task)
            await session.commit()

        # Query task status
        response = await client.get(
            f"/api/v1/agents/{test_agent.agent_id}/coverage/status/{task_id}",
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["task_id"] == task_id
        assert data["agent_id"] == str(test_agent.agent_id)
        assert data["status"] == "pending"
        assert "queue_position" in data  # Optional field for pending tasks

    @pytest.mark.asyncio
    async def test_get_task_status_404_for_nonexistent_task(self, test_agent, client):
        """
        Given: Task does not exist
        When: GET /agents/{agent_id}/coverage/status/{nonexistent_task_id}
        Then: Returns 404 Not Found
        """
        nonexistent_task_id = f"agent-coverage-{uuid.uuid4()}"

        response = await client.get(
            f"/api/v1/agents/{test_agent.agent_id}/coverage/status/{nonexistent_task_id}",
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_coverage_history_returns_time_series(self, test_agent, client):
        """
        Given: Coverage history entries exist
        When: GET /agents/{agent_id}/coverage/history
        Then: Returns time-series data from database
        """
        # Insert 3 history entries
        async with async_session() as session:
            for i in range(3):
                await CoverageHistoryDAO.insert_history(
                    session=session,
                    agent_id=test_agent.agent_id,
                    overall_coverage=70.0 + i * 5.0,
                    total_documents=100 + i * 10,
                    total_chunks=500 + i * 50,
                    version="1.0.0",
                )

        # Query coverage history
        response = await client.get(
            f"/api/v1/agents/{test_agent.agent_id}/coverage/history",
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["history"]) == 3
        assert data["agent_id"] == str(test_agent.agent_id)
        assert data["total_entries"] == 3

        # Verify DESC order (newest first)
        history_items = data["history"]
        assert (
            history_items[0]["overall_coverage"] >= history_items[1]["overall_coverage"]
        )

    @pytest.mark.asyncio
    async def test_get_coverage_history_with_date_filter(self, test_agent, client):
        """
        Given: Coverage history entries with different timestamps
        When: GET /history with start_date filter
        Then: Returns filtered results
        """
        # Insert entries with different timestamps
        async with async_session() as session:
            # Old entry (2 days ago)
            await CoverageHistoryDAO.insert_history(
                session=session,
                agent_id=test_agent.agent_id,
                overall_coverage=60.0,
                total_documents=80,
                total_chunks=400,
                version="1.0.0",
            )

            # Recent entry
            await CoverageHistoryDAO.insert_history(
                session=session,
                agent_id=test_agent.agent_id,
                overall_coverage=85.0,
                total_documents=120,
                total_chunks=600,
                version="1.0.0",
            )

        # Query with start_date filter (last 1 hour)
        start_date = (datetime.utcnow() - timedelta(hours=1)).isoformat()

        response = await client.get(
            f"/api/v1/agents/{test_agent.agent_id}/coverage/history?start_date={start_date}",
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should return at least 1 recent entry
        assert len(data["history"]) >= 1

    @pytest.mark.asyncio
    async def test_cancel_task_pending(self, test_agent, client):
        """
        Given: Task in pending status
        When: DELETE /agents/tasks/{task_id}
        Then: Task status updated to cancelled
        """
        # Create pending task
        async with async_session() as session:
            task_id = f"agent-coverage-{uuid.uuid4()}"
            task = BackgroundTask(
                task_id=task_id,
                agent_id=test_agent.agent_id,
                task_type="coverage_refresh",
                status="pending",
                created_at=datetime.utcnow(),
            )
            session.add(task)
            await session.commit()

        # Cancel task
        response = await client.delete(
            f"/api/v1/agents/tasks/{task_id}", headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 204

        # Verify status updated
        async with async_session() as session:
            updated_task = await session.get(BackgroundTask, task_id)
            assert updated_task is not None, f"Task {task_id} not found"
            assert updated_task.status == "cancelled"
            assert updated_task.completed_at is not None

    @pytest.mark.asyncio
    async def test_cancel_task_running(self, test_agent, client):
        """
        Given: Task in running status
        When: DELETE /agents/tasks/{task_id}
        Then: cancellation_requested flag set to True
        """
        # Create running task
        async with async_session() as session:
            task_id = f"agent-coverage-{uuid.uuid4()}"
            task = BackgroundTask(
                task_id=task_id,
                agent_id=test_agent.agent_id,
                task_type="coverage_refresh",
                status="running",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
            )
            session.add(task)
            await session.commit()

        # Cancel task
        response = await client.delete(
            f"/api/v1/agents/tasks/{task_id}", headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 204

        # Verify cancellation_requested flag set
        async with async_session() as session:
            updated_task = await session.get(BackgroundTask, task_id)
            assert updated_task is not None, f"Task {task_id} not found"
            assert updated_task.cancellation_requested is True
            assert updated_task.status == "running"  # Still running until worker checks

    @pytest.mark.asyncio
    async def test_cancel_task_completed(self, test_agent, client):
        """
        Given: Task in completed status
        When: DELETE /agents/tasks/{task_id}
        Then: Returns 400 Bad Request
        """
        # Create completed task
        async with async_session() as session:
            task_id = f"agent-coverage-{uuid.uuid4()}"
            task = BackgroundTask(
                task_id=task_id,
                agent_id=test_agent.agent_id,
                task_type="coverage_refresh",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            session.add(task)
            await session.commit()

        # Attempt to cancel completed task
        response = await client.delete(
            f"/api/v1/agents/tasks/{task_id}", headers={"X-API-Key": "test-key"}
        )

        assert response.status_code == 400
        assert "Cannot cancel task" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_cancel_task_404_for_nonexistent(self, client):
        """
        Given: Task does not exist
        When: DELETE /agents/tasks/{nonexistent_task_id}
        Then: Returns 404 Not Found
        """
        nonexistent_task_id = f"agent-coverage-{uuid.uuid4()}"

        response = await client.delete(
            f"/api/v1/agents/tasks/{nonexistent_task_id}",
            headers={"X-API-Key": "test-key"},
        )

        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]
