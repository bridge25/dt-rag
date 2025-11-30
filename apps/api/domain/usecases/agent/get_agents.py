"""
Get Agents Use Case

Business logic for retrieving and filtering agents.

@CODE:CLEAN-ARCHITECTURE-GET-AGENTS
"""

from dataclasses import dataclass
from typing import Optional, List

from ...entities.agent import Agent, calculate_agent_health_score
from ...repositories.agent_repository import IAgentRepository, AgentFilterParams


@dataclass
class GetAgentsResult:
    """Result of GetAgentsUseCase"""
    agents: List[Agent]
    total: int
    performant_count: int
    average_health_score: float
    average_coverage: float


class GetAgentsUseCase:
    """
    Get Agents Use Case

    Retrieves agents with optional filtering and calculates
    aggregate statistics.

    Business Logic:
    - Filter agents by status, level, coverage
    - Calculate performance metrics
    - Sort by health score or other criteria
    """

    def __init__(self, agent_repository: IAgentRepository):
        """
        Initialize use case with repository.

        Args:
            agent_repository: Agent data access
        """
        self._agent_repository = agent_repository

    async def execute(
        self,
        status: Optional[str] = None,
        level_min: Optional[int] = None,
        level_max: Optional[int] = None,
        min_coverage: Optional[float] = None,
        max_coverage: Optional[float] = None,
        taxonomy_version: Optional[str] = None,
        name_contains: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> GetAgentsResult:
        """
        Execute the use case.

        Args:
            status: Filter by agent status
            level_min: Minimum level filter
            level_max: Maximum level filter
            min_coverage: Minimum coverage filter
            max_coverage: Maximum coverage filter
            taxonomy_version: Filter by taxonomy version
            name_contains: Search by name
            limit: Maximum results
            offset: Pagination offset

        Returns:
            GetAgentsResult with agents and statistics
        """
        # Build filter params
        params = AgentFilterParams(
            status=status,
            level_min=level_min,
            level_max=level_max,
            min_coverage=min_coverage,
            max_coverage=max_coverage,
            taxonomy_version=taxonomy_version,
            name_contains=name_contains,
            limit=limit,
            offset=offset,
        )

        # Fetch agents
        agents = await self._agent_repository.get_all(params)
        total = await self._agent_repository.count(params)

        # Calculate statistics
        if agents:
            health_scores = [calculate_agent_health_score(a) for a in agents]
            performant_agents = [a for a in agents if a.stats.is_performant]
            coverages = [a.coverage_percent for a in agents]

            return GetAgentsResult(
                agents=agents,
                total=total,
                performant_count=len(performant_agents),
                average_health_score=sum(health_scores) / len(health_scores),
                average_coverage=sum(coverages) / len(coverages),
            )

        return GetAgentsResult(
            agents=[],
            total=0,
            performant_count=0,
            average_health_score=0.0,
            average_coverage=0.0,
        )
