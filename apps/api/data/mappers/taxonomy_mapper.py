"""
Taxonomy Mapper - ORM ↔ Entity Transformer

Transforms between SQLAlchemy Taxonomy models and Domain entities.

@CODE:CLEAN-ARCHITECTURE-TAXONOMY-MAPPER
"""

from typing import Any, List
from uuid import UUID
from datetime import datetime

from ...domain.entities.taxonomy import TaxonomyNode, TaxonomyEdge, TaxonomyTree
# Import from existing database module
from ...database import TaxonomyNode as NodeModel, TaxonomyEdge as EdgeModel


class TaxonomyMapper:
    """
    Taxonomy Mapper

    Transforms between database models and domain entities.
    """

    @staticmethod
    def node_to_domain(model: NodeModel) -> TaxonomyNode:
        """
        Transform TaxonomyNode ORM model to domain entity.

        Args:
            model: SQLAlchemy TaxonomyNode model

        Returns:
            Domain TaxonomyNode entity
        """
        return TaxonomyNode(
            node_id=model.node_id if isinstance(model.node_id, UUID) else UUID(str(model.node_id)),
            label=model.label or "",
            canonical_path=model.canonical_path or [],
            version=model.version or "1.0.0",
            confidence=model.confidence or 1.0,
            description=None,  # Not in current model
            parent_id=None,  # Derived from edges
            metadata={},
            created_at=datetime.utcnow(),  # Not in current model
        )

    @staticmethod
    def edge_to_domain(model: EdgeModel) -> TaxonomyEdge:
        """
        Transform TaxonomyEdge ORM model to domain entity.

        Args:
            model: SQLAlchemy TaxonomyEdge model

        Returns:
            Domain TaxonomyEdge entity
        """
        return TaxonomyEdge(
            parent_id=model.parent if isinstance(model.parent, UUID) else UUID(str(model.parent)),
            child_id=model.child if isinstance(model.child, UUID) else UUID(str(model.child)),
            version=model.version,
            weight=1.0,
        )

    @staticmethod
    def node_to_model_dict(entity: TaxonomyNode) -> dict[str, Any]:
        """
        Transform TaxonomyNode entity to model dictionary.

        Args:
            entity: Domain TaxonomyNode entity

        Returns:
            Dictionary for ORM model
        """
        return {
            "node_id": entity.node_id,
            "label": entity.label,
            "canonical_path": entity.canonical_path,
            "version": entity.version,
            "confidence": entity.confidence,
        }

    @staticmethod
    def edge_to_model_dict(entity: TaxonomyEdge) -> dict[str, Any]:
        """
        Transform TaxonomyEdge entity to model dictionary.

        Args:
            entity: Domain TaxonomyEdge entity

        Returns:
            Dictionary for ORM model
        """
        return {
            "parent": entity.parent_id,
            "child": entity.child_id,
            "version": entity.version,
        }

    @staticmethod
    def build_tree_from_nodes_and_edges(
        nodes: List[TaxonomyNode],
        edges: List[TaxonomyEdge],
        version: str,
    ) -> TaxonomyTree:
        """
        Build TaxonomyTree from nodes and edges.

        Args:
            nodes: List of taxonomy nodes
            edges: List of taxonomy edges
            version: Taxonomy version

        Returns:
            TaxonomyTree entity
        """
        return TaxonomyTree(
            version=version,
            nodes=nodes,
            edges=edges,
            metadata={
                "total_nodes": len(nodes),
                "total_edges": len(edges),
            },
            created_at=datetime.utcnow(),
        )
