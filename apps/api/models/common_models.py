"""
Common models for DT-RAG API
Local replacement for missing common_schemas
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# Search models
class SearchResult(BaseModel):
    """Search result model"""
    id: str = Field(..., description="Document/content ID")
    title: str = Field(..., description="Content title")
    content: str = Field(..., description="Content text")
    score: float = Field(..., description="Relevance score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    source: Optional[str] = Field(None, description="Content source")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")

class SearchQuery(BaseModel):
    """Search query model"""
    query: str = Field(..., description="Search query text")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    limit: int = Field(default=10, description="Maximum results")
    offset: int = Field(default=0, description="Results offset")

# Classification models
class ClassificationResult(BaseModel):
    """Classification result model"""
    label: str = Field(..., description="Predicted label")
    confidence: float = Field(..., description="Confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ClassificationRequest(BaseModel):
    """Classification request model"""
    text: str = Field(..., description="Text to classify")
    model_name: Optional[str] = Field(None, description="Model to use")
    options: Dict[str, Any] = Field(default_factory=dict, description="Classification options")

# Orchestration models
class OrchestrationStep(BaseModel):
    """Orchestration step model"""
    step_name: str = Field(..., description="Step name")
    step_type: str = Field(..., description="Step type")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Step input")
    output_data: Dict[str, Any] = Field(default_factory=dict, description="Step output")
    status: str = Field(default="pending", description="Step status")
    duration_ms: Optional[float] = Field(None, description="Execution duration")
    error: Optional[str] = Field(None, description="Error message if failed")

class OrchestrationResult(BaseModel):
    """Orchestration result model"""
    pipeline_id: str = Field(..., description="Pipeline execution ID")
    status: str = Field(..., description="Overall status")
    steps: List[OrchestrationStep] = Field(default_factory=list, description="Pipeline steps")
    total_duration_ms: float = Field(..., description="Total execution time")
    result: Dict[str, Any] = Field(default_factory=dict, description="Final result")

# Agent Factory models
class AgentConfig(BaseModel):
    """Agent configuration model"""
    agent_type: str = Field(..., description="Type of agent")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Agent parameters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Agent metadata")

class AgentInstance(BaseModel):
    """Agent instance model"""
    agent_id: str = Field(..., description="Unique agent ID")
    agent_type: str = Field(..., description="Agent type")
    status: str = Field(default="inactive", description="Agent status")
    config: AgentConfig = Field(..., description="Agent configuration")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = Field(None, description="Last activity timestamp")

# Document models
class Document(BaseModel):
    """Document model"""
    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Common response models
class StatusResponse(BaseModel):
    """Generic status response"""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
# Search API specific models
class SourceMeta(BaseModel):
    """Source metadata model"""
    source_type: str = Field(..., description="Type of source")
    source_id: str = Field(..., description="Source identifier")
    url: Optional[str] = Field(None, description="Source URL")
    title: Optional[str] = Field(None, description="Source title")
    created_at: Optional[datetime] = Field(None, description="Creation date")

class SearchHit(BaseModel):
    """Individual search hit model"""
    id: str = Field(..., description="Hit ID")
    score: float = Field(..., description="Relevance score")
    content: str = Field(..., description="Hit content")
    title: Optional[str] = Field(None, description="Hit title")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Hit metadata")
    source_meta: Optional[SourceMeta] = Field(None, description="Source metadata")

class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., description="Search query")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    limit: int = Field(default=10, ge=1, le=100, description="Result limit")
    offset: int = Field(default=0, ge=0, description="Result offset")
    include_metadata: bool = Field(default=True, description="Include metadata in results")
    search_type: Optional[str] = Field(default="hybrid", description="Type of search")

class SearchResponse(BaseModel):
    """Search response model"""
    query: str = Field(..., description="Original query")
    hits: List[SearchHit] = Field(default_factory=list, description="Search results")
    total_hits: int = Field(..., description="Total number of hits")
    search_time_ms: float = Field(..., description="Search execution time")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Applied filters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")

# Classification API specific models
class ClassifyRequest(BaseModel):
    """Classification request model"""
    text: str = Field(..., description="Text to classify")
    model_name: Optional[str] = Field(None, description="Classification model to use")
    confidence_threshold: Optional[float] = Field(default=0.5, description="Minimum confidence threshold")
    max_labels: Optional[int] = Field(default=5, description="Maximum number of labels to return")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional request metadata")

class ClassifyResponse(BaseModel):
    """Classification response model"""
    text: str = Field(..., description="Original text")
    predictions: List[ClassificationResult] = Field(default_factory=list, description="Classification predictions")
    model_name: str = Field(..., description="Model used for classification")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")

# Taxonomy models  
class TaxonomyNode(BaseModel):
    """Taxonomy node model"""
    id: str = Field(..., description="Node ID")
    name: str = Field(..., description="Node name")
    parent_id: Optional[str] = Field(None, description="Parent node ID")
    level: int = Field(..., description="Taxonomy level")
    description: Optional[str] = Field(None, description="Node description")
    children: List['TaxonomyNode'] = Field(default_factory=list, description="Child nodes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Node metadata")

# Enable forward references
TaxonomyNode.model_rebuild()

# Agent Factory API specific models
class FromCategoryRequest(BaseModel):
    """Request to create agent from category"""
    category: str = Field(..., description="Agent category")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Request metadata")

class RetrievalConfig(BaseModel):
    """Retrieval configuration model"""
    max_results: int = Field(default=10, description="Maximum retrieval results")
    similarity_threshold: float = Field(default=0.7, description="Similarity threshold")
    search_type: str = Field(default="hybrid", description="Search type (bm25|vector|hybrid)")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")

class FeaturesConfig(BaseModel):
    """Features configuration model"""
    enabled_features: List[str] = Field(default_factory=list, description="Enabled features")
    feature_parameters: Dict[str, Any] = Field(default_factory=dict, description="Feature parameters")
    experimental_features: List[str] = Field(default_factory=list, description="Experimental features")

class AgentManifest(BaseModel):
    """Agent manifest model"""
    agent_id: str = Field(..., description="Agent identifier")
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    version: str = Field(..., description="Agent version")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    retrieval_config: RetrievalConfig = Field(..., description="Retrieval configuration")
    features_config: FeaturesConfig = Field(..., description="Features configuration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Agent metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
