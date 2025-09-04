"""
문서 수집 파이프라인 데이터 모델
"""

import hashlib
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from uuid import UUID


class DocumentType(str, Enum):
    """문서 타입"""
    PDF = "pdf"
    MARKDOWN = "markdown" 
    HTML = "html"


class IngestionStatus(str, Enum):
    """수집 작업 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DLQ = "dlq"  # Dead Letter Queue


@dataclass
class DocumentMetadata:
    """문서 메타데이터"""
    filename: str
    content_type: str
    size_bytes: int
    doc_hash: str
    doc_type: DocumentType
    source_url: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_content(cls, filename: str, content: bytes, content_type: str, **kwargs) -> "DocumentMetadata":
        """콘텐츠로부터 메타데이터 생성"""
        doc_hash = hashlib.sha256(content).hexdigest()
        doc_type = cls._detect_document_type(filename, content_type)
        
        return cls(
            filename=filename,
            content_type=content_type,
            size_bytes=len(content),
            doc_hash=doc_hash,
            doc_type=doc_type,
            **kwargs
        )
    
    @staticmethod
    def _detect_document_type(filename: str, content_type: str) -> DocumentType:
        """파일명과 콘텐츠 타입으로 문서 타입 감지"""
        if content_type.startswith("application/pdf") or filename.endswith(".pdf"):
            return DocumentType.PDF
        elif content_type.startswith("text/markdown") or filename.endswith((".md", ".markdown")):
            return DocumentType.MARKDOWN
        elif content_type.startswith("text/html") or filename.endswith((".html", ".htm")):
            return DocumentType.HTML
        else:
            # 기본값으로 Markdown 처리
            return DocumentType.MARKDOWN


@dataclass  
class ChunkResult:
    """청킹 결과"""
    chunk_id: UUID
    text: str
    start_char: int
    end_char: int
    chunk_index: int
    metadata: Dict[str, Any]


@dataclass
class IngestionJob:
    """수집 작업"""
    job_id: UUID
    doc_metadata: DocumentMetadata
    status: IngestionStatus
    created_at: datetime
    updated_at: datetime
    chunks_created: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "job_id": str(self.job_id),
            "filename": self.doc_metadata.filename,
            "doc_hash": self.doc_metadata.doc_hash,
            "doc_type": self.doc_metadata.doc_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "chunks_created": self.chunks_created,
            "error_message": self.error_message,
            "retry_count": self.retry_count
        }


@dataclass
class ParseResult:
    """파싱 결과"""
    text: str
    metadata: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None