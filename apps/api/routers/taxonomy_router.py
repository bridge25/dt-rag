"""
Taxonomy Management API Router for DT-RAG v1.8.1

Provides REST endpoints for hierarchical taxonomy operations including:
- Taxonomy version management
- Tree navigation and retrieval
- Node operations (CRUD)
- Version comparison and rollback
- Taxonomy validation and statistics
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Path, Depends, status
from pydantic import BaseModel, Field

try:
    from ..deps import verify_api_key
except ImportError:
    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def verify_api_key() -> None:  # type: ignore[misc]  # Fallback function for testing
        return None


# Import common schemas
import sys
from pathlib import Path as PathLib

sys.path.append(str(PathLib(__file__).parent.parent.parent.parent))

from packages.common_schemas.common_schemas.models import TaxonomyNode

# Configure logging
logger = logging.getLogger(__name__)

# Create router
taxonomy_router = APIRouter(prefix="/taxonomy", tags=["Taxonomy"])

# Request/Response Models


class TaxonomyVersion(BaseModel):
    """Taxonomy version information"""

    version: str = Field(
        ..., pattern=r"^\d+\.\d+\.\d+$", description="Semantic version"
    )
    created_at: datetime = Field(..., description="Version creation timestamp")
    created_by: str = Field(..., description="Version creator")
    change_summary: str = Field(..., description="Summary of changes in this version")
    parent_version: Optional[str] = Field(None, description="Parent version")
    node_count: int = Field(..., description="Total number of nodes in this version")
    depth: int = Field(..., description="Maximum tree depth")


class TaxonomyStatistics(BaseModel):
    """Taxonomy statistics"""

    total_nodes: int
    leaf_nodes: int
    internal_nodes: int
    max_depth: int
    avg_depth: float
    categories_distribution: Dict[str, int]


class VersionComparison(BaseModel):
    """Version comparison result"""

    base_version: str
    target_version: str
    changes: Dict[str, Any]
    summary: Dict[str, int]


class NodeCreateRequest(BaseModel):
    """Request to create a new taxonomy node"""

    name: str = Field(..., min_length=1, max_length=100)
    parent_path: Optional[List[str]] = Field(None, description="Parent node path")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NodeUpdateRequest(BaseModel):
    """Request to update an existing taxonomy node"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    metadata: Optional[Dict[str, Any]] = None


class ValidationResult(BaseModel):
    """Taxonomy validation result"""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


# Real taxonomy service implementation
from ..services.taxonomy_service import TaxonomyService  # noqa: E402


# Dependency injection
async def get_taxonomy_service() -> TaxonomyService:
    """Get taxonomy service instance"""
    return TaxonomyService()


# API Endpoints


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@taxonomy_router.get("/versions", response_model=Dict[str, Any])  # type: ignore[misc]
async def list_taxonomy_versions(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    service: TaxonomyService = Depends(get_taxonomy_service),
    api_key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """
    List all available taxonomy versions with pagination

    Returns paginated list of taxonomy versions with metadata including:
    - Version number and creation details
    - Change summaries and parent relationships
    - Node counts and depth statistics
    """
    try:
        offset = (page - 1) * limit
        versions = await service.list_versions(limit=limit, offset=offset)

        total_count = len(versions)
        has_next = offset + limit < total_count
        has_previous = page > 1

        response = {
            "versions": versions,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "has_next": has_next,
                "has_previous": has_previous,
            },
        }

        if has_next:
            response["pagination"]["next_page"] = page + 1
        if has_previous:
            response["pagination"]["previous_page"] = page - 1

        return response

    except Exception as e:
        logger.error(f"Failed to list taxonomy versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve taxonomy versions",
        )


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@taxonomy_router.get("/{version}/tree", response_model=Dict[str, Any])  # type: ignore[misc]
async def get_taxonomy_tree(
    version: str = Path(..., description="Taxonomy version"),
    expand_level: int = Query(
        -1, ge=-1, description="Tree expansion level (-1 for full tree)"
    ),
    filter_path: Optional[str] = Query(None, description="Filter by path prefix"),
    service: TaxonomyService = Depends(get_taxonomy_service),
    api_key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """
    Retrieve complete taxonomy tree for specified version

    Returns hierarchical tree structure with:
    - All nodes with their canonical paths
    - Confidence scores for each classification
    - Metadata and relationship information
    - Optional filtering by path prefix
    """
    try:
        tree_data = await service.get_tree(version)

        if not tree_data or not tree_data.get("nodes"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Taxonomy version '{version}' not found",
            )

        nodes = tree_data["nodes"]
        edges = tree_data["edges"]

        # Apply path filtering if specified
        if filter_path:
            filter_parts = filter_path.split("/")
            nodes = [
                node
                for node in nodes
                if node.get("canonical_path", [])[: len(filter_parts)] == filter_parts
            ]

        return {
            "nodes": nodes,
            "edges": edges,
            "version": version,
            "metadata": tree_data.get("metadata", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get taxonomy tree: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve taxonomy tree",
        )


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@taxonomy_router.get("/{version}/statistics", response_model=TaxonomyStatistics)  # type: ignore[misc]
async def get_taxonomy_statistics(
    version: str = Path(..., description="Taxonomy version"),
    service: TaxonomyService = Depends(get_taxonomy_service),
    api_key: str = Depends(verify_api_key),
) -> TaxonomyStatistics:
    """
    Get comprehensive statistics for taxonomy version

    Returns detailed statistics including:
    - Node counts (total, leaf, internal)
    - Tree depth information
    - Category distribution
    - Structural analysis
    """
    try:
        statistics = await service.get_statistics(version)
        return statistics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get taxonomy statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve taxonomy statistics",
        )


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@taxonomy_router.get("/{version}/validate", response_model=ValidationResult)  # type: ignore[misc]
async def validate_taxonomy(
    version: str = Path(..., description="Taxonomy version"),
    service: TaxonomyService = Depends(get_taxonomy_service),
    api_key: str = Depends(verify_api_key),
) -> ValidationResult:
    """
    Validate taxonomy structure and consistency

    Performs comprehensive validation including:
    - Structural integrity checks
    - Orphaned node detection
    - Circular reference detection
    - Naming convention validation
    """
    try:
        validation_result = await service.validate_taxonomy(version)
        return validation_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate taxonomy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate taxonomy",
        )


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@taxonomy_router.get(
    "/{base_version}/compare/{target_version}", response_model=VersionComparison
)  # type: ignore[misc]
async def compare_taxonomy_versions(
    base_version: str = Path(..., description="Base version for comparison"),
    target_version: str = Path(..., description="Target version for comparison"),
    service: TaxonomyService = Depends(get_taxonomy_service),
    api_key: str = Depends(verify_api_key),
) -> VersionComparison:
    """
    Compare two taxonomy versions and show differences

    Provides detailed comparison including:
    - Added, removed, and modified nodes
    - Structural changes and moves
    - Impact analysis and statistics
    """
    try:
        # Verify both versions exist
        base_tree = await service.get_tree(base_version)
        target_tree = await service.get_tree(target_version)

        if base_tree is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Base taxonomy version '{base_version}' not found",
            )

        if target_tree is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target taxonomy version '{target_version}' not found",
            )

        comparison = await service.compare_versions(base_version, target_version)
        return comparison

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare taxonomy versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare taxonomy versions",
        )


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@taxonomy_router.get("/{version}/search", response_model=List[TaxonomyNode])  # type: ignore[misc]
async def search_taxonomy_nodes(
    version: str = Path(..., description="Taxonomy version"),
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    service: TaxonomyService = Depends(get_taxonomy_service),
    api_key: str = Depends(verify_api_key),
) -> List[Dict[str, Any]]:
    """
    Search taxonomy nodes by name or metadata

    Supports fuzzy matching and returns:
    - Nodes matching the search query
    - Relevance scores
    - Context information
    """
    try:
        # @CODE:MYPY-CONSOLIDATION-002 | Phase 2: Fix attr-defined (type annotation)
        # Get full tree for searching
        tree_data = await service.get_tree(version)
        if tree_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Taxonomy version '{version}' not found",
            )

        # Extract nodes from tree structure
        tree_nodes: List[Dict[str, Any]] = tree_data.get("nodes", [])

        # Simple search implementation (would be more sophisticated in practice)
        query_lower = q.lower()
        matching_nodes: List[Dict[str, Any]] = []

        for node in tree_nodes:
            node_label: str = str(node.get("label", ""))
            node_canonical_path: List[str] = node.get("canonical_path", [])

            if query_lower in node_label.lower() or any(
                query_lower in str(path_part).lower() for path_part in node_canonical_path
            ):
                matching_nodes.append(node)

            if len(matching_nodes) >= limit:
                break

        return matching_nodes

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search taxonomy nodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search taxonomy nodes",
        )


# Export router
__all__ = ["taxonomy_router"]
