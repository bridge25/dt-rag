"""
Get Agent By ID Use Case

Business logic for retrieving a single agent.

@CODE:CLEAN-ARCHITECTURE-GET-AGENT-BY-ID
"""

from uuid import UUID

from ...entities.agent import Agent, get_recommended_actions
from ...repositories.agent_repository import IAgentRepository


class AgentNotFoundError(Exception):
    """Raised when agent is not found"""
    def __init__(self, agent_id: UUID):
        self.agent_id = agent_id
        super().__init__(f"Agent not found: {agent_id}")


class GetAgentByIdUseCase:
    """
    Get Agent By ID Use Case

    Retrieves a specific agent by ID with optional
    recommendation generation.
    """

    def __init__(self, agent_repository: IAgentRepository):
        self._agent_repository = agent_repository

    async def execute(
        self,
        agent_id: UUID,
        include_recommendations: bool = False,
    ) -> Agent:
        """
        Execute the use case.

        Args:
            agent_id: Agent identifier
            include_recommendations: Generate improvement recommendations

        Returns:
            Agent entity

        Raises:
            AgentNotFoundError: If agent doesn't exist
        """
        agent = await self._agent_repository.get_by_id(agent_id)

        if agent is None:
            raise AgentNotFoundError(agent_id)

        return agent

    async def execute_with_recommendations(
        self,
        agent_id: UUID,
    ) -> tuple[Agent, list[str]]:
        """
        Execute and include recommendations.

        Args:
            agent_id: Agent identifier

        Returns:
            Tuple of (Agent, recommendations list)
        """
        agent = await self.execute(agent_id)
        recommendations = get_recommended_actions(agent)

        return agent, recommendations
