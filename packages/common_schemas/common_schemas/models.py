"""
Common Pydantic models for DT-RAG v1.8.1

Shared data models used across the search, classification, and orchestration systems
"""

from typing import List, Optional, Any, Dict, Union
from datetime import datetime
from pydantic import BaseModel, Field


class SourceMeta(BaseModel):
    """Source document metadata"""
    url: str = Field(..., description="Document source URL")
    title: str = Field(..., description="Document title")
    date: str = Field(..., description="Document date (ISO format)")
    author: Optional[str] = Field(None, description="Document author")
    content_type: Optional[str] = Field(None, description="MIME type of source document")
    language: Optional[str] = Field(None, description="Document language code")


class SearchHit(BaseModel):
    """Individual search result hit"""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    score: float = Field(..., description="Relevance score (0-1)")
    text: str = Field(..., description="Matched text content")
    source: SourceMeta = Field(..., description="Source document metadata")
    taxonomy_path: List[str] = Field(..., description="Hierarchical taxonomy path")
    highlights: Optional[List[str]] = Field(None, description="Highlighted text snippets")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional chunk metadata")


class SearchRequest(BaseModel):
    """Search request parameters"""
    q: str = Field(..., description="Search query text", min_length=1)
    max_results: int = Field(10, description="Maximum number of results", ge=1, le=100)
    canonical_in: Optional[List[List[str]]] = Field(None, description="Taxonomy paths to filter by")
    min_score: Optional[float] = Field(None, description="Minimum relevance score", ge=0, le=1)
    include_highlights: bool = Field(True, description="Include highlighted text snippets")
    search_mode: Optional[str] = Field("hybrid", description="Search mode: hybrid, bm25, vector")


class SearchResponse(BaseModel):
    """Search response with results"""
    hits: List[SearchHit] = Field(..., description="Search result hits")
    latency: float = Field(..., description="Search latency in seconds")
    request_id: str = Field(..., description="Unique request identifier")
    total_candidates: Optional[int] = Field(None, description="Total candidate documents considered")
    sources_count: Optional[int] = Field(None, description="Number of unique source documents")
    taxonomy_version: Optional[str] = Field(None, description="Taxonomy version used")
    query_analysis: Optional[Dict[str, Any]] = Field(None, description="Query analysis metadata")


# Additional models for orchestration and other systems

class ClassificationResult(BaseModel):
    """Document classification result"""
    taxonomy_path: List[str] = Field(..., description="Predicted taxonomy path")
    confidence: float = Field(..., description="Classification confidence (0-1)")
    alternatives: Optional[List[Dict[str, Union[List[str], float]]]] = Field(
        None, description="Alternative classifications with confidence scores"
    )


class DocumentChunk(BaseModel):
    """Document text chunk for processing"""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    text: str = Field(..., description="Chunk text content")
    start_char: int = Field(..., description="Start character position in document")
    end_char: int = Field(..., description="End character position in document")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Chunk metadata")


class ProcessingStatus(BaseModel):
    """Processing job status"""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: pending, processing, completed, failed")
    progress: Optional[float] = Field(None, description="Processing progress (0-1)")
    message: Optional[str] = Field(None, description="Status message")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")


class ErrorDetail(BaseModel):
    """Error detail information"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(..., description="Error occurrence timestamp")


# Additional models for taxonomy and classification

class TaxonomyNode(BaseModel):
    """Taxonomy node representation"""
    id: str = Field(..., description="Unique node identifier")
    name: str = Field(..., description="Node name/label")
    path: List[str] = Field(..., description="Full hierarchical path")
    parent_id: Optional[str] = Field(None, description="Parent node identifier")
    children: Optional[List["TaxonomyNode"]] = Field(None, description="Child nodes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional node metadata")
    level: int = Field(..., description="Depth level in hierarchy")


class ClassifyRequest(BaseModel):
    """Document classification request"""
    text: str = Field(..., description="Text content to classify", min_length=1)
    max_suggestions: int = Field(5, description="Maximum classification suggestions", ge=1, le=20)
    include_confidence: bool = Field(True, description="Include confidence scores")
    taxonomy_filter: Optional[List[str]] = Field(None, description="Filter to specific taxonomy branches")


class ClassifyResponse(BaseModel):
    """Document classification response"""
    classifications: List[ClassificationResult] = Field(..., description="Classification results")
    request_id: str = Field(..., description="Unique request identifier")
    processing_time: float = Field(..., description="Processing time in seconds")
    taxonomy_version: Optional[str] = Field(None, description="Taxonomy version used")


class FromCategoryRequest(BaseModel):
    """Request to create agent from category"""
    category_path: List[str] = Field(..., description="Taxonomy category path")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")
    features: Optional[Dict[str, bool]] = Field(None, description="Feature flags")


class RetrievalConfig(BaseModel):
    """Configuration for retrieval operations"""
    max_results: int = Field(10, description="Maximum results to retrieve", ge=1, le=100)
    similarity_threshold: float = Field(0.7, description="Similarity threshold", ge=0, le=1)
    rerank_enabled: bool = Field(True, description="Enable result reranking")
    include_metadata: bool = Field(True, description="Include document metadata")


class FeaturesConfig(BaseModel):
    """Configuration for agent features"""
    semantic_search: bool = Field(True, description="Enable semantic search")
    keyword_search: bool = Field(True, description="Enable keyword search")
    classification: bool = Field(True, description="Enable classification")
    summarization: bool = Field(False, description="Enable summarization")
    qa_mode: bool = Field(False, description="Enable Q&A mode")


class AgentManifest(BaseModel):
    """Agent configuration manifest"""
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    taxonomy_scope: List[str] = Field(..., description="Taxonomy scope for agent")
    retrieval_config: RetrievalConfig = Field(..., description="Retrieval configuration")
    features_config: FeaturesConfig = Field(..., description="Features configuration")
    created_at: datetime = Field(..., description="Creation timestamp")
    version: str = Field("1.0.0", description="Agent version")


# Update model references for forward compatibility
TaxonomyNode.model_rebuild()


# Export all models
__all__ = [
    "SourceMeta",
    "SearchHit",
    "SearchRequest",
    "SearchResponse",
    "ClassificationResult",
    "DocumentChunk",
    "ProcessingStatus",
    "ErrorDetail",
    "TaxonomyNode",
    "ClassifyRequest",
    "ClassifyResponse",
    "FromCategoryRequest",
    "RetrievalConfig",
    "FeaturesConfig",
    "AgentManifest"
]