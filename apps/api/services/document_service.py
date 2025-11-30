"""
Document Application Service

Orchestrates document-related operations and handles cross-cutting concerns.

@CODE:CLEAN-ARCHITECTURE-DOCUMENT-SERVICE
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from ..domain.entities.document import Document, DocumentChunk, DocumentWithChunks
from ..domain.repositories.document_repository import (
    IDocumentRepository,
    DocumentFilterParams,
    ChunkFilterParams,
    CreateDocumentParams,
    CreateChunkParams,
)

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Document Application Service

    Provides a high-level interface for document operations,
    orchestrating document and chunk management.

    Responsibilities:
    - Coordinate document use cases
    - Handle document ingestion workflows
    - Manage chunk operations
    - Provide unified document interface
    """

    def __init__(
        self,
        document_repository: IDocumentRepository,
        search_repository: Optional[Any] = None,
    ):
        """
        Initialize document service with dependencies.

        Args:
            document_repository: Repository for document data access
            search_repository: Optional search repository for embedding operations
        """
        self._document_repository = document_repository
        self._search_repository = search_repository

    # Document Operations

    async def get_documents(
        self,
        content_type: Optional[str] = None,
        source_url_contains: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Get paginated list of documents with filtering.

        Args:
            content_type: Filter by content type
            source_url_contains: Filter by source URL substring
            created_after: Filter by creation date (after)
            created_before: Filter by creation date (before)
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary containing documents list and pagination metadata
        """
        try:
            params = DocumentFilterParams(
                content_type=content_type,
                source_url_contains=source_url_contains,
                created_after=created_after,
                created_before=created_before,
                limit=page_size,
                offset=(page - 1) * page_size,
            )

            documents = await self._document_repository.get_all_documents(params)
            total = await self._document_repository.count_documents(params)

            return {
                "documents": [self._document_to_dict(d) for d in documents],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            }
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            raise

    async def get_document_by_id(
        self,
        doc_id: UUID,
        include_chunks: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Get document by ID with optional chunks.

        Args:
            doc_id: Document UUID
            include_chunks: Whether to include chunks

        Returns:
            Document dictionary or None
        """
        try:
            if include_chunks:
                result = await self._document_repository.get_document_with_chunks(doc_id)
                if result is None:
                    return None

                return {
                    "document": self._document_to_dict(result.document),
                    "chunks": [self._chunk_to_dict(c) for c in result.chunks],
                    "chunk_count": len(result.chunks),
                }
            else:
                document = await self._document_repository.get_document_by_id(doc_id)
                if document is None:
                    return None

                return {"document": self._document_to_dict(document)}
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            raise

    async def create_document(
        self,
        title: str,
        source_url: Optional[str] = None,
        content_type: str = "text/plain",
        file_size: Optional[int] = None,
        checksum: Optional[str] = None,
        version_tag: Optional[str] = None,
        license_tag: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new document.

        Args:
            title: Document title
            source_url: Optional source URL
            content_type: Content MIME type
            file_size: File size in bytes
            checksum: Content checksum
            version_tag: Version identifier
            license_tag: License identifier
            metadata: Additional metadata

        Returns:
            Created document dictionary
        """
        try:
            # Check for duplicate by checksum
            if checksum:
                existing = await self._document_repository.get_document_by_checksum(checksum)
                if existing:
                    logger.info(f"Document with checksum already exists: {existing.doc_id}")
                    return self._document_to_dict(existing)

            params = CreateDocumentParams(
                title=title,
                source_url=source_url,
                content_type=content_type,
                file_size=file_size,
                checksum=checksum,
                version_tag=version_tag,
                license_tag=license_tag,
                metadata=metadata,
            )

            document = await self._document_repository.create_document(params)

            logger.info(f"Created document: {document.doc_id}")
            return self._document_to_dict(document)
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise

    async def delete_document(self, doc_id: UUID) -> bool:
        """
        Delete a document and all its chunks.

        Args:
            doc_id: Document UUID

        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self._document_repository.delete_document(doc_id)

            if result:
                logger.info(f"Deleted document: {doc_id}")

            return result
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise

    # Chunk Operations

    async def get_chunks(
        self,
        doc_id: Optional[UUID] = None,
        has_embedding: Optional[bool] = None,
        has_pii: Optional[bool] = None,
        min_token_count: Optional[int] = None,
        max_token_count: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Get paginated list of chunks with filtering.

        Args:
            doc_id: Filter by document ID
            has_embedding: Filter by embedding presence
            has_pii: Filter by PII presence
            min_token_count: Minimum token count
            max_token_count: Maximum token count
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary containing chunks list and pagination metadata
        """
        try:
            params = ChunkFilterParams(
                doc_id=doc_id,
                has_embedding=has_embedding,
                has_pii=has_pii,
                min_token_count=min_token_count,
                max_token_count=max_token_count,
                limit=page_size,
                offset=(page - 1) * page_size,
            )

            chunks = await self._document_repository.get_chunks(params)
            total = await self._document_repository.count_chunks(params)

            return {
                "chunks": [self._chunk_to_dict(c) for c in chunks],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            }
        except Exception as e:
            logger.error(f"Failed to get chunks: {e}")
            raise

    async def get_chunk_by_id(self, chunk_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get chunk by ID.

        Args:
            chunk_id: Chunk UUID

        Returns:
            Chunk dictionary or None
        """
        try:
            chunk = await self._document_repository.get_chunk_by_id(chunk_id)

            if chunk is None:
                return None

            return self._chunk_to_dict(chunk)
        except Exception as e:
            logger.error(f"Failed to get chunk {chunk_id}: {e}")
            raise

    async def create_chunk(
        self,
        doc_id: UUID,
        text: str,
        chunk_index: int,
        span: tuple[int, int],
        token_count: int,
        embedding: Optional[List[float]] = None,
        has_pii: bool = False,
        pii_types: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new chunk.

        Args:
            doc_id: Parent document UUID
            text: Chunk text content
            chunk_index: Index within document
            span: Character span (start, end)
            token_count: Token count
            embedding: Optional embedding vector
            has_pii: Whether chunk contains PII
            pii_types: Types of PII detected
            metadata: Additional metadata

        Returns:
            Created chunk dictionary
        """
        try:
            params = CreateChunkParams(
                doc_id=doc_id,
                text=text,
                chunk_index=chunk_index,
                span=span,
                token_count=token_count,
                embedding=embedding,
                has_pii=has_pii,
                pii_types=pii_types,
                metadata=metadata,
            )

            chunk = await self._document_repository.create_chunk(params)

            logger.info(f"Created chunk: {chunk.chunk_id}")
            return self._chunk_to_dict(chunk)
        except Exception as e:
            logger.error(f"Failed to create chunk: {e}")
            raise

    async def create_chunks_batch(
        self,
        chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Create multiple chunks in batch.

        Args:
            chunks: List of chunk parameters

        Returns:
            List of created chunks
        """
        try:
            params_list = [
                CreateChunkParams(
                    doc_id=c["doc_id"],
                    text=c["text"],
                    chunk_index=c["chunk_index"],
                    span=c["span"],
                    token_count=c["token_count"],
                    embedding=c.get("embedding"),
                    has_pii=c.get("has_pii", False),
                    pii_types=c.get("pii_types"),
                    metadata=c.get("metadata"),
                )
                for c in chunks
            ]

            created = await self._document_repository.create_chunks_batch(params_list)

            logger.info(f"Created {len(created)} chunks")
            return [self._chunk_to_dict(c) for c in created]
        except Exception as e:
            logger.error(f"Failed to create chunks batch: {e}")
            raise

    async def update_chunk_embedding(
        self,
        chunk_id: UUID,
        embedding: List[float],
    ) -> Dict[str, Any]:
        """
        Update chunk embedding vector.

        Args:
            chunk_id: Chunk UUID
            embedding: Embedding vector

        Returns:
            Updated chunk dictionary
        """
        try:
            chunk = await self._document_repository.update_chunk_embedding(
                chunk_id, embedding
            )

            logger.info(f"Updated embedding for chunk: {chunk_id}")
            return self._chunk_to_dict(chunk)
        except Exception as e:
            logger.error(f"Failed to update chunk embedding {chunk_id}: {e}")
            raise

    # Embedding Workflow

    async def get_chunks_without_embeddings(
        self,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get chunks that need embedding generation.

        Args:
            limit: Maximum number of chunks

        Returns:
            List of chunks without embeddings
        """
        try:
            chunks = await self._document_repository.get_chunks_without_embeddings(limit)
            return [self._chunk_to_dict(c) for c in chunks]
        except Exception as e:
            logger.error(f"Failed to get chunks without embeddings: {e}")
            raise

    async def generate_embeddings_for_chunks(
        self,
        chunk_ids: Optional[List[UUID]] = None,
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Generate embeddings for chunks.

        Args:
            chunk_ids: Specific chunks to process (or all without embeddings)
            batch_size: Processing batch size

        Returns:
            Processing result dictionary
        """
        if not self._search_repository:
            raise ValueError("Search repository not configured for embedding generation")

        try:
            # Get chunks to process
            if chunk_ids:
                chunks = []
                for cid in chunk_ids:
                    chunk = await self._document_repository.get_chunk_by_id(cid)
                    if chunk:
                        chunks.append(chunk)
            else:
                chunks = await self._document_repository.get_chunks_without_embeddings(
                    batch_size
                )

            if not chunks:
                return {
                    "processed": 0,
                    "total": 0,
                    "message": "No chunks to process",
                }

            # Generate embeddings
            texts = [c.text for c in chunks]
            embeddings = await self._search_repository.generate_batch_embeddings(
                texts, batch_size
            )

            # Update chunks
            updated = 0
            for chunk, embedding in zip(chunks, embeddings):
                await self._document_repository.update_chunk_embedding(
                    chunk.chunk_id, embedding
                )
                updated += 1

            logger.info(f"Generated embeddings for {updated} chunks")
            return {
                "processed": updated,
                "total": len(chunks),
                "message": f"Successfully generated {updated} embeddings",
            }
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    # Statistics

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get document/chunk statistics.

        Returns:
            Statistics dictionary
        """
        try:
            return await self._document_repository.get_statistics()
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise

    # Helper Methods

    def _document_to_dict(self, document: Document) -> Dict[str, Any]:
        """Convert document entity to dictionary."""
        return {
            "doc_id": str(document.doc_id),
            "title": document.title,
            "source_url": document.source_url,
            "content_type": document.content_type,
            "file_size": document.file_size,
            "checksum": document.checksum,
            "version_tag": document.version_tag,
            "license_tag": document.license_tag,
            "metadata": document.metadata,
            "chunk_count": document.chunk_count,
            "total_tokens": document.total_tokens,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "processed_at": document.processed_at.isoformat() if document.processed_at else None,
        }

    def _chunk_to_dict(self, chunk: DocumentChunk) -> Dict[str, Any]:
        """Convert chunk entity to dictionary."""
        return {
            "chunk_id": str(chunk.chunk_id),
            "doc_id": str(chunk.doc_id),
            "text": chunk.text,
            "chunk_index": chunk.chunk_index,
            "span": chunk.span,
            "token_count": chunk.token_count,
            "has_embedding": chunk.has_embedding,
            "has_pii": chunk.has_pii,
            "pii_types": chunk.pii_types,
            "metadata": chunk.metadata,
            "created_at": chunk.created_at.isoformat() if chunk.created_at else None,
        }
