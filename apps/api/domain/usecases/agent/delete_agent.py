"""
Delete Agent Use Case

Business logic for deleting agents.

@CODE:CLEAN-ARCHITECTURE-DELETE-AGENT
"""

from uuid import UUID

from ...repositories.agent_repository import IAgentRepository
from .get_agent_by_id import AgentNotFoundError


class DeleteAgentUseCase:
    """
    Delete Agent Use Case

    Permanently deletes an agent and all associated data.

    Business Rules:
    - Agent must exist
    - Deletion is permanent (no soft delete)
    - Associated background tasks are cancelled
    """

    def __init__(self, agent_repository: IAgentRepository):
        self._agent_repository = agent_repository

    async def execute(self, agent_id: UUID) -> bool:
        """
        Execute the use case.

        Args:
            agent_id: Agent to delete

        Returns:
            True if deleted successfully

        Raises:
            AgentNotFoundError: If agent doesn't exist
        """
        # Verify agent exists
        existing = await self._agent_repository.get_by_id(agent_id)
        if existing is None:
            raise AgentNotFoundError(agent_id)

        # Delete agent
        success = await self._agent_repository.delete(agent_id)

        return success
