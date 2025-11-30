"""
Domain Layer - Clean Architecture Core

The Domain Layer is the innermost layer containing:
- Entities: Pure business models with validation and business rules
- Repositories: Interface contracts for data access (no implementation details)
- Use Cases: Business logic orchestration

Key Principles:
- NO dependencies on external frameworks (FastAPI, SQLAlchemy, etc.)
- Pure Python with type hints
- Business rules are encapsulated in entities
- Use cases orchestrate business operations

@CODE:CLEAN-ARCHITECTURE-DOMAIN
"""

from .entities import (
    Agent,
    AgentStatus,
    AgentStats,
    AgentConfig,
    Document,
    DocumentChunk,
    TaxonomyNode,
    TaxonomyEdge,
    SearchResult,
    SearchMetadata,
)

from .repositories import (
    IAgentRepository,
    IDocumentRepository,
    ITaxonomyRepository,
    ISearchRepository,
)

__all__ = [
    # Entities
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
    # Repository Interfaces
    "IAgentRepository",
    "IDocumentRepository",
    "ITaxonomyRepository",
    "ISearchRepository",
]
