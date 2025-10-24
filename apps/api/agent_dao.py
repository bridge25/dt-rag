import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.database import Agent, TaxonomyNode
from apps.knowledge_builder.coverage.meter import CoverageMeterService

logger = logging.getLogger(__name__)


class AgentDAO:
    # @IMPL:AGENT-GROWTH-001:0.3.1
    @staticmethod
    async def create_agent(
        session: AsyncSession,
        name: str,
        taxonomy_node_ids: List[UUID],
        taxonomy_version: str = "1.0.0",
        scope_description: Optional[str] = None,
        retrieval_config: Optional[Dict[str, Any]] = None,
        features_config: Optional[Dict[str, Any]] = None,
    ) -> Agent:
        node_ids_str = [str(nid) for nid in taxonomy_node_ids]

        query = select(TaxonomyNode.node_id).where(
            TaxonomyNode.node_id.in_(taxonomy_node_ids),
            TaxonomyNode.version == taxonomy_version,
        )
        result = await session.execute(query)
        existing_nodes = result.scalars().all()

        if len(existing_nodes) != len(taxonomy_node_ids):
            raise ValueError(
                f"Some taxonomy nodes do not exist for version {taxonomy_version}"
            )

        coverage_service = CoverageMeterService(session_factory=lambda: session)
        metrics = await coverage_service.calculate_coverage(
            taxonomy_version=taxonomy_version, node_ids=node_ids_str
        )

        default_retrieval_config = {"top_k": 5, "strategy": "hybrid"}
        default_features_config = {}

        agent = Agent(
            name=name,
            taxonomy_node_ids=taxonomy_node_ids,
            taxonomy_version=taxonomy_version,
            scope_description=scope_description,
            total_documents=metrics.total_documents,
            total_chunks=metrics.total_chunks,
            coverage_percent=metrics.coverage_percent,
            last_coverage_update=datetime.utcnow(),
            level=1,
            current_xp=0,
            total_queries=0,
            successful_queries=0,
            avg_faithfulness=0.0,
            avg_response_time_ms=0.0,
            retrieval_config=retrieval_config or default_retrieval_config,
            features_config=features_config or default_features_config,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_query_at=None,
        )

        session.add(agent)
        await session.commit()
        await session.refresh(agent)

        logger.info(f"Agent created: {agent.agent_id} - {agent.name}")

        return agent

    # @IMPL:AGENT-GROWTH-001:0.3.2
    @staticmethod
    async def get_agent(session: AsyncSession, agent_id: UUID) -> Optional[Agent]:
        query = select(Agent).where(Agent.agent_id == agent_id)
        result = await session.execute(query)
        agent = result.scalar_one_or_none()

        return agent

    # @IMPL:AGENT-GROWTH-001:0.3.3
    @staticmethod
    async def update_agent(session: AsyncSession, agent_id: UUID, **kwargs) -> Agent:
        query = select(Agent).where(Agent.agent_id == agent_id)
        result = await session.execute(query)
        agent = result.scalar_one_or_none()

        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found")

        for key, value in kwargs.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        agent.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(agent)

        logger.info(f"Agent updated: {agent.agent_id} - {agent.name}")

        return agent

    # @IMPL:AGENT-GROWTH-001:0.3.4
    @staticmethod
    async def delete_agent(session: AsyncSession, agent_id: UUID) -> bool:
        query = select(Agent).where(Agent.agent_id == agent_id)
        result = await session.execute(query)
        agent = result.scalar_one_or_none()

        if not agent:
            return False

        await session.delete(agent)
        await session.commit()

        logger.info(f"Agent deleted: {agent_id}")

        return True

    # @IMPL:AGENT-GROWTH-001:0.3.5
    @staticmethod
    async def list_agents(
        session: AsyncSession,
        level: Optional[int] = None,
        min_coverage: Optional[float] = None,
        max_results: int = 50,
    ) -> List[Agent]:
        query = select(Agent).order_by(Agent.created_at.desc())

        if level is not None:
            query = query.where(Agent.level == level)

        if min_coverage is not None:
            query = query.where(Agent.coverage_percent >= min_coverage)

        query = query.limit(max_results)

        result = await session.execute(query)
        agents = result.scalars().all()

        return list(agents)
