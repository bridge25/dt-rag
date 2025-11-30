"""
Agent Application Service

Orchestrates agent-related use cases and handles cross-cutting concerns.

@CODE:CLEAN-ARCHITECTURE-AGENT-SERVICE
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from ..domain.entities.agent import Agent
from ..domain.repositories.agent_repository import (
    IAgentRepository,
    AgentFilterParams,
    CreateAgentParams,
    UpdateAgentParams,
    AgentMetrics,
    AgentCoverage,
)
from ..domain.usecases.agent import (
    GetAgentsUseCase,
    GetAgentByIdUseCase,
    CreateAgentUseCase,
    UpdateAgentUseCase,
    DeleteAgentUseCase,
    QueryAgentUseCase,
)

logger = logging.getLogger(__name__)


class AgentService:
    """
    Agent Application Service

    Provides a high-level interface for agent operations,
    orchestrating use cases and managing transactions.

    Responsibilities:
    - Coordinate multiple use cases
    - Handle cross-cutting concerns (logging, caching, etc.)
    - Transform between DTOs and domain entities
    - Manage error handling and recovery
    """

    def __init__(
        self,
        agent_repository: IAgentRepository,
        search_repository: Optional[Any] = None,
    ):
        """
        Initialize agent service with dependencies.

        Args:
            agent_repository: Repository for agent data access
            search_repository: Optional search repository for query operations
        """
        self._agent_repository = agent_repository
        self._search_repository = search_repository

        # Initialize use cases
        self._get_agents = GetAgentsUseCase(agent_repository)
        self._get_agent_by_id = GetAgentByIdUseCase(agent_repository)
        self._create_agent = CreateAgentUseCase(agent_repository)
        self._update_agent = UpdateAgentUseCase(agent_repository)
        self._delete_agent = DeleteAgentUseCase(agent_repository)
        self._query_agent = QueryAgentUseCase(agent_repository, search_repository)

    # Query Operations

    async def get_agents(
        self,
        status: Optional[str] = None,
        level_min: Optional[int] = None,
        level_max: Optional[int] = None,
        min_coverage: Optional[float] = None,
        max_coverage: Optional[float] = None,
        taxonomy_version: Optional[str] = None,
        name_contains: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Get paginated list of agents with filtering.

        Args:
            status: Filter by agent status
            level_min: Minimum level filter
            level_max: Maximum level filter
            min_coverage: Minimum coverage percentage
            max_coverage: Maximum coverage percentage
            taxonomy_version: Filter by taxonomy version
            name_contains: Search by name substring
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary containing agents list and pagination metadata
        """
        try:
            result = await self._get_agents.execute(
                status=status,
                level_min=level_min,
                level_max=level_max,
                min_coverage=min_coverage,
                max_coverage=max_coverage,
                taxonomy_version=taxonomy_version,
                name_contains=name_contains,
                page=page,
                page_size=page_size,
            )

            return {
                "agents": [self._agent_to_dict(a) for a in result.agents],
                "total": result.total_count,
                "page": result.page,
                "page_size": result.page_size,
                "total_pages": result.total_pages,
                "statistics": result.statistics,
            }
        except Exception as e:
            logger.error(f"Failed to get agents: {e}")
            raise

    async def get_agent_by_id(self, agent_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get detailed agent information by ID.

        Args:
            agent_id: Agent UUID

        Returns:
            Agent dictionary or None if not found
        """
        try:
            result = await self._get_agent_by_id.execute(agent_id)

            if not result.found:
                return None

            return {
                "agent": self._agent_to_dict(result.agent),
                "metrics": result.metrics,
                "coverage": result.coverage,
            }
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            raise

    async def search_agents(
        self,
        query: str,
        max_results: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search agents by name.

        Args:
            query: Search query string
            max_results: Maximum number of results

        Returns:
            List of matching agents
        """
        try:
            agents = await self._agent_repository.search(query, max_results)
            return [self._agent_to_dict(a) for a in agents]
        except Exception as e:
            logger.error(f"Failed to search agents: {e}")
            raise

    # Command Operations

    async def create_agent(
        self,
        name: str,
        taxonomy_node_ids: List[UUID],
        taxonomy_version: str,
        scope_description: Optional[str] = None,
        retrieval_config: Optional[Dict[str, Any]] = None,
        features_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new agent.

        Args:
            name: Agent name
            taxonomy_node_ids: List of taxonomy node UUIDs
            taxonomy_version: Taxonomy version string
            scope_description: Optional scope description
            retrieval_config: Optional retrieval configuration
            features_config: Optional features configuration

        Returns:
            Created agent dictionary
        """
        try:
            params = CreateAgentParams(
                name=name,
                taxonomy_node_ids=taxonomy_node_ids,
                taxonomy_version=taxonomy_version,
                scope_description=scope_description,
                retrieval_config=retrieval_config or {},
                features_config=features_config or {},
            )

            result = await self._create_agent.execute(params)

            if not result.success:
                raise ValueError(result.message)

            logger.info(f"Created agent: {result.agent.agent_id}")
            return self._agent_to_dict(result.agent)
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise

    async def update_agent(
        self,
        agent_id: UUID,
        name: Optional[str] = None,
        scope_description: Optional[str] = None,
        retrieval_config: Optional[Dict[str, Any]] = None,
        features_config: Optional[Dict[str, Any]] = None,
        avatar_url: Optional[str] = None,
        rarity: Optional[str] = None,
        character_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing agent.

        Args:
            agent_id: Agent UUID
            name: New name (optional)
            scope_description: New scope description (optional)
            retrieval_config: New retrieval config (optional)
            features_config: New features config (optional)
            avatar_url: New avatar URL (optional)
            rarity: New rarity (optional)
            character_description: New character description (optional)

        Returns:
            Updated agent dictionary
        """
        try:
            params = UpdateAgentParams(
                name=name,
                scope_description=scope_description,
                retrieval_config=retrieval_config,
                features_config=features_config,
                avatar_url=avatar_url,
                rarity=rarity,
                character_description=character_description,
            )

            result = await self._update_agent.execute(agent_id, params)

            if not result.success:
                raise ValueError(result.message)

            logger.info(f"Updated agent: {agent_id}")
            return self._agent_to_dict(result.agent)
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id}: {e}")
            raise

    async def delete_agent(self, agent_id: UUID) -> bool:
        """
        Delete an agent.

        Args:
            agent_id: Agent UUID

        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self._delete_agent.execute(agent_id)

            if result.success:
                logger.info(f"Deleted agent: {agent_id}")

            return result.success
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            raise

    # Query Execution

    async def query_agent(
        self,
        agent_id: UUID,
        query: str,
        mode: str = "answer",
        top_k: int = 5,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a query against an agent.

        Args:
            agent_id: Agent UUID
            query: User query string
            mode: Query mode ("answer", "search", "hybrid")
            top_k: Number of results to return
            include_sources: Whether to include source documents

        Returns:
            Query response dictionary
        """
        try:
            result = await self._query_agent.execute(
                agent_id=agent_id,
                query=query,
                mode=mode,
                top_k=top_k,
                include_sources=include_sources,
            )

            return {
                "answer": result.answer,
                "sources": result.sources,
                "agent_id": str(agent_id),
                "query": query,
                "latency_ms": result.latency_ms,
                "xp_earned": result.xp_earned,
                "level_up": result.level_up,
            }
        except Exception as e:
            logger.error(f"Failed to query agent {agent_id}: {e}")
            raise

    # Metrics Operations

    async def get_agent_metrics(self, agent_id: UUID) -> Dict[str, Any]:
        """
        Get agent performance metrics.

        Args:
            agent_id: Agent UUID

        Returns:
            Metrics dictionary
        """
        try:
            metrics = await self._agent_repository.get_metrics(agent_id)
            return {
                "agent_id": str(metrics.agent_id),
                "total_queries": metrics.total_queries,
                "successful_queries": metrics.successful_queries,
                "success_rate": (
                    metrics.successful_queries / metrics.total_queries * 100
                    if metrics.total_queries > 0
                    else 0
                ),
                "avg_latency_ms": metrics.avg_latency_ms,
                "avg_faithfulness": metrics.avg_faithfulness,
                "queries_today": metrics.queries_today,
                "queries_this_week": metrics.queries_this_week,
                "level_progress_percent": metrics.level_progress_percent,
            }
        except Exception as e:
            logger.error(f"Failed to get metrics for agent {agent_id}: {e}")
            raise

    async def get_agent_coverage(self, agent_id: UUID) -> Dict[str, Any]:
        """
        Get agent coverage breakdown.

        Args:
            agent_id: Agent UUID

        Returns:
            Coverage dictionary
        """
        try:
            coverage = await self._agent_repository.get_coverage(agent_id)
            return {
                "agent_id": str(coverage.agent_id),
                "overall_coverage": coverage.overall_coverage,
                "node_coverage": coverage.node_coverage,
                "document_counts": coverage.document_counts,
                "target_counts": coverage.target_counts,
                "gaps": coverage.gaps,
                "calculated_at": coverage.calculated_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get coverage for agent {agent_id}: {e}")
            raise

    # Helper Methods

    def _agent_to_dict(self, agent: Agent) -> Dict[str, Any]:
        """Convert agent entity to dictionary for API response."""
        return {
            "agent_id": str(agent.agent_id),
            "name": agent.name,
            "taxonomy_node_ids": [str(nid) for nid in agent.taxonomy_node_ids],
            "taxonomy_version": agent.taxonomy_version,
            "scope_description": agent.scope_description,
            "coverage_percent": agent.coverage_percent,
            "total_documents": agent.total_documents,
            "total_chunks": agent.total_chunks,
            "level": agent.level,
            "current_xp": agent.current_xp,
            "xp_to_next_level": agent.xp_to_next_level,
            "level_progress": agent.level_progress,
            "stats": {
                "total_queries": agent.stats.total_queries,
                "successful_queries": agent.stats.successful_queries,
                "avg_faithfulness": agent.stats.avg_faithfulness,
                "avg_response_time_ms": agent.stats.avg_response_time_ms,
            },
            "config": {
                "top_k": agent.config.top_k,
                "enable_reranking": agent.config.enable_reranking,
                "enable_casebank": agent.config.enable_casebank,
                "enable_classification": agent.config.enable_classification,
            },
            "avatar_url": agent.avatar_url,
            "rarity": agent.rarity,
            "character_description": agent.character_description,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
            "last_query_at": agent.last_query_at.isoformat() if agent.last_query_at else None,
        }
