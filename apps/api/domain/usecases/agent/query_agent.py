"""
Query Agent Use Case

Business logic for querying an agent's knowledge scope.

@CODE:CLEAN-ARCHITECTURE-QUERY-AGENT
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import UUID
import time

from ...entities.search import SearchResult, SearchStrategy
from ...repositories.agent_repository import IAgentRepository
from ...repositories.search_repository import ISearchRepository, SearchParams
from .get_agent_by_id import AgentNotFoundError


@dataclass
class QueryAgentInput:
    """Input for QueryAgentUseCase"""
    query: str
    top_k: Optional[int] = None
    include_metadata: bool = True
    enable_reranking: bool = True


@dataclass
class QueryAgentResult:
    """Result of QueryAgentUseCase"""
    agent_id: UUID
    query: str
    results: List[SearchResult]
    total_results: int
    query_time_ms: float
    retrieval_strategy: str
    executed_at: datetime = field(default_factory=datetime.utcnow)


class QueryAgentUseCase:
    """
    Query Agent Use Case

    Queries an agent's knowledge scope using hybrid search.

    Business Logic:
    - Restrict search to agent's taxonomy scope
    - Track query statistics
    - Calculate XP from query
    - Apply agent's retrieval configuration
    """

    def __init__(
        self,
        agent_repository: IAgentRepository,
        search_repository: ISearchRepository,
    ):
        self._agent_repository = agent_repository
        self._search_repository = search_repository

    async def execute(
        self,
        agent_id: UUID,
        input_data: QueryAgentInput,
    ) -> QueryAgentResult:
        """
        Execute the use case.

        Args:
            agent_id: Agent to query
            input_data: Query parameters

        Returns:
            QueryAgentResult with search results

        Raises:
            AgentNotFoundError: If agent doesn't exist
            ValueError: If query is empty
        """
        # Validate input
        if not input_data.query or not input_data.query.strip():
            raise ValueError("Query cannot be empty")

        # Get agent
        agent = await self._agent_repository.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(agent_id)

        start_time = time.time()

        # Build search params with agent's configuration
        top_k = input_data.top_k or agent.config.retrieval_config.get("top_k", 5)
        strategy = agent.config.retrieval_config.get("strategy", "hybrid")

        # Build taxonomy filter from agent scope
        taxonomy_filter = [[str(nid)] for nid in agent.taxonomy_node_ids]

        search_params = SearchParams(
            query=input_data.query.strip(),
            top_k=top_k,
            strategy=SearchStrategy(strategy),
            bm25_weight=agent.config.retrieval_config.get("bm25_weight", 0.5),
            vector_weight=agent.config.retrieval_config.get("vector_weight", 0.5),
            enable_reranking=input_data.enable_reranking and
                agent.config.features_config.get("reranking_enabled", True),
            filters={
                "canonical_in": taxonomy_filter,
                "version": agent.taxonomy_version,
            },
            include_metadata=input_data.include_metadata,
        )

        # Execute search
        results = await self._search_repository.hybrid_search(search_params)

        query_time_ms = (time.time() - start_time) * 1000

        # Update agent query statistics (fire and forget)
        await self._update_agent_stats(
            agent_id=agent_id,
            success=len(results) > 0,
            latency_ms=query_time_ms,
        )

        return QueryAgentResult(
            agent_id=agent_id,
            query=input_data.query,
            results=results,
            total_results=len(results),
            query_time_ms=query_time_ms,
            retrieval_strategy=strategy,
            executed_at=datetime.utcnow(),
        )

    async def _update_agent_stats(
        self,
        agent_id: UUID,
        success: bool,
        latency_ms: float,
        faithfulness: float = 1.0,
    ) -> None:
        """Update agent statistics after query"""
        try:
            await self._agent_repository.increment_query_count(
                agent_id=agent_id,
                success=success,
                latency_ms=latency_ms,
                faithfulness=faithfulness,
            )

            # Calculate and award XP
            agent = await self._agent_repository.get_by_id(agent_id)
            if agent:
                xp_gained = agent.calculate_query_xp(latency_ms, faithfulness)
                new_level = None

                if agent.current_xp + xp_gained >= agent.xp_for_next_level:
                    new_level = min(100, agent.level + 1)

                await self._agent_repository.update_xp_and_level(
                    agent_id=agent_id,
                    xp_gained=xp_gained,
                    new_level=new_level,
                )
        except Exception:
            # Don't fail the query if stats update fails
            pass
