# @CODE:AGENT-GROWTH-002:API
# @CODE:AGENT-GROWTH-003:API
# @CODE:AGENT-GROWTH-004:API
import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.agent_dao import AgentDAO
from apps.api.background.agent_task_queue import AgentTaskQueue
from apps.api.background.coverage_history_dao import CoverageHistoryDAO
from apps.api.database import BackgroundTask, SearchDAO, TaxonomyNode
from apps.api.deps import verify_api_key
from apps.api.schemas.agent_schemas import (
    AgentCreateRequest,
    AgentListResponse,
    AgentResponse,
    AgentUpdateRequest,
    BackgroundTaskResponse,
    CoverageHistoryItem,
    CoverageHistoryResponse,
    CoverageResponse,
    GapListResponse,
    GapResponse,
    QueryRequest,
    QueryResponse,
    SearchResultItem,
    TaskStatusResponse,
)
from apps.core.db_session import async_session
from apps.knowledge_builder.coverage.meter import CoverageMeterService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


async def get_session():
    async with async_session() as session:
        yield session


async def validate_taxonomy_nodes(
    session: AsyncSession, taxonomy_node_ids: list, taxonomy_version: str
):
    query = select(TaxonomyNode.node_id).where(
        TaxonomyNode.node_id.in_(taxonomy_node_ids),
        TaxonomyNode.version == taxonomy_version,
    )
    result = await session.execute(query)
    existing_nodes = result.scalars().all()

    if len(existing_nodes) != len(taxonomy_node_ids):
        invalid_ids = set(str(nid) for nid in taxonomy_node_ids) - set(
            str(nid) for nid in existing_nodes
        )
        raise ValueError(f"Invalid taxonomy node IDs: {', '.join(invalid_ids)}")


@router.post(
    "/from-taxonomy",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create agent from taxonomy scope",
    description="Creates a new agent with specified taxonomy scope and calculates initial coverage.",
)
async def create_agent_from_taxonomy(
    request: AgentCreateRequest,
    session: AsyncSession = Depends(get_session),
    api_key=Depends(verify_api_key),
) -> AgentResponse:
    logger.info(f"Creating agent: {request.name}")

    try:
        await validate_taxonomy_nodes(
            session, request.taxonomy_node_ids, request.taxonomy_version
        )

        agent = await AgentDAO.create_agent(
            session=session,
            name=request.name,
            taxonomy_node_ids=request.taxonomy_node_ids,
            taxonomy_version=request.taxonomy_version,
            scope_description=request.scope_description,
            retrieval_config=request.retrieval_config,
            features_config=request.features_config,
        )

        logger.info(f"Agent created: {agent.agent_id}")
        return AgentResponse.model_validate(agent)

    except ValueError as e:
        logger.error(f"Invalid taxonomy nodes: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Agent creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")


@router.get(
    "/search",
    response_model=AgentListResponse,
    status_code=status.HTTP_200_OK,
    summary="Search agents by name",
    description="Searches agents by name using case-insensitive pattern matching.",
)
async def search_agents(
    q: str = None,
    max_results: int = 50,
    session: AsyncSession = Depends(get_session),
    api_key=Depends(verify_api_key),
) -> AgentListResponse:
    logger.info(f"Searching agents: query={q}, max_results={max_results}")

    try:
        if max_results > 100:
            raise HTTPException(status_code=422, detail="max_results must be <= 100")

        agents = await AgentDAO.search_agents(
            session=session, query=q, max_results=max_results
        )

        return AgentListResponse(
            agents=[AgentResponse.model_validate(agent) for agent in agents],
            total=len(agents),
            filters_applied={"query": q} if q else {},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get agent by ID",
    description="Retrieves agent details by agent ID.",
)
async def get_agent(
    agent_id: UUID,
    session: AsyncSession = Depends(get_session),
    api_key=Depends(verify_api_key),
) -> AgentResponse:
    logger.info(f"Retrieving agent: {agent_id}")

    try:
        agent = await AgentDAO.get_agent(session, agent_id)

        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        return AgentResponse.model_validate(agent)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/",
    response_model=AgentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List agents with filters",
    description="Lists agents with optional filtering by level and coverage.",
)
async def list_agents(
    level: Optional[int] = None,
    min_coverage: Optional[float] = None,
    max_results: int = 50,
    session: AsyncSession = Depends(get_session),
    api_key=Depends(verify_api_key),
) -> AgentListResponse:
    logger.info(
        f"Listing agents with filters: level={level}, min_coverage={min_coverage}, max_results={max_results}"
    )

    try:
        if max_results > 100:
            raise HTTPException(status_code=422, detail="max_results must be <= 100")

        agents = await AgentDAO.list_agents(
            session=session,
            level=level,
            min_coverage=min_coverage,
            max_results=max_results,
        )

        filters_applied = {}
        if level is not None:
            filters_applied["level"] = level
        if min_coverage is not None:
            filters_applied["min_coverage"] = min_coverage

        return AgentListResponse(
            agents=[AgentResponse.model_validate(agent) for agent in agents],
            total=len(agents),
            filters_applied=filters_applied,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{agent_id}/coverage",
    response_model=CoverageResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate agent coverage",
    description="Calculates and retrieves agent coverage metrics.",
)
async def get_agent_coverage(
    agent_id: UUID,
    session: AsyncSession = Depends(get_session),
    api_key=Depends(verify_api_key),
) -> CoverageResponse:
    logger.info(f"Calculating coverage for agent: {agent_id}")

    try:
        agent = await AgentDAO.get_agent(session, agent_id)

        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        coverage_service = CoverageMeterService(session_factory=lambda: session)
        node_ids_str = [str(nid) for nid in agent.taxonomy_node_ids]

        coverage_result = await coverage_service.calculate_coverage(
            taxonomy_version=agent.taxonomy_version, node_ids=node_ids_str
        )

        await AgentDAO.update_agent(
            session=session,
            agent_id=agent_id,
            coverage_percent=coverage_result.coverage_percent,
            last_coverage_update=datetime.utcnow(),
        )

        node_coverage = {}
        document_counts = {}
        target_counts = {}

        for node_id, coverage_data in coverage_result.node_coverage.items():
            doc_count = coverage_data.get("document_count", 0)
            chunk_count = coverage_data.get("chunk_count", 0)
            target_count = max(doc_count, 10)

            node_coverage[node_id] = (
                (doc_count / target_count * 100) if target_count > 0 else 0.0
            )
            document_counts[node_id] = doc_count
            target_counts[node_id] = target_count

        return CoverageResponse(
            agent_id=agent_id,
            overall_coverage=coverage_result.coverage_percent,
            node_coverage=node_coverage,
            document_counts=document_counts,
            target_counts=target_counts,
            version=agent.taxonomy_version,
            calculated_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Coverage calculation failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")


@router.get(
    "/{agent_id}/gaps",
    response_model=GapListResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect coverage gaps",
    description="Detects coverage gaps below the specified threshold.",
)
async def detect_coverage_gaps(
    agent_id: UUID,
    threshold: float = 0.5,
    session: AsyncSession = Depends(get_session),
    api_key=Depends(verify_api_key),
) -> GapListResponse:
    logger.info(f"Detecting gaps for agent: {agent_id}, threshold: {threshold}")

    try:
        if threshold < 0.0 or threshold > 1.0:
            raise HTTPException(
                status_code=422, detail="Threshold must be between 0.0 and 1.0"
            )

        agent = await AgentDAO.get_agent(session, agent_id)

        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        coverage_service = CoverageMeterService(session_factory=lambda: session)
        node_ids_str = [str(nid) for nid in agent.taxonomy_node_ids]

        coverage_result = await coverage_service.calculate_coverage(
            taxonomy_version=agent.taxonomy_version, node_ids=node_ids_str
        )

        gaps_list = await coverage_service.detect_gaps(coverage_result, threshold)

        gaps = []
        for gap in gaps_list:
            gaps.append(
                GapResponse(
                    node_id=UUID(gap.node_id),
                    current_coverage=gap.current_coverage,
                    target_coverage=gap.target_coverage,
                    missing_docs=gap.missing_docs,
                    recommendation=gap.recommendation,
                )
            )

        return GapListResponse(
            agent_id=agent_id,
            gaps=gaps,
            threshold=threshold,
            detected_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gap detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{agent_id}/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query agent's knowledge scope",
    description="Queries agent's knowledge scope using hybrid search.",
)
async def query_agent(
    agent_id: UUID,
    request: QueryRequest,
    session: AsyncSession = Depends(get_session),
    api_key=Depends(verify_api_key),
) -> QueryResponse:
    logger.info(f"Querying agent: {agent_id}, query: {request.query}")

    start_time = time.time()

    try:
        agent = await AgentDAO.get_agent(session, agent_id)

        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        top_k = (
            request.top_k
            if request.top_k is not None
            else agent.retrieval_config.get("top_k", 5)
        )

        taxonomy_node_ids_list = [[str(nid)] for nid in agent.taxonomy_node_ids]

        search_results = await SearchDAO.hybrid_search(
            query=request.query,
            filters={
                "canonical_in": taxonomy_node_ids_list,
                "version": agent.taxonomy_version,
            },
            topk=top_k,
        )

        await AgentDAO.update_agent(
            session=session,
            agent_id=agent_id,
            total_queries=agent.total_queries + 1,
            last_query_at=datetime.utcnow(),
        )

        results = []
        for result in search_results:
            results.append(
                SearchResultItem(
                    doc_id=UUID(
                        result.get("chunk_id", "00000000-0000-0000-0000-000000000000")
                    ),
                    chunk_id=UUID(
                        result.get("chunk_id", "00000000-0000-0000-0000-000000000000")
                    ),
                    content=result.get("text", ""),
                    score=result.get("score", 0.0),
                    metadata=(
                        result.get("metadata", {}) if request.include_metadata else None
                    ),
                )
            )

        query_time_ms = (time.time() - start_time) * 1000

        return QueryResponse(
            agent_id=agent_id,
            query=request.query,
            results=results,
            total_results=len(results),
            query_time_ms=query_time_ms,
            retrieval_strategy=agent.retrieval_config.get("strategy", "hybrid"),
            executed_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")


@router.patch(
    "/{agent_id}",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update agent configuration",
    description="Updates agent fields (name, scope_description, retrieval_config, features_config).",
)
async def update_agent(
    agent_id: UUID,
    request: AgentUpdateRequest,
    session: AsyncSession = Depends(get_session),
    api_key=Depends(verify_api_key),
) -> AgentResponse:
    logger.info(f"Updating agent: {agent_id}")

    try:
        agent = await AgentDAO.get_agent(session, agent_id)

        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        update_fields = request.model_dump(exclude_unset=True)

        if update_fields:
            await AgentDAO.update_agent(
                session=session, agent_id=agent_id, **update_fields
            )

            agent = await AgentDAO.get_agent(session, agent_id)

        logger.info(f"Agent updated: {agent_id}")
        return AgentResponse.model_validate(agent)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent update failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete agent",
    description="Permanently deletes agent and all associated data.",
)
async def delete_agent(
    agent_id: UUID,
    session: AsyncSession = Depends(get_session),
    api_key=Depends(verify_api_key),
):
    logger.info(f"Deleting agent: {agent_id}")

    try:
        agent = await AgentDAO.get_agent(session, agent_id)

        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        await AgentDAO.delete_agent(session, agent_id)

        logger.info(f"Agent deleted: {agent_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent deletion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{agent_id}/coverage/refresh",
    response_model=BackgroundTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Refresh agent coverage (background)",
    description="Triggers background coverage calculation and returns immediately with task ID.",
)
async def refresh_agent_coverage_background(
    agent_id: UUID,
    background: bool = True,
    session: AsyncSession = Depends(get_session),
    api_key=Depends(verify_api_key),
) -> BackgroundTaskResponse:
    logger.info(f"Triggering background coverage refresh for agent: {agent_id}")

    try:
        agent = await AgentDAO.get_agent(session, agent_id)

        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        if not background:
            coverage_service = CoverageMeterService(session_factory=lambda: session)
            node_ids_str = [str(nid) for nid in agent.taxonomy_node_ids]

            coverage_result = await coverage_service.calculate_coverage(
                taxonomy_version=agent.taxonomy_version, node_ids=node_ids_str
            )

            await AgentDAO.update_agent(
                session=session,
                agent_id=agent_id,
                coverage_percent=coverage_result.coverage_percent,
                last_coverage_update=datetime.utcnow(),
            )

            return BackgroundTaskResponse(
                task_id=f"sync-{agent_id}",
                agent_id=agent_id,
                task_type="coverage_refresh",
                status="completed",
                created_at=datetime.utcnow(),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                result={"coverage_percent": coverage_result.coverage_percent},
                error=None,
            )

        task_queue = AgentTaskQueue()
        await task_queue.initialize()

        task_id = await task_queue.enqueue_coverage_task(
            agent_id=agent_id,
            taxonomy_node_ids=agent.taxonomy_node_ids,
            taxonomy_version=agent.taxonomy_version,
        )

        task = BackgroundTask(
            task_id=task_id,
            agent_id=agent_id,
            task_type="coverage_refresh",
            status="pending",
            created_at=datetime.utcnow(),
        )
        session.add(task)
        await session.commit()

        logger.info(f"Created background task: {task_id}")
        return BackgroundTaskResponse(
            task_id=task_id,
            agent_id=agent_id,
            task_type="coverage_refresh",
            status="pending",
            created_at=task.created_at,
            started_at=None,
            completed_at=None,
            result=None,
            error=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to trigger background coverage refresh: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{agent_id}/coverage/status/{task_id}",
    response_model=TaskStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get background task status",
    description="Retrieves the status of a background coverage calculation task.",
)
async def get_coverage_task_status(
    agent_id: UUID,
    task_id: str,
    session: AsyncSession = Depends(get_session),
    api_key=Depends(verify_api_key),
) -> TaskStatusResponse:
    logger.info(f"Retrieving task status: {task_id} for agent: {agent_id}")

    try:
        agent = await AgentDAO.get_agent(session, agent_id)

        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        task = await session.get(BackgroundTask, task_id)

        if task is None:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        if task.agent_id != agent_id:
            raise HTTPException(
                status_code=404, detail=f"Task not found for this agent"
            )

        queue_position = None
        if task.status == "pending":
            task_queue = AgentTaskQueue()
            await task_queue.initialize()
            queue_position = await task_queue.get_queue_position(task_id)

        return TaskStatusResponse(
            task_id=task.task_id,
            agent_id=task.agent_id,
            task_type=task.task_type,
            status=task.status,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            result=task.result,
            error=task.error,
            queue_position=queue_position,
            estimated_completion_at=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve task status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{agent_id}/coverage/history",
    response_model=CoverageHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get coverage history",
    description="Retrieves time-series coverage data for the agent.",
)
async def get_coverage_history(
    agent_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: Optional[int] = 100,
    session: AsyncSession = Depends(get_session),
    api_key=Depends(verify_api_key),
) -> CoverageHistoryResponse:
    logger.info(f"Retrieving coverage history for agent: {agent_id}")

    try:
        agent = await AgentDAO.get_agent(session, agent_id)

        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        history_records = await CoverageHistoryDAO.query_history(
            session=session,
            agent_id=agent_id,
            from_date=start_date,
            to_date=end_date,
            limit=limit,
        )

        history_items = [
            CoverageHistoryItem(
                timestamp=record.timestamp,
                overall_coverage=record.overall_coverage,
                total_documents=record.total_documents,
                total_chunks=record.total_chunks,
            )
            for record in history_records
        ]

        return CoverageHistoryResponse(
            agent_id=agent_id,
            history=history_items,
            start_date=start_date,
            end_date=end_date,
            total_entries=len(history_items),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve coverage history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel background task",
    description="Cancels a pending or running coverage refresh task.",
)
async def cancel_background_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
    api_key=Depends(verify_api_key),
):
    logger.info(f"Cancelling task: {task_id}")

    try:
        task = await session.get(BackgroundTask, task_id)

        if task is None:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        if task.status in ["completed", "failed", "timeout", "cancelled"]:
            raise HTTPException(
                status_code=400, detail=f"Cannot cancel task with status: {task.status}"
            )

        if task.status == "pending":
            task_queue = AgentTaskQueue()
            await task_queue.initialize()
            removed = await task_queue.remove_job(task_id)

            if removed:
                logger.info(f"Task removed from queue: {task_id}")

            task.status = "cancelled"
            task.completed_at = datetime.utcnow()
            await session.commit()

        elif task.status == "running":
            task.cancellation_requested = True
            await session.commit()
            logger.info(f"Cancellation requested for running task: {task_id}")

        logger.info(f"Task cancelled: {task_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{agent_id}/query/stream",
    status_code=status.HTTP_200_OK,
    summary="Query agent with streaming response",
    description="Queries agent's knowledge scope and streams results using Server-Sent Events (SSE).",
)
async def query_agent_stream(
    agent_id: UUID,
    request: QueryRequest,
    session: AsyncSession = Depends(get_session),
    api_key=Depends(verify_api_key),
):
    logger.info(f"Streaming query for agent: {agent_id}, query: {request.query}")

    async def event_generator():
        try:
            agent = await AgentDAO.get_agent(session, agent_id)

            if agent is None:
                error_data = {"error": f"Agent not found: {agent_id}"}
                yield f"data: {json.dumps(error_data)}\n\n"
                return

            yield f"data: {json.dumps({'status': 'started', 'agent_id': str(agent_id)})}\n\n"
            await asyncio.sleep(0.1)

            top_k = (
                request.top_k
                if request.top_k is not None
                else agent.retrieval_config.get("top_k", 5)
            )
            taxonomy_node_ids_list = [[str(nid)] for nid in agent.taxonomy_node_ids]

            start_time = time.time()

            search_results = await SearchDAO.hybrid_search(
                query=request.query,
                filters={
                    "canonical_in": taxonomy_node_ids_list,
                    "version": agent.taxonomy_version,
                },
                topk=top_k,
            )

            await AgentDAO.update_agent(
                session=session,
                agent_id=agent_id,
                total_queries=agent.total_queries + 1,
                last_query_at=datetime.utcnow(),
            )

            for i, result in enumerate(search_results):
                result_item = {
                    "index": i,
                    "doc_id": result.get(
                        "chunk_id", "00000000-0000-0000-0000-000000000000"
                    ),
                    "chunk_id": result.get(
                        "chunk_id", "00000000-0000-0000-0000-000000000000"
                    ),
                    "content": result.get("text", ""),
                    "score": result.get("score", 0.0),
                    "metadata": (
                        result.get("metadata", {}) if request.include_metadata else None
                    ),
                }

                yield f"data: {json.dumps(result_item)}\n\n"
                await asyncio.sleep(0.05)

            query_time_ms = (time.time() - start_time) * 1000

            final_data = {
                "status": "completed",
                "total_results": len(search_results),
                "query_time_ms": query_time_ms,
                "retrieval_strategy": agent.retrieval_config.get("strategy", "hybrid"),
                "executed_at": datetime.utcnow().isoformat(),
            }

            yield f"data: {json.dumps(final_data)}\n\n"

        except Exception as e:
            logger.error(f"Streaming query failed: {e}", exc_info=True)
            error_data = {"error": "Query execution failed", "detail": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
