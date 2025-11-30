"""
Get Taxonomy Versions Use Case

Business logic for listing taxonomy versions.

@CODE:CLEAN-ARCHITECTURE-GET-TAXONOMY-VERSIONS
"""

from dataclasses import dataclass
from typing import List

from ...repositories.taxonomy_repository import ITaxonomyRepository, TaxonomyVersionInfo


@dataclass
class GetTaxonomyVersionsResult:
    """Result of GetTaxonomyVersionsUseCase"""
    versions: List[TaxonomyVersionInfo]
    total: int
    latest_version: str


class GetTaxonomyVersionsUseCase:
    """
    Get Taxonomy Versions Use Case

    Lists all available taxonomy versions.

    Business Logic:
    - List versions with pagination
    - Identify latest version
    - Include version metadata
    """

    def __init__(self, taxonomy_repository: ITaxonomyRepository):
        self._taxonomy_repository = taxonomy_repository

    async def execute(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> GetTaxonomyVersionsResult:
        """
        Execute the use case.

        Args:
            limit: Maximum versions to return
            offset: Pagination offset

        Returns:
            GetTaxonomyVersionsResult with versions list
        """
        versions = await self._taxonomy_repository.list_versions(limit, offset)
        latest = await self._taxonomy_repository.get_latest_version()

        return GetTaxonomyVersionsResult(
            versions=versions,
            total=len(versions),
            latest_version=latest or "1.0.0",
        )
