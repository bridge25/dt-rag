"""
Update Agent Use Case

Business logic for updating agent configuration.

@CODE:CLEAN-ARCHITECTURE-UPDATE-AGENT
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from uuid import UUID

from ...entities.agent import Agent
from ...repositories.agent_repository import IAgentRepository, UpdateAgentParams
from .get_agent_by_id import AgentNotFoundError


@dataclass
class UpdateAgentInput:
    """Input for UpdateAgentUseCase"""
    name: Optional[str] = None
    scope_description: Optional[str] = None
    retrieval_config: Optional[Dict[str, Any]] = None
    features_config: Optional[Dict[str, Any]] = None


class UpdateAgentUseCase:
    """
    Update Agent Use Case

    Updates agent configuration fields.

    Business Rules:
    - Only specified fields are updated
    - Name must be unique if changed
    - Config changes are merged, not replaced
    """

    def __init__(self, agent_repository: IAgentRepository):
        self._agent_repository = agent_repository

    async def execute(
        self,
        agent_id: UUID,
        input_data: UpdateAgentInput,
    ) -> Agent:
        """
        Execute the use case.

        Args:
            agent_id: Agent to update
            input_data: Update parameters

        Returns:
            Updated agent entity

        Raises:
            AgentNotFoundError: If agent doesn't exist
        """
        # Verify agent exists
        existing = await self._agent_repository.get_by_id(agent_id)
        if existing is None:
            raise AgentNotFoundError(agent_id)

        # Build update params (only non-None values)
        params = UpdateAgentParams(
            name=input_data.name,
            scope_description=input_data.scope_description,
            retrieval_config=input_data.retrieval_config,
            features_config=input_data.features_config,
        )

        # Check if there's anything to update
        has_updates = any([
            params.name is not None,
            params.scope_description is not None,
            params.retrieval_config is not None,
            params.features_config is not None,
        ])

        if not has_updates:
            return existing

        return await self._agent_repository.update(agent_id, params)
