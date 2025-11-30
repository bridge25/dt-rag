"""
Document Mapper - ORM ↔ Entity Transformer

Transforms between SQLAlchemy Document/Chunk models and Domain entities.

@CODE:CLEAN-ARCHITECTURE-DOCUMENT-MAPPER
"""

from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime

from ...domain.entities.document import Document, DocumentChunk
# Import from existing database module
from ...database import Document as DocumentModel, DocumentChunk as ChunkModel


class DocumentMapper:
    """
    Document Mapper

    Transforms between database models and domain entities.
    """

    @staticmethod
    def document_to_domain(model: DocumentModel) -> Document:
        """
        Transform Document ORM model to domain entity.

        Args:
            model: SQLAlchemy Document model

        Returns:
            Domain Document entity
        """
        return Document(
            doc_id=model.doc_id if isinstance(model.doc_id, UUID) else UUID(str(model.doc_id)),
            title=model.title,
            source_url=model.source_url,
            content_type=model.content_type,
            file_size=model.file_size,
            checksum=model.checksum,
            version_tag=model.version_tag,
            license_tag=model.license_tag,
            metadata=model.doc_metadata or {},
            chunk_metadata=model.chunk_metadata or {},
            created_at=model.created_at,
            processed_at=model.processed_at,
        )

    @staticmethod
    def chunk_to_domain(model: ChunkModel) -> DocumentChunk:
        """
        Transform Chunk ORM model to domain entity.

        Args:
            model: SQLAlchemy DocumentChunk model

        Returns:
            Domain DocumentChunk entity
        """
        # Parse span string to tuple
        span = (0, 0)
        if model.span:
            try:
                # Format: "start,end" or "[start,end)"
                span_str = model.span.strip("[]() ")
                parts = span_str.split(",")
                if len(parts) == 2:
                    span = (int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                span = (0, 0)

        return DocumentChunk(
            chunk_id=model.chunk_id if isinstance(model.chunk_id, UUID) else UUID(str(model.chunk_id)),
            doc_id=model.doc_id if isinstance(model.doc_id, UUID) else UUID(str(model.doc_id)),
            text=model.text,
            chunk_index=model.chunk_index,
            span=span,
            token_count=model.token_count,
            embedding=model.embedding,
            has_pii=model.has_pii,
            pii_types=model.pii_types or [],
            metadata=model.chunk_metadata or {},
            created_at=model.created_at,
        )

    @staticmethod
    def document_to_model_dict(entity: Document) -> dict[str, Any]:
        """
        Transform Document entity to model dictionary.

        Args:
            entity: Domain Document entity

        Returns:
            Dictionary for ORM model
        """
        return {
            "doc_id": entity.doc_id,
            "title": entity.title,
            "source_url": entity.source_url,
            "content_type": entity.content_type,
            "file_size": entity.file_size,
            "checksum": entity.checksum,
            "version_tag": entity.version_tag,
            "license_tag": entity.license_tag,
            "doc_metadata": entity.metadata,
            "chunk_metadata": entity.chunk_metadata,
            "created_at": entity.created_at,
            "processed_at": entity.processed_at,
        }

    @staticmethod
    def chunk_to_model_dict(entity: DocumentChunk) -> dict[str, Any]:
        """
        Transform Chunk entity to model dictionary.

        Args:
            entity: Domain DocumentChunk entity

        Returns:
            Dictionary for ORM model
        """
        return {
            "chunk_id": entity.chunk_id,
            "doc_id": entity.doc_id,
            "text": entity.text,
            "chunk_index": entity.chunk_index,
            "span": f"{entity.span[0]},{entity.span[1]}",
            "token_count": entity.token_count,
            "embedding": entity.embedding,
            "has_pii": entity.has_pii,
            "pii_types": entity.pii_types,
            "chunk_metadata": entity.metadata,
            "created_at": entity.created_at,
        }
