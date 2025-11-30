"""
Dependency Injection Container

Manages service instances and their dependencies following
Inversion of Control (IoC) and Dependency Injection patterns.

@CODE:CLEAN-ARCHITECTURE-DI-CONTAINER
"""

from typing import Optional, TypeVar, Type, Dict, Any
from functools import lru_cache
import logging

from sqlalchemy.ext.asyncio import AsyncSession

# Domain Repository Interfaces
from ..domain.repositories.agent_repository import IAgentRepository
from ..domain.repositories.document_repository import IDocumentRepository
from ..domain.repositories.taxonomy_repository import ITaxonomyRepository
from ..domain.repositories.search_repository import ISearchRepository

# Data Layer Repository Implementations
from ..data.repositories import (
    AgentRepositoryImpl,
    DocumentRepositoryImpl,
    TaxonomyRepositoryImpl,
    SearchRepositoryImpl,
)

# Application Services
from ..services import (
    AgentService,
    SearchService,
    DocumentService,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Container:
    """
    Dependency Injection Container

    Manages service lifecycles and dependency resolution.
    Uses factory pattern for scoped dependencies (per-request).

    Usage:
        container = Container()

        # Get singleton service
        settings = container.settings

        # Get scoped service (requires session)
        async with db_manager.async_session() as session:
            agent_service = container.get_agent_service(session)
            agents = await agent_service.get_agents()
    """

    _instance: Optional["Container"] = None
    _initialized: bool = False

    def __new__(cls) -> "Container":
        """Singleton pattern for container instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize container (only once due to singleton)."""
        if not self._initialized:
            self._settings = None
            self._singletons: Dict[str, Any] = {}
            Container._initialized = True
            logger.info("DI Container initialized")

    # Settings (Singleton)

    @property
    def settings(self):
        """Get application settings (singleton)."""
        if self._settings is None:
            from .config import get_settings
            self._settings = get_settings()
        return self._settings

    # Repository Factories (Scoped - per request)

    def get_agent_repository(self, session: AsyncSession) -> IAgentRepository:
        """
        Get agent repository instance.

        Args:
            session: Database session for this request

        Returns:
            IAgentRepository: Agent repository implementation
        """
        return AgentRepositoryImpl(session)

    def get_document_repository(self, session: AsyncSession) -> IDocumentRepository:
        """
        Get document repository instance.

        Args:
            session: Database session for this request

        Returns:
            IDocumentRepository: Document repository implementation
        """
        return DocumentRepositoryImpl(session)

    def get_taxonomy_repository(self, session: AsyncSession) -> ITaxonomyRepository:
        """
        Get taxonomy repository instance.

        Args:
            session: Database session for this request

        Returns:
            ITaxonomyRepository: Taxonomy repository implementation
        """
        return TaxonomyRepositoryImpl(session)

    def get_search_repository(self, session: AsyncSession) -> ISearchRepository:
        """
        Get search repository instance.

        Args:
            session: Database session for this request

        Returns:
            ISearchRepository: Search repository implementation
        """
        return SearchRepositoryImpl(session)

    # Service Factories (Scoped - per request)

    def get_agent_service(self, session: AsyncSession) -> AgentService:
        """
        Get agent service instance.

        Args:
            session: Database session for this request

        Returns:
            AgentService: Agent service with injected dependencies
        """
        agent_repo = self.get_agent_repository(session)
        search_repo = self.get_search_repository(session)
        return AgentService(agent_repo, search_repo)

    def get_search_service(self, session: AsyncSession) -> SearchService:
        """
        Get search service instance.

        Args:
            session: Database session for this request

        Returns:
            SearchService: Search service with injected dependencies
        """
        search_repo = self.get_search_repository(session)
        return SearchService(search_repo)

    def get_document_service(self, session: AsyncSession) -> DocumentService:
        """
        Get document service instance.

        Args:
            session: Database session for this request

        Returns:
            DocumentService: Document service with injected dependencies
        """
        document_repo = self.get_document_repository(session)
        search_repo = self.get_search_repository(session)
        return DocumentService(document_repo, search_repo)

    # Utility Methods

    def reset(self):
        """Reset container state (useful for testing)."""
        self._settings = None
        self._singletons.clear()
        logger.info("DI Container reset")


@lru_cache()
def get_container() -> Container:
    """
    Get the global container instance.

    Returns:
        Container: DI container singleton
    """
    return Container()


# FastAPI Dependency Injection Helpers

async def get_db_session():
    """
    FastAPI dependency for database session.

    Yields:
        AsyncSession: Database session for request scope
    """
    from ..database import db_manager

    async with db_manager.async_session() as session:
        yield session


async def get_agent_service(session: AsyncSession = None):
    """
    FastAPI dependency for agent service.

    Args:
        session: Injected database session

    Returns:
        AgentService: Agent service instance
    """
    from ..database import db_manager

    if session is None:
        async with db_manager.async_session() as session:
            yield get_container().get_agent_service(session)
    else:
        yield get_container().get_agent_service(session)


async def get_search_service(session: AsyncSession = None):
    """
    FastAPI dependency for search service.

    Args:
        session: Injected database session

    Returns:
        SearchService: Search service instance
    """
    from ..database import db_manager

    if session is None:
        async with db_manager.async_session() as session:
            yield get_container().get_search_service(session)
    else:
        yield get_container().get_search_service(session)


async def get_document_service(session: AsyncSession = None):
    """
    FastAPI dependency for document service.

    Args:
        session: Injected database session

    Returns:
        DocumentService: Document service instance
    """
    from ..database import db_manager

    if session is None:
        async with db_manager.async_session() as session:
            yield get_container().get_document_service(session)
    else:
        yield get_container().get_document_service(session)
