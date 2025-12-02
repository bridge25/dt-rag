"""
Document Repository Interface

Defines the contract for Document/Chunk data access operations.

@CODE:CLEAN-ARCHITECTURE-DOCUMENT-REPOSITORY
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from ..entities.document import Document, DocumentChunk, DocumentWithChunks


@dataclass
class DocumentFilterParams:
    """Parameters for filtering document queries"""
    content_type: Optional[str] = None
    source_url_contains: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    has_embeddings: Optional[bool] = None
    taxonomy_path: Optional[List[str]] = None
    limit: int = 50
    offset: int = 0


@dataclass
class ChunkFilterParams:
    """Parameters for filtering chunk queries"""
    doc_id: Optional[UUID] = None
    has_embedding: Optional[bool] = None
    has_pii: Optional[bool] = None
    min_token_count: Optional[int] = None
    max_token_count: Optional[int] = None
    limit: int = 100
    offset: int = 0


@dataclass
class CreateDocumentParams:
    """Parameters for creating a new document"""
    title: Optional[str] = None
    source_url: Optional[str] = None
    content_type: str = "text/plain"
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    version_tag: Optional[str] = None
    license_tag: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class CreateChunkParams:
    """Parameters for creating a new chunk"""
    doc_id: UUID
    text: str
    chunk_index: int
    span: tuple[int, int] = (0, 0)
    token_count: int = 0
    embedding: Optional[List[float]] = None
    has_pii: bool = False
    pii_types: List[str] = None
    metadata: Dict[str, Any] = None


class IDocumentRepository(ABC):
    """
    Document Repository Interface

    Defines all data access operations for Document entities.
    """

    # Document Operations

    @abstractmethod
    async def get_document_by_id(self, doc_id: UUID) -> Optional[Document]:
        """Get document by ID"""

    @abstractmethod
    async def get_all_documents(
        self,
        params: Optional[DocumentFilterParams] = None
    ) -> List[Document]:
        """Get all documents with optional filtering"""

    @abstractmethod
    async def create_document(self, params: CreateDocumentParams) -> Document:
        """Create a new document"""

    @abstractmethod
    async def delete_document(self, doc_id: UUID) -> bool:
        """Delete a document and all its chunks"""

    @abstractmethod
    async def get_document_by_checksum(self, checksum: str) -> Optional[Document]:
        """Find document by content checksum (for deduplication)"""

    @abstractmethod
    async def count_documents(
        self,
        params: Optional[DocumentFilterParams] = None
    ) -> int:
        """Count documents matching filters"""

    # Chunk Operations

    @abstractmethod
    async def get_chunk_by_id(self, chunk_id: UUID) -> Optional[DocumentChunk]:
        """Get chunk by ID"""

    @abstractmethod
    async def get_chunks_by_doc_id(self, doc_id: UUID) -> List[DocumentChunk]:
        """Get all chunks for a document"""

    @abstractmethod
    async def get_chunks(
        self,
        params: Optional[ChunkFilterParams] = None
    ) -> List[DocumentChunk]:
        """Get chunks with optional filtering"""

    @abstractmethod
    async def create_chunk(self, params: CreateChunkParams) -> DocumentChunk:
        """Create a new chunk"""

    @abstractmethod
    async def create_chunks_batch(
        self,
        chunks: List[CreateChunkParams]
    ) -> List[DocumentChunk]:
        """Create multiple chunks in batch"""

    @abstractmethod
    async def update_chunk_embedding(
        self,
        chunk_id: UUID,
        embedding: List[float]
    ) -> DocumentChunk:
        """Update chunk embedding vector"""

    @abstractmethod
    async def count_chunks(
        self,
        params: Optional[ChunkFilterParams] = None
    ) -> int:
        """Count chunks matching filters"""

    # Combined Operations

    @abstractmethod
    async def get_document_with_chunks(
        self,
        doc_id: UUID
    ) -> Optional[DocumentWithChunks]:
        """Get document with all its chunks"""

    @abstractmethod
    async def get_chunks_without_embeddings(
        self,
        limit: int = 100
    ) -> List[DocumentChunk]:
        """Get chunks that need embedding generation"""

    # Statistics

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get document/chunk statistics.

        Returns dict with:
        - total_documents: int
        - total_chunks: int
        - embedded_chunks: int
        - total_tokens: int
        - embedding_coverage: float (0-100)
        """
