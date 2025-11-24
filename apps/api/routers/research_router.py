# @CODE:RESEARCH-BACKEND-001:ROUTER
# @CODE:RESEARCH-BACKEND-001:SSE
"""
Research API Router

REST API endpoints for research session management:
- POST /api/v1/research - Start research session
- GET /api/v1/research/{id} - Get session status
- GET /api/v1/research/{id}/stream - Stream research events via SSE (Server-Sent Events)
- POST /api/v1/research/{id}/import - Import documents
- DELETE /api/v1/research/{id} - Cancel research

SSE (Server-Sent Events) Support:
- Last-Event-ID header for reconnection and event replay
- 6 event types: progress, stage_change, document_found, metrics_update, error, completed
- Connection cleanup on disconnect
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, Header
from fastapi.responses import StreamingResponse
from starlette.requests import Request
from pydantic import BaseModel, Field

from apps.api.schemas.research_schemas import (
    StartResearchRequest,
    StartResearchResponse,
    ConfirmResearchRequest,
    ResearchSession,
)
from apps.api.services.research_service import ResearchService
from apps.api.deps import verify_api_key
from apps.api.security.api_key_storage import APIKeyInfo
from apps.api.monitoring.research_metrics import get_research_metrics

logger = logging.getLogger(__name__)


class ResearchStatusResponse(BaseModel):
    """Response for GET /api/v1/research/{id}"""

    session: ResearchSession

    class Config:
        from_attributes = True


class ImportDocumentsResponse(BaseModel):
    """Response for POST /api/v1/research/{id}/import"""

    success: bool = Field(..., description="Whether import was successful")
    documentsImported: int = Field(
        ..., alias="documentsImported", description="Number of documents imported"
    )
    taxonomyUpdated: bool = Field(
        ..., alias="taxonomyUpdated", description="Whether taxonomy was updated"
    )

    class Config:
        populate_by_name = True


def create_research_router(
    research_service: Optional[ResearchService] = None,
) -> APIRouter:
    """
    Create research router with dependency injection

    Args:
        research_service: Optional ResearchService instance for testing

    Returns:
        Configured APIRouter
    """

    router = APIRouter(prefix="/api/v1/research", tags=["Research"])

    # Get or create research service
    _service = research_service

    async def get_research_service() -> ResearchService:
        """Dependency injection for research service"""
        nonlocal _service
        if _service is None:
            _service = ResearchService()
        return _service

    # POST /api/v1/research - Start research
    @router.post("", status_code=status.HTTP_201_CREATED, response_model=StartResearchResponse)
    async def start_research(
        request: StartResearchRequest,
        api_key: APIKeyInfo = Depends(verify_api_key),
        service: ResearchService = Depends(get_research_service),
    ) -> StartResearchResponse:
        """
        Start a new research session

        Args:
            request: StartResearchRequest with query and optional config
            api_key: Validated API key from header
            service: Research service instance

        Returns:
            StartResearchResponse with session ID and estimated duration

        Raises:
            400: Invalid request (empty query, invalid config)
            403: Invalid or missing API key
        """
        try:
            # Validate query
            if not request.query or not request.query.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Query cannot be empty",
                )

            # Convert config to dict if provided
            config_dict = None
            if request.config:
                config_dict = request.config.model_dump(by_alias=False)

            # Start research session
            session_id, estimated_duration = await service.start_research(
                query=request.query,
                user_id=api_key.key_id,
                config=config_dict,
            )

            logger.info(f"Started research session {session_id} for key {api_key.key_id}")

            return StartResearchResponse(
                session_id=session_id,
                estimated_duration=estimated_duration,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to start research: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start research session",
            )

    # GET /api/v1/research/{id} - Get session status
    @router.get("/{session_id}", response_model=ResearchStatusResponse)
    async def get_session_status(
        session_id: str,
        api_key: APIKeyInfo = Depends(verify_api_key),
        service: ResearchService = Depends(get_research_service),
    ) -> ResearchStatusResponse:
        """
        Get research session status

        Args:
            session_id: Session identifier
            api_key: Validated API key
            service: Research service instance

        Returns:
            Current session state and progress

        Raises:
            404: Session not found
            403: Invalid or missing API key
        """
        try:
            session = await service.get_session(session_id)

            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {session_id} not found",
                )

            logger.info(f"Retrieved session {session_id}")

            return ResearchStatusResponse(session=session)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get session status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve session status",
            )

    # POST /api/v1/research/{id}/import - Import documents
    @router.post("/{session_id}/import", response_model=Dict[str, Any])
    async def import_documents(
        session_id: str,
        request: ConfirmResearchRequest,
        api_key: APIKeyInfo = Depends(verify_api_key),
        service: ResearchService = Depends(get_research_service),
    ) -> Dict[str, Any]:
        """
        Import selected documents and finalize research

        Args:
            session_id: Session identifier
            request: ConfirmResearchRequest with document IDs
            api_key: Validated API key
            service: Research service instance

        Returns:
            Import result with success status and metadata

        Raises:
            400: Invalid request (empty document list)
            404: Session not found
            409: Session not in CONFIRMING stage
            403: Invalid or missing API key
        """
        try:
            # Validate request
            if not request.selected_document_ids or len(request.selected_document_ids) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one document must be selected",
                )

            # Import documents
            result = await service.import_documents(
                session_id=session_id,
                document_ids=request.selected_document_ids,
                taxonomy_id=request.taxonomy_id,
            )

            logger.info(
                f"Imported {result['documentsImported']} documents to session {session_id}"
            )

            return result

        except ValueError as e:
            # Check error message to determine status code
            error_msg = str(e)
            if "not found" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_msg,
                )
            elif "confirming stage" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=error_msg,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg,
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to import documents: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to import documents",
            )

    # DELETE /api/v1/research/{id} - Cancel research
    @router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def cancel_research(
        session_id: str,
        api_key: APIKeyInfo = Depends(verify_api_key),
        service: ResearchService = Depends(get_research_service),
    ) -> None:
        """
        Cancel research and delete session

        Args:
            session_id: Session identifier
            api_key: Validated API key
            service: Research service instance

        Returns:
            None (204 No Content)

        Raises:
            404: Session not found
            403: Invalid or missing API key
        """
        try:
            # Cancel research
            cancelled = await service.cancel_research(session_id)

            if not cancelled:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {session_id} not found",
                )

            logger.info(f"Cancelled research session {session_id}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to cancel research: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel research",
            )

    # GET /api/v1/research/{id}/stream - Stream research events via SSE
    @router.get("/{session_id}/stream")
    async def stream_research_events(
        session_id: str,
        request: Request,
        last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
        api_key: APIKeyInfo = Depends(verify_api_key),
        service: ResearchService = Depends(get_research_service),
    ) -> StreamingResponse:
        """
        Stream research events via SSE (Server-Sent Events)

        This endpoint provides real-time research progress updates via Server-Sent Events.
        Supports Last-Event-ID header for reconnection and event replay.

        Event Types (6 total):
        - progress: {"progress": float, "currentSource": Optional[str]}
        - stage_change: {"previousStage": str, "newStage": str}
        - document_found: {"document": dict, "totalCount": int}
        - metrics_update: {"metrics": dict}
        - error: {"message": str, "recoverable": bool}
        - completed: {"totalDocuments": int, "suggestedCategories": list, "qualityScore": float}

        Args:
            session_id: Session identifier
            request: Starlette request object for disconnect detection
            last_event_id: Optional Last-Event-ID header for reconnection
            api_key: Validated API key
            service: Research service instance

        Returns:
            StreamingResponse with text/event-stream media type

        Raises:
            404: Session not found
            403: Invalid or missing API key
        """

        async def event_generator():
            """
            Generate SSE events for research session

            This generator:
            1. Replays missed events if Last-Event-ID header is provided
            2. Streams live events as research progresses
            3. Closes on client disconnect or research completion
            """
            metrics = get_research_metrics()

            try:
                # Verify session exists
                session = await service.get_session(session_id)
                if session is None:
                    logger.warning(f"Session {session_id} not found for SSE stream")
                    return

                # Track SSE connection
                metrics.increment_active_sse_connections()

                logger.info(
                    f"Started SSE stream for session {session_id}, last_event_id={last_event_id}"
                )

                # Subscribe to events and stream them
                async for sse_event in service.subscribe_to_events(
                    session_id, last_event_id=last_event_id
                ):
                    # Check if client disconnected
                    if await request.is_disconnected():
                        logger.info(f"Client disconnected from stream for session {session_id}")
                        break

                    # Yield SSE event
                    yield sse_event

            except asyncio.CancelledError:
                logger.info(f"SSE stream for session {session_id} was cancelled")

            except Exception as e:
                logger.error(f"Error in SSE stream for session {session_id}: {e}")

            finally:
                logger.info(f"Closed SSE stream for session {session_id}")
                # Untrack SSE connection
                metrics.decrement_active_sse_connections()

        try:
            logger.info(f"Creating SSE stream for session {session_id}")

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Failed to create SSE stream for session {session_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to establish event stream",
            )

    return router


# Create default router instance
research_router = create_research_router()
