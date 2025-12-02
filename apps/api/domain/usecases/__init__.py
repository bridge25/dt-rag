"""
Use Cases - Business Logic Orchestration

Use Cases encapsulate business logic and orchestrate
operations across repositories. They are the entry point
for all business operations.

Key Principles:
- Single Responsibility: Each use case does one thing
- Input/Output DTOs: Define clear boundaries
- Repository Injection: Dependencies provided via constructor
- Pure Business Logic: No framework dependencies

@CODE:CLEAN-ARCHITECTURE-USECASES
"""

from .agent import (
    GetAgentsUseCase,
    GetAgentByIdUseCase,
    CreateAgentUseCase,
    UpdateAgentUseCase,
    DeleteAgentUseCase,
    QueryAgentUseCase,
)

from .search import (
    HybridSearchUseCase,
    ClassifyTextUseCase,
)

from .taxonomy import (
    GetTaxonomyTreeUseCase,
    GetTaxonomyVersionsUseCase,
)

__all__ = [
    # Agent Use Cases
    "GetAgentsUseCase",
    "GetAgentByIdUseCase",
    "CreateAgentUseCase",
    "UpdateAgentUseCase",
    "DeleteAgentUseCase",
    "QueryAgentUseCase",
    # Search Use Cases
    "HybridSearchUseCase",
    "ClassifyTextUseCase",
    # Taxonomy Use Cases
    "GetTaxonomyTreeUseCase",
    "GetTaxonomyVersionsUseCase",
]
