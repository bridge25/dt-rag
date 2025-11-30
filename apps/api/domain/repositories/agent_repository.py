"""
Agent Repository Interface

Defines the contract for Agent data access operations.
Implementation can be PostgreSQL, Mock, or any other data source.

@CODE:CLEAN-ARCHITECTURE-AGENT-REPOSITORY
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from ..entities.agent import Agent, AgentStats, AgentConfig


@dataclass
class AgentFilterParams:
    """Parameters for filtering agent queries"""
    status: Optional[str] = None
    level_min: Optional[int] = None
    level_max: Optional[int] = None
    min_coverage: Optional[float] = None
    max_coverage: Optional[float] = None
    taxonomy_version: Optional[str] = None
    name_contains: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class CreateAgentParams:
    """Parameters for creating a new agent"""
    name: str
    taxonomy_node_ids: List[UUID]
    taxonomy_version: str
    scope_description: Optional[str] = None
    retrieval_config: Dict[str, Any] = field(default_factory=dict)
    features_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateAgentParams:
    """Parameters for updating an agent"""
    name: Optional[str] = None
    scope_description: Optional[str] = None
    retrieval_config: Optional[Dict[str, Any]] = None
    features_config: Optional[Dict[str, Any]] = None
    coverage_percent: Optional[float] = None
    total_documents: Optional[int] = None
    total_chunks: Optional[int] = None
    level: Optional[int] = None
    current_xp: Optional[float] = None
    total_queries: Optional[int] = None
    successful_queries: Optional[int] = None
    avg_faithfulness: Optional[float] = None
    avg_response_time_ms: Optional[float] = None
    avatar_url: Optional[str] = None
    rarity: Optional[str] = None
    character_description: Optional[str] = None
    last_query_at: Optional[datetime] = None
    last_coverage_update: Optional[datetime] = None


@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    agent_id: UUID
    total_queries: int
    successful_queries: int
    avg_latency_ms: float
    avg_faithfulness: float
    queries_today: int
    queries_this_week: int
    level_progress_percent: float


@dataclass
class AgentCoverage:
    """Agent coverage breakdown"""
    agent_id: UUID
    overall_coverage: float
    node_coverage: Dict[str, float]  # node_id -> coverage percent
    document_counts: Dict[str, int]  # node_id -> doc count
    target_counts: Dict[str, int]  # node_id -> target doc count
    gaps: List[str]  # node_ids with low coverage
    calculated_at: datetime


class IAgentRepository(ABC):
    """
    Agent Repository Interface

    Defines all data access operations for Agent entities.
    Implementations must provide concrete data access logic.
    """

    @abstractmethod
    async def get_by_id(self, agent_id: UUID) -> Optional[Agent]:
        """
        Get agent by ID.

        Args:
            agent_id: Unique agent identifier

        Returns:
            Agent if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all(self, params: Optional[AgentFilterParams] = None) -> List[Agent]:
        """
        Get all agents with optional filtering.

        Args:
            params: Filter parameters

        Returns:
            List of agents matching filters
        """
        pass

    @abstractmethod
    async def search(self, query: str, max_results: int = 50) -> List[Agent]:
        """
        Search agents by name.

        Args:
            query: Search query string
            max_results: Maximum results to return

        Returns:
            List of matching agents
        """
        pass

    @abstractmethod
    async def create(self, params: CreateAgentParams) -> Agent:
        """
        Create a new agent.

        Args:
            params: Agent creation parameters

        Returns:
            Created agent entity
        """
        pass

    @abstractmethod
    async def update(self, agent_id: UUID, params: UpdateAgentParams) -> Agent:
        """
        Update an existing agent.

        Args:
            agent_id: Agent to update
            params: Update parameters

        Returns:
            Updated agent entity

        Raises:
            ValueError: If agent not found
        """
        pass

    @abstractmethod
    async def delete(self, agent_id: UUID) -> bool:
        """
        Delete an agent.

        Args:
            agent_id: Agent to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def get_metrics(self, agent_id: UUID) -> AgentMetrics:
        """
        Get agent performance metrics.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent metrics

        Raises:
            ValueError: If agent not found
        """
        pass

    @abstractmethod
    async def get_coverage(self, agent_id: UUID) -> AgentCoverage:
        """
        Get agent coverage breakdown.

        Args:
            agent_id: Agent identifier

        Returns:
            Coverage details

        Raises:
            ValueError: If agent not found
        """
        pass

    @abstractmethod
    async def increment_query_count(
        self,
        agent_id: UUID,
        success: bool,
        latency_ms: float,
        faithfulness: float
    ) -> None:
        """
        Increment agent query statistics.

        Args:
            agent_id: Agent identifier
            success: Whether query was successful
            latency_ms: Query latency in milliseconds
            faithfulness: Faithfulness score (0-1)
        """
        pass

    @abstractmethod
    async def update_xp_and_level(
        self,
        agent_id: UUID,
        xp_gained: float,
        new_level: Optional[int] = None
    ) -> Agent:
        """
        Update agent XP and optionally level.

        Args:
            agent_id: Agent identifier
            xp_gained: XP to add
            new_level: Optional new level

        Returns:
            Updated agent
        """
        pass

    @abstractmethod
    async def count(self, params: Optional[AgentFilterParams] = None) -> int:
        """
        Count agents matching filters.

        Args:
            params: Filter parameters

        Returns:
            Number of matching agents
        """
        pass
