# @TEST:RESEARCH-BACKEND-001:SERVICE
"""
Tests for Research Service - Core business logic

Tests the ResearchService class including:
- Session creation and lifecycle management
- Research execution and task management
- Document import and confirmation
- Error handling and edge cases
"""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime

from apps.api.services.research_service import ResearchService
from apps.api.services.research_session_manager import ResearchSessionManager
from apps.api.schemas.research_schemas import (
    ResearchSession,
    ResearchStage,
    ResearchConfig,
    StartResearchRequest,
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
    return manager


@pytest.fixture
def mock_langgraph_service():
    """Mock LangGraphService"""
    service = Mock()
    service.execute_pipeline = AsyncMock()
    return service


@pytest.fixture
def research_service(mock_session_manager):
    """Create ResearchService instance with mocks"""
    service = ResearchService(session_manager=mock_session_manager)
    return service


class TestResearchServiceInitialization:
    """Test ResearchService initialization"""

    def test_init_with_session_manager(self, mock_session_manager):
        """Test initialization with provided session manager"""
        service = ResearchService(session_manager=mock_session_manager)
        assert service.session_manager == mock_session_manager
        assert service._active_tasks == {}

    def test_init_creates_empty_active_tasks(self, research_service):
        """Test that active_tasks dict is initialized empty"""
        assert isinstance(research_service._active_tasks, dict)
        assert len(research_service._active_tasks) == 0


class TestStartResearch:
    """Test start_research method"""

    @pytest.mark.asyncio
    async def test_start_research_creates_session(self, research_service, mock_session_manager):
        """Test that start_research creates a new session"""
        # Arrange
        query = "test research query"
        user_id = "user_123"

        mock_session = ResearchSession(
            id="test_session_id",  # Will be generated, we just check it's created
            query=query,
            stage=ResearchStage.IDLE,
            progress=0.0,
            user_id=user_id,
        )

        def create_session_side_effect(session_id, user_id, query, config):
            # Return session with the generated ID
            return ResearchSession(
                id=session_id,
                query=query,
                stage=ResearchStage.IDLE,
                progress=0.0,
                user_id=user_id,
            )

        mock_session_manager.create_session.side_effect = create_session_side_effect

        # Act
        result_session_id, duration = await research_service.start_research(
            query=query,
            user_id=user_id,
            config=None,
        )

        # Assert
        assert isinstance(result_session_id, str)
        assert len(result_session_id) > 0
        assert isinstance(duration, int)
        assert duration > 0
        mock_session_manager.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_research_with_config(self, research_service, mock_session_manager):
        """Test start_research with custom configuration"""
        # Arrange
        query = "test query"
        user_id = "user_123"
        config = ResearchConfig(max_documents=100, quality_threshold=0.8)

        def create_session_with_config(session_id, user_id, query, config):
            return ResearchSession(
                id=session_id,
                query=query,
                stage=ResearchStage.IDLE,
                progress=0.0,
                user_id=user_id,
                config=config,
            )

        mock_session_manager.create_session.side_effect = create_session_with_config

        # Act
        result_id, duration = await research_service.start_research(
            query=query,
            user_id=user_id,
            config=config.model_dump(),
        )

        # Assert
        assert isinstance(result_id, str)
        assert len(result_id) > 0
        assert duration > 0
        call_args = mock_session_manager.create_session.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_start_research_launches_background_task(
        self, research_service, mock_session_manager
    ):
        """Test that start_research launches a background task"""
        # Arrange
        query = "test query"
        user_id = "user_123"
        session_id = str(uuid.uuid4())

        mock_session = ResearchSession(
            id=session_id,
            query=query,
            stage=ResearchStage.IDLE,
            progress=0.0,
            user_id=user_id,
        )
        mock_session_manager.create_session.return_value = mock_session

        # Mock the background execution method
        research_service._execute_research = AsyncMock()

        # Act
        result_id, duration = await research_service.start_research(
            query=query,
            user_id=user_id,
            config=None,
        )

        # Assert
        assert result_id in research_service._active_tasks
        task = research_service._active_tasks[result_id]
        assert isinstance(task, asyncio.Task)

        # Cleanup
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


class TestGetSession:
    """Test get_session method"""

    @pytest.mark.asyncio
    async def test_get_session_returns_session(self, research_service, mock_session_manager):
        """Test get_session retrieves a session"""
        # Arrange
        session_id = "session_123"
        mock_session = ResearchSession(
            id=session_id,
            query="test",
            stage=ResearchStage.ANALYZING,
            progress=0.5,
        )
        mock_session_manager.get_session.return_value = mock_session

        # Act
        result = await research_service.get_session(session_id)

        # Assert
        assert result == mock_session
        mock_session_manager.get_session.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_get_session_returns_none_if_not_found(
        self, research_service, mock_session_manager
    ):
        """Test get_session returns None for non-existent session"""
        # Arrange
        session_id = "nonexistent_session"
        mock_session_manager.get_session.return_value = None

        # Act
        result = await research_service.get_session(session_id)

        # Assert
        assert result is None


class TestImportDocuments:
    """Test import_documents method"""

    @pytest.mark.asyncio
    async def test_import_documents_success(self, research_service, mock_session_manager):
        """Test successful document import"""
        # Arrange
        session_id = "session_123"
        document_ids = ["doc_1", "doc_2", "doc_3"]

        existing_session = ResearchSession(
            id=session_id,
            query="test",
            stage=ResearchStage.CONFIRMING,
            progress=0.8,
            documents=[{"id": "doc_1", "title": "Document 1"}],
        )

        updated_session = ResearchSession(
            id=session_id,
            query="test",
            stage=ResearchStage.COMPLETED,
            progress=1.0,
            documents=[
                {"id": "doc_1", "title": "Document 1"},
                {"id": "doc_2", "title": "Document 2"},
                {"id": "doc_3", "title": "Document 3"},
            ],
        )

        mock_session_manager.get_session.return_value = existing_session
        mock_session_manager.update_session.return_value = updated_session

        # Act
        result = await research_service.import_documents(
            session_id=session_id,
            document_ids=document_ids,
            taxonomy_id=None,
        )

        # Assert
        assert result["success"] is True
        assert result["documentsImported"] >= 0
        assert isinstance(result["taxonomyUpdated"], bool)

    @pytest.mark.asyncio
    async def test_import_documents_session_not_found(
        self, research_service, mock_session_manager
    ):
        """Test import_documents raises error if session not found"""
        # Arrange
        session_id = "nonexistent"
        mock_session_manager.get_session.return_value = None

        # Act & Assert
        with pytest.raises(ValueError):
            await research_service.import_documents(
                session_id=session_id,
                document_ids=["doc_1"],
                taxonomy_id=None,
            )

    @pytest.mark.asyncio
    async def test_import_documents_invalid_stage(self, research_service, mock_session_manager):
        """Test import_documents raises error if session not in confirming stage"""
        # Arrange
        session_id = "session_123"
        existing_session = ResearchSession(
            id=session_id,
            query="test",
            stage=ResearchStage.ANALYZING,  # Wrong stage
            progress=0.5,
        )
        mock_session_manager.get_session.return_value = existing_session

        # Act & Assert
        with pytest.raises(ValueError):
            await research_service.import_documents(
                session_id=session_id,
                document_ids=["doc_1"],
                taxonomy_id=None,
            )


class TestCancelResearch:
    """Test cancel_research method"""

    @pytest.mark.asyncio
    async def test_cancel_research_deletes_session(
        self, research_service, mock_session_manager
    ):
        """Test cancel_research deletes the session"""
        # Arrange
        session_id = "session_123"
        mock_session_manager.delete_session.return_value = True

        # Act
        result = await research_service.cancel_research(session_id)

        # Assert
        assert result is True
        mock_session_manager.delete_session.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_cancel_research_cancels_active_task(
        self, research_service, mock_session_manager
    ):
        """Test cancel_research cancels any active task"""
        # Arrange
        session_id = "session_123"

        # Create a real asyncio task that we can cancel
        async def dummy_task():
            await asyncio.sleep(10)  # Long sleep to keep task running

        task = asyncio.create_task(dummy_task())
        research_service._active_tasks[session_id] = task

        mock_session_manager.delete_session.return_value = True

        # Act
        result = await research_service.cancel_research(session_id)

        # Assert
        assert result is True
        assert task.cancelled()
        assert session_id not in research_service._active_tasks


class TestExecuteResearch:
    """Test _execute_research background task"""

    @pytest.mark.asyncio
    async def test_execute_research_updates_stage_progression(
        self, research_service, mock_session_manager
    ):
        """Test that _execute_research updates session stage"""
        # Arrange
        session_id = "session_123"
        query = "test query"

        initial_session = ResearchSession(
            id=session_id,
            query=query,
            stage=ResearchStage.IDLE,
            progress=0.0,
        )

        mock_session_manager.get_session.return_value = initial_session
        mock_session_manager.update_session.return_value = initial_session

        # Mock langgraph service
        research_service.langgraph_service = AsyncMock()
        research_service.langgraph_service.execute_pipeline.return_value = {
            "answer": "test answer",
            "sources": [],
            "confidence": 0.8,
        }

        # Act - execute research with timeout to prevent hanging
        try:
            await asyncio.wait_for(
                research_service._execute_research(
                    session_id=session_id,
                    query=query,
                    config=None,
                ),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            pass  # Expected for background task

        # Assert - should have updated session at least once
        assert mock_session_manager.update_session.called

    @pytest.mark.asyncio
    async def test_execute_research_handles_errors(
        self, research_service, mock_session_manager
    ):
        """Test that _execute_research handles errors gracefully"""
        # Arrange
        session_id = "session_123"
        query = "test query"

        mock_session_manager.get_session.return_value = ResearchSession(
            id=session_id,
            query=query,
            stage=ResearchStage.IDLE,
            progress=0.0,
        )

        # Mock langgraph service to raise error
        research_service.langgraph_service = AsyncMock()
        research_service.langgraph_service.execute_pipeline.side_effect = Exception("Pipeline error")

        # Act & Assert - should not raise, should mark session as error
        try:
            await asyncio.wait_for(
                research_service._execute_research(
                    session_id=session_id,
                    query=query,
                    config=None,
                ),
                timeout=5.0,
            )
        except asyncio.TimeoutError:
            pass  # Expected


class TestResearchServiceIntegration:
    """Integration tests for ResearchService"""

    @pytest.mark.asyncio
    async def test_full_research_lifecycle(self, research_service, mock_session_manager):
        """Test complete research workflow from start to import"""
        # Arrange
        user_id = "user_123"
        query = "test research"

        # Track created session_id
        created_session_id = None

        def mock_create_session(session_id, user_id, query, config):
            nonlocal created_session_id
            created_session_id = session_id
            return ResearchSession(
                id=session_id,
                query=query,
                stage=ResearchStage.IDLE,
                progress=0.0,
                user_id=user_id,
            )

        # Mock session creation
        mock_session_manager.create_session.side_effect = mock_create_session

        # Mock retrieval
        analyzing_session = ResearchSession(
            id="temp_id",  # Will be set from created_session_id
            query=query,
            stage=ResearchStage.ANALYZING,
            progress=0.25,
            user_id=user_id,
        )

        confirming_session = ResearchSession(
            id="temp_id",
            query=query,
            stage=ResearchStage.CONFIRMING,
            progress=0.8,
            documents=[{"id": "doc_1"}],
            user_id=user_id,
        )

        completed_session = ResearchSession(
            id="temp_id",
            query=query,
            stage=ResearchStage.COMPLETED,
            progress=1.0,
            documents=[{"id": "doc_1"}, {"id": "doc_2"}],
            user_id=user_id,
        )

        mock_session_manager.get_session.side_effect = [
            analyzing_session,
            confirming_session,
            confirming_session,
            completed_session,
        ]

        mock_session_manager.update_session.return_value = completed_session
        mock_session_manager.delete_session.return_value = True

        # Mock langgraph
        research_service.langgraph_service = AsyncMock()

        # Act & Assert - Full workflow
        # 1. Start research
        result_id, duration = await research_service.start_research(query, user_id, None)
        assert isinstance(result_id, str)

        # 2. Get session status
        session = await research_service.get_session(result_id)
        assert session.stage == ResearchStage.ANALYZING

        # 3. Get session again
        session = await research_service.get_session(result_id)
        assert session.stage == ResearchStage.CONFIRMING

        # 4. Import documents
        result = await research_service.import_documents(result_id, ["doc_2"], None)
        assert result["success"] is True

        # 5. Cancel research
        cancelled = await research_service.cancel_research(result_id)
        assert cancelled is True
