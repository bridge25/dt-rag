"""
Domain Entities - Pure Business Models

Entities are the core business objects with:
- Immutable data structures (using dataclasses with frozen=True)
- Business rules and validation
- NO framework dependencies

@CODE:CLEAN-ARCHITECTURE-ENTITIES
"""

from .agent import Agent, AgentStatus, AgentStats, AgentConfig
from .document import Document, DocumentChunk
from .taxonomy import TaxonomyNode, TaxonomyEdge
from .search import SearchResult, SearchMetadata

__all__ = [
    "Agent",
    "AgentStatus",
    "AgentStats",
    "AgentConfig",
    "Document",
    "DocumentChunk",
    "TaxonomyNode",
    "TaxonomyEdge",
    "SearchResult",
    "SearchMetadata",
]
