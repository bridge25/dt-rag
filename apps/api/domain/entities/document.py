"""
Document Entity - Core Business Model

Represents documents and their chunks in the knowledge base.

Business Rules:
- Document must have a unique identifier
- Chunks must belong to a document
- Chunk text cannot be empty
- Token count must be non-negative

@CODE:CLEAN-ARCHITECTURE-DOCUMENT-ENTITY
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


@dataclass(frozen=True)
class DocumentChunk:
    """
    Document Chunk Entity

    A chunk is a segment of a document optimized for retrieval.
    Each chunk has its own embedding for vector search.

    Attributes:
        chunk_id: Unique chunk identifier
        doc_id: Parent document identifier
        text: Chunk text content
        chunk_index: Position in document (0-indexed)
        span: Character range in original document (start, end)
        token_count: Number of tokens in chunk
        embedding: Optional pre-computed embedding vector
        has_pii: Whether chunk contains PII
        pii_types: Types of PII detected
        metadata: Additional chunk metadata
    """
    chunk_id: UUID
    doc_id: UUID
    text: str
    chunk_index: int
    span: tuple[int, int] = (0, 0)
    token_count: int = 0
    embedding: Optional[List[float]] = None
    has_pii: bool = False
    pii_types: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate business rules"""
        if not self.text or not self.text.strip():
            raise ValueError("Chunk text cannot be empty")
        if self.token_count < 0:
            raise ValueError("Token count must be non-negative")
        if self.chunk_index < 0:
            raise ValueError("Chunk index must be non-negative")

    @property
    def char_count(self) -> int:
        """Get character count of chunk text"""
        return len(self.text)

    @property
    def has_embedding(self) -> bool:
        """Check if chunk has a pre-computed embedding"""
        return self.embedding is not None and len(self.embedding) > 0


@dataclass(frozen=True)
class Document:
    """
    Document Entity

    A document is a source of knowledge that gets chunked
    and embedded for retrieval operations.

    Attributes:
        doc_id: Unique document identifier
        title: Document title
        source_url: Original source URL
        content_type: MIME type of document
        file_size: Size in bytes
        checksum: Content hash for deduplication
        version_tag: Version identifier
        license_tag: License information
        metadata: Additional document metadata
        chunk_metadata: Chunking configuration used
    """
    doc_id: UUID
    title: Optional[str] = None
    source_url: Optional[str] = None
    content_type: str = "text/plain"
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    version_tag: Optional[str] = None
    license_tag: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def display_title(self) -> str:
        """Get display title, falling back to source URL or ID"""
        if self.title:
            return self.title
        if self.source_url:
            return self.source_url.split("/")[-1]
        return str(self.doc_id)[:8]

    @property
    def is_processed(self) -> bool:
        """Check if document has been processed"""
        return self.processed_at is not None


@dataclass(frozen=True)
class DocumentWithChunks:
    """Document with its associated chunks"""
    document: Document
    chunks: List[DocumentChunk] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        """Calculate total token count across all chunks"""
        return sum(chunk.token_count for chunk in self.chunks)

    @property
    def total_chunks(self) -> int:
        """Get number of chunks"""
        return len(self.chunks)

    @property
    def embedding_coverage(self) -> float:
        """Calculate percentage of chunks with embeddings"""
        if not self.chunks:
            return 0.0
        embedded = sum(1 for chunk in self.chunks if chunk.has_embedding)
        return (embedded / len(self.chunks)) * 100


# Business Logic Functions

def calculate_optimal_chunk_size(
    doc_content_type: str,
    avg_query_length: int = 50
) -> int:
    """
    Calculate optimal chunk size based on document type.

    Business Rules:
    - Code: 500 tokens (preserve function context)
    - Markdown/Docs: 300 tokens (semantic paragraphs)
    - Plain text: 200 tokens (general content)
    """
    if "code" in doc_content_type or doc_content_type in ["text/x-python", "text/javascript"]:
        return 500
    if "markdown" in doc_content_type or "html" in doc_content_type:
        return 300
    return 200


def should_filter_pii(chunk: DocumentChunk) -> bool:
    """Determine if chunk should be filtered due to PII"""
    sensitive_pii_types = {"ssn", "credit_card", "password", "api_key"}
    return chunk.has_pii and bool(set(chunk.pii_types) & sensitive_pii_types)
