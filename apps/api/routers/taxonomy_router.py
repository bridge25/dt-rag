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

# Import common schemas
import sys
from datetime import datetime
from pathlib import Path as PathLib
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

sys.path.append(str(PathLib(__file__).parent.parent.parent.parent))

from apps.api.database import TaxonomyNode

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


# Mock data and services (would be replaced with actual implementations)


class TaxonomyService:
    """Mock taxonomy service"""

    async def list_versions(
        self, limit: int = 50, offset: int = 0
    ) -> List[TaxonomyVersion]:
        """List available taxonomy versions"""
        # Mock implementation
        return [
            TaxonomyVersion(
                version="1.8.1",
                created_at=datetime.utcnow(),
                created_by="system",
                change_summary="Added AI/ML subcategories",
                parent_version="1.8.0",
                node_count=150,
                depth=5,
            ),
            TaxonomyVersion(
                version="1.8.0",
                created_at=datetime.utcnow(),
                created_by="admin",
                change_summary="Major taxonomy restructure",
                parent_version="1.7.9",
                node_count=142,
                depth=4,
            ),
        ]

    async def get_tree(
        self, version: str, expand_level: int = -1
    ) -> List[Dict[str, Any]]:
        """Get taxonomy tree for a specific version"""
        # Mock implementation
        if version not in ["1.8.1", "1.8.0"]:
            return None

        return [
            TaxonomyNode(
                node_id="root-tech",
                label="Technology",
                canonical_path=["Technology"],
                version=version,
                confidence=1.0,
            ),
            TaxonomyNode(
                node_id="tech-ai",
                label="Artificial Intelligence",
                canonical_path=["Technology", "AI"],
                version=version,
                confidence=0.95,
            ),
            TaxonomyNode(
                node_id="ai-ml",
                label="Machine Learning",
                canonical_path=["Technology", "AI", "Machine Learning"],
                version=version,
                confidence=0.92,
            ),
        ]

    async def get_statistics(self, version: str) -> TaxonomyStatistics:
        """Get taxonomy statistics"""
        return TaxonomyStatistics(
            total_nodes=150,
            leaf_nodes=95,
            internal_nodes=55,
            max_depth=5,
            avg_depth=3.2,
            categories_distribution={
                "Technology": 45,
                "Science": 38,
                "Business": 32,
                "Arts": 25,
                "Other": 10,
            },
        )

    async def compare_versions(
        self, base_version: str, target_version: str
    ) -> VersionComparison:
        """Compare two taxonomy versions"""
        return VersionComparison(
            base_version=base_version,
            target_version=target_version,
            changes={
                "added_nodes": ["Technology/AI/Machine Learning/Deep Learning"],
                "removed_nodes": [],
                "modified_nodes": ["Technology/AI/Natural Language Processing"],
                "moved_nodes": [],
            },
            summary={"added": 1, "removed": 0, "modified": 1, "moved": 0},
        )

    async def validate_taxonomy(self, version: str) -> ValidationResult:
        """Validate taxonomy structure"""
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Node 'Technology/AI/NLP' could be more specific"],
            suggestions=["Consider adding 'Computer Vision' subcategory under AI"],
        )


# Dependency injection
async def get_taxonomy_service() -> TaxonomyService:
    """Get taxonomy service instance"""
    return TaxonomyService()


# API Endpoints


@taxonomy_router.get("/versions", response_model=Dict[str, Any])
async def list_taxonomy_versions(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    service: TaxonomyService = Depends(get_taxonomy_service),
) -> None:
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

        # Mock total count (would come from database)
        total_count = 25
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


@taxonomy_router.get("/{version}/tree", response_model=List[Dict[str, Any]])
async def get_taxonomy_tree(
    version: str = Path(..., description="Taxonomy version"),
    expand_level: int = Query(
        -1, ge=-1, description="Tree expansion level (-1 for full tree)"
    ),
    filter_path: Optional[str] = Query(None, description="Filter by path prefix"),
    service: TaxonomyService = Depends(get_taxonomy_service),
) -> None:
    """
    Retrieve complete taxonomy tree for specified version

    Returns hierarchical tree structure with:
    - All nodes with their canonical paths
    - Confidence scores for each classification
    - Metadata and relationship information
    - Optional filtering by path prefix
    """
    try:
        tree = await service.get_tree(version, expand_level)

        if tree is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Taxonomy version '{version}' not found",
            )

        # Apply path filtering if specified
        if filter_path:
            filter_parts = filter_path.split("/")
            tree = [
                node
                for node in tree
                if node.canonical_path[: len(filter_parts)] == filter_parts
            ]

        return tree

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get taxonomy tree: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve taxonomy tree",
        )


@taxonomy_router.get("/{version}/statistics", response_model=TaxonomyStatistics)
async def get_taxonomy_statistics(
    version: str = Path(..., description="Taxonomy version"),
    service: TaxonomyService = Depends(get_taxonomy_service),
) -> None:
    """
    Get comprehensive statistics for taxonomy version

    Returns detailed statistics including:
    - Node counts (total, leaf, internal)
    - Tree depth information
    - Category distribution
    - Structural analysis
    """
    try:
        # Verify version exists first
        tree = await service.get_tree(version)
        if tree is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Taxonomy version '{version}' not found",
            )

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


@taxonomy_router.get("/{version}/validate", response_model=ValidationResult)
async def validate_taxonomy(
    version: str = Path(..., description="Taxonomy version"),
    service: TaxonomyService = Depends(get_taxonomy_service),
) -> None:
    """
    Validate taxonomy structure and consistency

    Performs comprehensive validation including:
    - Structural integrity checks
    - Orphaned node detection
    - Circular reference detection
    - Naming convention validation
    """
    try:
        # Verify version exists first
        tree = await service.get_tree(version)
        if tree is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Taxonomy version '{version}' not found",
            )

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


@taxonomy_router.get(
    "/{base_version}/compare/{target_version}", response_model=VersionComparison
)
async def compare_taxonomy_versions(
    base_version: str = Path(..., description="Base version for comparison"),
    target_version: str = Path(..., description="Target version for comparison"),
    service: TaxonomyService = Depends(get_taxonomy_service),
) -> None:
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


@taxonomy_router.get("/{version}/search", response_model=List[Dict[str, Any]])
async def search_taxonomy_nodes(
    version: str = Path(..., description="Taxonomy version"),
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    service: TaxonomyService = Depends(get_taxonomy_service),
) -> None:
    """
    Search taxonomy nodes by name or metadata

    Supports fuzzy matching and returns:
    - Nodes matching the search query
    - Relevance scores
    - Context information
    """
    try:
        # Get full tree for searching
        tree = await service.get_tree(version)
        if tree is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Taxonomy version '{version}' not found",
            )

        # Simple search implementation (would be more sophisticated in practice)
        query_lower = q.lower()
        matching_nodes = []

        for node in tree:
            if query_lower in node.label.lower() or any(
                query_lower in path_part.lower() for path_part in node.canonical_path
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
