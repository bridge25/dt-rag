"""
Real Classification Service using Semantic Similarity
Replaces mock classification with actual ML-based taxonomy classification
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime

from packages.common_schemas.common_schemas.models import (
    ClassifyRequest, ClassifyResponse, TaxonomyNode
)

logger = logging.getLogger(__name__)


class SemanticClassifier:
    """Semantic similarity-based document classifier"""

    def __init__(self, embedding_service, taxonomy_dao, confidence_threshold: float = 0.7):
        """
        Initialize semantic classifier

        Args:
            embedding_service: EmbeddingService instance for text embeddings
            taxonomy_dao: TaxonomyDAO for accessing taxonomy nodes
            confidence_threshold: Minimum confidence for automatic classification
        """
        self.embedding_service = embedding_service
        self.taxonomy_dao = taxonomy_dao
        self.confidence_threshold = confidence_threshold
        logger.info(f"SemanticClassifier initialized with threshold={confidence_threshold}")

    async def classify(
        self,
        text: str,
        confidence_threshold: Optional[float] = None,
        top_k: int = 5,
        correlation_id: Optional[str] = None
    ) -> ClassifyResponse:
        """
        Classify text using semantic similarity to taxonomy nodes

        Args:
            text: Text to classify
            confidence_threshold: Override default threshold
            top_k: Number of candidate classifications to return

        Returns:
            ClassifyResponse with canonical path, candidates, and HITL flag
        """
        threshold = confidence_threshold if confidence_threshold is not None else self.confidence_threshold

        text_embedding = await self.embedding_service.generate_embedding(text)

        taxonomy_nodes = await self.taxonomy_dao.get_all_leaf_nodes()

        if not taxonomy_nodes:
            logger.warning("No taxonomy nodes available for classification")
            return self._fallback_response(text)

        similarities = await self._compute_similarities(text_embedding, taxonomy_nodes)

        top_candidates = self._get_top_candidates(similarities, taxonomy_nodes, top_k)

        if not top_candidates:
            return self._fallback_response(text)

        best_match = top_candidates[0]
        best_confidence = best_match["confidence"]

        hitl_needed = best_confidence < threshold

        canonical_path = best_match["path"]

        candidates = [
            TaxonomyNode(
                node_id=cand["node_id"],
                label=cand["label"],
                canonical_path=cand["path"],
                version="1.8.1",
                confidence=cand["confidence"]
            )
            for cand in top_candidates
        ]

        reasoning = self._generate_reasoning(text, best_match, text_embedding, best_confidence)

        return ClassifyResponse(
            canonical=canonical_path,
            candidates=candidates,
            hitl=hitl_needed,
            confidence=best_confidence,
            reasoning=reasoning
        )

    async def _compute_similarities(
        self,
        text_embedding: List[float],
        taxonomy_nodes: List[Dict[str, Any]]
    ) -> List[float]:
        """Compute cosine similarity between text and taxonomy node embeddings"""
        text_vec = np.array(text_embedding)

        similarities = []
        for node in taxonomy_nodes:
            node_embedding = node.get("embedding")
            if node_embedding is None:
                similarities.append(0.0)
                continue

            node_vec = np.array(node_embedding)

            similarity = self._cosine_similarity(text_vec, node_vec)
            similarities.append(float(similarity))

        return similarities

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def _get_top_candidates(
        self,
        similarities: List[float],
        taxonomy_nodes: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Get top-k classification candidates sorted by similarity"""
        candidates = []
        for idx, similarity in enumerate(similarities):
            node = taxonomy_nodes[idx]
            candidates.append({
                "node_id": node["id"],
                "label": node["name"],
                "path": node["path"],
                "confidence": similarity
            })

        candidates.sort(key=lambda x: x["confidence"], reverse=True)
        return candidates[:top_k]

    def _generate_reasoning(
        self,
        text: str,
        best_match: Dict[str, Any],
        text_embedding: List[float],
        confidence: float
    ) -> List[str]:
        """Generate human-readable reasoning for classification"""
        reasoning = []

        reasoning.append(f"Semantic similarity score: {confidence:.2f}")

        reasoning.append(f"Best matching taxonomy: {' > '.join(best_match['path'])}")

        if confidence >= 0.85:
            reasoning.append("High confidence classification based on strong semantic match")
        elif confidence >= self.confidence_threshold:
            reasoning.append("Moderate confidence classification - automatic assignment")
        else:
            reasoning.append("Low confidence - human review recommended")

        text_keywords = set(text.lower().split())
        path_keywords = set(' '.join(best_match['path']).lower().split())
        common_keywords = text_keywords & path_keywords

        if common_keywords:
            reasoning.append(f"Keyword overlap detected: {', '.join(list(common_keywords)[:3])}")

        return reasoning

    def _fallback_response(self, text: str) -> ClassifyResponse:
        """Fallback response when classification fails"""
        logger.warning("Classification fallback triggered")

        return ClassifyResponse(
            canonical=["Uncategorized"],
            candidates=[
                TaxonomyNode(
                    node_id="uncategorized",
                    label="Uncategorized",
                    canonical_path=["Uncategorized"],
                    version="1.8.1",
                    confidence=0.5
                )
            ],
            hitl=True,
            confidence=0.5,
            reasoning=[
                "Classification failed - no taxonomy nodes available",
                "Manual categorization required"
            ]
        )


class TaxonomyDAO:
    """Data Access Object for taxonomy operations"""

    def __init__(self, db_session):
        """Initialize with database session"""
        self.db_session = db_session

    async def get_all_leaf_nodes(self) -> List[Dict[str, Any]]:
        """Get all leaf taxonomy nodes with embeddings"""
        from sqlalchemy import select, text
        from apps.api.database import Taxonomy

        query = select(Taxonomy).where(Taxonomy.is_active == True)
        result = await self.db_session.execute(query)
        nodes = result.scalars().all()

        leaf_nodes = []
        for node in nodes:
            if not node.children_ids or len(node.children_ids) == 0:
                leaf_nodes.append({
                    "id": node.id,
                    "name": node.name,
                    "path": node.path if node.path else [node.name],
                    "embedding": node.embedding if hasattr(node, 'embedding') else None
                })

        return leaf_nodes

    async def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get taxonomy node by ID"""
        from sqlalchemy import select
        from apps.api.database import Taxonomy

        query = select(Taxonomy).where(Taxonomy.id == node_id)
        result = await self.db_session.execute(query)
        node = result.scalar_one_or_none()

        if node is None:
            return None

        return {
            "id": node.id,
            "name": node.name,
            "path": node.path if node.path else [node.name],
            "embedding": node.embedding if hasattr(node, 'embedding') else None,
            "parent_id": node.parent_id,
            "children_ids": node.children_ids
        }
