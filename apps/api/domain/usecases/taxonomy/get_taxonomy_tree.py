"""
Get Taxonomy Tree Use Case

Business logic for retrieving taxonomy tree.

@CODE:CLEAN-ARCHITECTURE-GET-TAXONOMY-TREE
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

from ...entities.taxonomy import TaxonomyTree, validate_taxonomy_structure
from ...repositories.taxonomy_repository import ITaxonomyRepository


class TaxonomyVersionNotFoundError(Exception):
    """Raised when taxonomy version is not found"""
    def __init__(self, version: str):
        self.version = version
        super().__init__(f"Taxonomy version not found: {version}")


@dataclass
class TaxonomyTreeResult:
    """Result of GetTaxonomyTreeUseCase"""
    tree: TaxonomyTree
    statistics: Dict[str, Any]
    validation: Dict[str, Any]
    retrieved_at: datetime


class GetTaxonomyTreeUseCase:
    """
    Get Taxonomy Tree Use Case

    Retrieves taxonomy tree with statistics and validation.

    Business Logic:
    - Fetch complete tree for version
    - Calculate tree statistics
    - Validate tree structure
    """

    def __init__(self, taxonomy_repository: ITaxonomyRepository):
        self._taxonomy_repository = taxonomy_repository

    async def execute(
        self,
        version: str,
        include_validation: bool = True,
    ) -> TaxonomyTreeResult:
        """
        Execute the use case.

        Args:
            version: Taxonomy version to retrieve
            include_validation: Whether to validate structure

        Returns:
            TaxonomyTreeResult with tree and metadata

        Raises:
            TaxonomyVersionNotFoundError: If version doesn't exist
        """
        # Get tree
        tree = await self._taxonomy_repository.get_tree(version)

        if not tree.nodes:
            raise TaxonomyVersionNotFoundError(version)

        # Get statistics
        statistics = await self._taxonomy_repository.get_statistics(version)

        # Validate if requested
        validation: Dict[str, Any] = {"is_valid": True, "errors": [], "warnings": []}
        if include_validation:
            validation_errors = validate_taxonomy_structure(tree)
            validation = {
                "is_valid": len(validation_errors) == 0,
                "errors": validation_errors,
                "warnings": [],
            }

        return TaxonomyTreeResult(
            tree=tree,
            statistics=statistics,
            validation=validation,
            retrieved_at=datetime.utcnow(),
        )
