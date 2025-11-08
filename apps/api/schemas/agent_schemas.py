# @CODE:AGENT-GROWTH-002:SCHEMA
# @CODE:AGENT-GROWTH-003:SCHEMA
# @CODE:POKEMON-IMAGE-COMPLETE-001-SCHEMA-001
from pydantic import BaseModel, Field, UUID4, ConfigDict
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

# Pokemon Avatar System Types
Rarity = Literal["Common", "Rare", "Epic", "Legendary"]


class AgentCreateRequest(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=255, description="Agent display name"
    )
    taxonomy_node_ids: List[UUID4] = Field(
        ..., min_length=1, description="Selected taxonomy node IDs"
    )
    taxonomy_version: str = Field(default="1.0.0", description="Taxonomy version")
    scope_description: Optional[str] = Field(
        None, max_length=500, description="Human-readable scope description"
    )
    retrieval_config: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {"top_k": 5, "strategy": "hybrid"},
        description="Retrieval configuration",
    )
    features_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Feature flags configuration"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Breast Cancer Treatment Specialist",
                    "taxonomy_node_ids": ["550e8400-e29b-41d4-a716-446655440000"],
                    "taxonomy_version": "1.0.0",
                    "scope_description": "Agent focused on breast cancer diagnosis and treatment protocols",
                    "retrieval_config": {"top_k": 10, "strategy": "hybrid"},
                    "features_config": {},
                }
            ]
        }
    )


class AgentResponse(BaseModel):
    agent_id: UUID4 = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Agent display name")
    taxonomy_node_ids: List[UUID4] = Field(
        ..., description="Assigned taxonomy node IDs"
    )
    taxonomy_version: str = Field(..., description="Taxonomy version")
    scope_description: Optional[str] = Field(
        None, description="Human-readable scope description"
    )
    total_documents: int = Field(..., description="Total documents in agent scope")
    total_chunks: int = Field(..., description="Total chunks in agent scope")
    coverage_percent: float = Field(
        ..., ge=0.0, le=100.0, description="Coverage percentage"
    )
    last_coverage_update: Optional[datetime] = Field(
        None, description="Last coverage update timestamp"
    )
    level: int = Field(..., ge=1, le=5, description="Agent level (1-5)")
    current_xp: int = Field(..., ge=0, description="Current experience points")
    total_queries: int = Field(..., ge=0, description="Total queries executed")
    successful_queries: int = Field(..., ge=0, description="Successful queries count")
    avg_faithfulness: float = Field(
        ..., ge=0.0, le=1.0, description="Average faithfulness score"
    )
    avg_response_time_ms: float = Field(
        ..., ge=0.0, description="Average response time in milliseconds"
    )
    retrieval_config: Dict[str, Any] = Field(..., description="Retrieval configuration")
    features_config: Dict[str, Any] = Field(
        ..., description="Feature flags configuration"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_query_at: Optional[datetime] = Field(None, description="Last query timestamp")

    # Pokemon Avatar System Fields (SPEC-POKEMON-IMAGE-COMPLETE-001)
    avatar_url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL to agent's Pokemon-style avatar image"
    )
    rarity: Rarity = Field(
        default="Common",
        description="Agent rarity tier (Pokemon card style)"
    )
    character_description: Optional[str] = Field(
        None,
        max_length=500,
        description="Character description for AI-generated avatars (future feature)"
    )

    model_config = ConfigDict(from_attributes=True)


class AgentListResponse(BaseModel):
    agents: List[AgentResponse] = Field(..., description="List of agents")
    total: int = Field(..., ge=0, description="Total count of agents")
    filters_applied: Dict[str, Any] = Field(
        ..., description="Filters applied to the query"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "agents": [],
                    "total": 0,
                    "filters_applied": {"level": 1, "min_coverage": 50.0},
                }
            ]
        }
    )


class CoverageResponse(BaseModel):
    agent_id: UUID4 = Field(..., description="Agent ID")
    overall_coverage: float = Field(
        ..., ge=0.0, le=100.0, description="Overall coverage percentage"
    )
    node_coverage: Dict[str, float] = Field(
        ..., description="Per-node coverage {node_id: percentage}"
    )
    document_counts: Dict[str, int] = Field(..., description="Per-node document count")
    target_counts: Dict[str, int] = Field(..., description="Per-node target count")
    version: str = Field(..., description="Taxonomy version")
    calculated_at: datetime = Field(..., description="Calculation timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                    "overall_coverage": 75.5,
                    "node_coverage": {"550e8400-e29b-41d4-a716-446655440000": 80.0},
                    "document_counts": {"550e8400-e29b-41d4-a716-446655440000": 100},
                    "target_counts": {"550e8400-e29b-41d4-a716-446655440000": 125},
                    "version": "1.0.0",
                    "calculated_at": "2025-10-12T10:30:00Z",
                }
            ]
        }
    )


class GapResponse(BaseModel):
    node_id: UUID4 = Field(..., description="Node ID with coverage gap")
    current_coverage: float = Field(
        ..., ge=0.0, le=100.0, description="Current coverage percentage"
    )
    target_coverage: float = Field(
        ..., ge=0.0, le=100.0, description="Target coverage percentage"
    )
    missing_docs: int = Field(..., ge=0, description="Estimated missing documents")
    recommendation: str = Field(..., description="Recommendation to close the gap")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "node_id": "550e8400-e29b-41d4-a716-446655440000",
                    "current_coverage": 30.0,
                    "target_coverage": 50.0,
                    "missing_docs": 20,
                    "recommendation": "Collect 20 more documents for this topic",
                }
            ]
        }
    )


class GapListResponse(BaseModel):
    agent_id: UUID4 = Field(..., description="Agent ID")
    gaps: List[GapResponse] = Field(..., description="List of coverage gaps")
    threshold: float = Field(..., ge=0.0, le=1.0, description="Coverage threshold used")
    detected_at: datetime = Field(..., description="Detection timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                    "gaps": [],
                    "threshold": 0.5,
                    "detected_at": "2025-10-12T10:30:00Z",
                }
            ]
        }
    )


class QueryRequest(BaseModel):
    query: str = Field(
        ..., min_length=1, max_length=1000, description="User query text"
    )
    top_k: Optional[int] = Field(
        None, ge=1, le=50, description="Override agent's retrieval_config.top_k"
    )
    streaming: bool = Field(default=False, description="Enable streaming response")
    include_metadata: bool = Field(
        default=True, description="Include document metadata in results"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "query": "What are the latest treatments for HER2-positive breast cancer?",
                    "top_k": 10,
                    "streaming": False,
                    "include_metadata": True,
                }
            ]
        }
    )


class SearchResultItem(BaseModel):
    doc_id: UUID4 = Field(..., description="Document ID")
    chunk_id: UUID4 = Field(..., description="Chunk ID")
    content: str = Field(..., description="Chunk text content")
    score: float = Field(..., ge=0.0, description="Relevance score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "doc_id": "123e4567-e89b-12d3-a456-426614174000",
                    "chunk_id": "223e4567-e89b-12d3-a456-426614174001",
                    "content": "HER2-positive breast cancer treatment includes...",
                    "score": 0.95,
                    "metadata": {
                        "title": "Breast Cancer Treatment Guidelines",
                        "source": "PubMed",
                    },
                }
            ]
        }
    )


class QueryResponse(BaseModel):
    agent_id: UUID4 = Field(..., description="Agent ID")
    query: str = Field(..., description="Original query text")
    results: List[SearchResultItem] = Field(..., description="Search results")
    total_results: int = Field(..., ge=0, description="Total results count")
    query_time_ms: float = Field(
        ..., ge=0.0, description="Query execution time in milliseconds"
    )
    retrieval_strategy: str = Field(..., description="Retrieval strategy used")
    executed_at: datetime = Field(..., description="Execution timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                    "query": "HER2-positive breast cancer treatment",
                    "results": [],
                    "total_results": 0,
                    "query_time_ms": 250.5,
                    "retrieval_strategy": "hybrid",
                    "executed_at": "2025-10-12T10:30:00Z",
                }
            ]
        }
    )


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Updated agent name"
    )
    scope_description: Optional[str] = Field(
        None, max_length=500, description="Updated scope description"
    )
    retrieval_config: Optional[Dict[str, Any]] = Field(
        None, description="Updated retrieval configuration"
    )
    features_config: Optional[Dict[str, Any]] = Field(
        None, description="Updated features configuration"
    )

    # Pokemon Avatar System Fields (SPEC-POKEMON-IMAGE-COMPLETE-001)
    avatar_url: Optional[str] = Field(
        None,
        max_length=500,
        description="Updated avatar URL"
    )
    rarity: Optional[Rarity] = Field(
        None,
        description="Updated rarity tier"
    )
    character_description: Optional[str] = Field(
        None,
        max_length=500,
        description="Updated character description"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Advanced Cancer Research Agent",
                    "scope_description": "Enhanced agent for cancer research with expanded scope",
                    "retrieval_config": {"top_k": 15, "strategy": "hybrid"},
                    "features_config": {"enable_cache": True},
                    "avatar_url": "/avatars/epic/default-1.png",
                    "rarity": "Epic",
                    "character_description": "An Epic-tier research specialist",
                }
            ]
        }
    )


class BackgroundTaskResponse(BaseModel):
    task_id: str = Field(..., description="Background task ID")
    agent_id: UUID4 = Field(..., description="Agent ID")
    task_type: str = Field(..., description="Task type (coverage_refresh)")
    status: str = Field(
        ..., description="Task status (pending, running, completed, failed)"
    )
    created_at: datetime = Field(..., description="Task creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Task start timestamp")
    completed_at: Optional[datetime] = Field(
        None, description="Task completion timestamp"
    )
    result: Optional[Dict[str, Any]] = Field(None, description="Task result data")
    error: Optional[str] = Field(None, description="Error message if failed")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "task_id": "task-123e4567-e89b-12d3-a456-426614174000",
                    "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                    "task_type": "coverage_refresh",
                    "status": "completed",
                    "created_at": "2025-10-12T10:30:00Z",
                    "started_at": "2025-10-12T10:30:01Z",
                    "completed_at": "2025-10-12T10:30:45Z",
                    "result": {"coverage_percent": 85.5},
                    "error": None,
                }
            ]
        }
    )


class TaskStatusResponse(BackgroundTaskResponse):
    queue_position: Optional[int] = Field(
        None, description="Queue position (only for pending tasks)"
    )
    estimated_completion_at: Optional[datetime] = Field(
        None, description="Estimated completion time"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "task_id": "agent-coverage-123e4567",
                    "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                    "task_type": "coverage_refresh",
                    "status": "pending",
                    "created_at": "2025-10-12T10:30:00Z",
                    "started_at": None,
                    "completed_at": None,
                    "result": None,
                    "error": None,
                    "queue_position": 5,
                    "estimated_completion_at": "2025-10-12T10:35:00Z",
                }
            ]
        }
    )


class CoverageHistoryItem(BaseModel):
    timestamp: datetime = Field(..., description="Measurement timestamp")
    overall_coverage: float = Field(
        ..., ge=0.0, le=100.0, description="Overall coverage percentage"
    )
    total_documents: int = Field(..., ge=0, description="Total documents at this time")
    total_chunks: int = Field(..., ge=0, description="Total chunks at this time")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "timestamp": "2025-10-12T10:30:00Z",
                    "overall_coverage": 75.5,
                    "total_documents": 1000,
                    "total_chunks": 5000,
                }
            ]
        }
    )


class CoverageHistoryResponse(BaseModel):
    agent_id: UUID4 = Field(..., description="Agent ID")
    history: List[CoverageHistoryItem] = Field(
        ..., description="Coverage history timeline"
    )
    start_date: Optional[datetime] = Field(None, description="Filter start date")
    end_date: Optional[datetime] = Field(None, description="Filter end date")
    total_entries: int = Field(..., ge=0, description="Total history entries")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "agent_id": "123e4567-e89b-12d3-a456-426614174000",
                    "history": [],
                    "start_date": "2025-10-01T00:00:00Z",
                    "end_date": "2025-10-12T23:59:59Z",
                    "total_entries": 0,
                }
            ]
        }
    )
