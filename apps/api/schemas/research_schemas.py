# @CODE:RESEARCH-BACKEND-001:SCHEMA
"""
Research Session Schema Models

Pydantic models for research session management.
Supports camelCase field aliases for frontend compatibility with TypeScript types.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ResearchStage(str, Enum):
    """Research session stage enumeration"""

    IDLE = "idle"
    ANALYZING = "analyzing"
    SEARCHING = "searching"
    COLLECTING = "collecting"
    ORGANIZING = "organizing"
    CONFIRMING = "confirming"
    COMPLETED = "completed"
    ERROR = "error"


class ResearchConfig(BaseModel):
    """Research configuration for customizing search behavior"""

    max_documents: int = Field(
        default=50,
        ge=1,
        le=1000,
        alias="maxDocuments",
        description="Maximum number of documents to collect"
    )
    quality_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        alias="qualityThreshold",
        description="Minimum quality score threshold (0-1)"
    )
    sources_filter: Optional[List[str]] = Field(
        default=None,
        alias="sourcesFilter",
        description="List of source types to include (web, pdf, api, database)"
    )
    depth_level: str = Field(
        default="medium",
        pattern="^(shallow|medium|deep)$",
        alias="depthLevel",
        description="Search depth level (shallow, medium, deep)"
    )

    model_config = ConfigDict(populate_by_name=True)


class StartResearchRequest(BaseModel):
    """Request to start a new research session"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Research query text"
    )
    config: Optional[ResearchConfig] = Field(
        default=None,
        description="Optional research configuration"
    )

    model_config = ConfigDict(populate_by_name=True)


class ConfirmResearchRequest(BaseModel):
    """Request to confirm and finalize research results"""

    selected_document_ids: List[str] = Field(
        ...,
        min_length=1,
        alias="selectedDocumentIds",
        description="List of selected document IDs to confirm"
    )
    taxonomy_id: Optional[str] = Field(
        default=None,
        alias="taxonomyId",
        description="Optional taxonomy ID for organizing results"
    )

    model_config = ConfigDict(populate_by_name=True)


class StartResearchResponse(BaseModel):
    """Response when research session is created"""

    session_id: str = Field(
        ...,
        alias="sessionId",
        description="Unique research session ID"
    )
    estimated_duration: int = Field(
        ...,
        ge=0,
        alias="estimatedDuration",
        description="Estimated duration in seconds"
    )

    model_config = ConfigDict(populate_by_name=True)


class ResearchEvent(BaseModel):
    """Event published during research session execution"""

    event_id: str = Field(
        ...,
        description="Unique event ID"
    )
    event_type: str = Field(
        ...,
        description="Type of event (progress, stage_change, document_found, etc.)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Event timestamp"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data"
    )

    model_config = ConfigDict(populate_by_name=True)


class ResearchSession(BaseModel):
    """Active research session state"""

    id: str = Field(
        ...,
        description="Unique session ID"
    )
    query: str = Field(
        ...,
        description="Research query"
    )
    stage: ResearchStage = Field(
        ...,
        description="Current research stage"
    )
    progress: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Progress percentage (0-1)"
    )
    documents: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Discovered documents"
    )
    events: List[ResearchEvent] = Field(
        default_factory=list,
        description="Session events"
    )
    config: Optional[ResearchConfig] = Field(
        default=None,
        description="Research configuration"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID if session is user-specific"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Session creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )

    model_config = ConfigDict(populate_by_name=True)
