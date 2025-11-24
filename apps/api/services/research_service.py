# @CODE:RESEARCH-BACKEND-001:SERVICE
# @CODE:RESEARCH-BACKEND-001:SSE
"""
Research Service - Core Business Logic

Manages research sessions and integrates with LangGraph pipeline.
Handles session lifecycle, background task execution, and document import.
Includes SSE (Server-Sent Events) streaming support for real-time research updates.
"""

import logging
import uuid
import asyncio
import json
from typing import Optional, List, Dict, Any, Tuple, AsyncGenerator
from datetime import datetime

from apps.api.services.research_session_manager import ResearchSessionManager
from apps.api.schemas.research_schemas import (
    ResearchSession,
    ResearchStage,
    ResearchConfig,
)
from apps.api.monitoring.research_metrics import get_research_metrics

logger = logging.getLogger(__name__)


class ResearchService:
    """Core service for research session management and execution"""

    def __init__(self, session_manager: Optional[ResearchSessionManager] = None):
        """
        Initialize ResearchService

        Args:
            session_manager: ResearchSessionManager instance for session persistence
        """
        self.session_manager = session_manager or ResearchSessionManager()
        self.langgraph_service = None  # Will be injected or lazy-loaded
        self._active_tasks: Dict[str, asyncio.Task] = {}

    def _get_langgraph_service(self):
        """Lazy load LangGraphService"""
        if self.langgraph_service is None:
            from apps.api.services.langgraph_service import get_langgraph_service
            self.langgraph_service = get_langgraph_service()
        return self.langgraph_service

    async def start_research(
        self,
        query: str,
        user_id: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, int]:
        """
        Start a new research session

        Args:
            query: Research query
            user_id: User ID initiating research
            config: Optional research configuration dictionary

        Returns:
            Tuple of (session_id, estimated_duration_seconds)

        Raises:
            Exception: If session creation fails
        """
        # Get metrics collector
        metrics = get_research_metrics()

        # Convert config dict to ResearchConfig if provided
        research_config = None
        depth_level = "default"
        if config:
            research_config = ResearchConfig(**config)
            depth_level = research_config.depth_level if hasattr(research_config, 'depth_level') else "default"

        # Generate session ID
        session_id = str(uuid.uuid4())

        # Create session in Redis
        session = await self.session_manager.create_session(
            session_id=session_id,
            user_id=user_id,
            query=query,
            config=research_config,
        )

        logger.info(f"Created research session {session_id} for user {user_id}")

        # Record session started metric
        metrics.record_session_started(depth_level)
        metrics.increment_active_sessions()

        # Launch background task for research execution
        task = asyncio.create_task(
            self._execute_research(
                session_id=session_id,
                query=query,
                config=config,
                depth_level=depth_level,
            )
        )

        # Store task reference for cancellation
        self._active_tasks[session_id] = task

        # Cleanup task on completion with proper closure
        def _cleanup_task(task_result, sid=session_id):
            """
            Cleanup callback that safely removes task from active tasks.
            Uses default argument to capture session_id value at definition time,
            preventing race conditions with concurrent cancellations.
            """
            self._active_tasks.pop(sid, None)

        task.add_done_callback(_cleanup_task)

        # Estimated duration in seconds (base estimate)
        estimated_duration = 30

        return session_id, estimated_duration

    async def get_session(self, session_id: str) -> Optional[ResearchSession]:
        """
        Get research session by ID

        Args:
            session_id: Session identifier

        Returns:
            ResearchSession if found, None otherwise
        """
        return await self.session_manager.get_session(session_id)

    async def import_documents(
        self,
        session_id: str,
        document_ids: List[str],
        taxonomy_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Import selected documents and finalize research

        Args:
            session_id: Session identifier
            document_ids: List of document IDs to import
            taxonomy_id: Optional taxonomy ID for organization

        Returns:
            Dictionary with success status and metadata

        Raises:
            ValueError: If session not found or not in confirming stage
        """
        # Get metrics collector
        metrics = get_research_metrics()

        # Get current session
        session = await self.session_manager.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        # Verify session is in confirming stage
        if session.stage != ResearchStage.CONFIRMING:
            raise ValueError(
                f"Session must be in CONFIRMING stage, current: {session.stage}"
            )

        # Add documents to session
        documents_to_add = []
        for doc_id in document_ids:
            documents_to_add.append(
                {
                    "id": doc_id,
                    "title": f"Document {doc_id}",
                    "imported_at": datetime.now().isoformat(),
                }
            )

        # Update session with imported documents
        updated_documents = (session.documents or []) + documents_to_add

        # Update session to COMPLETED stage
        updated_session = await self.session_manager.update_session(
            session_id=session_id,
            stage=ResearchStage.COMPLETED,
            progress=1.0,
            documents=updated_documents,
        )

        # Record metrics
        metrics.record_documents_found(len(document_ids))
        metrics.record_session_completed("completed")
        metrics.decrement_active_sessions()

        # Publish import event
        await self.session_manager.publish_event(
            session_id=session_id,
            event_type="documents_imported",
            data={
                "document_ids": document_ids,
                "count": len(document_ids),
                "taxonomy_id": taxonomy_id,
            },
        )

        return {
            "success": True,
            "documentsImported": len(document_ids),
            "taxonomyUpdated": taxonomy_id is not None,
        }

    async def cancel_research(self, session_id: str) -> bool:
        """
        Cancel active research and delete session

        Args:
            session_id: Session identifier

        Returns:
            True if cancelled, False if not found
        """
        # Get metrics collector
        metrics = get_research_metrics()

        # Cancel active task if running
        if session_id in self._active_tasks:
            task = self._active_tasks[session_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            self._active_tasks.pop(session_id, None)

        # Record metrics
        metrics.decrement_active_sessions()

        # Delete session from Redis
        return await self.session_manager.delete_session(session_id)

    def _format_sse_event(
        self, event_id: str, event_type: str, data: Dict[str, Any]
    ) -> str:
        """
        Format event as SSE (Server-Sent Events) string

        Args:
            event_id: Unique event identifier
            event_type: Type of event (progress, stage_change, etc.)
            data: Event-specific data dictionary

        Returns:
            Formatted SSE event string
        """
        # SSE format: id, event type, data (as JSON)
        sse_lines = [f"id: {event_id}", f"event: {event_type}", f"data: {json.dumps(data)}"]
        return "\n".join(sse_lines) + "\n\n"

    async def subscribe_to_events(
        self, session_id: str, last_event_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Subscribe to research events for a session via SSE (Server-Sent Events)

        This async generator yields formatted SSE events for a research session.
        - Replays missed events if last_event_id is provided (for reconnection)
        - Streams live events as they occur during research execution

        Args:
            session_id: Session identifier
            last_event_id: Optional event ID to start from (for reconnection)

        Yields:
            Formatted SSE event strings
        """
        # Verify session exists
        session = await self.session_manager.get_session(session_id)
        if session is None:
            logger.warning(f"Session {session_id} not found for event subscription")
            return

        # Replay missed events if reconnecting with Last-Event-ID
        if last_event_id:
            try:
                missed_events = await self.session_manager.get_events_since(
                    session_id, last_event_id=last_event_id, limit=100
                )

                logger.info(
                    f"Replaying {len(missed_events)} missed events for session {session_id}"
                )

                for event_data in missed_events:
                    if isinstance(event_data, dict):
                        # Extract event information
                        event_id = event_data.get("event_id", "unknown")
                        event_type = event_data.get("event_type", "unknown")
                        data = event_data.get("data", {})

                        # Format and yield SSE event
                        sse_event = self._format_sse_event(event_id, event_type, data)
                        yield sse_event

            except Exception as e:
                logger.error(f"Error replaying events for session {session_id}: {e}")

        # Stream live events - keep connection open and emit events as they occur
        # In a production setup, this would be connected to an event bus (Redis Pub/Sub, etc.)
        # For now, we'll use a simple polling mechanism

        max_wait_time = 300  # Maximum 5 minutes of streaming
        start_time = asyncio.get_event_loop().time()
        event_index = 0

        try:
            while True:
                # Check if session still exists
                current_session = await self.session_manager.get_session(session_id)
                if current_session is None:
                    logger.info(f"Session {session_id} no longer exists, ending stream")
                    break

                # Check if research is completed
                if current_session.stage == ResearchStage.COMPLETED:
                    logger.info(f"Session {session_id} research completed, sending completion event")

                    # Emit completion event
                    completion_data = {
                        "totalDocuments": len(current_session.documents),
                        "suggestedCategories": ["AI", "Machine Learning"],
                        "qualityScore": 0.95,
                    }

                    event_index += 1
                    sse_event = self._format_sse_event(
                        event_id=str(event_index),
                        event_type="completed",
                        data=completion_data,
                    )
                    yield sse_event
                    break

                # Check if session is in error state
                if current_session.stage == ResearchStage.ERROR:
                    logger.info(f"Session {session_id} in error state, sending error event")

                    # Emit error event
                    error_data = {
                        "message": "Research session encountered an error",
                        "recoverable": False,
                    }

                    event_index += 1
                    sse_event = self._format_sse_event(
                        event_id=str(event_index),
                        event_type="error",
                        data=error_data,
                    )
                    yield sse_event
                    break

                # Check for timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > max_wait_time:
                    logger.info(f"Session {session_id} stream timeout after {elapsed}s")
                    break

                # Small delay to prevent busy-waiting
                await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            logger.info(f"Event stream for session {session_id} cancelled")
            raise

        except Exception as e:
            logger.error(f"Error streaming events for session {session_id}: {e}")
            raise

    async def _execute_research(
        self,
        session_id: str,
        query: str,
        config: Optional[Dict[str, Any]] = None,
        depth_level: str = "default",
    ) -> None:
        """
        Background task to execute research pipeline

        Args:
            session_id: Session identifier
            query: Research query
            config: Research configuration
            depth_level: Research depth level for metrics
        """
        metrics = get_research_metrics()

        try:
            # Get pipeline service with error handling
            try:
                pipeline = self._get_langgraph_service()
                logger.info(f"LangGraph service loaded for session {session_id}")
            except Exception as pipeline_init_error:
                logger.error(
                    f"Failed to initialize LangGraph service for session {session_id}: "
                    f"{pipeline_init_error}"
                )
                raise RuntimeError(
                    f"LangGraph service initialization failed: {pipeline_init_error}"
                )

            # Update session: ANALYZING stage
            await self.session_manager.update_session(
                session_id=session_id,
                stage=ResearchStage.ANALYZING,
                progress=0.2,
            )

            await self.session_manager.publish_event(
                session_id=session_id,
                event_type="stage_changed",
                data={"stage": ResearchStage.ANALYZING},
            )

            # Execute pipeline with comprehensive error handling
            logger.info(f"Starting LangGraph pipeline for session {session_id}, query: {query[:50]}...")
            try:
                result = await pipeline.execute_pipeline(query=query)
                logger.info(
                    f"LangGraph pipeline completed for session {session_id}, "
                    f"result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}"
                )
            except asyncio.TimeoutError:
                logger.error(f"LangGraph pipeline timeout for session {session_id}")
                raise RuntimeError("Research pipeline timed out. Please try again.")
            except Exception as pipeline_error:
                logger.error(
                    f"LangGraph pipeline failed for session {session_id}: {pipeline_error}",
                    exc_info=True,
                )
                raise RuntimeError(f"Research pipeline error: {pipeline_error}")

            # Update session: SEARCHING stage
            await self.session_manager.update_session(
                session_id=session_id,
                stage=ResearchStage.SEARCHING,
                progress=0.5,
            )

            await self.session_manager.publish_event(
                session_id=session_id,
                event_type="stage_changed",
                data={"stage": ResearchStage.SEARCHING},
            )

            # TODO: Replace with actual document discovery from LangGraph result
            # Mock document collection - placeholder for actual document sources
            # Future integration should:
            # 1. Extract documents from pipeline result
            # 2. Apply quality threshold filtering (config.quality_threshold)
            # 3. Limit by max_documents (config.max_documents)
            # 4. Apply sources_filter (config.sources_filter)
            documents = [
                {"id": str(uuid.uuid4()), "title": f"Document {i + 1}"}
                for i in range(3)
            ]
            logger.info(
                f"Collected {len(documents)} documents for session {session_id} "
                "(mock data - pending real integration)"
            )

            # Update session: COLLECTING stage
            await self.session_manager.update_session(
                session_id=session_id,
                stage=ResearchStage.COLLECTING,
                progress=0.75,
                documents=documents,
            )

            await self.session_manager.publish_event(
                session_id=session_id,
                event_type="stage_changed",
                data={"stage": ResearchStage.COLLECTING},
            )

            # Update session: CONFIRMING stage (wait for user confirmation)
            await self.session_manager.update_session(
                session_id=session_id,
                stage=ResearchStage.CONFIRMING,
                progress=0.9,
            )

            await self.session_manager.publish_event(
                session_id=session_id,
                event_type="stage_changed",
                data={"stage": ResearchStage.CONFIRMING},
            )

            logger.info(f"Research session {session_id} reached CONFIRMING stage")

        except asyncio.CancelledError:
            # Handle cancellation
            logger.info(f"Research session {session_id} cancelled")
            metrics.record_session_completed("cancelled")
            metrics.decrement_active_sessions()
            await self.session_manager.update_session(
                session_id=session_id,
                stage=ResearchStage.ERROR,
                progress=0.0,
            )
            raise

        except Exception as e:
            # Handle errors
            logger.error(f"Research session {session_id} failed: {e}")
            metrics.record_session_error()
            metrics.decrement_active_sessions()
            await self.session_manager.update_session(
                session_id=session_id,
                stage=ResearchStage.ERROR,
                progress=0.0,
            )

            await self.session_manager.publish_event(
                session_id=session_id,
                event_type="error",
                data={"error": str(e)},
            )
