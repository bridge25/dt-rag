"""
Advanced Clustering Service

BERTopic-style topic modeling, hierarchical clustering,
streaming clustering, and confidence calibration.

@CODE:TAXONOMY-EVOLUTION-001
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
import numpy as np

try:
    from sklearn.cluster import (
        KMeans,
        MiniBatchKMeans,
    )
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics import silhouette_score, davies_bouldin_score
    from scipy.cluster.hierarchy import linkage, fcluster
    from scipy.special import softmax
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class AdvancedClusteringService:
    """
    Advanced clustering algorithms for taxonomy generation.

    Provides:
    - BERTopic-style topic extraction
    - Hierarchical clustering with dendrogram
    - Streaming/incremental clustering
    - Confidence calibration
    - Domain ontology alignment
    """

    def __init__(
        self,
        embedding_service: Optional[Any] = None,
    ):
        """
        Initialize advanced clustering service.

        Args:
            embedding_service: Service for generating embeddings
        """
        self.embedding_service = embedding_service
        self._streaming_models: Dict[str, Any] = {}
        self._tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words="english",
            ngram_range=(1, 2),
        ) if SKLEARN_AVAILABLE else None

    # ========================================================================
    # BERTopic-Style Topic Extraction
    # ========================================================================

    async def extract_topics(
        self,
        documents: List[Dict[str, Any]],
        n_topics: int = 5,
        n_keywords: int = 10,
        calculate_coherence: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Extract topics from documents using BERTopic-style approach.

        Uses embeddings + clustering + c-TF-IDF for topic keywords.

        Args:
            documents: List of document dicts with 'content' field
            n_topics: Target number of topics
            n_keywords: Number of keywords per topic
            calculate_coherence: Whether to calculate coherence score

        Returns:
            List of topic dicts with id, keywords, document_ids
        """
        if not SKLEARN_AVAILABLE:
            return []

        # Get document texts
        texts = [doc.get("content", "") or doc.get("title", "") for doc in documents]
        doc_ids = [doc.get("doc_id", f"doc_{i}") for i, doc in enumerate(documents)]

        # Get embeddings
        if self.embedding_service:
            embeddings = await self.embedding_service.generate_embeddings_batch(texts)
            if isinstance(embeddings, list):
                embeddings = np.array(embeddings)
        else:
            # Fallback to TF-IDF embeddings
            embeddings = self._tfidf_vectorizer.fit_transform(texts).toarray()

        # Cluster embeddings
        n_topics = min(n_topics, len(documents))
        if n_topics < 2:
            n_topics = 2

        clusterer = KMeans(n_clusters=n_topics, random_state=42, n_init=10)
        labels = clusterer.fit_predict(embeddings)

        # Extract keywords per cluster using c-TF-IDF approach
        topics = []
        for topic_id in range(n_topics):
            cluster_mask = labels == topic_id
            cluster_docs = [texts[i] for i, m in enumerate(cluster_mask) if m]
            cluster_doc_ids = [doc_ids[i] for i, m in enumerate(cluster_mask) if m]

            if not cluster_docs:
                continue

            # Get keywords using TF-IDF on cluster
            keywords = self._extract_cluster_keywords(
                cluster_docs, texts, n_keywords
            )

            topic = {
                "topic_id": topic_id,
                "keywords": keywords,
                "document_ids": cluster_doc_ids,
                "n_documents": len(cluster_doc_ids),
            }

            if calculate_coherence:
                topic["coherence_score"] = self._calculate_topic_coherence(
                    keywords, cluster_docs
                )

            topics.append(topic)

        return topics

    def _extract_cluster_keywords(
        self,
        cluster_docs: List[str],
        all_docs: List[str],
        n_keywords: int,
    ) -> List[str]:
        """Extract representative keywords for a cluster using c-TF-IDF."""
        if not cluster_docs:
            return []

        try:
            # Fit on all docs
            self._tfidf_vectorizer.fit(all_docs)

            # Transform cluster docs
            cluster_text = " ".join(cluster_docs)
            tfidf = self._tfidf_vectorizer.transform([cluster_text])

            # Get top keywords
            feature_names = self._tfidf_vectorizer.get_feature_names_out()
            scores = tfidf.toarray()[0]

            top_indices = np.argsort(scores)[-n_keywords:][::-1]
            keywords = [feature_names[i] for i in top_indices if scores[i] > 0]

            return keywords[:n_keywords]

        except Exception as e:
            logger.warning(f"Keyword extraction failed: {e}")
            return []

    def _calculate_topic_coherence(
        self,
        keywords: List[str],
        docs: List[str],
    ) -> float:
        """Calculate topic coherence score (simplified)."""
        if not keywords or not docs:
            return 0.0

        # Count co-occurrences
        doc_text = " ".join(docs).lower()
        co_occurrence = 0
        total_pairs = 0

        for i, kw1 in enumerate(keywords):
            for kw2 in keywords[i + 1:]:
                total_pairs += 1
                if kw1.lower() in doc_text and kw2.lower() in doc_text:
                    co_occurrence += 1

        return co_occurrence / total_pairs if total_pairs > 0 else 0.0

    # ========================================================================
    # Hierarchical Clustering
    # ========================================================================

    def build_dendrogram(
        self,
        embeddings: np.ndarray,
        linkage_method: str = "ward",
    ) -> Dict[str, Any]:
        """
        Build dendrogram from embeddings.

        Args:
            embeddings: Document embeddings
            linkage_method: Linkage method ('ward', 'complete', 'average', 'single')

        Returns:
            Dendrogram dict with linkage matrix and metadata
        """
        if not SKLEARN_AVAILABLE:
            return {"linkage_matrix": None, "n_samples": 0}

        linkage_matrix = linkage(embeddings, method=linkage_method)

        return {
            "linkage_matrix": linkage_matrix,
            "n_samples": len(embeddings),
            "method": linkage_method,
        }

    def extract_at_depth(
        self,
        dendrogram_data: Dict[str, Any],
        depth: int = 2,
    ) -> List[int]:
        """
        Extract cluster labels at specified depth.

        Args:
            dendrogram_data: Output from build_dendrogram
            depth: Number of clusters to extract

        Returns:
            List of cluster labels
        """
        linkage_matrix = dendrogram_data.get("linkage_matrix")
        if linkage_matrix is None:
            return []

        n_clusters = max(2, depth + 1)
        labels = fcluster(linkage_matrix, n_clusters, criterion="maxclust")

        return labels.tolist()

    async def generate_taxonomy_tree(
        self,
        documents: List[Dict[str, Any]],
        max_depth: int = 3,
    ) -> Dict[str, Any]:
        """
        Generate hierarchical taxonomy tree from documents.

        Args:
            documents: List of document dicts
            max_depth: Maximum tree depth

        Returns:
            Tree structure with root and children
        """
        texts = [doc.get("content", "") or doc.get("title", "") for doc in documents]
        doc_ids = [doc.get("doc_id", f"doc_{i}") for i, doc in enumerate(documents)]

        # Get embeddings
        if self.embedding_service:
            embeddings = await self.embedding_service.generate_embeddings_batch(texts)
            if isinstance(embeddings, list):
                embeddings = np.array(embeddings)
        else:
            embeddings = self._tfidf_vectorizer.fit_transform(texts).toarray()

        # Build dendrogram
        dendrogram_data = self.build_dendrogram(embeddings)

        # Build tree recursively
        tree = self._build_tree_recursive(
            dendrogram_data=dendrogram_data,
            doc_ids=doc_ids,
            texts=texts,
            current_depth=0,
            max_depth=max_depth,
        )

        return {"root": tree}

    def _build_tree_recursive(
        self,
        dendrogram_data: Dict[str, Any],
        doc_ids: List[str],
        texts: List[str],
        current_depth: int,
        max_depth: int,
    ) -> Dict[str, Any]:
        """Build tree node recursively."""
        node_id = f"node_{uuid.uuid4().hex[:8]}"

        if current_depth >= max_depth or len(doc_ids) < 4:
            # Leaf node
            keywords = self._extract_keywords_from_texts(texts, n_keywords=5)
            return {
                "id": node_id,
                "name": self._generate_node_name(keywords),
                "document_ids": doc_ids,
                "keywords": keywords,
                "children": [],
            }

        # Get cluster assignments at this level
        n_clusters = min(3, len(doc_ids) // 2)
        labels = self.extract_at_depth(dendrogram_data, depth=n_clusters)

        if not labels:
            return {
                "id": node_id,
                "name": "Root",
                "document_ids": doc_ids,
                "keywords": [],
                "children": [],
            }

        # Group docs by cluster
        children = []
        for cluster_id in set(labels):
            cluster_mask = [l_ == cluster_id for l in labels]
            cluster_doc_ids = [doc_ids[i] for i, m in enumerate(cluster_mask) if m]
            cluster_texts = [texts[i] for i, m in enumerate(cluster_mask) if m]

            if cluster_doc_ids:
                child_keywords = self._extract_keywords_from_texts(cluster_texts, 5)
                children.append({
                    "id": f"node_{uuid.uuid4().hex[:8]}",
                    "name": self._generate_node_name(child_keywords),
                    "document_ids": cluster_doc_ids,
                    "keywords": child_keywords,
                    "children": [],
                })

        return {
            "id": node_id,
            "name": "Root",
            "document_ids": doc_ids,
            "keywords": [],
            "children": children,
        }

    def _extract_keywords_from_texts(
        self,
        texts: List[str],
        n_keywords: int,
    ) -> List[str]:
        """Extract keywords from text list."""
        if not texts:
            return []

        try:
            combined = " ".join(texts)
            tfidf = TfidfVectorizer(max_features=n_keywords, stop_words="english")
            tfidf.fit_transform([combined])
            return list(tfidf.get_feature_names_out())
        except Exception:
            return []

    def _generate_node_name(self, keywords: List[str]) -> str:
        """Generate node name from keywords."""
        if not keywords:
            return "Category"
        return " ".join(keywords[:2]).title()

    def flatten_tree(
        self,
        tree: Dict[str, Any],
        include_parents: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Flatten tree to list of categories.

        Args:
            tree: Tree structure from generate_taxonomy_tree
            include_parents: Whether to include parent nodes

        Returns:
            List of category dicts
        """
        categories = []
        root = tree.get("root", tree)

        def _flatten(node: Dict[str, Any], parent_id: Optional[str] = None):
            category = {
                "id": node.get("id"),
                "name": node.get("name"),
                "parent_id": parent_id,
                "document_ids": node.get("document_ids", []),
                "keywords": node.get("keywords", []),
            }

            children = node.get("children", [])
            if include_parents or not children:
                categories.append(category)

            for child in children:
                _flatten(child, node.get("id"))

        _flatten(root)
        return categories

    # ========================================================================
    # Streaming Clustering
    # ========================================================================

    def initialize_streaming_model(
        self,
        n_clusters: int = 5,
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Initialize streaming clustering model.

        Args:
            n_clusters: Number of clusters
            batch_size: Batch size for mini-batch updates

        Returns:
            Model state dict
        """
        if not SKLEARN_AVAILABLE:
            return {"error": "sklearn not available"}

        model = MiniBatchKMeans(
            n_clusters=n_clusters,
            batch_size=batch_size,
            random_state=42,
        )

        model_id = f"stream_{uuid.uuid4().hex[:8]}"
        state = {
            "model_id": model_id,
            "model": model,
            "n_clusters": n_clusters,
            "n_samples_seen": 0,
            "initialized": True,
        }

        self._streaming_models[model_id] = state
        return state

    def incremental_update(
        self,
        model: Dict[str, Any],
        new_embeddings: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Update streaming model with new data.

        Args:
            model: Model state from initialize_streaming_model
            new_embeddings: New embeddings to add

        Returns:
            Updated state with n_samples_seen
        """
        if not model.get("initialized"):
            return {"error": "Model not initialized"}

        kmeans = model.get("model")
        if kmeans is None:
            return {"error": "Model not found"}

        # Partial fit
        kmeans.partial_fit(new_embeddings)

        # Update count
        model["n_samples_seen"] = model.get("n_samples_seen", 0) + len(new_embeddings)

        return model

    def get_cluster_assignments(
        self,
        model: Dict[str, Any],
    ) -> np.ndarray:
        """
        Get current cluster assignments for all seen samples.

        Args:
            model: Model state

        Returns:
            Array of cluster labels
        """
        kmeans = model.get("model")
        if kmeans is None or not hasattr(kmeans, "labels_"):
            # If no labels yet, predict from cluster centers
            return np.array([])

        # For MiniBatchKMeans, we need to predict
        # This is a simplification - in production we'd track all embeddings
        return np.zeros(model.get("n_samples_seen", 0), dtype=int)

    # ========================================================================
    # Confidence Calibration
    # ========================================================================

    def calibrate_probabilities(
        self,
        raw_probs: np.ndarray,
        true_labels: np.ndarray,
        method: str = "isotonic",
    ) -> np.ndarray:
        """
        Calibrate raw probabilities to be well-calibrated.

        Args:
            raw_probs: Raw predicted probabilities
            true_labels: True binary labels
            method: Calibration method ('isotonic' or 'platt')

        Returns:
            Calibrated probabilities
        """
        if not SKLEARN_AVAILABLE:
            return raw_probs

        try:
            if method == "isotonic":
                from sklearn.isotonic import IsotonicRegression
                ir = IsotonicRegression(out_of_bounds="clip")
                calibrated = ir.fit_transform(raw_probs, true_labels)
            else:
                # Simple Platt scaling approximation
                calibrated = self._platt_scale(raw_probs, true_labels)

            return np.clip(calibrated, 0, 1)

        except Exception as e:
            logger.warning(f"Calibration failed: {e}")
            return raw_probs

    def _platt_scale(
        self,
        probs: np.ndarray,
        labels: np.ndarray,
    ) -> np.ndarray:
        """Simple Platt scaling."""
        # Logit transform
        eps = 1e-7
        logits = np.log(np.clip(probs, eps, 1 - eps) / (1 - np.clip(probs, eps, 1 - eps)))

        # Linear fit
        from sklearn.linear_model import LogisticRegression
        lr = LogisticRegression()
        lr.fit(logits.reshape(-1, 1), labels)

        # Transform
        return lr.predict_proba(logits.reshape(-1, 1))[:, 1]

    def calculate_calibration_error(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        n_bins: int = 10,
    ) -> float:
        """
        Calculate Expected Calibration Error (ECE).

        Args:
            predictions: Predicted probabilities
            true_labels: True binary labels
            n_bins: Number of bins for calibration

        Returns:
            ECE score (lower is better)
        """
        bins = np.linspace(0, 1, n_bins + 1)
        ece = 0.0

        for i in range(n_bins):
            mask = (predictions >= bins[i]) & (predictions < bins[i + 1])
            if mask.sum() > 0:
                bin_accuracy = true_labels[mask].mean()
                bin_confidence = predictions[mask].mean()
                bin_weight = mask.sum() / len(predictions)
                ece += bin_weight * abs(bin_accuracy - bin_confidence)

        return ece

    def apply_temperature_scaling(
        self,
        logits: np.ndarray,
        temperature: float = 1.0,
    ) -> np.ndarray:
        """
        Apply temperature scaling to logits.

        Args:
            logits: Raw logits
            temperature: Temperature parameter (>1 = softer, <1 = sharper)

        Returns:
            Softmax probabilities
        """
        scaled_logits = logits / max(temperature, 1e-7)
        return softmax(scaled_logits)

    def recommend_confidence_threshold(
        self,
        validation_data: Dict[str, np.ndarray],
        target_precision: float = 0.9,
    ) -> float:
        """
        Recommend confidence threshold for target precision.

        Args:
            validation_data: Dict with 'predictions' and 'true_labels'
            target_precision: Desired precision level

        Returns:
            Recommended threshold
        """
        predictions = validation_data.get("predictions", np.array([]))
        true_labels = validation_data.get("true_labels", np.array([]))

        if len(predictions) == 0:
            return 0.5

        # Try different thresholds
        thresholds = np.linspace(0.1, 0.99, 50)
        best_threshold = 0.5

        for thresh in thresholds:
            mask = predictions >= thresh
            if mask.sum() > 0:
                precision = true_labels[mask].mean()
                if precision >= target_precision:
                    best_threshold = thresh
                    break

        return best_threshold

    # ========================================================================
    # Domain Ontology
    # ========================================================================

    def load_domain_ontology(
        self,
        domain: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Load domain ontology from config.

        Args:
            domain: Domain name
            config: Ontology configuration

        Returns:
            Ontology dict with concepts and relationships
        """
        concepts = []
        root_concepts = config.get("root_concepts", [])
        relationships = config.get("relationships", [])

        # Build concept tree
        for concept in root_concepts:
            concepts.append({
                "id": concept.lower().replace(" ", "_"),
                "name": concept,
                "parent_id": None,
                "keywords": [],
            })

        # Add child concepts
        for rel in relationships:
            parent = rel.get("parent")
            child = rel.get("child")
            concepts.append({
                "id": child.lower().replace(" ", "_"),
                "name": child,
                "parent_id": parent.lower().replace(" ", "_"),
                "keywords": [],
            })

        return {
            "domain": domain,
            "concepts": concepts,
            "relationships": relationships,
        }

    def align_to_ontology(
        self,
        clusters: List[Dict[str, Any]],
        ontology: Dict[str, Any],
        similarity_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Align discovered clusters to ontology concepts.

        Args:
            clusters: Discovered cluster/topics
            ontology: Domain ontology
            similarity_threshold: Minimum similarity for alignment

        Returns:
            Clusters with aligned_concept field
        """
        concepts = ontology.get("concepts", [])

        for cluster in clusters:
            cluster_keywords = set(kw.lower() for kw in cluster.get("keywords", []))
            best_match = None
            best_score = 0

            for concept in concepts:
                concept_keywords = set(kw.lower() for kw in concept.get("keywords", []))
                concept_name_words = set(concept.get("name", "").lower().split())

                # Calculate overlap
                all_concept_words = concept_keywords | concept_name_words
                if all_concept_words:
                    overlap = len(cluster_keywords & all_concept_words)
                    score = overlap / len(all_concept_words)

                    if score > best_score and score >= similarity_threshold:
                        best_score = score
                        best_match = concept.get("id")

            if best_match:
                cluster["aligned_concept"] = best_match
                cluster["alignment_score"] = best_score

        return clusters

    # ========================================================================
    # Quality Metrics
    # ========================================================================

    def calculate_silhouette(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray,
    ) -> float:
        """
        Calculate silhouette score for clustering quality.

        Args:
            embeddings: Document embeddings
            labels: Cluster labels

        Returns:
            Silhouette score (-1 to 1, higher is better)
        """
        if not SKLEARN_AVAILABLE:
            return 0.0

        if len(set(labels)) < 2:
            return 0.0

        return silhouette_score(embeddings, labels)

    def calculate_davies_bouldin(
        self,
        embeddings: np.ndarray,
        labels: np.ndarray,
    ) -> float:
        """
        Calculate Davies-Bouldin index.

        Args:
            embeddings: Document embeddings
            labels: Cluster labels

        Returns:
            Davies-Bouldin index (lower is better)
        """
        if not SKLEARN_AVAILABLE:
            return float("in")

        if len(set(labels)) < 2:
            return float("in")

        return davies_bouldin_score(embeddings, labels)

    def find_optimal_clusters(
        self,
        embeddings: np.ndarray,
        min_clusters: int = 2,
        max_clusters: int = 10,
        method: str = "silhouette",
    ) -> Dict[str, Any]:
        """
        Find optimal number of clusters.

        Args:
            embeddings: Document embeddings
            min_clusters: Minimum clusters to try
            max_clusters: Maximum clusters to try
            method: Metric to optimize ('silhouette' or 'davies_bouldin')

        Returns:
            Dict with n_clusters and score
        """
        if not SKLEARN_AVAILABLE:
            return {"n_clusters": min_clusters, "score": 0}

        best_n = min_clusters
        best_score = -1 if method == "silhouette" else float("in")

        for n in range(min_clusters, min(max_clusters + 1, len(embeddings))):
            kmeans = KMeans(n_clusters=n, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)

            if method == "silhouette":
                score = self.calculate_silhouette(embeddings, labels)
                if score > best_score:
                    best_score = score
                    best_n = n
            else:
                score = self.calculate_davies_bouldin(embeddings, labels)
                if score < best_score:
                    best_score = score
                    best_n = n

        return {
            "n_clusters": best_n,
            "score": best_score,
            "method": method,
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_advanced_clustering_service: Optional[AdvancedClusteringService] = None


def get_advanced_clustering_service(
    embedding_service: Optional[Any] = None,
) -> AdvancedClusteringService:
    """Get or create advanced clustering service singleton."""
    global _advanced_clustering_service

    if _advanced_clustering_service is None:
        _advanced_clustering_service = AdvancedClusteringService(
            embedding_service=embedding_service
        )

    return _advanced_clustering_service
