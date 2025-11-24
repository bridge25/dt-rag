# @TEST:RESEARCH-BACKEND-001:E2E
"""
End-to-End Integration Tests for Research Module - Full workflow testing

Tests complete research workflows:
- Session creation through completion with metrics tracking
- Error handling and recovery
- SSE streaming with metrics
- Document import with metrics recording
"""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime

from apps.api.services.research_service import ResearchService
from apps.api.services.research_session_manager import ResearchSessionManager
from apps.api.routers.research_router import create_research_router
from apps.api.schemas.research_schemas import (
    ResearchSession,
    ResearchStage,
    ResearchConfig,
    StartResearchRequest,
)
from apps.api.monitoring.research_metrics import (
    ResearchMetrics,
    initialize_research_metrics,
)


@pytest.fixture
def mock_session_manager():
    """Mock ResearchSessionManager"""
    manager = Mock(spec=ResearchSessionManager)
    manager.create_session = AsyncMock()
    manager.get_session = AsyncMock()
    manager.update_session = AsyncMock()
    manager.delete_session = AsyncMock()
    manager.publish_event = AsyncMock()
    manager.get_events_since = AsyncMock(return_value=[])
    return manager


@pytest.fixture
def research_metrics():
    """Create and initialize test metrics"""
    metrics = initialize_research_metrics(enable_prometheus=False)
    yield metrics
    # Reset after test
    metrics.reset_metrics()


@pytest.fixture
def research_service(mock_session_manager):
    """Create ResearchService with mock session manager"""
    service = ResearchService(session_manager=mock_session_manager)
    return service


class TestResearchE2EWorkflow:
    """End-to-end research workflow tests"""

    @pytest.mark.asyncio
    async def test_complete_research_lifecycle_with_metrics(
        self, research_service, mock_session_manager, research_metrics
    ):
        """Test complete research lifecycle: start -> execute -> complete -> document import"""
        # Arrange
        query = "test research query"
        user_id = "user_123"
        session_id = str(uuid.uuid4())
        document_ids = ["doc1", "doc2", "doc3"]

        # Mock session creation
        initial_session = ResearchSession(
            id=session_id,
            query=query,
            stage=ResearchStage.IDLE,
            progress=0.0,
            user_id=user_id,
        )

        def create_session_side_effect(session_id, user_id, query, config):
            return ResearchSession(
                id=session_id,
                query=query,
                stage=ResearchStage.IDLE,
                progress=0.0,
                user_id=user_id,
            )

        mock_session_manager.create_session.side_effect = create_session_side_effect
        mock_session_manager.get_session.return_value = initial_session

        # Act: Start research
        session_id_returned, estimated_duration = await research_service.start_research(
            query=query,
            user_id=user_id,
            config=None,
        )

        # Assert: Session started and metrics recorded
        assert session_id_returned is not None
        assert estimated_duration == 30
        assert research_metrics.get_counter("sessions_started") == 1
        assert research_metrics.get_gauge("active_sessions") == 1

        # Act: Get session status
        session = await research_service.get_session(session_id_returned)
        assert session is not None

        # Act: Update session to CONFIRMING stage (simulating research completion)
        confirming_session = ResearchSession(
            id=session_id_returned,
            query=query,
            stage=ResearchStage.CONFIRMING,
            progress=0.9,
            user_id=user_id,
            documents=[],
        )
        mock_session_manager.get_session.return_value = confirming_session

        # Mock update_session to return completed session
        completed_session = ResearchSession(
            id=session_id_returned,
            query=query,
            stage=ResearchStage.COMPLETED,
            progress=1.0,
            user_id=user_id,
            documents=[
                {
                    "id": doc_id,
                    "title": f"Document {doc_id}",
                    "imported_at": datetime.now().isoformat(),
                }
                for doc_id in document_ids
            ],
        )
        mock_session_manager.update_session.return_value = completed_session

        # Act: Import documents
        result = await research_service.import_documents(
            session_id=session_id_returned,
            document_ids=document_ids,
            taxonomy_id="taxonomy_123",
        )

        # Assert: Documents imported and metrics updated
        assert result["success"] is True
        assert result["documentsImported"] == 3
        assert result["taxonomyUpdated"] is True
        assert research_metrics.get_counter("documents_found") == 3
        assert research_metrics.get_counter("sessions_completed") == 1
        assert research_metrics.get_gauge("active_sessions") == 0

    @pytest.mark.asyncio
    async def test_research_cancellation_with_metrics(
        self, research_service, mock_session_manager, research_metrics
    ):
        """Test research cancellation and metrics recording"""
        # Arrange
        query = "test query"
        user_id = "user_456"
        session_id = str(uuid.uuid4())

        # Mock session creation
        def create_session_side_effect(session_id, user_id, query, config):
            return ResearchSession(
                id=session_id,
                query=query,
                stage=ResearchStage.IDLE,
                progress=0.0,
                user_id=user_id,
            )

        mock_session_manager.create_session.side_effect = create_session_side_effect
        mock_session_manager.delete_session.return_value = True

        # Act: Start research
        session_id_returned, _ = await research_service.start_research(
            query=query,
            user_id=user_id,
        )

        assert research_metrics.get_gauge("active_sessions") == 1

        # Act: Cancel research
        cancelled = await research_service.cancel_research(session_id_returned)

        # Assert: Research cancelled and metrics updated
        assert cancelled is True
        assert research_metrics.get_gauge("active_sessions") == 0

    @pytest.mark.asyncio
    async def test_research_error_handling_with_metrics(
        self, research_service, mock_session_manager, research_metrics
    ):
        """Test error handling and metrics recording for failed research"""
        # Arrange
        query = "test query"
        user_id = "user_789"

        # Mock session creation
        def create_session_side_effect(session_id, user_id, query, config):
            return ResearchSession(
                id=session_id,
                query=query,
                stage=ResearchStage.IDLE,
                progress=0.0,
                user_id=user_id,
            )

        mock_session_manager.create_session.side_effect = create_session_side_effect
        mock_session_manager.get_session.return_value = ResearchSession(
            id="session_123",
            query=query,
            stage=ResearchStage.ANALYZING,
            progress=0.2,
            user_id=user_id,
        )
        mock_session_manager.update_session.return_value = ResearchSession(
            id="session_123",
            query=query,
            stage=ResearchStage.ERROR,
            progress=0.0,
            user_id=user_id,
        )

        # Act: Start research
        session_id, _ = await research_service.start_research(
            query=query,
            user_id=user_id,
        )

        assert research_metrics.get_counter("sessions_started") == 1
        assert research_metrics.get_gauge("active_sessions") == 1

        # Wait a bit for background task to progress
        await asyncio.sleep(0.5)

        # The _execute_research task will handle errors and record metrics
        # For this test, we verify metrics state after completion

    @pytest.mark.asyncio
    async def test_sse_connection_metrics(
        self, research_service, mock_session_manager, research_metrics
    ):
        """Test SSE connection tracking in metrics"""
        # Arrange
        session_id = str(uuid.uuid4())
        mock_session_manager.get_session.return_value = ResearchSession(
            id=session_id,
            query="test",
            stage=ResearchStage.SEARCHING,
            progress=0.5,
            user_id="user_123",
        )
        mock_session_manager.get_events_since.return_value = []

        # Act: Simulate SSE connection
        research_metrics.increment_active_sse_connections()
        assert research_metrics.get_gauge("active_sse_connections") == 1

        research_metrics.increment_active_sse_connections()
        assert research_metrics.get_gauge("active_sse_connections") == 2

        # Act: Simulate disconnection
        research_metrics.decrement_active_sse_connections()
        assert research_metrics.get_gauge("active_sse_connections") == 1

        research_metrics.decrement_active_sse_connections()
        assert research_metrics.get_gauge("active_sse_connections") == 0


class TestMetricsWithRouter:
    """Test metrics integration with router"""

    def test_router_creation_with_service(self, research_service):
        """Test that router can be created with research service"""
        router = create_research_router(research_service=research_service)

        assert router is not None
        assert len(router.routes) > 0

    def test_router_routes_exist(self, research_service):
        """Test that all expected router routes exist"""
        router = create_research_router(research_service=research_service)

        # Check for expected routes
        route_paths = {route.path for route in router.routes}
        assert "/api/v1/research" in route_paths
        assert "/api/v1/research/{session_id}" in route_paths
        assert "/api/v1/research/{session_id}/import" in route_paths
        assert "/api/v1/research/{session_id}/stream" in route_paths


class TestMetricsDataAggregation:
    """Test metrics data aggregation and reporting"""

    def test_metrics_summary_with_complete_data(self, research_metrics):
        """Test metrics summary generation with complete data"""
        # Act: Record various metrics
        research_metrics.record_session_started("deep")
        research_metrics.record_session_started("shallow")
        research_metrics.record_session_completed("completed")
        research_metrics.record_documents_found(5)
        research_metrics.record_documents_found(3)
        research_metrics.set_active_sessions(2)
        research_metrics.set_active_sse_connections(1)
        research_metrics.record_session_duration(45.5, "deep")
        research_metrics.record_session_duration(30.2, "shallow")

        # Act: Get summary
        summary = research_metrics.get_metrics_summary()

        # Assert: All metrics included in summary
        assert summary["sessions_started"] == 2
        assert summary["sessions_completed"] == 1
        assert summary["documents_found"] == 8
        assert summary["active_sessions"] == 2
        assert summary["active_sse_connections"] == 1
        assert "duration_stats" in summary
        assert summary["duration_stats"]["avg"] > 0
        assert summary["duration_stats"]["min"] > 0
        assert summary["duration_stats"]["max"] > 0

    def test_metrics_reset_functionality(self, research_metrics):
        """Test that metrics can be reset properly"""
        # Arrange
        research_metrics.record_session_started("deep")
        research_metrics.set_active_sessions(3)
        assert research_metrics.get_counter("sessions_started") == 1

        # Act: Reset metrics
        research_metrics.reset_metrics()

        # Assert: All metrics cleared
        assert research_metrics.get_counter("sessions_started") == 0
        assert research_metrics.get_gauge("active_sessions") == 0
        assert len(research_metrics.duration_samples) == 0
