from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class DocumentFormatV1(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    CSV = "csv"
    HTML = "html"
    TXT = "txt"


class ProcessingStatusV1(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadCommandV1(BaseModel):
    kind: Literal["Command"] = "Command"
    name: Literal["DocumentUpload"] = "DocumentUpload"
    version: Literal["v1"] = "v1"
    correlationId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    idempotencyKey: Optional[str] = Field(None, max_length=255)

    command_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_name: str = Field(..., min_length=1, max_length=255)
    file_content: bytes = Field(...)
    file_format: DocumentFormatV1 = Field(...)
    taxonomy_path: List[str] = Field(..., min_items=1, max_items=10)
    source_url: Optional[str] = Field(None, max_length=2000)
    author: Optional[str] = Field(None, max_length=200)
    language: str = Field(default="ko", pattern="^[a-z]{2}$")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    requested_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("file_content")
    def validate_file_size(cls, v):
        max_size = 50 * 1024 * 1024
        if len(v) > max_size:
            raise ValueError(f"File size exceeds {max_size} bytes")
        return v

    @validator("file_name")
    def validate_file_extension(cls, v, values):
        if "file_format" in values:
            expected_ext = f".{values['file_format'].value}"
            if not v.lower().endswith(expected_ext):
                raise ValueError(f"File extension must be {expected_ext}")
        return v


class ChunkV1(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = Field(..., min_length=1, max_length=10000)
    token_count: int = Field(..., ge=1)
    position: int = Field(..., ge=0)
    has_pii: bool = Field(default=False)
    pii_types: List[str] = Field(default_factory=list)


class DocumentProcessedEventV1(BaseModel):
    kind: Literal["Event"] = "Event"
    name: Literal["DocumentProcessed"] = "DocumentProcessed"
    version: Literal["v1"] = "v1"
    correlationId: str = Field(...)

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    command_id: str = Field(...)
    status: ProcessingStatusV1 = Field(...)
    document_id: Optional[str] = Field(None)
    chunks: List[ChunkV1] = Field(default_factory=list)
    total_chunks: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    processing_duration_ms: float = Field(..., ge=0.0)
    error_message: Optional[str] = Field(None, max_length=1000)
    error_code: Optional[str] = Field(None, max_length=100)
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class JobStatusQueryV1(BaseModel):
    job_id: str = Field(...)


class JobStatusResponseV1(BaseModel):
    job_id: str = Field(...)
    command_id: str = Field(...)
    status: ProcessingStatusV1 = Field(...)
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    current_stage: Optional[str] = Field(None, max_length=100)
    chunks_processed: int = Field(default=0, ge=0)
    total_chunks: int = Field(default=0, ge=0)
    error_message: Optional[str] = Field(None, max_length=1000)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    estimated_completion_at: Optional[datetime] = Field(None)
