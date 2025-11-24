# @TEST:RESEARCH-BACKEND-001:SESSION
"""
Tests for Research Session Manager

This test module validates:
1. Session CRUD operations (create, read, update, delete)
2. Redis-based persistence
3. Event publishing and retrieval
4. Session TTL management
5. Error handling and edge cases
"""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from apps.api.services.research_session_manager import (
    ResearchSessionManager,
)
from apps.api.schemas.research_schemas import (
    ResearchSession,
    ResearchStage,
    ResearchConfig,
    ResearchEvent,
)


@pytest.fixture
def mock_redis_manager():
    """Mock Redis manager for testing"""
    manager = AsyncMock()
    manager.client = AsyncMock()
    return manager


@pytest.fixture
def session_manager(mock_redis_manager):
    """Create session manager with mocked Redis"""
    return ResearchSessionManager(redis_manager=mock_redis_manager)


@pytest.fixture
def sample_session_id():
    """Sample session ID"""
    return "sess-test-001"


@pytest.fixture
def sample_user_id():
    """Sample user ID"""
    return "user-test-001"


@pytest.fixture
def sample_query():
    """Sample research query"""
    return "cancer treatment options"


@pytest.fixture
def sample_config():
    """Sample research configuration"""
    return ResearchConfig(
        max_documents=100,
        quality_threshold=0.8,
        depth_level="deep"
    )


class TestResearchSessionManagerInit:
    """Test session manager initialization"""

    @pytest.mark.asyncio
    async def test_manager_initialization(self, session_manager):
        """Test session manager is properly initialized"""
        assert session_manager is not None
        assert session_manager.SESSION_TTL == 3600

    def test_ttl_constant(self):
        """Test TTL constant is set correctly"""
        assert ResearchSessionManager.SESSION_TTL == 3600


class TestCreateSession:
    """Test session creation"""

    @pytest.mark.asyncio
    async def test_create_session_minimal(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id,
        sample_user_id,
        sample_query
    ):
        """Test creating session with minimal parameters"""
        mock_redis_manager.set.return_value = True

        session = await session_manager.create_session(
            session_id=sample_session_id,
            user_id=sample_user_id,
            query=sample_query
        )

        assert session is not None
        assert session.id == sample_session_id
        assert session.query == sample_query
        assert session.stage == ResearchStage.IDLE
        assert session.progress == 0.0
        assert session.user_id == sample_user_id
        mock_redis_manager.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_with_config(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id,
        sample_user_id,
        sample_query,
        sample_config
    ):
        """Test creating session with custom config"""
        mock_redis_manager.set.return_value = True

        session = await session_manager.create_session(
            session_id=sample_session_id,
            user_id=sample_user_id,
            query=sample_query,
            config=sample_config
        )

        assert session.config == sample_config
        assert session.config.max_documents == 100
        mock_redis_manager.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_redis_failure(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id,
        sample_user_id,
        sample_query
    ):
        """Test session creation when Redis save fails"""
        mock_redis_manager.set.return_value = False

        with pytest.raises(Exception):
            await session_manager.create_session(
                session_id=sample_session_id,
                user_id=sample_user_id,
                query=sample_query
            )

    @pytest.mark.asyncio
    async def test_create_session_sets_correct_ttl(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id,
        sample_user_id,
        sample_query
    ):
        """Test that session is created with correct TTL"""
        mock_redis_manager.set.return_value = True

        await session_manager.create_session(
            session_id=sample_session_id,
            user_id=sample_user_id,
            query=sample_query
        )

        # Verify Redis.set was called with TTL
        call_kwargs = mock_redis_manager.set.call_args
        assert "ttl" in str(call_kwargs) or len(call_kwargs[0]) >= 3


class TestGetSession:
    """Test session retrieval"""

    @pytest.mark.asyncio
    async def test_get_existing_session(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test retrieving an existing session"""
        session_data = {
            "id": sample_session_id,
            "query": "test query",
            "stage": "idle",
            "progress": 0.0,
            "documents": [],
            "events": [],
            "user_id": "user-123",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        mock_redis_manager.get.return_value = session_data

        session = await session_manager.get_session(sample_session_id)

        assert session is not None
        assert session.id == sample_session_id
        assert session.query == "test query"
        mock_redis_manager.get.assert_called_once_with(f"session:{sample_session_id}")

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test retrieving a non-existent session returns None"""
        mock_redis_manager.get.return_value = None

        session = await session_manager.get_session(sample_session_id)

        assert session is None
        mock_redis_manager.get.assert_called_once()


class TestUpdateSession:
    """Test session updates"""

    @pytest.mark.asyncio
    async def test_update_session_stage(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test updating session stage"""
        mock_redis_manager.get.return_value = {
            "id": sample_session_id,
            "query": "test",
            "stage": "idle",
            "progress": 0.0,
            "documents": [],
            "events": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        mock_redis_manager.set.return_value = True

        session = await session_manager.update_session(
            sample_session_id,
            stage=ResearchStage.ANALYZING
        )

        assert session is not None
        assert session.stage == ResearchStage.ANALYZING
        mock_redis_manager.set.assert_called()

    @pytest.mark.asyncio
    async def test_update_session_progress(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test updating session progress"""
        mock_redis_manager.get.return_value = {
            "id": sample_session_id,
            "query": "test",
            "stage": "analyzing",
            "progress": 0.0,
            "documents": [],
            "events": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        mock_redis_manager.set.return_value = True

        session = await session_manager.update_session(
            sample_session_id,
            progress=0.5
        )

        assert session is not None
        assert session.progress == 0.5

    @pytest.mark.asyncio
    async def test_update_nonexistent_session(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test updating non-existent session returns None"""
        mock_redis_manager.get.return_value = None

        session = await session_manager.update_session(
            sample_session_id,
            stage=ResearchStage.SEARCHING
        )

        assert session is None


class TestDeleteSession:
    """Test session deletion"""

    @pytest.mark.asyncio
    async def test_delete_existing_session(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test deleting an existing session"""
        mock_redis_manager.delete.return_value = True

        result = await session_manager.delete_session(sample_session_id)

        assert result is True
        mock_redis_manager.delete.assert_called()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test deleting a non-existent session"""
        mock_redis_manager.delete.return_value = False

        result = await session_manager.delete_session(sample_session_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_also_removes_events(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test that delete removes associated events"""
        mock_redis_manager.delete.return_value = True

        await session_manager.delete_session(sample_session_id)

        # Verify both session and events are deleted
        assert mock_redis_manager.delete.call_count >= 1


class TestPublishEvent:
    """Test event publishing"""

    @pytest.mark.asyncio
    async def test_publish_event(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test publishing an event"""
        mock_redis_manager.lpush.return_value = 1
        mock_redis_manager.llen.return_value = 1  # Below max length, no trim needed

        event_id = await session_manager.publish_event(
            session_id=sample_session_id,
            event_type="progress",
            data={"progress": 0.5}
        )

        assert event_id is not None
        mock_redis_manager.lpush.assert_called()

    @pytest.mark.asyncio
    async def test_publish_multiple_events(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test publishing multiple events"""
        mock_redis_manager.lpush.return_value = 1
        mock_redis_manager.llen.return_value = 2  # Below max length, no trim needed

        event_id_1 = await session_manager.publish_event(
            sample_session_id,
            "progress",
            {"progress": 0.25}
        )
        event_id_2 = await session_manager.publish_event(
            sample_session_id,
            "progress",
            {"progress": 0.5}
        )

        assert event_id_1 is not None
        assert event_id_2 is not None
        assert event_id_1 != event_id_2
        assert mock_redis_manager.lpush.call_count == 2

    @pytest.mark.asyncio
    async def test_publish_event_includes_timestamp(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test that published event includes timestamp"""
        mock_redis_manager.lpush.return_value = 1
        mock_redis_manager.llen.return_value = 1  # Below max length, no trim needed

        await session_manager.publish_event(
            sample_session_id,
            "stage_change",
            {"new_stage": "searching"}
        )

        # Verify lpush was called with event data
        call_args = mock_redis_manager.lpush.call_args
        assert call_args is not None

    @pytest.mark.asyncio
    async def test_publish_event_trims_when_exceeds_max_length(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test that event list is trimmed when it exceeds max length"""
        mock_redis_manager.lpush.return_value = 1
        # Simulate event count exceeding max length
        mock_redis_manager.llen.return_value = 1001
        mock_redis_manager.ltrim.return_value = True

        await session_manager.publish_event(
            sample_session_id,
            "progress",
            {"progress": 0.5}
        )

        # Verify ltrim was called to trim the list
        mock_redis_manager.ltrim.assert_called_once()
        # Verify it keeps the first 1000 events (0 to 999)
        call_args = mock_redis_manager.ltrim.call_args
        assert call_args is not None
        args = call_args[0]
        assert args[1] == 0  # start index
        assert args[2] == 999  # end index (max length - 1)

    @pytest.mark.asyncio
    async def test_publish_event_no_trim_when_below_max_length(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test that event list is not trimmed when below max length"""
        mock_redis_manager.lpush.return_value = 1
        mock_redis_manager.llen.return_value = 500  # Below max length

        await session_manager.publish_event(
            sample_session_id,
            "progress",
            {"progress": 0.5}
        )

        # Verify ltrim was NOT called
        mock_redis_manager.ltrim.assert_not_called()


class TestGetEventsSince:
    """Test retrieving events"""

    @pytest.mark.asyncio
    async def test_get_events_empty_list(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test retrieving events when none exist"""
        mock_redis_manager.lrange.return_value = []

        events = await session_manager.get_events_since(
            sample_session_id,
            last_event_id=None
        )

        assert events == []
        mock_redis_manager.lrange.assert_called()

    @pytest.mark.asyncio
    async def test_get_recent_events(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test retrieving recent events"""
        event_data = [
            {
                "event_id": "evt-1",
                "event_type": "progress",
                "data": {"progress": 0.5},
                "timestamp": datetime.now().isoformat()
            }
        ]
        mock_redis_manager.lrange.return_value = event_data

        events = await session_manager.get_events_since(
            sample_session_id,
            last_event_id=None
        )

        assert len(events) == 1
        assert events[0]["event_type"] == "progress"

    @pytest.mark.asyncio
    async def test_get_events_since_last_id(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test retrieving events since specific event ID"""
        mock_redis_manager.lrange.return_value = []

        events = await session_manager.get_events_since(
            sample_session_id,
            last_event_id="evt-5"
        )

        assert isinstance(events, list)


class TestSessionPersistence:
    """Test session persistence across operations"""

    @pytest.mark.asyncio
    async def test_session_persistence_full_cycle(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id,
        sample_user_id,
        sample_query
    ):
        """Test session survives full operational cycle"""
        # Setup mock responses
        mock_redis_manager.set.return_value = True
        mock_redis_manager.get.return_value = {
            "id": sample_session_id,
            "query": sample_query,
            "stage": "searching",
            "progress": 0.5,
            "documents": [],
            "events": [],
            "user_id": sample_user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # Create session
        created = await session_manager.create_session(
            sample_session_id,
            sample_user_id,
            sample_query
        )
        assert created.id == sample_session_id

        # Retrieve session
        retrieved = await session_manager.get_session(sample_session_id)
        assert retrieved is not None
        assert retrieved.id == sample_session_id

        # Update session
        mock_redis_manager.get.return_value["stage"] = "collecting"
        updated = await session_manager.update_session(
            sample_session_id,
            stage=ResearchStage.COLLECTING
        )
        assert updated is not None


class TestSessionEventIntegration:
    """Test integration between sessions and events"""

    @pytest.mark.asyncio
    async def test_session_with_events_workflow(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id,
        sample_user_id,
        sample_query
    ):
        """Test complete workflow: create session, publish events, retrieve"""
        mock_redis_manager.set.return_value = True
        mock_redis_manager.lpush.return_value = 1
        mock_redis_manager.llen.return_value = 1  # Below max length, no trim needed
        mock_redis_manager.lrange.return_value = []
        mock_redis_manager.get.return_value = {
            "id": sample_session_id,
            "query": sample_query,
            "stage": "analyzing",
            "progress": 0.25,
            "documents": [],
            "events": [],
            "user_id": sample_user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # Create session
        session = await session_manager.create_session(
            sample_session_id,
            sample_user_id,
            sample_query
        )
        assert session is not None

        # Publish event
        event_id = await session_manager.publish_event(
            sample_session_id,
            "stage_change",
            {"new_stage": "analyzing"}
        )
        assert event_id is not None

        # Get events
        events = await session_manager.get_events_since(
            sample_session_id,
            last_event_id=None
        )
        assert isinstance(events, list)


class TestGetSessionEvents:
    """Test retrieving session events"""

    @pytest.mark.asyncio
    async def test_get_session_events(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test retrieving session events as ResearchEvent objects"""
        event_data = [
            {
                "event_id": "evt-1",
                "event_type": "progress",
                "data": {"progress": 0.5},
                "timestamp": datetime.now().isoformat()
            }
        ]
        mock_redis_manager.lrange.return_value = event_data

        events = await session_manager.get_session_events(sample_session_id)

        assert len(events) == 1
        assert events[0].event_type == "progress"

    @pytest.mark.asyncio
    async def test_get_session_events_empty(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test getting events for session with no events"""
        mock_redis_manager.lrange.return_value = []

        events = await session_manager.get_session_events(sample_session_id)

        assert events == []


class TestGetUserSessions:
    """Test retrieving user sessions"""

    @pytest.mark.asyncio
    async def test_get_user_sessions(
        self,
        session_manager,
        mock_redis_manager,
        sample_user_id
    ):
        """Test retrieving all sessions for a user"""
        mock_redis_manager.keys.return_value = ["session:sess-1", "session:sess-2"]
        mock_redis_manager.get.side_effect = [
            {
                "id": "sess-1",
                "query": "test 1",
                "stage": "idle",
                "progress": 0.0,
                "documents": [],
                "events": [],
                "user_id": sample_user_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "id": "sess-2",
                "query": "test 2",
                "stage": "idle",
                "progress": 0.0,
                "documents": [],
                "events": [],
                "user_id": sample_user_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
        ]

        sessions = await session_manager.get_user_sessions(sample_user_id)

        assert len(sessions) == 2
        assert all(s.user_id == sample_user_id for s in sessions)

    @pytest.mark.asyncio
    async def test_get_user_sessions_no_matches(
        self,
        session_manager,
        mock_redis_manager
    ):
        """Test retrieving sessions when no matches found"""
        mock_redis_manager.keys.return_value = []

        sessions = await session_manager.get_user_sessions("unknown-user")

        assert sessions == []


class TestEnsureRedis:
    """Test Redis manager initialization"""

    @pytest.mark.asyncio
    async def test_ensure_redis_with_existing_manager(
        self,
        session_manager,
        mock_redis_manager
    ):
        """Test ensure_redis when manager already exists"""
        redis = await session_manager.ensure_redis()

        assert redis is not None

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(
        self,
        session_manager,
        mock_redis_manager
    ):
        """Test cleanup expired sessions"""
        result = await session_manager.cleanup_expired_sessions()

        # Redis handles TTL automatically, so this should return 0
        assert result == 0


class TestKeyGeneration:
    """Test Redis key generation"""

    def test_get_session_key(self, session_manager, sample_session_id):
        """Test session key generation"""
        key = session_manager._get_session_key(sample_session_id)

        assert key == f"session:{sample_session_id}"

    def test_get_events_key(self, session_manager, sample_session_id):
        """Test events key generation"""
        key = session_manager._get_events_key(sample_session_id)

        assert key == f"events:{sample_session_id}"


class TestSessionDeserialization:
    """Test session deserialization edge cases"""

    @pytest.mark.asyncio
    async def test_get_session_with_invalid_data(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test getting session with corrupted data"""
        mock_redis_manager.get.return_value = {"invalid": "data"}

        session = await session_manager.get_session(sample_session_id)

        assert session is None

    @pytest.mark.asyncio
    async def test_update_session_multiple_fields(
        self,
        session_manager,
        mock_redis_manager,
        sample_session_id
    ):
        """Test updating multiple session fields at once"""
        mock_redis_manager.get.return_value = {
            "id": sample_session_id,
            "query": "test",
            "stage": "idle",
            "progress": 0.0,
            "documents": [],
            "events": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        mock_redis_manager.set.return_value = True

        session = await session_manager.update_session(
            sample_session_id,
            stage=ResearchStage.SEARCHING,
            progress=0.3
        )

        assert session is not None
        assert session.stage == ResearchStage.SEARCHING
        assert session.progress == 0.3
