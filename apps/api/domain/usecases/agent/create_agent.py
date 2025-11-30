"""
Create Agent Use Case

Business logic for creating new agents.

@CODE:CLEAN-ARCHITECTURE-CREATE-AGENT
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from uuid import UUID

from ...entities.agent import Agent
from ...repositories.agent_repository import IAgentRepository, CreateAgentParams
from ...repositories.taxonomy_repository import ITaxonomyRepository


class InvalidTaxonomyNodesError(Exception):
    """Raised when taxonomy nodes are invalid"""
    def __init__(self, invalid_ids: List[str]):
        self.invalid_ids = invalid_ids
        super().__init__(f"Invalid taxonomy node IDs: {', '.join(invalid_ids)}")


class AgentNameExistsError(Exception):
    """Raised when agent name already exists"""
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Agent with name '{name}' already exists")


@dataclass
class CreateAgentInput:
    """Input for CreateAgentUseCase"""
    name: str
    taxonomy_node_ids: List[UUID]
    taxonomy_version: str
    scope_description: Optional[str] = None
    retrieval_config: Dict[str, Any] = field(default_factory=lambda: {
        "strategy": "hybrid",
        "top_k": 5,
    })
    features_config: Dict[str, Any] = field(default_factory=lambda: {
        "reranking_enabled": True,
    })


class CreateAgentUseCase:
    """
    Create Agent Use Case

    Creates a new agent with validated taxonomy scope.

    Business Rules:
    - Agent name must be unique
    - Taxonomy nodes must exist in specified version
    - At least one taxonomy node required
    - Initial coverage is calculated after creation
    """

    def __init__(
        self,
        agent_repository: IAgentRepository,
        taxonomy_repository: ITaxonomyRepository,
    ):
        self._agent_repository = agent_repository
        self._taxonomy_repository = taxonomy_repository

    async def execute(self, input_data: CreateAgentInput) -> Agent:
        """
        Execute the use case.

        Args:
            input_data: Agent creation parameters

        Returns:
            Created agent entity

        Raises:
            InvalidTaxonomyNodesError: If taxonomy nodes don't exist
            AgentNameExistsError: If name already taken
            ValueError: If validation fails
        """
        # Validate input
        if not input_data.name or not input_data.name.strip():
            raise ValueError("Agent name cannot be empty")

        if not input_data.taxonomy_node_ids:
            raise ValueError("At least one taxonomy node is required")

        # Validate taxonomy nodes exist
        await self._validate_taxonomy_nodes(
            input_data.taxonomy_node_ids,
            input_data.taxonomy_version,
        )

        # Check for duplicate name
        existing = await self._agent_repository.search(
            input_data.name.strip(),
            max_results=1,
        )
        for agent in existing:
            if agent.name.lower() == input_data.name.strip().lower():
                raise AgentNameExistsError(input_data.name)

        # Create agent
        params = CreateAgentParams(
            name=input_data.name.strip(),
            taxonomy_node_ids=input_data.taxonomy_node_ids,
            taxonomy_version=input_data.taxonomy_version,
            scope_description=input_data.scope_description,
            retrieval_config=input_data.retrieval_config,
            features_config=input_data.features_config,
        )

        agent = await self._agent_repository.create(params)

        return agent

    async def _validate_taxonomy_nodes(
        self,
        node_ids: List[UUID],
        version: str,
    ) -> None:
        """Validate that all taxonomy nodes exist"""
        invalid_ids = []

        for node_id in node_ids:
            node = await self._taxonomy_repository.get_node_by_id(node_id, version)
            if node is None:
                invalid_ids.append(str(node_id))

        if invalid_ids:
            raise InvalidTaxonomyNodesError(invalid_ids)
