"""
Agent-related ORM models.

@CODE:DATABASE-PKG-005
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from ..connection import Base, get_json_type, get_array_type, get_uuid_type, DATABASE_URL

__all__ = ["Agent", "BackgroundTask", "CoverageHistory"]


class Agent(Base):
    """Agent model for AI agent management."""
    __tablename__ = "agents"
    __table_args__ = {'extend_existing': True}

    agent_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    taxonomy_node_ids: Mapped[List[uuid.UUID]] = mapped_column(
        get_array_type(UUID(as_uuid=True) if "postgresql" in DATABASE_URL else String),
        nullable=False,
    )
    taxonomy_version: Mapped[str] = mapped_column(Text, nullable=False, default="1.0.0")
    scope_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coverage_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_coverage_update: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_xp: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_queries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_queries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_faithfulness: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_response_time_ms: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    retrieval_config: Mapped[Dict[str, Any]] = mapped_column(
        get_json_type(), default=dict
    )
    features_config: Mapped[Dict[str, Any]] = mapped_column(
        get_json_type(), default=dict
    )
    # Avatar System
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    rarity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    character_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_query_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Agent(id={self.agent_id}, name='{self.name}', level={self.level}, coverage={self.coverage_percent:.2f}%)>"


class BackgroundTask(Base):
    """Background task model for async task management."""
    __tablename__ = "background_tasks"
    __table_args__ = {'extend_existing': True}

    task_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(),
        ForeignKey("agents.agent_id", ondelete="CASCADE"),
        nullable=False,
    )
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        get_json_type(), nullable=True
    )
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    webhook_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    webhook_retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancellation_requested: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    queue_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    progress_percentage: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    estimated_completion_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    def __repr__(self) -> str:
        return f"<BackgroundTask(id={self.task_id}, agent_id={self.agent_id}, type='{self.task_type}', status='{self.status}')>"


class CoverageHistory(Base):
    """Coverage history model for time-series tracking."""
    __tablename__ = "coverage_history"
    __table_args__ = {'extend_existing': True}

    history_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(),
        ForeignKey("agents.agent_id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    overall_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    total_documents: Mapped[int] = mapped_column(Integer, nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")

    def __repr__(self) -> str:
        return f"<CoverageHistory(id={self.history_id}, agent_id={self.agent_id}, coverage={self.overall_coverage:.2f}%, timestamp={self.timestamp})>"
