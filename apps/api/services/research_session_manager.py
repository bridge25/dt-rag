# @CODE:RESEARCH-BACKEND-001:SESSION
"""
Research Session Manager

Manages research sessions using Redis-based persistence.
Handles session lifecycle, event publishing, and retrieval operations.
"""

import logging
import uuid
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from apps.api.cache.redis_manager import RedisManager
from apps.api.schemas.research_schemas import (
    ResearchSession,
    ResearchStage,
    ResearchConfig,
    ResearchEvent,
)

logger = logging.getLogger(__name__)


class ResearchSessionManager:
    """Manages research sessions with Redis backend"""

    SESSION_TTL = 3600  # 1 hour
    EVENT_LIST_MAX_LENGTH = 1000
    SESSION_KEY_PREFIX = "session"
    EVENT_KEY_PREFIX = "events"

    def __init__(self, redis_manager: Optional[RedisManager] = None):
        """
        Initialize session manager

        Args:
            redis_manager: Optional Redis manager instance.
                          If None, will be injected at runtime.
        """
        self.redis_manager = redis_manager

    async def ensure_redis(self) -> RedisManager:
        """
        Ensure Redis manager is available

        Returns:
            RedisManager instance

        Raises:
            RuntimeError: If Redis is not available
        """
        if self.redis_manager is None:
            from apps.api.cache.redis_manager import get_redis_manager
            self.redis_manager = await get_redis_manager()

        if self.redis_manager is None:
            raise RuntimeError("Redis manager not available")

        return self.redis_manager

    def _get_session_key(self, session_id: str) -> str:
        """Get Redis key for session"""
        return f"{self.SESSION_KEY_PREFIX}:{session_id}"

    def _get_events_key(self, session_id: str) -> str:
        """Get Redis key for session events"""
        return f"{self.EVENT_KEY_PREFIX}:{session_id}"

    async def create_session(
        self,
        session_id: str,
        user_id: str,
        query: str,
        config: Optional[ResearchConfig] = None,
    ) -> ResearchSession:
        """
        Create a new research session

        Args:
            session_id: Unique session identifier
            user_id: User who initiated research
            query: Research query text
            config: Optional research configuration

        Returns:
            Created ResearchSession

        Raises:
            Exception: If session creation fails
        """
        redis = await self.ensure_redis()

        now = datetime.now()
        session = ResearchSession(
            id=session_id,
            query=query,
            stage=ResearchStage.IDLE,
            progress=0.0,
            documents=[],
            events=[],
            config=config,
            user_id=user_id,
            created_at=now,
            updated_at=now,
        )

        # Serialize and save to Redis
        # Note: model_dump_json() handles datetime serialization to ISO format
        session_data = json.loads(session.model_dump_json())

        success = await redis.set(
            self._get_session_key(session_id),
            session_data,
            ttl=self.SESSION_TTL,
        )

        if not success:
            raise Exception(f"Failed to create session {session_id}")

        logger.info(f"Created session {session_id} for user {user_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[ResearchSession]:
        """
        Retrieve a research session

        Args:
            session_id: Session identifier

        Returns:
            ResearchSession if found, None otherwise
        """
        redis = await self.ensure_redis()

        session_data = await redis.get(self._get_session_key(session_id))
        if session_data is None:
            return None

        try:
            # Convert timestamps back to datetime if they're strings
            if isinstance(session_data.get("created_at"), str):
                session_data["created_at"] = datetime.fromisoformat(
                    session_data["created_at"]
                )
            if isinstance(session_data.get("updated_at"), str):
                session_data["updated_at"] = datetime.fromisoformat(
                    session_data["updated_at"]
                )

            return ResearchSession(**session_data)
        except Exception as e:
            logger.error(f"Error deserializing session {session_id}: {e}")
            return None

    async def update_session(
        self,
        session_id: str,
        **updates: Any,
    ) -> Optional[ResearchSession]:
        """
        Update a research session

        Args:
            session_id: Session identifier
            **updates: Fields to update (stage, progress, documents, etc.)

        Returns:
            Updated ResearchSession if found, None otherwise
        """
        redis = await self.ensure_redis()

        # Get current session
        session = await self.get_session(session_id)
        if session is None:
            return None

        # Update fields
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.updated_at = datetime.now()

        # Save updated session
        # Note: model_dump_json() handles datetime serialization consistently
        session_data = json.loads(session.model_dump_json())

        success = await redis.set(
            self._get_session_key(session_id),
            session_data,
            ttl=self.SESSION_TTL,
        )

        if not success:
            logger.error(f"Failed to update session {session_id}")
            return None

        logger.info(f"Updated session {session_id}")
        return session

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a research session and associated events

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False otherwise
        """
        redis = await self.ensure_redis()

        # Delete session
        session_deleted = await redis.delete(self._get_session_key(session_id))

        # Delete events
        events_deleted = await redis.delete(self._get_events_key(session_id))

        if session_deleted or events_deleted:
            logger.info(f"Deleted session {session_id}")

        return session_deleted

    async def publish_event(
        self,
        session_id: str,
        event_type: str,
        data: Dict[str, Any],
    ) -> str:
        """
        Publish an event for a research session

        Args:
            session_id: Session identifier
            event_type: Type of event
            data: Event-specific data

        Returns:
            Event ID
        """
        redis = await self.ensure_redis()

        event_id = str(uuid.uuid4())
        now = datetime.now()

        event = ResearchEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=now,
            data=data,
        )

        # Serialize event
        # Note: model_dump_json() handles datetime serialization consistently
        event_data = json.loads(event.model_dump_json())

        # Push to event list (using LPUSH for chronological order)
        await redis.lpush(
            self._get_events_key(session_id),
            event_data,
        )

        # Trim event list to max length to prevent memory overflow
        # LTRIM keeps elements from start to stop (inclusive)
        # We keep the most recent EVENT_LIST_MAX_LENGTH events
        events_key = self._get_events_key(session_id)
        event_count = await redis.llen(events_key)
        if event_count > self.EVENT_LIST_MAX_LENGTH:
            await redis.ltrim(events_key, 0, self.EVENT_LIST_MAX_LENGTH - 1)
            logger.debug(
                f"Trimmed event list for session {session_id}: "
                f"{event_count} -> {self.EVENT_LIST_MAX_LENGTH}"
            )

        logger.debug(
            f"Published event {event_id} for session {session_id}: {event_type}"
        )

        return event_id

    async def get_events_since(
        self,
        session_id: str,
        last_event_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve events for a session

        Args:
            session_id: Session identifier
            last_event_id: Optional event ID to retrieve events after
            limit: Maximum events to retrieve

        Returns:
            List of event dictionaries
        """
        redis = await self.ensure_redis()

        # Get events from Redis list
        # LRANGE gets from index 0 to limit-1
        events_data = await redis.lrange(
            self._get_events_key(session_id),
            0,
            limit - 1,
        )

        if not events_data:
            return []

        # If last_event_id is provided, filter events after that ID
        # Note: We include events AFTER the last_event_id (not including it)
        # This follows SSE reconnection semantics where Last-Event-ID indicates
        # the last event the client successfully received
        if last_event_id:
            filtered_events = []
            found_last = False
            for event in events_data:
                if found_last:
                    filtered_events.append(event)
                elif isinstance(event, dict) and event.get("event_id") == last_event_id:
                    found_last = True
                    # Include the matched event itself for replay
                    # This ensures clients don't miss the boundary event on reconnection
                    filtered_events.append(event)

            return filtered_events

        return events_data

    async def get_session_events(self, session_id: str) -> List[ResearchEvent]:
        """
        Get all events for a session as ResearchEvent objects

        Args:
            session_id: Session identifier

        Returns:
            List of ResearchEvent objects
        """
        events_data = await self.get_events_since(session_id, limit=1000)

        events = []
        for event_data in events_data:
            try:
                if isinstance(event_data, dict):
                    # Convert timestamp back to datetime
                    if isinstance(event_data.get("timestamp"), str):
                        event_data["timestamp"] = datetime.fromisoformat(
                            event_data["timestamp"]
                        )

                    events.append(ResearchEvent(**event_data))
            except Exception as e:
                logger.error(f"Error deserializing event: {e}")
                continue

        return events

    async def get_user_sessions(self, user_id: str) -> List[ResearchSession]:
        """
        Get all sessions for a user

        Args:
            user_id: User identifier

        Returns:
            List of ResearchSession objects
        """
        redis = await self.ensure_redis()

        # Get all session keys for user
        pattern = f"{self.SESSION_KEY_PREFIX}:*"
        keys = await redis.keys(pattern)

        sessions = []
        for key in keys:
            # Extract session_id from key
            session_id = key.split(":")[-1] if ":" in key else key

            session = await self.get_session(session_id)
            if session and session.user_id == user_id:
                sessions.append(session)

        return sessions

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions

        Note: Redis handles TTL automatically, but this method can be
        used for manual cleanup if needed.

        Returns:
            Number of sessions cleaned up
        """
        # Redis automatically removes expired keys
        # This is a placeholder for manual cleanup if needed
        logger.info("Expired sessions cleaned up by Redis TTL")
        return 0
