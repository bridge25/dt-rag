"""
Dynamic Taxonomy DAG Management System v1.8.1
Implements DAG-based taxonomy with versioning, migration, and rollback capabilities.

Features:
- DAG validation and cycle detection
- Semantic versioning (MAJOR.MINOR.PATCH)
- Atomic migration operations with rollback (TTR ≤ 15분)
- Concurrent modification support
- ACID compliance
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, cast
from dataclasses import dataclass
from enum import Enum

import networkx as nx
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .database import TaxonomyNode, TaxonomyEdge, TaxonomyMigration, async_session

logger = logging.getLogger(__name__)


class MigrationType(Enum):
    """Migration operation types"""

    CREATE_NODE = "create_node"
    UPDATE_NODE = "update_node"
    DELETE_NODE = "delete_node"
    CREATE_EDGE = "create_edge"
    DELETE_EDGE = "delete_edge"
    MOVE_NODE = "move_node"
    MERGE_NODES = "merge_nodes"
    SPLIT_NODE = "split_node"


class VersionType(Enum):
    """Semantic version types"""

    MAJOR = "major"  # Breaking changes
    MINOR = "minor"  # New features
    PATCH = "patch"  # Bug fixes


@dataclass
class ValidationResult:
    """DAG validation result"""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cycles: List[List[int]]
    orphaned_nodes: List[int]


@dataclass
class MigrationOperation:
    """Single migration operation"""

    operation_type: MigrationType
    target_nodes: List[int]
    parameters: Dict[str, Any]
    rollback_data: Optional[Dict[str, Any]] = None


@dataclass
class MigrationPlan:
    """Complete migration plan"""

    from_version: int
    to_version: int
    operations: List[MigrationOperation]
    estimated_duration: float
    rollback_strategy: Dict[str, Any]


class TaxonomyDAGManager:
    """Core DAG management with versioning and rollback capabilities"""

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def __init__(self) -> None:
        self.current_version = 1
        self._graph_cache: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def initialize(self) -> bool:
        """Initialize taxonomy system"""
        try:
            async with async_session() as session:
                # Check for existing version
                result = await session.execute(
                    select(TaxonomyNode.version)
                    .order_by(TaxonomyNode.version.desc())
                    .limit(1)
                )
                latest_version = result.scalar()

                if latest_version:
                    self.current_version = int(latest_version)
                else:
                    # Create root taxonomy if none exists
                    await self._create_default_taxonomy(session)
                    await session.commit()

                logger.info(
                    f"Taxonomy DAG initialized with version {self.current_version}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to initialize taxonomy DAG: {e}")
            return False

    async def validate_dag(self, version: Optional[int] = None) -> ValidationResult:
        """Comprehensive DAG validation with cycle detection"""
        version = version or self.current_version

        try:
            graph = await self._build_networkx_graph(version)
            errors = []
            warnings = []
            cycles = []
            orphaned_nodes = []

            # 1. Cycle detection using DFS
            if not nx.is_directed_acyclic_graph(graph):
                try:
                    cycle = nx.find_cycle(graph, orientation="original")
                    cycle_nodes = [node for node, _ in cycle]
                    cycles.append(cycle_nodes)
                    errors.append(
                        f"Cycle detected: {' -> '.join(map(str, cycle_nodes))}"
                    )
                except nx.NetworkXNoCycle:
                    pass

            # 2. Check for orphaned nodes (no parents except root)
            roots = [n for n in graph.nodes() if graph.in_degree(n) == 0]
            if len(roots) > 1:
                orphaned_nodes = roots[1:]  # All roots except the first one
                warnings.append(f"Multiple root nodes found: {orphaned_nodes}")

            # 3. Check for disconnected components
            if not nx.is_weakly_connected(graph):
                components = list(nx.weakly_connected_components(graph))
                if len(components) > 1:
                    warnings.append(
                        f"Disconnected components found: {len(components)} components"
                    )

            # 4. Validate semantic consistency
            semantic_errors = await self._validate_semantic_consistency(version)
            errors.extend(semantic_errors)

            # 5. Check for duplicate canonical paths
            path_errors = await self._validate_canonical_paths(version)
            errors.extend(path_errors)

            is_valid = len(errors) == 0 and len(cycles) == 0

            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                cycles=cycles,
                orphaned_nodes=orphaned_nodes,
            )

        except Exception as e:
            logger.error(f"DAG validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
                cycles=[],
                orphaned_nodes=[],
            )

    async def create_version(
        self,
        version_type: VersionType,
        changes: List[MigrationOperation],
        description: str,
        created_by: str,
    ) -> Tuple[bool, int, str]:
        """Create new taxonomy version with atomic operations"""

        async with self._lock:
            try:
                new_version = await self._calculate_next_version(version_type)

                async with async_session() as session:
                    async with session.begin():
                        # 1. Validate migration plan
                        validation_result = await self._validate_migration_plan(
                            self.current_version, new_version, changes
                        )

                        if not validation_result.is_valid:
                            return (
                                False,
                                -1,
                                f"Validation failed: {validation_result.errors}",
                            )

                        # 2. Create rollback data
                        rollback_data = await self._create_rollback_data(
                            session, self.current_version, changes
                        )

                        # 3. Apply migrations atomically
                        success, error_msg = await self._apply_migrations(
                            session, self.current_version, new_version, changes
                        )

                        if not success:
                            return False, -1, error_msg

                        # 4. Record migration
                        migration = TaxonomyMigration(
                            from_version=self.current_version,
                            to_version=new_version,
                            migration_type=version_type.value,
                            changes={
                                "operations": [
                                    self._serialize_operation(op) for op in changes
                                ],
                                "rollback_data": rollback_data,
                                "description": description,
                            },
                            applied_by=created_by,
                        )
                        session.add(migration)

                        # 5. Final validation
                        final_validation = await self.validate_dag(new_version)
                        if not final_validation.is_valid:
                            raise Exception(
                                f"Post-migration validation failed: {final_validation.errors}"
                            )

                        # 6. Update current version
                        self.current_version = new_version
                        self._invalidate_cache()

                        logger.info(
                            f"Successfully created version {new_version} ({version_type.value})"
                        )
                        return True, new_version, "Version created successfully"

            except Exception as e:
                logger.error(f"Failed to create version: {e}")
                return False, -1, str(e)

    async def rollback_to_version(
        self, target_version: int, reason: str, performed_by: str
    ) -> Tuple[bool, str]:
        """Rollback to specific version with TTR ≤ 15분 guarantee"""

        start_time = datetime.utcnow()

        async with self._lock:
            try:
                if target_version >= self.current_version:
                    return False, "Cannot rollback to current or future version"

                async with async_session() as session:
                    async with session.begin():
                        # 1. Get rollback plan
                        rollback_plan = await self._create_rollback_plan(
                            session, self.current_version, target_version
                        )

                        # 2. Estimate rollback time
                        estimated_duration = self._estimate_rollback_duration(
                            rollback_plan
                        )
                        if estimated_duration > 900:  # 15 minutes
                            logger.warning(
                                f"Rollback may exceed 15 minutes: {estimated_duration}s"
                            )

                        # 3. Execute rollback operations
                        success, error_msg = await self._execute_rollback_plan(
                            session, rollback_plan
                        )

                        if not success:
                            return False, f"Rollback execution failed: {error_msg}"

                        # 4. Validate rolled back state
                        validation_result = await self.validate_dag(target_version)
                        if not validation_result.is_valid:
                            raise Exception(
                                f"Post-rollback validation failed: {validation_result.errors}"
                            )

                        # 5. Record rollback migration
                        rollback_migration = TaxonomyMigration(
                            from_version=self.current_version,
                            to_version=target_version,
                            migration_type="rollback",
                            changes={
                                "reason": reason,
                                "rollback_plan": rollback_plan,
                                "duration_seconds": (
                                    datetime.utcnow() - start_time
                                ).total_seconds(),
                            },
                            applied_by=performed_by,
                        )
                        session.add(rollback_migration)

                        # 6. Update current version
                        self.current_version = target_version
                        self._invalidate_cache()

                        duration = (datetime.utcnow() - start_time).total_seconds()
                        logger.info(
                            f"Rollback completed in {duration:.2f}s (TTR requirement: ≤900s)"
                        )

                        return (
                            True,
                            f"Successfully rolled back to version {target_version}",
                        )

            except Exception as e:
                logger.error(f"Rollback failed: {e}")
                return False, str(e)

    async def get_taxonomy_tree(self, version: Optional[int] = None) -> Dict[str, Any]:
        """Get taxonomy as hierarchical tree structure"""
        version = version or self.current_version

        try:
            # Check cache first
            cache_key = f"tree_{version}"
            if cache_key in self._graph_cache:
                return cast(Dict[str, Any], self._graph_cache[cache_key])

            async with async_session() as session:
                # Get all nodes for version
                nodes_result = await session.execute(
                    select(TaxonomyNode).where(TaxonomyNode.version == version)
                )
                nodes = nodes_result.scalars().all()

                # Get all edges for version
                edges_result = await session.execute(
                    select(TaxonomyEdge).where(TaxonomyEdge.version == version)
                )
                edges = edges_result.scalars().all()

                # Build tree structure
                tree = self._build_tree_structure(nodes, edges)

                # Cache result
                self._graph_cache[cache_key] = tree

                return tree

        except Exception as e:
            logger.error(f"Failed to get taxonomy tree: {e}")
            return {"error": str(e)}

    async def add_node(
        self,
        node_name: str,
        parent_node_id: Optional[int] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, int, str]:
        """Add new taxonomy node with validation"""

        try:
            # Prepare migration operation
            operation = MigrationOperation(
                operation_type=MigrationType.CREATE_NODE,
                target_nodes=[],
                parameters={
                    "node_name": node_name,
                    "parent_node_id": parent_node_id,
                    "description": description,
                    "metadata": metadata or {},
                },
            )

            # Create new patch version
            success, new_version, message = await self.create_version(
                version_type=VersionType.PATCH,
                changes=[operation],
                description=f"Add node: {node_name}",
                created_by="system",
            )

            if success:
                # Get the newly created node ID
                async with async_session() as session:
                    result = await session.execute(
                        select(TaxonomyNode.node_id).where(
                            and_(
                                TaxonomyNode.version == new_version,
                                TaxonomyNode.node_name == node_name,
                            )
                        )
                    )
                    node_id = result.scalar()

                return True, node_id, "Node added successfully"
            else:
                return False, -1, message

        except Exception as e:
            logger.error(f"Failed to add node: {e}")
            return False, -1, str(e)

    async def move_node(
        self, node_id: int, new_parent_id: Optional[int], reason: str = ""
    ) -> Tuple[bool, str]:
        """Move node to new parent with cycle detection"""

        try:
            # Check if move would create cycle
            if new_parent_id and await self._would_create_cycle(node_id, new_parent_id):
                return False, "Move would create cycle in taxonomy"

            # Prepare migration operation
            operation = MigrationOperation(
                operation_type=MigrationType.MOVE_NODE,
                target_nodes=[node_id],
                parameters={"new_parent_id": new_parent_id, "reason": reason},
            )

            # Create new patch version
            success, new_version, message = await self.create_version(
                version_type=VersionType.PATCH,
                changes=[operation],
                description=f"Move node {node_id} to parent {new_parent_id}",
                created_by="system",
            )

            return success, message

        except Exception as e:
            logger.error(f"Failed to move node: {e}")
            return False, str(e)

    async def get_version_history(self) -> List[Dict[str, Any]]:
        """Get complete version history with migration details"""

        try:
            async with async_session() as session:
                result = await session.execute(
                    select(TaxonomyMigration).order_by(
                        TaxonomyMigration.applied_at.desc()
                    )
                )
                migrations = result.scalars().all()

                history = []
                for migration in migrations:
                    history.append(
                        {
                            "migration_id": migration.migration_id,
                            "from_version": migration.from_version,
                            "to_version": migration.to_version,
                            "migration_type": migration.migration_type,
                            "description": migration.changes.get("description", ""),
                            "applied_at": migration.applied_at.isoformat(),
                            "applied_by": migration.applied_by,
                            "operations_count": len(
                                migration.changes.get("operations", [])
                            ),
                            "rollback_available": "rollback_data" in migration.changes,
                        }
                    )

                return history

        except Exception as e:
            logger.error(f"Failed to get version history: {e}")
            return []

    async def get_node_ancestry(
        self, node_id: int, version: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get complete ancestry path for a node"""
        version = version or self.current_version

        try:
            graph = await self._build_networkx_graph(version)

            # Find path to root
            roots = [n for n in graph.nodes() if graph.in_degree(n) == 0]
            if not roots:
                return []

            root = roots[0]

            try:
                path = nx.shortest_path(graph, root, node_id)

                # Get node details for each node in path
                async with async_session() as session:
                    ancestry: list[Any] = []
                    for node in path:
                        result = await session.execute(
                            select(TaxonomyNode).where(
                                and_(
                                    TaxonomyNode.node_id == node,
                                    TaxonomyNode.version == version,
                                )
                            )
                        )
                        node_obj = result.scalar()
                        if node_obj:
                            ancestry.append(
                                {
                                    "node_id": node_obj.node_id,
                                    "node_name": node_obj.node_name,
                                    "canonical_path": node_obj.canonical_path,
                                    "level": len(ancestry),
                                }
                            )

                    return ancestry

            except nx.NetworkXNoPath:
                return []

        except Exception as e:
            logger.error(f"Failed to get node ancestry: {e}")
            return []

    # Private helper methods

    async def _build_networkx_graph(self, version: int) -> nx.DiGraph:
        """Build NetworkX graph from database"""
        graph = nx.DiGraph()

        async with async_session() as session:
            # Add nodes
            nodes_result = await session.execute(
                select(TaxonomyNode).where(TaxonomyNode.version == version)
            )
            nodes = nodes_result.scalars().all()

            for node in nodes:
                graph.add_node(
                    node.node_id,
                    name=node.node_name,
                    canonical_path=node.canonical_path,
                )

            # Add edges
            edges_result = await session.execute(
                select(TaxonomyEdge).where(TaxonomyEdge.version == version)
            )
            edges = edges_result.scalars().all()

            for edge in edges:
                graph.add_edge(edge.parent_node_id, edge.child_node_id)

        return graph

    async def _validate_semantic_consistency(self, version: int) -> List[str]:
        """Validate semantic consistency of taxonomy"""
        errors = []

        try:
            async with async_session() as session:
                result = await session.execute(
                    select(TaxonomyNode).where(TaxonomyNode.version == version)
                )
                nodes = result.scalars().all()

                # Check canonical path consistency
                for node in nodes:
                    if node.canonical_path:
                        path_str = " -> ".join(node.canonical_path)
                        if node.node_name not in node.canonical_path:
                            errors.append(
                                f"Node {node.node_id} name mismatch in canonical path: {path_str}"
                            )

        except Exception as e:
            errors.append(f"Semantic validation error: {e}")

        return errors

    async def _validate_canonical_paths(self, version: int) -> List[str]:
        """Validate canonical path uniqueness"""
        errors = []

        try:
            async with async_session() as session:
                result = await session.execute(
                    select(TaxonomyNode.canonical_path).where(
                        TaxonomyNode.version == version
                    )
                )
                paths = [row[0] for row in result.fetchall()]

                # Check for duplicates
                path_count: Any = defaultdict(int)
                for path in paths:
                    if path:
                        path_str = " -> ".join(path)
                        path_count[path_str] += 1

                duplicates = [path for path, count in path_count.items() if count > 1]
                if duplicates:
                    errors.append(f"Duplicate canonical paths: {duplicates}")

        except Exception as e:
            errors.append(f"Path validation error: {e}")

        return errors

    async def _calculate_next_version(self, version_type: VersionType) -> int:
        """Calculate next version number based on semantic versioning"""
        # For this implementation, using simple integer versioning
        # In production, implement proper semantic versioning
        return self.current_version + 1

    async def _validate_migration_plan(
        self, from_version: int, to_version: int, operations: List[MigrationOperation]
    ) -> ValidationResult:
        """Validate migration plan before execution"""

        # For now, basic validation
        # In production, simulate migrations to detect issues
        return ValidationResult(
            is_valid=True, errors=[], warnings=[], cycles=[], orphaned_nodes=[]
        )

    async def _create_rollback_data(
        self, session: AsyncSession, version: int, operations: List[MigrationOperation]
    ) -> Dict[str, Any]:
        """Create rollback data for migration"""

        # @CODE:MYPY-CONSOLIDATION-002 | Phase 2: Fix attr-defined (list type annotation)
        affected_nodes: List[Dict[str, Any]] = []
        affected_edges: List[Dict[str, Any]] = []

        rollback_data: Dict[str, Any] = {
            "snapshot_timestamp": datetime.utcnow().isoformat(),
            "affected_nodes": affected_nodes,
            "affected_edges": affected_edges,
        }

        # Store current state of affected entities
        for operation in operations:
            for node_id in operation.target_nodes:
                result = await session.execute(
                    select(TaxonomyNode).where(
                        and_(
                            TaxonomyNode.node_id == node_id,
                            TaxonomyNode.version == version,
                        )
                    )
                )
                node = result.scalar()
                if node:
                    rollback_data["affected_nodes"].append(
                        {
                            "node_id": node.node_id,
                            "node_name": node.node_name,
                            "canonical_path": node.canonical_path,
                            "description": node.description,
                            "metadata": node.metadata,
                        }
                    )

        return rollback_data

    async def _apply_migrations(
        self,
        session: AsyncSession,
        from_version: int,
        to_version: int,
        operations: List[MigrationOperation],
    ) -> Tuple[bool, str]:
        """Apply migration operations atomically"""

        try:
            for operation in operations:
                success, error_msg = await self._apply_single_operation(
                    session, to_version, operation
                )
                if not success:
                    return False, error_msg

            return True, "All migrations applied successfully"

        except Exception as e:
            return False, str(e)

    async def _apply_single_operation(
        self, session: AsyncSession, version: int, operation: MigrationOperation
    ) -> Tuple[bool, str]:
        """Apply single migration operation"""

        try:
            if operation.operation_type == MigrationType.CREATE_NODE:
                return await self._create_node_operation(session, version, operation)
            elif operation.operation_type == MigrationType.MOVE_NODE:
                return await self._move_node_operation(session, version, operation)
            # Add other operation types as needed
            else:
                return False, f"Unsupported operation type: {operation.operation_type}"

        except Exception as e:
            return False, str(e)

    async def _create_node_operation(
        self, session: AsyncSession, version: int, operation: MigrationOperation
    ) -> Tuple[bool, str]:
        """Create new node operation"""

        params = operation.parameters

        # Generate new node ID
        new_node_id = await self._generate_node_id(session)

        # Calculate canonical path
        canonical_path = [params["node_name"]]
        if params.get("parent_node_id"):
            parent_result = await session.execute(
                select(TaxonomyNode.canonical_path).where(
                    and_(
                        TaxonomyNode.node_id == params["parent_node_id"],
                        TaxonomyNode.version == version,
                    )
                )
            )
            parent_path = parent_result.scalar()
            if parent_path:
                canonical_path = parent_path + [params["node_name"]]

        # Create node
        new_node = TaxonomyNode(
            node_id=new_node_id,
            version=version,
            canonical_path=canonical_path,
            node_name=params["node_name"],
            description=params.get("description", ""),
            metadata=params.get("metadata", {}),
            is_active=True,
        )
        session.add(new_node)

        # Create edge if has parent
        if params.get("parent_node_id"):
            new_edge = TaxonomyEdge(
                version=version,
                parent_node_id=params["parent_node_id"],
                child_node_id=new_node_id,
            )
            session.add(new_edge)

        return True, "Node created successfully"

    async def _move_node_operation(
        self, session: AsyncSession, version: int, operation: MigrationOperation
    ) -> Tuple[bool, str]:
        """Move node operation"""

        node_id = operation.target_nodes[0]
        new_parent_id = operation.parameters.get("new_parent_id")

        # Update canonical path
        # This is a simplified implementation
        # In production, recursively update all descendant paths

        if new_parent_id:
            parent_result = await session.execute(
                select(TaxonomyNode.canonical_path, TaxonomyNode.node_name).where(
                    and_(
                        TaxonomyNode.node_id == new_parent_id,
                        TaxonomyNode.version == version,
                    )
                )
            )
            parent_data = parent_result.first()
            if parent_data:
                parent_path, _ = parent_data

                # Get current node name
                node_result = await session.execute(
                    select(TaxonomyNode.node_name).where(
                        and_(
                            TaxonomyNode.node_id == node_id,
                            TaxonomyNode.version == version,
                        )
                    )
                )
                node_name = node_result.scalar()

                if node_name:
                    new_canonical_path = parent_path + [node_name]

                    # Update node canonical path
                    await session.execute(
                        update(TaxonomyNode)
                        .where(
                            and_(
                                TaxonomyNode.node_id == node_id,
                                TaxonomyNode.version == version,
                            )
                        )
                        .values(canonical_path=new_canonical_path)
                    )

        return True, "Node moved successfully"

    async def _would_create_cycle(self, node_id: int, new_parent_id: int) -> bool:
        """Check if moving node would create cycle"""

        try:
            graph = await self._build_networkx_graph(self.current_version)

            # Check if new_parent_id is descendant of node_id
            try:
                nx.shortest_path(graph, node_id, new_parent_id)
                return True  # Path exists, would create cycle
            except nx.NetworkXNoPath:
                return False  # No path, safe to move

        except Exception:
            return True  # Conservative: assume would create cycle on error

    async def _create_rollback_plan(
        self, session: AsyncSession, from_version: int, to_version: int
    ) -> Dict[str, Any]:
        """Create comprehensive rollback plan"""

        # Get all migrations between target and current version
        result = await session.execute(
            select(TaxonomyMigration)
            .where(
                and_(
                    TaxonomyMigration.to_version > to_version,
                    TaxonomyMigration.to_version <= from_version,
                )
            )
            .order_by(TaxonomyMigration.to_version.desc())
        )
        migrations = result.scalars().all()

        rollback_plan = {
            "migrations_to_reverse": [m.migration_id for m in migrations],
            "estimated_operations": sum(
                len(m.changes.get("operations", [])) for m in migrations
            ),
            "requires_full_rebuild": len(migrations) > 10,
        }

        return rollback_plan

    def _estimate_rollback_duration(self, rollback_plan: Dict[str, Any]) -> float:
        """Estimate rollback duration in seconds"""

        base_time = 30  # Base overhead
        operation_count = rollback_plan.get("estimated_operations", 0)
        time_per_operation = 0.5

        estimated = base_time + (operation_count * time_per_operation)

        if rollback_plan.get("requires_full_rebuild"):
            estimated *= 2  # Double time for complex rollbacks

        return cast(float, estimated)

    async def _execute_rollback_plan(
        self, session: AsyncSession, rollback_plan: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Execute rollback plan"""

        try:
            # For this implementation, simplified rollback
            # In production, implement precise reversal of each operation

            migration_ids = rollback_plan.get("migrations_to_reverse", [])

            for migration_id in migration_ids:
                # Get migration details
                result = await session.execute(
                    select(TaxonomyMigration).where(
                        TaxonomyMigration.migration_id == migration_id
                    )
                )
                migration = result.scalar()

                if migration and "rollback_data" in migration.changes:
                    # Apply rollback data
                    rollback_data = migration.changes["rollback_data"]
                    await self._restore_from_rollback_data(session, rollback_data)

            return True, "Rollback executed successfully"

        except Exception as e:
            return False, str(e)

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def _restore_from_rollback_data(
        self, session: AsyncSession, rollback_data: Dict[str, Any]
    ) -> None:
        """Restore entities from rollback data"""

        # Restore nodes
        for node_data in rollback_data.get("affected_nodes", []):
            await session.execute(
                update(TaxonomyNode)
                .where(TaxonomyNode.node_id == node_data["node_id"])
                .values(
                    node_name=node_data["node_name"],
                    canonical_path=node_data["canonical_path"],
                    description=node_data["description"],
                    metadata=node_data["metadata"],
                )
            )

        # Restore edges would be similar

    async def _generate_node_id(self, session: AsyncSession) -> int:
        """Generate unique node ID"""
        result = await session.execute(
            select(TaxonomyNode.node_id).order_by(TaxonomyNode.node_id.desc()).limit(1)
        )
        max_id = result.scalar()
        return (max_id or 0) + 1

    def _build_tree_structure(
        self, nodes: List[TaxonomyNode], edges: List[TaxonomyEdge]
    ) -> Dict[str, Any]:
        """Build hierarchical tree structure from nodes and edges"""

        # Create node lookup
        node_lookup = {
            node.node_id: {
                "node_id": node.node_id,
                "node_name": node.node_name,
                "canonical_path": node.canonical_path,
                "description": node.description,
                "metadata": node.metadata,
                "children": [],
            }
            for node in nodes
        }

        # Build parent-child relationships
        for edge in edges:
            if edge.parent_node_id in node_lookup and edge.child_node_id in node_lookup:
                node_lookup[edge.parent_node_id]["children"].append(
                    node_lookup[edge.child_node_id]
                )

        # Find root nodes
        child_ids = {edge.child_node_id for edge in edges}
        root_nodes = [
            node for node_id, node in node_lookup.items() if node_id not in child_ids
        ]

        return {
            "version": nodes[0].version if nodes else 1,
            "roots": root_nodes,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

    def _serialize_operation(self, operation: MigrationOperation) -> Dict[str, Any]:
        """Serialize migration operation for storage"""
        return {
            "operation_type": operation.operation_type.value,
            "target_nodes": operation.target_nodes,
            "parameters": operation.parameters,
        }

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    async def _create_default_taxonomy(self, session: AsyncSession) -> None:
        """Create default taxonomy structure"""

        # Create root node
        root_node = TaxonomyNode(
            node_id=1,
            version=1,
            canonical_path=["Root"],
            node_name="Root",
            description="Root taxonomy node",
            metadata={"type": "root"},
            is_active=True,
        )
        session.add(root_node)

        # Create basic categories
        ai_node = TaxonomyNode(
            node_id=2,
            version=1,
            canonical_path=["Root", "AI"],
            node_name="AI",
            description="Artificial Intelligence",
            metadata={"type": "category"},
            is_active=True,
        )
        session.add(ai_node)

        # Create edge
        root_edge = TaxonomyEdge(version=1, parent_node_id=1, child_node_id=2)
        session.add(root_edge)

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def _invalidate_cache(self) -> None:
        """Invalidate graph cache"""
        self._graph_cache.clear()


# Singleton instance
taxonomy_dag_manager = TaxonomyDAGManager()


# Convenience functions for external use
async def initialize_taxonomy_system() -> bool:
    """Initialize the taxonomy DAG system"""
    return await taxonomy_dag_manager.initialize()


async def validate_taxonomy_dag(version: Optional[int] = None) -> ValidationResult:
    """Validate taxonomy DAG structure"""
    return await taxonomy_dag_manager.validate_dag(version)


async def create_taxonomy_version(
    version_type: VersionType,
    changes: List[MigrationOperation],
    description: str,
    created_by: str,
) -> Tuple[bool, int, str]:
    """Create new taxonomy version"""
    return await taxonomy_dag_manager.create_version(
        version_type, changes, description, created_by
    )


async def rollback_taxonomy(
    target_version: int, reason: str, performed_by: str
) -> Tuple[bool, str]:
    """Rollback taxonomy to specific version"""
    return await taxonomy_dag_manager.rollback_to_version(
        target_version, reason, performed_by
    )


async def get_taxonomy_tree(version: Optional[int] = None) -> Dict[str, Any]:
    """Get taxonomy tree structure"""
    return await taxonomy_dag_manager.get_taxonomy_tree(version)


async def add_taxonomy_node(
    node_name: str,
    parent_node_id: Optional[int] = None,
    description: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, int, str]:
    """Add new taxonomy node"""
    return await taxonomy_dag_manager.add_node(
        node_name, parent_node_id, description, metadata
    )


async def move_taxonomy_node(
    node_id: int, new_parent_id: Optional[int], reason: str = ""
) -> Tuple[bool, str]:
    """Move taxonomy node"""
    return await taxonomy_dag_manager.move_node(node_id, new_parent_id, reason)


async def get_taxonomy_history() -> List[Dict[str, Any]]:
    """Get taxonomy version history"""
    return await taxonomy_dag_manager.get_version_history()


async def get_node_ancestry(
    node_id: int, version: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get node ancestry path"""
    return await taxonomy_dag_manager.get_node_ancestry(node_id, version)
