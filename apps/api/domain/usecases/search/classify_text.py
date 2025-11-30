"""
Classify Text Use Case

Business logic for classifying text into taxonomy categories.

@CODE:CLEAN-ARCHITECTURE-CLASSIFY-TEXT
"""

from dataclasses import dataclass
from typing import Optional, List

from ...repositories.search_repository import ISearchRepository


@dataclass
class ClassificationResult:
    """Result of ClassifyTextUseCase"""
    canonical_path: List[str]
    label: str
    confidence: float
    reasoning: List[str]
    node_id: Optional[str] = None
    version: Optional[str] = None


class ClassifyTextUseCase:
    """
    Classify Text Use Case

    Classifies text into taxonomy categories using
    semantic similarity.

    Business Logic:
    - Use embedding similarity to find best category
    - Consider hint paths if provided
    - Return confidence score
    """

    def __init__(self, search_repository: ISearchRepository):
        self._search_repository = search_repository

    async def execute(
        self,
        text: str,
        hint_paths: Optional[List[List[str]]] = None,
    ) -> ClassificationResult:
        """
        Execute the use case.

        Args:
            text: Text to classify
            hint_paths: Optional hint paths to guide classification

        Returns:
            ClassificationResult with category and confidence

        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Text to classify cannot be empty")

        result = await self._search_repository.classify_text(
            text=text.strip(),
            hint_paths=hint_paths,
        )

        return ClassificationResult(
            canonical_path=result.get("canonical", ["AI", "General"]),
            label=result.get("label", "General"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", []),
            node_id=str(result.get("node_id")) if result.get("node_id") else None,
            version=str(result.get("version")) if result.get("version") else None,
        )
