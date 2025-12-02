"""
Q-Table ORM model for reinforcement learning persistence.

@CODE:DATABASE-PKG-007
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from ..connection import Base

__all__ = ["QTableEntry"]


class QTableEntry(Base):
    """
    Persistent Q-Table storage for reinforcement learning weight optimization.

    Previously Q-Table data was stored in-memory and lost on server restart.
    This model provides PostgreSQL-backed persistence with JSON storage for Q-values.

    Schema:
    - id: Auto-increment primary key
    - state_hash: 64-char hash uniquely identifying the state
    - q_values: JSON array of 6 floats (Q-values for each action)
    - updated_at: Last update timestamp
    - access_count: Number of times this entry was accessed
    """
    __tablename__ = "q_table_entries"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    q_values: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    access_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<QTableEntry(hash={self.state_hash[:16]}..., access_count={self.access_count})>"
