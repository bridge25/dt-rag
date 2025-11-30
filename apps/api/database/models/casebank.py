"""
CaseBank-related ORM models.

@CODE:DATABASE-PKG-006
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY

from ..connection import Base, get_json_type, get_array_type, get_uuid_type

__all__ = ["CaseBank", "CaseBankArchive", "ExecutionLog"]


class CaseBank(Base):
    """CaseBank model for storing Q&A cases."""
    __tablename__ = "case_bank"
    __table_args__ = {'extend_existing': True}

    case_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), nullable=False)
    category_path: Mapped[Optional[List[str]]] = mapped_column(
        get_array_type(String), nullable=True
    )
    quality: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("NOW()")
    )

    # Version management
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Lifecycle status
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    # Timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    # Performance metrics
    success_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Additional fields for consolidation & reflection
    query_vector: Mapped[Optional[List[float]]] = mapped_column(
        ARRAY(Float), nullable=True, comment="Query embedding vector for similarity search"
    )
    usage_count: Mapped[int] = mapped_column(
        Integer, nullable=False, insert_default=0, server_default=text("0"),
        comment="Number of times this case was matched"
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Last time this case was used in a query"
    )


class ExecutionLog(Base):
    """Execution log model for tracking case usage."""
    __tablename__ = "execution_log"
    __table_args__ = {'extend_existing': True}

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(
        Text, ForeignKey("case_bank.case_id"), nullable=False
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        get_json_type(), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    case = relationship("CaseBank", backref="execution_logs")


class CaseBankArchive(Base):
    """CaseBank archive model for storing archived cases."""
    __tablename__ = "case_bank_archive"
    __table_args__ = {'extend_existing': True}

    archive_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    case_id: Mapped[uuid.UUID] = mapped_column(get_uuid_type(), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Dict[str, Any]] = mapped_column(get_json_type(), nullable=False)
    category_path: Mapped[Optional[List[str]]] = mapped_column(
        get_array_type(String), nullable=True
    )
    quality: Mapped[Optional[float]] = mapped_column(Float)
    success_rate: Mapped[Optional[float]] = mapped_column(Float)
    archived_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    archived_reason: Mapped[Optional[str]] = mapped_column(String(255))
