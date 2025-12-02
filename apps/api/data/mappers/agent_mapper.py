"""
Agent Mapper - ORM ↔ Entity Transformer

Transforms between SQLAlchemy Agent model and Domain Agent entity.

@CODE:CLEAN-ARCHITECTURE-AGENT-MAPPER
"""

from typing import Any
from uuid import UUID
from datetime import datetime

from ...domain.entities.agent import (
    Agent,
    AgentStatus,
    AgentRarity,
    AgentStats,
    AgentConfig,
)
# Import from existing database module
from ...database import Agent as AgentModel


class AgentMapper:
    """
    Agent Mapper

    Transforms between database model and domain entity.

    ORM Model (snake_case) ↔ Domain Entity (camelCase)
    """

    @staticmethod
    def to_domain(model: AgentModel) -> Agent:
        """
        Transform ORM model to domain entity.

        Args:
            model: SQLAlchemy Agent model

        Returns:
            Domain Agent entity
        """
        # Map status
        status = AgentStatus.ACTIVE
        if hasattr(model, 'status'):
            try:
                status = AgentStatus(model.status)
            except (ValueError, AttributeError):
                status = AgentStatus.ACTIVE

        # Map rarity
        rarity = AgentRarity.COMMON
        if model.rarity:
            try:
                rarity = AgentRarity(model.rarity)
            except ValueError:
                rarity = AgentRarity.COMMON

        # Build stats
        stats = AgentStats(
            total_queries=model.total_queries,
            successful_queries=model.successful_queries,
            avg_faithfulness=model.avg_faithfulness,
            avg_response_time_ms=model.avg_response_time_ms,
        )

        # Build config
        config = AgentConfig(
            retrieval_config=model.retrieval_config or {},
            features_config=model.features_config or {},
        )

        # Map taxonomy_node_ids (handle both UUID and string)
        taxonomy_node_ids = []
        if model.taxonomy_node_ids:
            for nid in model.taxonomy_node_ids:
                if isinstance(nid, UUID):
                    taxonomy_node_ids.append(nid)
                else:
                    taxonomy_node_ids.append(UUID(str(nid)))

        return Agent(
            agent_id=model.agent_id if isinstance(model.agent_id, UUID) else UUID(str(model.agent_id)),
            name=model.name,
            taxonomy_node_ids=taxonomy_node_ids,
            taxonomy_version=model.taxonomy_version,
            coverage_percent=model.coverage_percent,
            total_documents=model.total_documents,
            total_chunks=model.total_chunks,
            level=model.level,
            current_xp=model.current_xp,
            stats=stats,
            config=config,
            status=status,
            scope_description=model.scope_description,
            avatar_url=model.avatar_url,
            rarity=rarity,
            character_description=model.character_description,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_query_at=model.last_query_at,
            last_coverage_update=model.last_coverage_update,
        )

    @staticmethod
    def to_model_dict(entity: Agent) -> dict[str, Any]:
        """
        Transform domain entity to model dictionary.

        Used for creating/updating ORM models.

        Args:
            entity: Domain Agent entity

        Returns:
            Dictionary for ORM model
        """
        return {
            "agent_id": entity.agent_id,
            "name": entity.name,
            "taxonomy_node_ids": [str(nid) for nid in entity.taxonomy_node_ids],
            "taxonomy_version": entity.taxonomy_version,
            "coverage_percent": entity.coverage_percent,
            "total_documents": entity.total_documents,
            "total_chunks": entity.total_chunks,
            "level": entity.level,
            "current_xp": entity.current_xp,
            "total_queries": entity.stats.total_queries,
            "successful_queries": entity.stats.successful_queries,
            "avg_faithfulness": entity.stats.avg_faithfulness,
            "avg_response_time_ms": entity.stats.avg_response_time_ms,
            "retrieval_config": entity.config.retrieval_config,
            "features_config": entity.config.features_config,
            "scope_description": entity.scope_description,
            "avatar_url": entity.avatar_url,
            "rarity": entity.rarity.value if entity.rarity else None,
            "character_description": entity.character_description,
            "created_at": entity.created_at,
            "updated_at": datetime.utcnow(),
            "last_query_at": entity.last_query_at,
            "last_coverage_update": entity.last_coverage_update,
        }

    @staticmethod
    def update_model(model: AgentModel, updates: dict[str, Any]) -> AgentModel:
        """
        Apply updates to ORM model.

        Args:
            model: SQLAlchemy Agent model to update
            updates: Dictionary of updates

        Returns:
            Updated model (same instance)
        """
        for key, value in updates.items():
            if value is not None and hasattr(model, key):
                setattr(model, key, value)

        model.updated_at = datetime.utcnow()
        return model
