"""
Repository Interfaces - Data Access Contracts

Repositories define the contract for data access without
specifying implementation details. This enables:
- Testability (mock implementations)
- Flexibility (swap database, API, etc.)
- Dependency Inversion Principle

@CODE:CLEAN-ARCHITECTURE-REPOSITORIES
"""

from .agent_repository import IAgentRepository, AgentFilterParams, CreateAgentParams
from .document_repository import IDocumentRepository, DocumentFilterParams
from .taxonomy_repository import ITaxonomyRepository
from .search_repository import ISearchRepository, SearchParams

__all__ = [
    "IAgentRepository",
    "AgentFilterParams",
    "CreateAgentParams",
    "IDocumentRepository",
    "DocumentFilterParams",
    "ITaxonomyRepository",
    "ISearchRepository",
    "SearchParams",
]
