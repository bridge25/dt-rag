"""
Taxonomy Evolution Service

ML-powered automatic taxonomy generation using document clustering,
keyword extraction, and semantic analysis.

@CODE:TAXONOMY-EVOLUTION-001
"""

import asyncio
import logging
import re
import time
from collections import Counter
from datetime import datetime
from typing import List, Dict, Any, Optional, TYPE_CHECKING

import numpy as np

try:
    from sklearn.cluster import KMeans, AgglomerativeClustering
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False

from ..models.evolution_models import (
    GeneratorConfig,
    GenerationAlgorithm,
    Granularity,
    ProposalStatus,
    SuggestionType,
    ProposedCategory,
    TaxonomyProposal,
    EvolutionSuggestion,
    ClusteringResult,
)

if TYPE_CHECKING:
    from ..embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


# Common stop words for keyword extraction
STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
    "from", "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "and", "but", "if", "or",
    "because", "until", "while", "this", "that", "these", "those", "it",
    "its", "their", "them", "they", "we", "us", "our", "you", "your",
    "he", "she", "him", "her", "his", "about", "also", "using", "based",
}


class TaxonomyEvolutionService:
    """
    Service for generating and evolving taxonomies using ML techniques.

    Uses document embeddings and clustering to automatically discover
    category structures from document content.
    """

    def __init__(self, embedding_service: "EmbeddingService"):
        """
        Initialize the evolution service.

        Args:
            embedding_service: Service for generating document embeddings
        """
        self.embedding_service = embedding_service
        self._tfidf_vectorizer = None

    async def generate_taxonomy(
        self,
        documents: List[Dict[str, Any]],
        config: GeneratorConfig,
    ) -> TaxonomyProposal:
        """
        Generate a taxonomy proposal from a set of documents.

        Args:
            documents: List of documents with 'doc_id', 'content', and 'title'
            config: Generator configuration

        Returns:
            TaxonomyProposal with generated categories
        """
        start_time = time.time()
        proposal_id = f"prop_{int(time.time())}_{np.random.randint(10000):04d}"

        # Validate input
        if not documents:
            return TaxonomyProposal(
                proposal_id=proposal_id,
                status=ProposalStatus.FAILED,
                categories=[],
                config=config,
                total_documents=0,
                processing_time_seconds=time.time() - start_time,
                created_at=datetime.utcnow(),
                error_message="No documents provided for taxonomy generation",
            )

        logger.info(f"Starting taxonomy generation for {len(documents)} documents")

        try:
            # Step 1: Generate embeddings
            texts = [self._get_document_text(doc) for doc in documents]
            embeddings = await self.embedding_service.batch_generate_embeddings(texts)

            if not embeddings or len(embeddings) != len(documents):
                raise ValueError("Failed to generate embeddings for all documents")

            # Step 2: Determine optimal number of clusters
            n_clusters = config.n_clusters
            if n_clusters is None:
                n_clusters = self._estimate_cluster_count(
                    len(documents),
                    config.granularity,
                )

            # Ensure we don't have more clusters than documents
            n_clusters = min(n_clusters, len(documents))

            # Step 3: Cluster documents
            clusters = self._cluster_documents(
                embeddings=embeddings,
                algorithm=config.algorithm,
                n_clusters=n_clusters,
                min_cluster_size=config.min_cluster_size,
            )

            if not clusters:
                raise ValueError("Clustering produced no valid clusters")

            # Step 4: Generate categories from clusters
            categories = []
            for cluster in clusters:
                # Get documents in this cluster
                cluster_docs = [documents[int(doc_id)] for doc_id in cluster.document_ids]

                # Skip if below minimum size
                if len(cluster_docs) < config.min_documents_per_category:
                    continue

                # Extract keywords
                keywords = self._extract_keywords(cluster_docs, max_keywords=10)

                # Generate label
                label = self._generate_label(keywords)

                # Create category
                category = ProposedCategory(
                    id=f"cat_{cluster.cluster_id}_{np.random.randint(10000):04d}",
                    name=label,
                    description=f"Category covering {len(cluster_docs)} documents related to {', '.join(keywords[:3])}",
                    parent_id=None,
                    confidence_score=cluster.confidence,
                    document_count=len(cluster_docs),
                    sample_document_ids=[doc["doc_id"] for doc in cluster_docs[:5]],
                    keywords=keywords,
                    centroid_embedding=cluster.centroid,
                )
                categories.append(category)

            processing_time = time.time() - start_time

            return TaxonomyProposal(
                proposal_id=proposal_id,
                status=ProposalStatus.COMPLETED,
                categories=categories,
                config=config,
                total_documents=len(documents),
                processing_time_seconds=processing_time,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                metadata={
                    "algorithm": config.algorithm.value,
                    "n_clusters_requested": config.n_clusters,
                    "n_clusters_actual": len(categories),
                },
            )

        except Exception as e:
            logger.error(f"Taxonomy generation failed: {e}")
            return TaxonomyProposal(
                proposal_id=proposal_id,
                status=ProposalStatus.FAILED,
                categories=[],
                config=config,
                total_documents=len(documents),
                processing_time_seconds=time.time() - start_time,
                created_at=datetime.utcnow(),
                error_message=str(e),
            )

    def _get_document_text(self, doc: Dict[str, Any]) -> str:
        """Extract text content from document"""
        title = doc.get("title", "")
        content = doc.get("content", "")
        return f"{title} {content}".strip()

    def _estimate_cluster_count(
        self,
        doc_count: int,
        granularity: Granularity,
    ) -> int:
        """
        Estimate optimal number of clusters based on document count and granularity.

        Args:
            doc_count: Number of documents
            granularity: Desired taxonomy granularity

        Returns:
            Estimated number of clusters
        """
        # Base ratio of clusters to documents
        ratios = {
            Granularity.COARSE: 0.05,  # ~5% of docs
            Granularity.MEDIUM: 0.1,   # ~10% of docs
            Granularity.FINE: 0.2,     # ~20% of docs
        }

        ratio = ratios.get(granularity, 0.1)
        estimated = int(doc_count * ratio)

        # Clamp to reasonable range
        return max(3, min(estimated, 50))

    def _cluster_documents(
        self,
        embeddings: List[List[float]],
        algorithm: GenerationAlgorithm,
        n_clusters: int = 5,
        min_cluster_size: int = 5,
    ) -> List[ClusteringResult]:
        """
        Cluster documents based on their embeddings.

        Args:
            embeddings: Document embeddings
            algorithm: Clustering algorithm to use
            n_clusters: Number of clusters for KMeans
            min_cluster_size: Minimum cluster size for HDBSCAN

        Returns:
            List of ClusteringResult objects
        """
        if not embeddings:
            return []

        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn not available for clustering")
            return []

        try:
            X = np.array(embeddings)

            if algorithm == GenerationAlgorithm.KMEANS:
                # Adjust n_clusters if we have fewer samples
                actual_clusters = min(n_clusters, len(X))
                if actual_clusters < 2:
                    actual_clusters = 1

                model = KMeans(
                    n_clusters=actual_clusters,
                    random_state=42,
                    n_init=10,
                )
                labels = model.fit_predict(X)
                centroids = model.cluster_centers_

            elif algorithm == GenerationAlgorithm.HIERARCHICAL:
                actual_clusters = min(n_clusters, len(X))
                model = AgglomerativeClustering(n_clusters=actual_clusters)
                labels = model.fit_predict(X)
                # Calculate centroids manually
                centroids = []
                for i in range(actual_clusters):
                    mask = labels == i
                    if mask.any():
                        centroids.append(X[mask].mean(axis=0))
                centroids = np.array(centroids)

            elif algorithm == GenerationAlgorithm.HDBSCAN and HDBSCAN_AVAILABLE:
                model = hdbscan.HDBSCAN(
                    min_cluster_size=min_cluster_size,
                    min_samples=2,
                )
                labels = model.fit_predict(X)
                # Calculate centroids for each cluster
                unique_labels = set(labels) - {-1}  # Exclude noise
                centroids = []
                for label in unique_labels:
                    mask = labels == label
                    centroids.append(X[mask].mean(axis=0))
                centroids = np.array(centroids) if centroids else np.array([])

            else:
                # Default to KMeans
                actual_clusters = min(n_clusters, len(X))
                model = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
                labels = model.fit_predict(X)
                centroids = model.cluster_centers_

            # Build clustering results
            results = []
            unique_labels = sorted(set(labels))

            for i, cluster_id in enumerate(unique_labels):
                if cluster_id == -1:  # Skip noise cluster from HDBSCAN
                    continue

                mask = labels == cluster_id
                doc_indices = np.where(mask)[0]

                # Calculate confidence based on cluster cohesion
                if len(centroids) > i:
                    centroid = centroids[i].tolist()
                    # Calculate average distance to centroid
                    distances = np.linalg.norm(X[mask] - centroids[i], axis=1)
                    avg_distance = np.mean(distances) if len(distances) > 0 else 1.0
                    confidence = max(0.0, min(1.0, 1.0 - avg_distance / 2.0))
                else:
                    centroid = X[mask].mean(axis=0).tolist() if mask.any() else []
                    confidence = 0.5

                results.append(ClusteringResult(
                    cluster_id=int(cluster_id),
                    document_ids=[str(idx) for idx in doc_indices],
                    centroid=centroid,
                    keywords=[],  # Will be filled later
                    label=f"Cluster {cluster_id}",
                    confidence=confidence,
                    size=int(mask.sum()),
                ))

            return results

        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return []

    def _extract_keywords(
        self,
        documents: List[Dict[str, Any]],
        max_keywords: int = 10,
    ) -> List[str]:
        """
        Extract keywords from a set of documents using TF-IDF.

        Args:
            documents: List of documents
            max_keywords: Maximum number of keywords to return

        Returns:
            List of keywords sorted by importance
        """
        if not documents:
            return []

        try:
            # Combine all document text
            texts = [self._get_document_text(doc) for doc in documents]

            if not any(texts):
                return []

            # Use TF-IDF to find important terms
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words="english",
                ngram_range=(1, 2),
            )

            tfidf_matrix = vectorizer.fit_transform(texts)

            # Get feature names and their importance
            feature_names = vectorizer.get_feature_names_out()

            # Sum TF-IDF scores across all documents
            scores = np.array(tfidf_matrix.sum(axis=0)).flatten()

            # Sort by score
            top_indices = scores.argsort()[::-1]

            # Filter and clean keywords
            keywords = []
            for idx in top_indices:
                if len(keywords) >= max_keywords:
                    break

                keyword = feature_names[idx]

                # Skip single-char or very short words
                if len(keyword) < 3:
                    continue

                # Skip if contains only stop words
                words = keyword.lower().split()
                if all(w in STOP_WORDS for w in words):
                    continue

                keywords.append(keyword)

            return keywords

        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}")

            # Fallback: simple word frequency
            word_counts: Counter[str] = Counter()
            for doc in documents:
                text = self._get_document_text(doc).lower()
                words = re.findall(r"\b[a-z]{3,}\b", text)
                word_counts.update(w for w in words if w not in STOP_WORDS)

            return [word for word, _ in word_counts.most_common(max_keywords)]

    def _generate_label(self, keywords: List[str]) -> str:
        """
        Generate a human-readable category label from keywords.

        Args:
            keywords: List of keywords

        Returns:
            Generated label string
        """
        if not keywords:
            return "Unnamed Category"

        # Take top 2-3 most important keywords
        top_keywords = keywords[:3]

        # Capitalize and join
        label_parts = [kw.title() for kw in top_keywords]

        # Create label
        if len(label_parts) == 1:
            return label_parts[0]
        elif len(label_parts) == 2:
            return f"{label_parts[0]} & {label_parts[1]}"
        else:
            return f"{label_parts[0]}, {label_parts[1]} & {label_parts[2]}"

    async def detect_merge_opportunities(
        self,
        categories: List[Dict[str, Any]],
        threshold: float = 0.8,
    ) -> List[EvolutionSuggestion]:
        """
        Detect categories that could be merged due to high similarity.

        Args:
            categories: List of category data with embeddings
            threshold: Similarity threshold for merge suggestion

        Returns:
            List of merge suggestions
        """
        suggestions = []

        for i, cat1 in enumerate(categories):
            for j, cat2 in enumerate(categories[i + 1:], start=i + 1):
                # Calculate similarity
                if "embedding" in cat1 and "embedding" in cat2:
                    similarity = self.embedding_service.calculate_similarity(
                        cat1["embedding"],
                        cat2["embedding"],
                    )

                    if similarity >= threshold:
                        suggestion = self._create_merge_suggestion(
                            category_ids=[cat1["id"], cat2["id"]],
                            overlap_score=similarity,
                            shared_keywords=self._find_shared_keywords(
                                cat1.get("keywords", []),
                                cat2.get("keywords", []),
                            ),
                            affected_docs=cat1.get("doc_count", 0) + cat2.get("doc_count", 0),
                        )
                        suggestions.append(suggestion)

        return suggestions

    def _find_shared_keywords(
        self,
        keywords1: List[str],
        keywords2: List[str],
    ) -> List[str]:
        """Find keywords shared between two lists"""
        set1 = {k.lower() for k in keywords1}
        set2 = {k.lower() for k in keywords2}
        return list(set1 & set2)

    def _create_merge_suggestion(
        self,
        category_ids: List[str],
        overlap_score: float,
        shared_keywords: List[str],
        affected_docs: int,
    ) -> EvolutionSuggestion:
        """Create a merge suggestion"""
        now = datetime.utcnow()

        # Calculate confidence based on overlap
        confidence = min(1.0, overlap_score + 0.1)

        # Calculate impact score
        impact_score = min(1.0, affected_docs / 100)

        return EvolutionSuggestion(
            id=f"sug_merge_{int(time.time())}",
            suggestion_type=SuggestionType.MERGE,
            confidence=confidence,
            impact_score=impact_score,
            affected_documents=affected_docs,
            details={
                "source_categories": category_ids,
                "overlap_score": overlap_score,
                "shared_keywords": shared_keywords,
                "suggested_name": " & ".join([f"Category {cid}" for cid in category_ids]),
            },
            created_at=now,
            expires_at=now,  # Will be set in __post_init__
        )


# Create a global instance (will be initialized with embedding service on startup)
_evolution_service: Optional[TaxonomyEvolutionService] = None


def get_evolution_service(embedding_service: "EmbeddingService") -> TaxonomyEvolutionService:
    """Get or create the evolution service instance"""
    global _evolution_service
    if _evolution_service is None:
        _evolution_service = TaxonomyEvolutionService(embedding_service)
    return _evolution_service
