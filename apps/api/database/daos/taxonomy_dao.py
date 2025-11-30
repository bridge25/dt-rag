"""
Taxonomy Data Access Object.

@CODE:DATABASE-PKG-014
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..connection import async_session

logger = logging.getLogger(__name__)

__all__ = ["TaxonomyDAO"]


class TaxonomyDAO:
    """Taxonomy data access."""

    @staticmethod
    async def get_tree(version: str) -> List[Dict[str, Any]]:
        """Get taxonomy tree from database."""
        async with async_session() as session:
            try:
                # Real query - SQLAlchemy 2.0 style
                query = text(
                    """
                    SELECT node_id, label, canonical_path, version
                    FROM taxonomy_nodes
                    WHERE version = :version
                    ORDER BY canonical_path
                """
                )
                result = await session.execute(query, {"version": version})
                rows = result.fetchall()

                if not rows:
                    # Insert default data
                    await TaxonomyDAO._insert_default_taxonomy(session, version)
                    result = await session.execute(query, {"version": version})
                    rows = result.fetchall()

                # Convert to tree structure
                tree = []
                for row in rows:
                    node = {
                        "label": row[1],  # label column
                        "version": row[3],
                        "node_id": str(row[0]),
                        "canonical_path": row[2],
                        "children": [],
                    }
                    tree.append(node)

                return tree

            except Exception as e:
                logger.error(f"Taxonomy query failed: {e}")
                # Fallback data
                return await TaxonomyDAO._get_fallback_tree(version)

    @staticmethod
    async def _insert_default_taxonomy(session: AsyncSession, version: str) -> None:
        """Insert default taxonomy data."""
        default_nodes = [
            ("AI", ["AI"], version),
            ("RAG", ["AI", "RAG"], version),
            ("ML", ["AI", "ML"], version),
            ("Taxonomy", ["AI", "Taxonomy"], version),
            ("General", ["AI", "General"], version),
        ]

        for label, path, ver in default_nodes:
            insert_query = text(
                """
                INSERT INTO taxonomy_nodes (label, canonical_path, version)
                VALUES (:label, :canonical_path, :version)
                ON CONFLICT DO NOTHING
            """
            )
            await session.execute(
                insert_query, {"label": label, "canonical_path": path, "version": ver}
            )

        await session.commit()

    @staticmethod
    async def _get_fallback_tree(version: str) -> List[Dict[str, Any]]:
        """Fallback tree (when DB connection fails)."""
        return [
            {
                "label": "AI",
                "version": version,
                "node_id": "ai_root_001",
                "canonical_path": ["AI"],
                "children": [
                    {
                        "label": "RAG",
                        "version": version,
                        "node_id": "ai_rag_001",
                        "canonical_path": ["AI", "RAG"],
                        "children": [],
                    },
                    {
                        "label": "ML",
                        "version": version,
                        "node_id": "ai_ml_001",
                        "canonical_path": ["AI", "ML"],
                        "children": [],
                    },
                ],
            }
        ]
