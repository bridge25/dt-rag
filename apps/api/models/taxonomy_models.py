"""
Taxonomy models for DT-RAG API
Local replacement for missing common_schemas
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class TaxonomyNodeType(str, Enum):
    """Taxonomy node types"""
    ROOT = "root"
    CATEGORY = "category"
    SUBCATEGORY = "subcategory"
    LEAF = "leaf"

class TaxonomyNode(BaseModel):
    """Taxonomy node model"""
    id: str = Field(..., description="Unique node identifier")
    name: str = Field(..., description="Node display name")
    description: Optional[str] = Field(None, description="Node description")
    node_type: TaxonomyNodeType = Field(default=TaxonomyNodeType.LEAF, description="Node type")
    parent_id: Optional[str] = Field(None, description="Parent node ID")
    children_ids: List[str] = Field(default_factory=list, description="Child node IDs")
    level: int = Field(default=0, description="Depth level in hierarchy")
    path: List[str] = Field(default_factory=list, description="Path from root")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    version: str = Field(default="1.0.0", description="Node version")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    is_active: bool = Field(default=True, description="Whether node is active")

    class Config:
        """Pydantic configuration"""
        schema_extra = {
            "example": {
                "id": "tech_ai",
                "name": "Artificial Intelligence",
                "description": "AI and machine learning technologies",
                "node_type": "category",
                "parent_id": "tech",
                "children_ids": ["tech_ai_ml", "tech_ai_nlp"],
                "level": 2,
                "path": ["root", "tech", "tech_ai"],
                "metadata": {"color": "#1f77b4", "icon": "robot"},
                "version": "1.0.0",
                "is_active": True
            }
        }

class TaxonomyVersion(BaseModel):
    """Taxonomy version model"""
    version_id: str = Field(..., description="Version identifier")
    version_number: str = Field(..., description="Semantic version")
    description: Optional[str] = Field(None, description="Version description")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Version creator")
    is_active: bool = Field(default=False, description="Whether this is the active version")
    nodes_count: int = Field(default=0, description="Number of nodes in this version")
    changes_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of changes")

class TaxonomyStats(BaseModel):
    """Taxonomy statistics model"""
    total_nodes: int = Field(default=0, description="Total number of nodes")
    total_levels: int = Field(default=0, description="Maximum depth")
    nodes_by_type: Dict[str, int] = Field(default_factory=dict, description="Count by node type")
    nodes_by_level: Dict[int, int] = Field(default_factory=dict, description="Count by level")
    active_nodes: int = Field(default=0, description="Number of active nodes")
    inactive_nodes: int = Field(default=0, description="Number of inactive nodes")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class TaxonomyTreeResponse(BaseModel):
    """Taxonomy tree response model"""
    root_node: TaxonomyNode = Field(..., description="Root node with full tree")
    version: str = Field(..., description="Taxonomy version")
    stats: TaxonomyStats = Field(..., description="Tree statistics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class TaxonomySearchResult(BaseModel):
    """Taxonomy search result model"""
    nodes: List[TaxonomyNode] = Field(default_factory=list, description="Matching nodes")
    total_count: int = Field(default=0, description="Total matching nodes")
    query: str = Field(..., description="Search query")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Applied filters")