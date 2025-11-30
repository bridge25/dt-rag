"""
Taxonomy-related ORM models.

@CODE:DATABASE-PKG-004
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Integer, Float, DateTime, Text, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from ..connection import Base, get_array_type, get_uuid_type, DATABASE_URL

__all__ = ["TaxonomyNode", "TaxonomyEdge", "TaxonomyMigration"]


class TaxonomyNode(Base):
    """Taxonomy node model for hierarchical classification."""
    __tablename__ = "taxonomy_nodes"
    __table_args__ = {'extend_existing': True}

    node_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), primary_key=True, default=uuid.uuid4
    )
    label: Mapped[Optional[str]] = mapped_column(Text)
    canonical_path: Mapped[Optional[List[str]]] = mapped_column(get_array_type(str))
    version: Mapped[Optional[str]] = mapped_column(Text)
    confidence: Mapped[Optional[float]] = mapped_column(Float)


class TaxonomyEdge(Base):
    """Taxonomy edge model for parent-child relationships."""
    __tablename__ = "taxonomy_edges"
    __table_args__ = {'extend_existing': True}

    parent: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), ForeignKey("taxonomy_nodes.node_id"), primary_key=True
    )
    child: Mapped[uuid.UUID] = mapped_column(
        get_uuid_type(), ForeignKey("taxonomy_nodes.node_id"), primary_key=True
    )
    version: Mapped[str] = mapped_column(Text, primary_key=True)


class TaxonomyMigration(Base):
    """Taxonomy migration model for version tracking."""
    __tablename__ = "taxonomy_migrations"
    __table_args__ = {'extend_existing': True}

    migration_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    from_version: Mapped[Optional[str]] = mapped_column(Text)
    to_version: Mapped[Optional[str]] = mapped_column(Text)
    from_path: Mapped[Optional[List[str]]] = mapped_column(get_array_type(str))
    to_path: Mapped[Optional[List[str]]] = mapped_column(get_array_type(str))
    rationale: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=text("now()")
    )
