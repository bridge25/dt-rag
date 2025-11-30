"""
Taxonomy Repository Implementation

SQLAlchemy implementation of ITaxonomyRepository interface.

@CODE:CLEAN-ARCHITECTURE-TAXONOMY-REPOSITORY-IMPL
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from ...domain.entities.taxonomy import TaxonomyNode, TaxonomyEdge, TaxonomyTree, TaxonomyMigration
from ...domain.repositories.taxonomy_repository import (
    ITaxonomyRepository,
    CreateNodeParams,
    TaxonomyVersionInfo,
    TaxonomyComparison,
)
from ..mappers.taxonomy_mapper import TaxonomyMapper
from ...database import TaxonomyNode as NodeModel, TaxonomyEdge as EdgeModel, TaxonomyMigration as MigrationModel

logger = logging.getLogger(__name__)


class TaxonomyRepositoryImpl(ITaxonomyRepository):
    """
    Taxonomy Repository Implementation

    SQLAlchemy-based implementation of taxonomy data access.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    # Version Operations

    async def list_versions(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[TaxonomyVersionInfo]:
        """List all taxonomy versions"""
        try:
            query = text("""
                SELECT DISTINCT version,
                       COUNT(*) as node_count,
                       MIN(node_id) as first_node_id
                FROM taxonomy_nodes
                WHERE version IS NOT NULL
                GROUP BY version
                ORDER BY version DESC
                LIMIT :limit OFFSET :offset
            """)

            result = await self._session.execute(
                query, {"limit": limit, "offset": offset}
            )
            rows = result.fetchall()

            versions = []
            for row in rows:
                versions.append(TaxonomyVersionInfo(
                    version=row[0],
                    node_count=row[1],
                    created_at=datetime.utcnow(),
                    created_by="system",
                    change_summary=f"Taxonomy version {row[0]}",
                    parent_version=None,
                    depth=0,
                ))

            if not versions:
                return [TaxonomyVersionInfo(
                    version="1.0.0",
                    node_count=0,
                    created_at=datetime.utcnow(),
                    created_by="system",
                )]

            return versions
        except Exception as e:
            logger.error(f"Failed to list versions: {e}")
            return [TaxonomyVersionInfo(
                version="1.0.0",
                node_count=0,
                created_at=datetime.utcnow(),
                created_by="system",
            )]

    async def get_latest_version(self) -> Optional[str]:
        """Get the latest taxonomy version string"""
        versions = await self.list_versions(limit=1)
        if versions:
            return versions[0].version
        return "1.0.0"

    # Tree Operations

    async def get_tree(self, version: str) -> TaxonomyTree:
        """Get complete taxonomy tree for a version"""
        try:
            # Get nodes
            node_result = await self._session.execute(
                select(NodeModel).where(NodeModel.version == version)
            )
            node_models = node_result.scalars().all()

            # Get edges
            edge_result = await self._session.execute(
                select(EdgeModel).where(EdgeModel.version == version)
            )
            edge_models = edge_result.scalars().all()

            nodes = [TaxonomyMapper.node_to_domain(m) for m in node_models]
            edges = [TaxonomyMapper.edge_to_domain(m) for m in edge_models]

            return TaxonomyMapper.build_tree_from_nodes_and_edges(nodes, edges, version)
        except Exception as e:
            logger.error(f"Failed to get tree for version {version}: {e}")
            return TaxonomyTree(version=version, nodes=[], edges=[])

    async def get_node_by_id(
        self,
        node_id: UUID,
        version: Optional[str] = None
    ) -> Optional[TaxonomyNode]:
        """Get a specific node by ID"""
        try:
            query = select(NodeModel).where(NodeModel.node_id == node_id)
            if version:
                query = query.where(NodeModel.version == version)

            result = await self._session.execute(query)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return TaxonomyMapper.node_to_domain(model)
        except Exception as e:
            logger.error(f"Failed to get node {node_id}: {e}")
            raise

    async def get_nodes_by_path(
        self,
        canonical_path: List[str],
        version: str
    ) -> List[TaxonomyNode]:
        """Get nodes matching a canonical path"""
        try:
            result = await self._session.execute(
                select(NodeModel).where(
                    NodeModel.version == version,
                    NodeModel.canonical_path == canonical_path
                )
            )
            models = result.scalars().all()

            return [TaxonomyMapper.node_to_domain(m) for m in models]
        except Exception as e:
            logger.error(f"Failed to get nodes by path: {e}")
            raise

    async def get_children(
        self,
        node_id: UUID,
        version: str
    ) -> List[TaxonomyNode]:
        """Get direct children of a node"""
        try:
            # Get child IDs from edges
            edge_result = await self._session.execute(
                select(EdgeModel.child).where(
                    EdgeModel.parent == node_id,
                    EdgeModel.version == version
                )
            )
            child_ids = [row[0] for row in edge_result.fetchall()]

            if not child_ids:
                return []

            # Get child nodes
            node_result = await self._session.execute(
                select(NodeModel).where(NodeModel.node_id.in_(child_ids))
            )
            models = node_result.scalars().all()

            return [TaxonomyMapper.node_to_domain(m) for m in models]
        except Exception as e:
            logger.error(f"Failed to get children for {node_id}: {e}")
            raise

    async def get_ancestors(
        self,
        node_id: UUID,
        version: str
    ) -> List[TaxonomyNode]:
        """Get all ancestors of a node (path to root)"""
        try:
            node = await self.get_node_by_id(node_id, version)
            if node is None:
                return []

            ancestors = []
            for i in range(len(node.canonical_path) - 1):
                path = node.canonical_path[:i + 1]
                nodes = await self.get_nodes_by_path(path, version)
                ancestors.extend(nodes)

            return ancestors
        except Exception as e:
            logger.error(f"Failed to get ancestors for {node_id}: {e}")
            raise

    # Node CRUD

    async def create_node(self, params: CreateNodeParams) -> TaxonomyNode:
        """Create a new taxonomy node"""
        try:
            model = NodeModel(
                node_id=uuid4(),
                label=params.label,
                canonical_path=params.canonical_path,
                version=params.version,
                confidence=params.confidence,
            )

            self._session.add(model)
            await self._session.commit()
            await self._session.refresh(model)

            return TaxonomyMapper.node_to_domain(model)
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to create node: {e}")
            raise

    async def create_nodes_batch(
        self,
        nodes: List[CreateNodeParams]
    ) -> List[TaxonomyNode]:
        """Create multiple nodes in batch"""
        try:
            models = []
            for params in nodes:
                model = NodeModel(
                    node_id=uuid4(),
                    label=params.label,
                    canonical_path=params.canonical_path,
                    version=params.version,
                    confidence=params.confidence,
                )
                models.append(model)

            self._session.add_all(models)
            await self._session.commit()

            for model in models:
                await self._session.refresh(model)

            return [TaxonomyMapper.node_to_domain(m) for m in models]
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to create nodes batch: {e}")
            raise

    async def update_node(
        self,
        node_id: UUID,
        label: Optional[str] = None,
        description: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TaxonomyNode:
        """Update a taxonomy node"""
        try:
            result = await self._session.execute(
                select(NodeModel).where(NodeModel.node_id == node_id)
            )
            model = result.scalar_one_or_none()

            if model is None:
                raise ValueError(f"Node not found: {node_id}")

            if label is not None:
                model.label = label
            if confidence is not None:
                model.confidence = confidence

            await self._session.commit()
            await self._session.refresh(model)

            return TaxonomyMapper.node_to_domain(model)
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to update node {node_id}: {e}")
            raise

    async def delete_node(self, node_id: UUID) -> bool:
        """Delete a taxonomy node"""
        try:
            result = await self._session.execute(
                select(NodeModel).where(NodeModel.node_id == node_id)
            )
            model = result.scalar_one_or_none()

            if model is None:
                return False

            await self._session.delete(model)
            await self._session.commit()

            return True
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to delete node {node_id}: {e}")
            raise

    # Edge Operations

    async def create_edge(
        self,
        parent_id: UUID,
        child_id: UUID,
        version: str
    ) -> TaxonomyEdge:
        """Create an edge between nodes"""
        try:
            model = EdgeModel(
                parent=parent_id,
                child=child_id,
                version=version,
            )

            self._session.add(model)
            await self._session.commit()

            return TaxonomyEdge(
                parent_id=parent_id,
                child_id=child_id,
                version=version,
            )
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to create edge: {e}")
            raise

    async def delete_edge(
        self,
        parent_id: UUID,
        child_id: UUID,
        version: str
    ) -> bool:
        """Delete an edge between nodes"""
        try:
            result = await self._session.execute(
                select(EdgeModel).where(
                    EdgeModel.parent == parent_id,
                    EdgeModel.child == child_id,
                    EdgeModel.version == version
                )
            )
            model = result.scalar_one_or_none()

            if model is None:
                return False

            await self._session.delete(model)
            await self._session.commit()

            return True
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to delete edge: {e}")
            raise

    # Version Management

    async def create_version(
        self,
        version: str,
        created_by: str,
        change_summary: Optional[str] = None,
        parent_version: Optional[str] = None
    ) -> TaxonomyVersionInfo:
        """Create a new taxonomy version"""
        return TaxonomyVersionInfo(
            version=version,
            node_count=0,
            created_at=datetime.utcnow(),
            created_by=created_by,
            change_summary=change_summary,
            parent_version=parent_version,
        )

    async def compare_versions(
        self,
        base_version: str,
        target_version: str
    ) -> TaxonomyComparison:
        """Compare two taxonomy versions"""
        base_tree = await self.get_tree(base_version)
        target_tree = await self.get_tree(target_version)

        base_map = {node.node_id: node for node in base_tree.nodes}
        target_map = {node.node_id: node for node in target_tree.nodes}

        added = [n for n in target_tree.nodes if n.node_id not in base_map]
        removed = [n for n in base_tree.nodes if n.node_id not in target_map]
        modified = []

        for node_id, target_node in target_map.items():
            if node_id in base_map:
                base_node = base_map[node_id]
                if base_node.label != target_node.label or base_node.canonical_path != target_node.canonical_path:
                    modified.append({
                        "node_id": str(node_id),
                        "old": {"label": base_node.label, "path": base_node.canonical_path},
                        "new": {"label": target_node.label, "path": target_node.canonical_path},
                    })

        return TaxonomyComparison(
            base_version=base_version,
            target_version=target_version,
            added_nodes=added,
            removed_nodes=removed,
            modified_nodes=modified,
            total_changes=len(added) + len(removed) + len(modified),
        )

    # Migration

    async def get_migrations(
        self,
        from_version: Optional[str] = None,
        to_version: Optional[str] = None,
        limit: int = 100
    ) -> List[TaxonomyMigration]:
        """Get migration records"""
        try:
            query = select(MigrationModel)

            conditions = []
            if from_version:
                conditions.append(MigrationModel.from_version == from_version)
            if to_version:
                conditions.append(MigrationModel.to_version == to_version)

            if conditions:
                from sqlalchemy import and_
                query = query.where(and_(*conditions))

            query = query.limit(limit)

            result = await self._session.execute(query)
            models = result.scalars().all()

            return [
                TaxonomyMigration(
                    migration_id=m.migration_id,
                    from_version=m.from_version,
                    to_version=m.to_version,
                    from_path=m.from_path or [],
                    to_path=m.to_path or [],
                    rationale=m.rationale,
                    created_at=m.created_at or datetime.utcnow(),
                )
                for m in models
            ]
        except Exception as e:
            logger.error(f"Failed to get migrations: {e}")
            return []

    async def create_migration(
        self,
        from_version: str,
        to_version: str,
        from_path: List[str],
        to_path: List[str],
        rationale: Optional[str] = None
    ) -> TaxonomyMigration:
        """Record a migration"""
        try:
            model = MigrationModel(
                from_version=from_version,
                to_version=to_version,
                from_path=from_path,
                to_path=to_path,
                rationale=rationale,
            )

            self._session.add(model)
            await self._session.commit()
            await self._session.refresh(model)

            return TaxonomyMigration(
                migration_id=model.migration_id,
                from_version=from_version,
                to_version=to_version,
                from_path=from_path,
                to_path=to_path,
                rationale=rationale,
                created_at=model.created_at or datetime.utcnow(),
            )
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to create migration: {e}")
            raise

    # Statistics

    async def get_statistics(self, version: str) -> Dict[str, Any]:
        """Get taxonomy statistics for a version"""
        tree = await self.get_tree(version)

        if not tree.nodes:
            return {
                "total_nodes": 0,
                "leaf_nodes": 0,
                "internal_nodes": 0,
                "max_depth": 0,
                "avg_depth": 0.0,
                "categories_distribution": {},
            }

        # Calculate leaf vs internal nodes
        parent_ids = {e.parent_id for e in tree.edges}
        leaf_nodes = [n for n in tree.nodes if n.node_id not in parent_ids]
        internal_nodes = [n for n in tree.nodes if n.node_id in parent_ids]

        depths = [n.depth for n in tree.nodes]

        return {
            "total_nodes": len(tree.nodes),
            "leaf_nodes": len(leaf_nodes),
            "internal_nodes": len(internal_nodes),
            "max_depth": max(depths) if depths else 0,
            "avg_depth": sum(depths) / len(depths) if depths else 0.0,
            "categories_distribution": {},
        }

    # Validation

    async def validate_structure(self, version: str) -> Dict[str, Any]:
        """Validate taxonomy structure"""
        from ...domain.entities.taxonomy import validate_taxonomy_structure

        tree = await self.get_tree(version)
        errors = validate_taxonomy_structure(tree)

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": [],
            "suggestions": [],
        }
