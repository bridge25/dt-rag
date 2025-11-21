"""
Common models for DT-RAG API
Local replacement for missing common_schemas

@CODE:API-001
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# Search models
class SearchResult(BaseModel):
    """Search result model"""

    id: str = Field(..., description="Document/content ID")
    title: str = Field(..., description="Content title")
    content: str = Field(..., description="Content text")
    score: float = Field(..., description="Relevance score")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
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
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ClassificationRequest(BaseModel):
    """Classification request model"""

    text: str = Field(..., description="Text to classify")
    model_name: Optional[str] = Field(None, description="Model to use")
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Classification options"
    )


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
    steps: List[OrchestrationStep] = Field(
        default_factory=list, description="Pipeline steps"
    )
    total_duration_ms: float = Field(..., description="Total execution time")
    result: Dict[str, Any] = Field(default_factory=dict, description="Final result")


# Agent Factory models
class AgentConfig(BaseModel):
    """Agent configuration model"""

    agent_type: str = Field(..., description="Type of agent")
    capabilities: List[str] = Field(
        default_factory=list, description="Agent capabilities"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Agent parameters"
    )
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
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Document metadata"
    )
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
