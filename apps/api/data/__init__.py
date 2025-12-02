"""
Data Layer - Infrastructure Implementation

The Data Layer implements the repository interfaces defined
in the Domain Layer. It handles:
- Database communication (SQLAlchemy models)
- External API calls (embedding services)
- Data transformation (mappers)
- Caching and optimization

Key Principles:
- Implements Domain repository interfaces
- Contains framework-specific code (SQLAlchemy, httpx)
- Transforms between ORM models and domain entities
- Handles data persistence and retrieval

@CODE:CLEAN-ARCHITECTURE-DATA
"""

from .repositories import (
    AgentRepositoryImpl,
    DocumentRepositoryImpl,
    TaxonomyRepositoryImpl,
    SearchRepositoryImpl,
)

from .mappers import (
    AgentMapper,
    DocumentMapper,
    TaxonomyMapper,
)

__all__ = [
    # Repository Implementations
    "AgentRepositoryImpl",
    "DocumentRepositoryImpl",
    "TaxonomyRepositoryImpl",
    "SearchRepositoryImpl",
    # Mappers
    "AgentMapper",
    "DocumentMapper",
    "TaxonomyMapper",
]
