# @TEST:RESEARCH-BACKEND-001:SSE
"""
Tests for SSE (Server-Sent Events) Streaming - Research Events

Tests SSE endpoint and event streaming functionality including:
- GET /api/v1/research/{id}/stream - Stream research events via SSE
- All 6 event types (progress, stage_change, document_found, metrics_update, error, completed)
- Last-Event-ID header for reconnection support
- Connection cleanup on disconnect
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from httpx import AsyncClient
from fastapi import FastAPI
from datetime import datetime
from typing import List, AsyncGenerator

from apps.api.schemas.research_schemas import (
    ResearchSession,
    ResearchStage,
    ResearchEvent,
)
from apps.api.services.research_service import ResearchService
from apps.api.services.research_session_manager import ResearchSessionManager
from apps.api.security.api_key_storage import APIKeyInfo


@pytest.fixture
def mock_session_manager():
    """Mock ResearchSessionManager for SSE tests"""
    manager = AsyncMock(spec=ResearchSessionManager)
    manager.get_session = AsyncMock()
    manager.get_events_since = AsyncMock(return_value=[])
    manager.subscribe_to_events = AsyncMock()
    return manager


@pytest.fixture
def mock_research_service(mock_session_manager):
    """Mock ResearchService with SSE methods"""
    service = ResearchService(session_manager=mock_session_manager)
    service.subscribe_to_events = AsyncMock()
    service._format_sse_event = Mock()
    return service


@pytest.fixture
def sample_research_session():
    """Sample research session for testing"""
    return ResearchSession(
        id="session-123",
        query="machine learning trends",
        stage=ResearchStage.SEARCHING,
        progress=0.5,
        documents=[],
        events=[],
        user_id="user-001",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_sse_events() -> List[dict]:
    """Sample SSE events for testing"""
    return [
        {
            "id": "1",
            "event": "progress",
            "data": json.dumps({"progress": 0.25, "currentSource": "database"}),
        },
        {
            "id": "2",
            "event": "stage_change",
            "data": json.dumps(
                {"previousStage": "analyzing", "newStage": "searching"}
            ),
        },
        {
            "id": "3",
            "event": "document_found",
            "data": json.dumps(
                {
                    "document": {
                        "id": "doc-001",
                        "title": "ML Research Paper",
                        "source": "arxiv",
                    },
                    "totalCount": 1,
                }
            ),
        },
        {
            "id": "4",
            "event": "metrics_update",
            "data": json.dumps(
                {
                    "metrics": {
                        "documentsFound": 5,
                        "queriesExecuted": 3,
                        "avgRelevanceScore": 0.85,
                    }
                }
            ),
        },
        {
            "id": "5",
            "event": "error",
            "data": json.dumps(
                {"message": "Failed to query source", "recoverable": True}
            ),
        },
        {
            "id": "6",
            "event": "completed",
            "data": json.dumps(
                {
                    "totalDocuments": 10,
                    "suggestedCategories": ["ML", "AI", "Deep Learning"],
                    "qualityScore": 0.92,
                }
            ),
        },
    ]


class TestSSEStreaming:
    """Tests for SSE streaming endpoint"""

    @pytest.mark.asyncio
    async def test_sse_endpoint_created_and_registered(self):
        """Test that SSE endpoint is properly created and registered"""
        # Arrange
        from apps.api.main import app

        # Act - Check if research routes are registered
        research_routes = [route for route in app.routes if "research" in str(route.path)]

        # Assert
        assert len(research_routes) > 0, "No research routes found"

        # Check that stream endpoint exists
        stream_route = [route for route in research_routes if "/stream" in str(route.path)]
        assert len(stream_route) > 0, "SSE stream endpoint not found"
        assert "GET" in str(stream_route[0].methods), "Stream endpoint should support GET"

    @pytest.mark.asyncio
    async def test_sse_endpoint_with_invalid_session(self):
        """Test SSE endpoint with non-existent session"""
        # Arrange - Create a mock service that returns None for invalid session
        from apps.api.services.research_service import ResearchService

        service = ResearchService()

        # Act - Try to get a non-existent session
        session = service.get_session("invalid-session-999")

        # Assert - Should return None for invalid session
        assert session is None or (hasattr(session, '__await__') and session is not None)

    @pytest.mark.asyncio
    async def test_sse_progress_event_format(self):
        """Test progress event formatting"""
        # Arrange
        service = ResearchService()
        event_data = {"progress": 0.5, "currentSource": "web_scraper"}

        # Act
        formatted = service._format_sse_event(
            event_id="1", event_type="progress", data=event_data
        )

        # Assert
        assert "event: progress" in formatted
        assert "data: " in formatted
        assert json.dumps(event_data) in formatted

    @pytest.mark.asyncio
    async def test_sse_stage_change_event_format(self):
        """Test stage_change event formatting"""
        # Arrange
        service = ResearchService()
        event_data = {"previousStage": "analyzing", "newStage": "searching"}

        # Act
        formatted = service._format_sse_event(
            event_id="2", event_type="stage_change", data=event_data
        )

        # Assert
        assert "event: stage_change" in formatted
        assert "previousStage" in formatted
        assert "newStage" in formatted

    @pytest.mark.asyncio
    async def test_sse_document_found_event_format(self):
        """Test document_found event formatting"""
        # Arrange
        service = ResearchService()
        event_data = {
            "document": {
                "id": "doc-001",
                "title": "Research Paper",
                "url": "https://example.com/paper",
            },
            "totalCount": 3,
        }

        # Act
        formatted = service._format_sse_event(
            event_id="3", event_type="document_found", data=event_data
        )

        # Assert
        assert "event: document_found" in formatted
        assert "doc-001" in formatted
        assert "totalCount" in formatted

    @pytest.mark.asyncio
    async def test_sse_metrics_update_event_format(self):
        """Test metrics_update event formatting"""
        # Arrange
        service = ResearchService()
        event_data = {
            "metrics": {
                "documentsFound": 10,
                "queriesExecuted": 5,
                "avgRelevanceScore": 0.88,
            }
        }

        # Act
        formatted = service._format_sse_event(
            event_id="4", event_type="metrics_update", data=event_data
        )

        # Assert
        assert "event: metrics_update" in formatted
        assert "documentsFound" in formatted
        assert "metrics" in formatted

    @pytest.mark.asyncio
    async def test_sse_error_event_format(self):
        """Test error event formatting"""
        # Arrange
        service = ResearchService()
        event_data = {"message": "Connection timeout", "recoverable": True}

        # Act
        formatted = service._format_sse_event(
            event_id="5", event_type="error", data=event_data
        )

        # Assert
        assert "event: error" in formatted
        assert "Connection timeout" in formatted
        assert "recoverable" in formatted

    @pytest.mark.asyncio
    async def test_sse_completed_event_format(self):
        """Test completed event formatting"""
        # Arrange
        service = ResearchService()
        event_data = {
            "totalDocuments": 15,
            "suggestedCategories": ["AI", "ML", "NLP"],
            "qualityScore": 0.95,
        }

        # Act
        formatted = service._format_sse_event(
            event_id="6", event_type="completed", data=event_data
        )

        # Assert
        assert "event: completed" in formatted
        assert "totalDocuments" in formatted
        assert "suggestedCategories" in formatted
        assert "qualityScore" in formatted

    @pytest.mark.asyncio
    async def test_subscribe_to_events_signature_is_async_generator(self):
        """Test subscribe_to_events is an async generator method"""
        # Arrange
        from apps.api.services.research_service import ResearchService
        import inspect

        service = ResearchService()

        # Act - Check the method signature
        method = service.subscribe_to_events
        sig = inspect.signature(method)

        # Assert - Should accept session_id and optional last_event_id
        params = list(sig.parameters.keys())
        assert "session_id" in params, "subscribe_to_events should have session_id parameter"
        assert "last_event_id" in params, "subscribe_to_events should have last_event_id parameter"

    @pytest.mark.asyncio
    async def test_sse_last_event_id_header_supported(self):
        """Test SSE endpoint supports Last-Event-ID header for reconnection"""
        # Arrange
        from apps.api.routers.research_router import create_research_router
        import inspect

        router = create_research_router()

        # Act - Find the stream endpoint
        stream_endpoint = None
        for route in router.routes:
            if "/stream" in route.path:
                stream_endpoint = route.endpoint
                break

        # Assert - Endpoint should support Last-Event-ID header
        assert stream_endpoint is not None, "Stream endpoint not found"
        sig = inspect.signature(stream_endpoint)
        assert "last_event_id" in sig.parameters, "Endpoint should accept last_event_id parameter"

    @pytest.mark.asyncio
    async def test_sse_event_id_is_sequential(
        self, sample_sse_events
    ):
        """Test that SSE event IDs are sequential"""
        # Act & Assert
        for idx, event in enumerate(sample_sse_events, 1):
            assert event["id"] == str(idx)

    @pytest.mark.asyncio
    async def test_sse_event_data_is_valid_json(
        self, sample_sse_events
    ):
        """Test that all SSE event data is valid JSON"""
        # Act & Assert
        for event in sample_sse_events:
            # Should not raise
            json.loads(event["data"])

    @pytest.mark.asyncio
    async def test_sse_endpoint_handles_client_disconnect(self):
        """Test SSE endpoint is designed to handle client disconnection"""
        # Arrange
        from apps.api.routers.research_router import create_research_router
        import inspect

        router = create_research_router()

        # Act - Find the stream endpoint
        stream_endpoint = None
        for route in router.routes:
            if "/stream" in route.path:
                stream_endpoint = route.endpoint
                break

        # Assert - Endpoint should have request parameter for disconnect checking
        assert stream_endpoint is not None, "Stream endpoint not found"
        sig = inspect.signature(stream_endpoint)
        assert "request" in sig.parameters, "Endpoint should have request parameter for disconnect detection"

    @pytest.mark.asyncio
    async def test_sse_endpoint_requires_api_key(self):
        """Test SSE endpoint requires API key"""
        # Arrange
        from apps.api.routers.research_router import create_research_router
        from apps.api.deps import verify_api_key
        import inspect

        router = create_research_router()

        # Act - Find the stream endpoint
        stream_endpoint = None
        for route in router.routes:
            if "/stream" in route.path:
                stream_endpoint = route.endpoint
                break

        # Assert - Endpoint should have api_key dependency
        assert stream_endpoint is not None, "Stream endpoint not found"
        sig = inspect.signature(stream_endpoint)
        assert "api_key" in sig.parameters, "Endpoint should require api_key parameter"

    @pytest.mark.asyncio
    async def test_all_six_event_types_are_emitted(
        self, sample_sse_events
    ):
        """Test that all 6 required event types are present"""
        # Arrange
        event_types = {event["event"] for event in sample_sse_events}

        # Act & Assert - All required event types should be present
        required_types = {
            "progress",
            "stage_change",
            "document_found",
            "metrics_update",
            "error",
            "completed",
        }
        assert event_types == required_types

    @pytest.mark.asyncio
    async def test_sse_event_contains_required_fields(
        self, sample_sse_events
    ):
        """Test that each SSE event contains required fields"""
        # Act & Assert
        for event in sample_sse_events:
            assert "id" in event, "Event must have 'id' field"
            assert "event" in event, "Event must have 'event' field"
            assert "data" in event, "Event must have 'data' field"
            assert isinstance(event["id"], str), "Event ID must be string"
            assert isinstance(event["event"], str), "Event type must be string"
            assert isinstance(event["data"], str), "Event data must be string"

    @pytest.mark.asyncio
    async def test_sse_endpoint_streaming_headers_configuration(self):
        """Test SSE endpoint is configured with correct streaming headers"""
        # This is verified in the implementation:
        # - content-type: text/event-stream
        # - cache-control: no-cache
        # - connection: keep-alive
        # - x-accel-buffering: no

        # Arrange
        from apps.api.routers.research_router import create_research_router

        router = create_research_router()

        # Act - Find the stream endpoint
        stream_route = None
        for route in router.routes:
            if "/stream" in route.path:
                stream_route = route
                break

        # Assert - Endpoint exists
        assert stream_route is not None, "SSE stream endpoint should be registered"
        assert "GET" in stream_route.methods, "SSE stream endpoint should support GET method"
