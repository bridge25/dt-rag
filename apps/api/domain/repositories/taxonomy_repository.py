"""
Taxonomy Repository Interface

Defines the contract for Taxonomy data access operations.

@CODE:CLEAN-ARCHITECTURE-TAXONOMY-REPOSITORY
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from ..entities.taxonomy import TaxonomyNode, TaxonomyEdge, TaxonomyTree, TaxonomyMigration


@dataclass
class CreateNodeParams:
    """Parameters for creating a taxonomy node"""
    label: str
    canonical_path: List[str]
    version: str
    confidence: float = 1.0
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    metadata: Dict[str, Any] = None


@dataclass
class TaxonomyVersionInfo:
    """Information about a taxonomy version"""
    version: str
    node_count: int
    created_at: datetime
    created_by: str
    change_summary: Optional[str] = None
    parent_version: Optional[str] = None
    depth: int = 0


@dataclass
class TaxonomyComparison:
    """Comparison between two taxonomy versions"""
    base_version: str
    target_version: str
    added_nodes: List[TaxonomyNode]
    removed_nodes: List[TaxonomyNode]
    modified_nodes: List[Dict[str, Any]]  # {node_id, old, new}
    total_changes: int


class ITaxonomyRepository(ABC):
    """
    Taxonomy Repository Interface

    Defines all data access operations for Taxonomy entities.
    """

    # Version Operations

    @abstractmethod
    async def list_versions(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[TaxonomyVersionInfo]:
        """List all taxonomy versions"""
        pass

    @abstractmethod
    async def get_latest_version(self) -> Optional[str]:
        """Get the latest taxonomy version string"""
        pass

    # Tree Operations

    @abstractmethod
    async def get_tree(self, version: str) -> TaxonomyTree:
        """Get complete taxonomy tree for a version"""
        pass

    @abstractmethod
    async def get_node_by_id(
        self,
        node_id: UUID,
        version: Optional[str] = None
    ) -> Optional[TaxonomyNode]:
        """Get a specific node by ID"""
        pass

    @abstractmethod
    async def get_nodes_by_path(
        self,
        canonical_path: List[str],
        version: str
    ) -> List[TaxonomyNode]:
        """Get nodes matching a canonical path"""
        pass

    @abstractmethod
    async def get_children(
        self,
        node_id: UUID,
        version: str
    ) -> List[TaxonomyNode]:
        """Get direct children of a node"""
        pass

    @abstractmethod
    async def get_ancestors(
        self,
        node_id: UUID,
        version: str
    ) -> List[TaxonomyNode]:
        """Get all ancestors of a node (path to root)"""
        pass

    # Node CRUD

    @abstractmethod
    async def create_node(self, params: CreateNodeParams) -> TaxonomyNode:
        """Create a new taxonomy node"""
        pass

    @abstractmethod
    async def create_nodes_batch(
        self,
        nodes: List[CreateNodeParams]
    ) -> List[TaxonomyNode]:
        """Create multiple nodes in batch"""
        pass

    @abstractmethod
    async def update_node(
        self,
        node_id: UUID,
        label: Optional[str] = None,
        description: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TaxonomyNode:
        """Update a taxonomy node"""
        pass

    @abstractmethod
    async def delete_node(self, node_id: UUID) -> bool:
        """Delete a taxonomy node"""
        pass

    # Edge Operations

    @abstractmethod
    async def create_edge(
        self,
        parent_id: UUID,
        child_id: UUID,
        version: str
    ) -> TaxonomyEdge:
        """Create an edge between nodes"""
        pass

    @abstractmethod
    async def delete_edge(
        self,
        parent_id: UUID,
        child_id: UUID,
        version: str
    ) -> bool:
        """Delete an edge between nodes"""
        pass

    # Version Management

    @abstractmethod
    async def create_version(
        self,
        version: str,
        created_by: str,
        change_summary: Optional[str] = None,
        parent_version: Optional[str] = None
    ) -> TaxonomyVersionInfo:
        """Create a new taxonomy version"""
        pass

    @abstractmethod
    async def compare_versions(
        self,
        base_version: str,
        target_version: str
    ) -> TaxonomyComparison:
        """Compare two taxonomy versions"""
        pass

    # Migration

    @abstractmethod
    async def get_migrations(
        self,
        from_version: Optional[str] = None,
        to_version: Optional[str] = None,
        limit: int = 100
    ) -> List[TaxonomyMigration]:
        """Get migration records"""
        pass

    @abstractmethod
    async def create_migration(
        self,
        from_version: str,
        to_version: str,
        from_path: List[str],
        to_path: List[str],
        rationale: Optional[str] = None
    ) -> TaxonomyMigration:
        """Record a migration"""
        pass

    # Statistics

    @abstractmethod
    async def get_statistics(self, version: str) -> Dict[str, Any]:
        """
        Get taxonomy statistics for a version.

        Returns dict with:
        - total_nodes: int
        - leaf_nodes: int
        - internal_nodes: int
        - max_depth: int
        - avg_depth: float
        - categories_distribution: Dict[str, int]
        """
        pass

    # Validation

    @abstractmethod
    async def validate_structure(self, version: str) -> Dict[str, Any]:
        """
        Validate taxonomy structure.

        Returns dict with:
        - is_valid: bool
        - errors: List[str]
        - warnings: List[str]
        - suggestions: List[str]
        """
        pass
