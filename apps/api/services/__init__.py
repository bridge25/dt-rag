"""
API Services Package

Application Services Layer - Clean Architecture

Application services orchestrate use cases and handle cross-cutting concerns.
They serve as the primary entry point for the presentation layer (routers).

Core Services (Clean Architecture):
- AgentService: Agent CRUD, querying, metrics
- SearchService: Hybrid search, classification, embeddings
- TaxonomyService: Taxonomy versioning, tree management
- DocumentService: Document and chunk management

Legacy Services:
- langgraph_service: LangGraph pipeline integration
- ml_classifier: ML-based text classification
- avatar_service: Pokemon avatar system
- leveling_service: Agent leveling and XP system

@CODE:CLEAN-ARCHITECTURE-SERVICES-LAYER
"""

# Clean Architecture Services
from .agent_service import AgentService
from .search_service import SearchService
from .document_service import DocumentService

# Legacy Services (to be migrated)
from .taxonomy_service import TaxonomyService
from .langgraph_service import LangGraphService
from .avatar_service import AvatarService
from .leveling_service import LevelingService

__all__ = [
    # Clean Architecture Services
    "AgentService",
    "SearchService",
    "DocumentService",
    # Legacy Services
    "TaxonomyService",
    "LangGraphService",
    "AvatarService",
    "LevelingService",
]
