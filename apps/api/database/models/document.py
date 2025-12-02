"""
Document-related ORM models.

@CODE:DATABASE-PKG-003
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from ..connection import Base, get_json_type, get_array_type, get_uuid_type, get_vector_type

__all__ = ["Document", "DocumentChunk", "Embedding", "DocTaxonomy"]


class Document(Base):
    """Document model for storing document metadata."""
    __tablename__ = "documents"
    __table_args__ = {'extend_existing': True}

    doc_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    version_tag: Mapped[Optional[str]] = mapped_column(Text)
    license_tag: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    title: Mapped[Optional[str]] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(100), default="text/plain")
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    checksum: Mapped[Optional[str]] = mapped_column(String(64))
    doc_metadata: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), default=dict)
    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(
        get_json_type(), default=dict
    )
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DocumentChunk(Base):
    """Document chunk model for storing text chunks."""
    __tablename__ = "chunks"
    __table_args__ = {'extend_existing': True}

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    doc_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(),
        ForeignKey("documents.doc_id", ondelete="CASCADE"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    span: Mapped[str] = mapped_column(String(50), nullable=False, default="0,0")
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        get_array_type(Float), nullable=True
    )
    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(
        get_json_type(), default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    has_pii: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pii_types: Mapped[Optional[List[str]]] = mapped_column(
        get_array_type(String), default=list
    )


class Embedding(Base):
    """Embedding model for storing vector embeddings."""
    __tablename__ = "embeddings"
    __table_args__ = {'extend_existing': True}

    embedding_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(),
        ForeignKey("chunks.chunk_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    vec: Mapped[List[float]] = mapped_column(get_vector_type(1536), nullable=False)
    model_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default="text-embedding-ada-002"
    )
    bm25_tokens: Mapped[Optional[List[str]]] = mapped_column(get_array_type(String))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DocTaxonomy(Base):
    """Document-Taxonomy mapping model."""
    __tablename__ = "doc_taxonomy"
    __table_args__ = {'extend_existing': True}

    doc_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(),
        ForeignKey("documents.doc_id", ondelete="CASCADE"),
        primary_key=True,
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(),
        ForeignKey("taxonomy_nodes.node_id", ondelete="CASCADE"),
        primary_key=True,
    )
    version: Mapped[str] = mapped_column(Text, primary_key=True)

    path: Mapped[List[str]] = mapped_column(get_array_type(String), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    hitl_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
