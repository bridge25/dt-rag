"""
Agent Repository Implementation

SQLAlchemy implementation of IAgentRepository interface.

@CODE:CLEAN-ARCHITECTURE-AGENT-REPOSITORY-IMPL
"""

from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ...domain.entities.agent import Agent
from ...domain.repositories.agent_repository import (
    IAgentRepository,
    AgentFilterParams,
    CreateAgentParams,
    UpdateAgentParams,
    AgentMetrics,
    AgentCoverage,
)
from ..mappers.agent_mapper import AgentMapper
from ...database import Agent as AgentModel

logger = logging.getLogger(__name__)


class AgentRepositoryImpl(IAgentRepository):
    """
    Agent Repository Implementation

    SQLAlchemy-based implementation of agent data access.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def get_by_id(self, agent_id: UUID) -> Optional[Agent]:
        """Get agent by ID"""
        try:
            result = await self._session.execute(
                select(AgentModel).where(AgentModel.agent_id == agent_id)
            )
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return AgentMapper.to_domain(model)
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            raise

    async def get_all(self, params: Optional[AgentFilterParams] = None) -> List[Agent]:
        """Get all agents with optional filtering"""
        try:
            query = select(AgentModel)

            if params:
                conditions = []

                if params.status:
                    # Status field may not exist in current model
                    pass

                if params.level_min is not None:
                    conditions.append(AgentModel.level >= params.level_min)

                if params.level_max is not None:
                    conditions.append(AgentModel.level <= params.level_max)

                if params.min_coverage is not None:
                    conditions.append(AgentModel.coverage_percent >= params.min_coverage)

                if params.max_coverage is not None:
                    conditions.append(AgentModel.coverage_percent <= params.max_coverage)

                if params.taxonomy_version:
                    conditions.append(AgentModel.taxonomy_version == params.taxonomy_version)

                if params.name_contains:
                    conditions.append(AgentModel.name.ilike(f"%{params.name_contains}%"))

                if conditions:
                    query = query.where(and_(*conditions))

                query = query.limit(params.limit).offset(params.offset)

            result = await self._session.execute(query)
            models = result.scalars().all()

            return [AgentMapper.to_domain(m) for m in models]
        except Exception as e:
            logger.error(f"Failed to get agents: {e}")
            raise

    async def search(self, query: str, max_results: int = 50) -> List[Agent]:
        """Search agents by name"""
        try:
            stmt = (
                select(AgentModel)
                .where(AgentModel.name.ilike(f"%{query}%"))
                .limit(max_results)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [AgentMapper.to_domain(m) for m in models]
        except Exception as e:
            logger.error(f"Failed to search agents: {e}")
            raise

    async def create(self, params: CreateAgentParams) -> Agent:
        """Create a new agent"""
        try:
            model = AgentModel(
                agent_id=uuid4(),
                name=params.name,
                taxonomy_node_ids=[str(nid) for nid in params.taxonomy_node_ids],
                taxonomy_version=params.taxonomy_version,
                scope_description=params.scope_description,
                retrieval_config=params.retrieval_config,
                features_config=params.features_config,
                coverage_percent=0.0,
                total_documents=0,
                total_chunks=0,
                level=1,
                current_xp=0.0,
                total_queries=0,
                successful_queries=0,
                avg_faithfulness=0.0,
                avg_response_time_ms=0.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self._session.add(model)
            await self._session.commit()
            await self._session.refresh(model)

            return AgentMapper.to_domain(model)
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to create agent: {e}")
            raise

    async def update(self, agent_id: UUID, params: UpdateAgentParams) -> Agent:
        """Update an existing agent"""
        try:
            result = await self._session.execute(
                select(AgentModel).where(AgentModel.agent_id == agent_id)
            )
            model = result.scalar_one_or_none()

            if model is None:
                raise ValueError(f"Agent not found: {agent_id}")

            # Apply updates
            update_dict = {}
            if params.name is not None:
                update_dict["name"] = params.name
            if params.scope_description is not None:
                update_dict["scope_description"] = params.scope_description
            if params.retrieval_config is not None:
                update_dict["retrieval_config"] = params.retrieval_config
            if params.features_config is not None:
                update_dict["features_config"] = params.features_config
            if params.coverage_percent is not None:
                update_dict["coverage_percent"] = params.coverage_percent
            if params.total_documents is not None:
                update_dict["total_documents"] = params.total_documents
            if params.total_chunks is not None:
                update_dict["total_chunks"] = params.total_chunks
            if params.level is not None:
                update_dict["level"] = params.level
            if params.current_xp is not None:
                update_dict["current_xp"] = params.current_xp
            if params.total_queries is not None:
                update_dict["total_queries"] = params.total_queries
            if params.successful_queries is not None:
                update_dict["successful_queries"] = params.successful_queries
            if params.avg_faithfulness is not None:
                update_dict["avg_faithfulness"] = params.avg_faithfulness
            if params.avg_response_time_ms is not None:
                update_dict["avg_response_time_ms"] = params.avg_response_time_ms
            if params.avatar_url is not None:
                update_dict["avatar_url"] = params.avatar_url
            if params.rarity is not None:
                update_dict["rarity"] = params.rarity
            if params.character_description is not None:
                update_dict["character_description"] = params.character_description
            if params.last_query_at is not None:
                update_dict["last_query_at"] = params.last_query_at
            if params.last_coverage_update is not None:
                update_dict["last_coverage_update"] = params.last_coverage_update

            update_dict["updated_at"] = datetime.utcnow()

            AgentMapper.update_model(model, update_dict)

            await self._session.commit()
            await self._session.refresh(model)

            return AgentMapper.to_domain(model)
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to update agent {agent_id}: {e}")
            raise

    async def delete(self, agent_id: UUID) -> bool:
        """Delete an agent"""
        try:
            result = await self._session.execute(
                select(AgentModel).where(AgentModel.agent_id == agent_id)
            )
            model = result.scalar_one_or_none()

            if model is None:
                return False

            await self._session.delete(model)
            await self._session.commit()

            return True
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            raise

    async def get_metrics(self, agent_id: UUID) -> AgentMetrics:
        """Get agent performance metrics"""
        agent = await self.get_by_id(agent_id)
        if agent is None:
            raise ValueError(f"Agent not found: {agent_id}")

        return AgentMetrics(
            agent_id=agent_id,
            total_queries=agent.stats.total_queries,
            successful_queries=agent.stats.successful_queries,
            avg_latency_ms=agent.stats.avg_response_time_ms,
            avg_faithfulness=agent.stats.avg_faithfulness,
            queries_today=0,  # Would need additional query
            queries_this_week=0,  # Would need additional query
            level_progress_percent=agent.level_progress,
        )

    async def get_coverage(self, agent_id: UUID) -> AgentCoverage:
        """Get agent coverage breakdown"""
        agent = await self.get_by_id(agent_id)
        if agent is None:
            raise ValueError(f"Agent not found: {agent_id}")

        return AgentCoverage(
            agent_id=agent_id,
            overall_coverage=agent.coverage_percent,
            node_coverage={str(nid): agent.coverage_percent for nid in agent.taxonomy_node_ids},
            document_counts={str(nid): agent.total_documents for nid in agent.taxonomy_node_ids},
            target_counts={str(nid): 10 for nid in agent.taxonomy_node_ids},
            gaps=[],
            calculated_at=datetime.utcnow(),
        )

    async def increment_query_count(
        self,
        agent_id: UUID,
        success: bool,
        latency_ms: float,
        faithfulness: float
    ) -> None:
        """Increment agent query statistics"""
        try:
            result = await self._session.execute(
                select(AgentModel).where(AgentModel.agent_id == agent_id)
            )
            model = result.scalar_one_or_none()

            if model is None:
                return

            # Update stats
            model.total_queries += 1
            if success:
                model.successful_queries += 1

            # Update rolling averages
            total = model.total_queries
            model.avg_response_time_ms = (
                (model.avg_response_time_ms * (total - 1) + latency_ms) / total
            )
            model.avg_faithfulness = (
                (model.avg_faithfulness * (total - 1) + faithfulness) / total
            )
            model.last_query_at = datetime.utcnow()
            model.updated_at = datetime.utcnow()

            await self._session.commit()
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to increment query count for {agent_id}: {e}")

    async def update_xp_and_level(
        self,
        agent_id: UUID,
        xp_gained: float,
        new_level: Optional[int] = None
    ) -> Agent:
        """Update agent XP and optionally level"""
        try:
            result = await self._session.execute(
                select(AgentModel).where(AgentModel.agent_id == agent_id)
            )
            model = result.scalar_one_or_none()

            if model is None:
                raise ValueError(f"Agent not found: {agent_id}")

            model.current_xp += xp_gained
            if new_level is not None:
                model.level = new_level
                # Reset XP for new level
                model.current_xp = model.current_xp - (new_level - 1) ** 2 * 100

            model.updated_at = datetime.utcnow()

            await self._session.commit()
            await self._session.refresh(model)

            return AgentMapper.to_domain(model)
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to update XP for {agent_id}: {e}")
            raise

    async def count(self, params: Optional[AgentFilterParams] = None) -> int:
        """Count agents matching filters"""
        try:
            query = select(func.count()).select_from(AgentModel)

            if params:
                conditions = []

                if params.level_min is not None:
                    conditions.append(AgentModel.level >= params.level_min)
                if params.level_max is not None:
                    conditions.append(AgentModel.level <= params.level_max)
                if params.min_coverage is not None:
                    conditions.append(AgentModel.coverage_percent >= params.min_coverage)
                if params.max_coverage is not None:
                    conditions.append(AgentModel.coverage_percent <= params.max_coverage)
                if params.taxonomy_version:
                    conditions.append(AgentModel.taxonomy_version == params.taxonomy_version)
                if params.name_contains:
                    conditions.append(AgentModel.name.ilike(f"%{params.name_contains}%"))

                if conditions:
                    query = query.where(and_(*conditions))

            result = await self._session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to count agents: {e}")
            raise
