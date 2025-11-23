"""
Taxonomy Suggestion Engine

ML-powered suggestion generation for taxonomy evolution.
Detects overlaps, proposes merges/splits, and suggests new categories.

@CODE:TAXONOMY-EVOLUTION-001
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from ..models.evolution_models import (
    SuggestionType,
    EvolutionSuggestion,
)

logger = logging.getLogger(__name__)


class SuggestionEngine:
    """
    Engine for generating taxonomy evolution suggestions.

    Uses embedding similarity and usage patterns to identify:
    - Overlapping categories that could be merged
    - Large categories that should be split
    - Missing categories from zero-result queries
    """

    def __init__(
        self,
        embedding_service: Optional[Any] = None,
        metrics_service: Optional[Any] = None,
    ):
        """
        Initialize suggestion engine.

        Args:
            embedding_service: Service for embedding operations and similarity
            metrics_service: Service for usage metrics and zero-result patterns
        """
        self.embedding_service = embedding_service
        self.metrics_service = metrics_service

    # ========================================================================
    # Overlap Detection
    # ========================================================================

    async def detect_overlapping_categories(
        self,
        categories: List[Dict[str, Any]],
        threshold: float = 0.8,
    ) -> List[Dict[str, Any]]:
        """
        Detect categories with high semantic overlap.

        Uses embedding similarity to find category pairs that
        may represent the same concept and could be merged.

        Args:
            categories: List of category dicts with 'id', 'name', 'embedding', 'keywords'
            threshold: Minimum similarity score to consider as overlap

        Returns:
            List of overlap results with categories, similarity, and shared keywords
        """
        overlaps = []
        n = len(categories)

        for i in range(n):
            for j in range(i + 1, n):
                cat_a = categories[i]
                cat_b = categories[j]

                # Calculate similarity using embedding service
                similarity = self._calculate_category_similarity(cat_a, cat_b)

                if similarity >= threshold:
                    # Find shared keywords
                    keywords_a = set(cat_a.get("keywords", []))
                    keywords_b = set(cat_b.get("keywords", []))
                    shared = keywords_a & keywords_b

                    overlaps.append({
                        "categories": [cat_a["id"], cat_b["id"]],
                        "category_names": [cat_a["name"], cat_b["name"]],
                        "similarity": similarity,
                        "shared_keywords": list(shared),
                    })

        return overlaps

    def _calculate_category_similarity(
        self,
        cat_a: Dict[str, Any],
        cat_b: Dict[str, Any],
    ) -> float:
        """Calculate similarity between two categories."""
        if self.embedding_service is None:
            return 0.0

        emb_a = cat_a.get("embedding", [])
        emb_b = cat_b.get("embedding", [])

        if not emb_a or not emb_b:
            return 0.0

        return self.embedding_service.calculate_similarity(emb_a, emb_b)

    # ========================================================================
    # Merge Suggestions
    # ========================================================================

    async def generate_merge_suggestions(
        self,
        categories: List[Dict[str, Any]],
        overlap_threshold: float = 0.8,
    ) -> List[EvolutionSuggestion]:
        """
        Generate merge suggestions for overlapping categories.

        Args:
            categories: List of category dicts
            overlap_threshold: Minimum similarity for merge suggestion

        Returns:
            List of merge suggestions
        """
        overlaps = await self.detect_overlapping_categories(
            categories, threshold=overlap_threshold
        )

        suggestions = []
        for overlap in overlaps:
            # Get category details
            cat_ids = overlap["categories"]
            cat_names = overlap["category_names"]

            # Find categories by ID
            cat_a = next((c for c in categories if c["id"] == cat_ids[0]), None)
            cat_b = next((c for c in categories if c["id"] == cat_ids[1]), None)

            if not cat_a or not cat_b:
                continue

            # Calculate affected documents
            doc_count_a = cat_a.get("document_count", 0)
            doc_count_b = cat_b.get("document_count", 0)
            affected = doc_count_a + doc_count_b

            # Generate suggested name
            suggested_name = self._generate_merged_name(cat_a, cat_b)

            # Calculate impact score (normalized by total docs)
            total_docs = sum(c.get("document_count", 0) for c in categories)
            impact = affected / total_docs if total_docs > 0 else 0.0

            suggestion = EvolutionSuggestion(
                id=f"sug_{uuid.uuid4().hex[:12]}",
                suggestion_type=SuggestionType.MERGE,
                confidence=overlap["similarity"],
                impact_score=impact,
                affected_documents=affected,
                details={
                    "source_categories": cat_ids,
                    "source_names": cat_names,
                    "suggested_name": suggested_name,
                    "shared_keywords": overlap["shared_keywords"],
                    "similarity": overlap["similarity"],
                },
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            suggestions.append(suggestion)

        return suggestions

    def _generate_merged_name(
        self,
        cat_a: Dict[str, Any],
        cat_b: Dict[str, Any],
    ) -> str:
        """Generate a suggested name for merged category."""
        # Use the category with more documents as base
        if cat_a.get("document_count", 0) >= cat_b.get("document_count", 0):
            base = cat_a
            other = cat_b
        else:
            base = cat_b
            other = cat_a

        # Check for common keywords
        keywords_a = set(cat_a.get("keywords", []))
        keywords_b = set(cat_b.get("keywords", []))
        shared = keywords_a & keywords_b

        if shared:
            # Use most common shared keyword
            return " & ".join(sorted(shared)[:2]).title()

        # Fallback: combine names
        return f"{base['name']} & {other['name']}"

    # ========================================================================
    # Split Suggestions
    # ========================================================================

    async def generate_split_suggestions(
        self,
        categories: List[Dict[str, Any]],
        max_documents_threshold: int = 100,
    ) -> List[EvolutionSuggestion]:
        """
        Generate split suggestions for large categories.

        Categories with document count exceeding threshold are
        candidates for splitting into more specific subcategories.

        Args:
            categories: List of category dicts
            max_documents_threshold: Max documents before suggesting split

        Returns:
            List of split suggestions
        """
        suggestions = []

        for category in categories:
            doc_count = category.get("document_count", 0)

            if doc_count > max_documents_threshold:
                # Generate proposed splits based on keywords
                proposed_splits = self._propose_subcategories(category)

                # Calculate impact
                total_docs = sum(c.get("document_count", 0) for c in categories)
                impact = doc_count / total_docs if total_docs > 0 else 0.0

                # Confidence based on how much over threshold
                over_ratio = doc_count / max_documents_threshold
                confidence = min(0.95, 0.5 + (over_ratio - 1) * 0.15)

                suggestion = EvolutionSuggestion(
                    id=f"sug_{uuid.uuid4().hex[:12]}",
                    suggestion_type=SuggestionType.SPLIT,
                    confidence=confidence,
                    impact_score=impact,
                    affected_documents=doc_count,
                    details={
                        "source_category": category["id"],
                        "source_name": category["name"],
                        "document_count": doc_count,
                        "proposed_splits": proposed_splits,
                        "reason": f"Category has {doc_count} documents (threshold: {max_documents_threshold})",
                    },
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=30),
                )
                suggestions.append(suggestion)

        return suggestions

    def _propose_subcategories(
        self,
        category: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """
        Propose subcategories for a large category.

        Uses keywords to suggest potential splits.
        """
        keywords = category.get("keywords", [])
        name = category.get("name", "Unknown")

        if len(keywords) < 2:
            return [
                {"name": f"{name} - Part 1", "focus": "primary"},
                {"name": f"{name} - Part 2", "focus": "secondary"},
            ]

        # Create subcategories from top keywords
        splits = []
        for i, kw in enumerate(keywords[:3]):
            splits.append({
                "name": f"{name}: {kw.title()}",
                "focus": kw,
                "estimated_docs": category.get("document_count", 0) // (i + 2),
            })

        return splits

    # ========================================================================
    # New Category Suggestions
    # ========================================================================

    async def generate_new_category_suggestions(
        self,
        taxonomy_id: str,
        min_query_count: int = 10,
        min_days_observed: int = 5,
    ) -> List[EvolutionSuggestion]:
        """
        Generate new category suggestions from zero-result queries.

        Analyzes patterns of queries that return no results to
        identify potential missing categories.

        Args:
            taxonomy_id: ID of taxonomy to analyze
            min_query_count: Minimum times query appeared
            min_days_observed: Minimum days query has been observed

        Returns:
            List of new category suggestions
        """
        if self.metrics_service is None:
            return []

        # Get zero result patterns
        patterns = await self.metrics_service.get_zero_result_patterns(
            taxonomy_id, min_occurrences=min_query_count
        )

        suggestions = []
        grouped_queries = self._group_similar_zero_queries(patterns)

        for group in grouped_queries:
            if not group:
                continue

            # Check if meets criteria
            primary_query = group[0]
            query_text = getattr(primary_query, "query_text", str(primary_query))
            first_seen = getattr(primary_query, "first_seen", datetime.utcnow())
            occurrence_count = getattr(primary_query, "occurrence_count", 0)

            days_observed = (datetime.utcnow() - first_seen).days

            if occurrence_count < min_query_count:
                continue
            if days_observed < min_days_observed:
                continue

            # Generate suggested name from query
            suggested_name = self._generate_category_name_from_query(query_text)

            # Calculate confidence based on frequency and duration
            confidence = min(0.95, 0.5 + (occurrence_count / 100) + (days_observed / 30))

            total_occurrences = sum(
                getattr(q, "occurrence_count", 0) for q in group
            )

            suggestion = EvolutionSuggestion(
                id=f"sug_{uuid.uuid4().hex[:12]}",
                suggestion_type=SuggestionType.NEW_CATEGORY,
                confidence=confidence,
                impact_score=min(1.0, total_occurrences / 100),
                affected_documents=0,  # New category has no documents yet
                details={
                    "suggested_name": suggested_name,
                    "source_queries": [
                        getattr(q, "query_text", str(q)) for q in group
                    ],
                    "total_occurrences": total_occurrences,
                    "days_observed": days_observed,
                },
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            suggestions.append(suggestion)

        return suggestions

    def _group_similar_zero_queries(
        self,
        patterns: List[Any],
    ) -> List[List[Any]]:
        """Group similar zero-result queries together."""
        if not patterns:
            return []

        # Simple grouping by shared words
        groups = []
        used = set()

        for i, pattern in enumerate(patterns):
            if i in used:
                continue

            query_text = getattr(pattern, "query_text", str(pattern))
            words_i = set(query_text.lower().split())

            group = [pattern]
            used.add(i)

            for j, other in enumerate(patterns):
                if j in used:
                    continue

                other_text = getattr(other, "query_text", str(other))
                words_j = set(other_text.lower().split())

                # Check for significant word overlap
                overlap = len(words_i & words_j)
                if overlap >= 1 and overlap / max(len(words_i), len(words_j)) > 0.3:
                    group.append(other)
                    used.add(j)

            groups.append(group)

        return groups

    def _generate_category_name_from_query(self, query: str) -> str:
        """Generate a category name from a query string."""
        # Clean and capitalize
        words = query.strip().split()
        if not words:
            return "Unknown Category"

        # Title case and join
        return " ".join(w.capitalize() for w in words[:3])

    # ========================================================================
    # Ranking
    # ========================================================================

    def rank_suggestions(
        self,
        suggestions: List[EvolutionSuggestion],
        strategy: str = "combined",
    ) -> List[EvolutionSuggestion]:
        """
        Rank suggestions by priority.

        Args:
            suggestions: List of suggestions to rank
            strategy: Ranking strategy - 'impact', 'confidence', or 'combined'

        Returns:
            Sorted list of suggestions
        """
        if not suggestions:
            return []

        if strategy == "impact":
            return sorted(suggestions, key=lambda s: s.impact_score, reverse=True)
        elif strategy == "confidence":
            return sorted(suggestions, key=lambda s: s.confidence, reverse=True)
        else:  # combined
            return sorted(
                suggestions,
                key=lambda s: (s.confidence + s.impact_score) / 2,
                reverse=True,
            )

    # ========================================================================
    # Pipeline
    # ========================================================================

    async def generate_all_suggestions(
        self,
        taxonomy_id: str,
        categories: List[Dict[str, Any]],
        merge_threshold: float = 0.8,
        split_threshold: int = 100,
        min_query_count: int = 10,
    ) -> List[EvolutionSuggestion]:
        """
        Generate all types of suggestions for a taxonomy.

        Runs merge, split, and new category detection in parallel
        and returns a ranked combined list.

        Args:
            taxonomy_id: Taxonomy to analyze
            categories: Current categories
            merge_threshold: Similarity threshold for merge suggestions
            split_threshold: Document threshold for split suggestions
            min_query_count: Minimum queries for new category suggestions

        Returns:
            Ranked list of all suggestions
        """
        all_suggestions = []

        # Generate merge suggestions
        try:
            merge_suggestions = await self.generate_merge_suggestions(
                categories, overlap_threshold=merge_threshold
            )
            all_suggestions.extend(merge_suggestions)
        except Exception as e:
            logger.warning(f"Failed to generate merge suggestions: {e}")

        # Generate split suggestions
        try:
            split_suggestions = await self.generate_split_suggestions(
                categories, max_documents_threshold=split_threshold
            )
            all_suggestions.extend(split_suggestions)
        except Exception as e:
            logger.warning(f"Failed to generate split suggestions: {e}")

        # Generate new category suggestions
        try:
            new_cat_suggestions = await self.generate_new_category_suggestions(
                taxonomy_id, min_query_count=min_query_count
            )
            all_suggestions.extend(new_cat_suggestions)
        except Exception as e:
            logger.warning(f"Failed to generate new category suggestions: {e}")

        # Filter expired and rank
        valid = self.filter_expired(all_suggestions)
        return self.rank_suggestions(valid, strategy="combined")

    def filter_expired(
        self,
        suggestions: List[EvolutionSuggestion],
    ) -> List[EvolutionSuggestion]:
        """
        Filter out expired suggestions.

        Args:
            suggestions: List of suggestions to filter

        Returns:
            List of non-expired suggestions
        """
        now = datetime.utcnow()
        return [s for s in suggestions if s.expires_at > now]


# ============================================================================
# Singleton Instance
# ============================================================================

_suggestion_engine: Optional[SuggestionEngine] = None


def get_suggestion_engine(
    embedding_service: Optional[Any] = None,
    metrics_service: Optional[Any] = None,
) -> SuggestionEngine:
    """Get or create suggestion engine singleton."""
    global _suggestion_engine

    if _suggestion_engine is None:
        _suggestion_engine = SuggestionEngine(
            embedding_service=embedding_service,
            metrics_service=metrics_service,
        )

    return _suggestion_engine
