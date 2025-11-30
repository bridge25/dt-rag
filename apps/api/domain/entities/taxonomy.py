"""
Taxonomy Entity - Core Business Model

Represents hierarchical taxonomy nodes and their relationships.

Business Rules:
- Taxonomy forms a DAG (Directed Acyclic Graph)
- Each node has a canonical path representing its lineage
- Version follows semantic versioning
- Confidence score must be between 0 and 1

@CODE:CLEAN-ARCHITECTURE-TAXONOMY-ENTITY
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


@dataclass(frozen=True)
class TaxonomyNode:
    """
    Taxonomy Node Entity

    Represents a category in the knowledge taxonomy tree.
    Forms a DAG structure for document classification.

    Attributes:
        node_id: Unique node identifier
        label: Human-readable node label
        canonical_path: Path from root (e.g., ["AI", "ML", "NLP"])
        version: Taxonomy version this node belongs to
        confidence: Classification confidence threshold (0-1)
        description: Optional detailed description
        parent_id: Optional parent node ID
        metadata: Additional node metadata
    """
    node_id: UUID
    label: str
    canonical_path: List[str]
    version: str
    confidence: float = 1.0
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate business rules"""
        if not self.label or not self.label.strip():
            raise ValueError("Node label cannot be empty")
        if not self.canonical_path:
            raise ValueError("Canonical path cannot be empty")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")

    @property
    def depth(self) -> int:
        """Get node depth in tree (0 for root)"""
        return len(self.canonical_path) - 1

    @property
    def is_root(self) -> bool:
        """Check if node is a root node"""
        return len(self.canonical_path) == 1

    @property
    def parent_path(self) -> Optional[List[str]]:
        """Get parent's canonical path"""
        if self.is_root:
            return None
        return self.canonical_path[:-1]

    @property
    def full_label(self) -> str:
        """Get full path as a readable string"""
        return " > ".join(self.canonical_path)


@dataclass(frozen=True)
class TaxonomyEdge:
    """
    Taxonomy Edge Entity

    Represents a parent-child relationship in the taxonomy.

    Attributes:
        parent_id: Parent node identifier
        child_id: Child node identifier
        version: Taxonomy version
        weight: Optional edge weight for ranking
    """
    parent_id: UUID
    child_id: UUID
    version: str
    weight: float = 1.0

    def __post_init__(self) -> None:
        """Validate business rules"""
        if self.parent_id == self.child_id:
            raise ValueError("Parent and child cannot be the same node")


@dataclass(frozen=True)
class TaxonomyTree:
    """
    Taxonomy Tree Entity

    Complete taxonomy structure with nodes and edges.

    Attributes:
        version: Semantic version of this taxonomy
        nodes: List of all nodes
        edges: List of all edges
        metadata: Tree-level metadata
    """
    version: str
    nodes: List[TaxonomyNode] = field(default_factory=list)
    edges: List[TaxonomyEdge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def total_nodes(self) -> int:
        """Get total number of nodes"""
        return len(self.nodes)

    @property
    def max_depth(self) -> int:
        """Get maximum tree depth"""
        if not self.nodes:
            return 0
        return max(node.depth for node in self.nodes)

    @property
    def root_nodes(self) -> List[TaxonomyNode]:
        """Get all root nodes"""
        return [node for node in self.nodes if node.is_root]

    def get_children(self, node_id: UUID) -> List[TaxonomyNode]:
        """Get direct children of a node"""
        child_ids = {edge.child_id for edge in self.edges if edge.parent_id == node_id}
        return [node for node in self.nodes if node.node_id in child_ids]

    def get_ancestors(self, node_id: UUID) -> List[TaxonomyNode]:
        """Get all ancestors of a node (path to root)"""
        node_map = {node.node_id: node for node in self.nodes}
        target_node = node_map.get(node_id)
        if not target_node:
            return []

        ancestors = []
        for i in range(len(target_node.canonical_path) - 1):
            path = target_node.canonical_path[:i + 1]
            for node in self.nodes:
                if node.canonical_path == path:
                    ancestors.append(node)
                    break
        return ancestors


@dataclass(frozen=True)
class TaxonomyMigration:
    """
    Taxonomy Migration Record

    Tracks changes between taxonomy versions.

    Attributes:
        migration_id: Unique migration identifier
        from_version: Source version
        to_version: Target version
        from_path: Original canonical path
        to_path: New canonical path
        rationale: Reason for migration
    """
    migration_id: int
    from_version: str
    to_version: str
    from_path: List[str]
    to_path: List[str]
    rationale: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


# Business Logic Functions

def validate_taxonomy_structure(tree: TaxonomyTree) -> List[str]:
    """
    Validate taxonomy tree structure.

    Returns list of validation errors (empty if valid).
    """
    errors = []

    # Check for duplicate paths
    paths = [tuple(node.canonical_path) for node in tree.nodes]
    if len(paths) != len(set(paths)):
        errors.append("Duplicate canonical paths detected")

    # Check for orphaned edges
    node_ids = {node.node_id for node in tree.nodes}
    for edge in tree.edges:
        if edge.parent_id not in node_ids:
            errors.append(f"Edge references non-existent parent: {edge.parent_id}")
        if edge.child_id not in node_ids:
            errors.append(f"Edge references non-existent child: {edge.child_id}")

    # Check for cycles (simplified - full DAG validation would need DFS)
    parent_map: Dict[UUID, UUID] = {}
    for edge in tree.edges:
        if edge.child_id in parent_map:
            errors.append(f"Node {edge.child_id} has multiple parents (not a tree)")
        parent_map[edge.child_id] = edge.parent_id

    return errors


def calculate_node_coverage(
    node: TaxonomyNode,
    document_count: int,
    target_count: int = 10
) -> float:
    """
    Calculate coverage percentage for a taxonomy node.

    Business Rules:
    - 100% coverage when document_count >= target_count
    - Linear scaling below target
    """
    if target_count <= 0:
        return 100.0
    return min(100.0, (document_count / target_count) * 100)


def find_coverage_gaps(
    tree: TaxonomyTree,
    node_doc_counts: Dict[UUID, int],
    threshold: float = 0.5
) -> List[TaxonomyNode]:
    """
    Find nodes with coverage below threshold.

    Returns list of nodes that need more documents.
    """
    gaps = []
    for node in tree.nodes:
        doc_count = node_doc_counts.get(node.node_id, 0)
        coverage = calculate_node_coverage(node, doc_count)
        if coverage < threshold * 100:
            gaps.append(node)
    return gaps
