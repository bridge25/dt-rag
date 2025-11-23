"""
Tests for Advanced Clustering Algorithms

Tests for BERTopic integration, hierarchical clustering,
streaming clustering, and confidence calibration.
TDD RED phase - tests written before implementation.

@TEST:TAXONOMY-EVOLUTION-001
"""

import pytest
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_documents() -> List[Dict[str, Any]]:
    """Sample documents for clustering tests"""
    return [
        {"doc_id": "doc_1", "title": "Machine Learning Basics", "content": "Introduction to machine learning algorithms and neural networks."},
        {"doc_id": "doc_2", "title": "Deep Learning Networks", "content": "Deep neural networks and backpropagation training methods."},
        {"doc_id": "doc_3", "title": "Natural Language Processing", "content": "NLP techniques including tokenization and embeddings."},
        {"doc_id": "doc_4", "title": "Computer Vision", "content": "Image recognition and convolutional neural networks."},
        {"doc_id": "doc_5", "title": "Database Design", "content": "Relational database design and SQL optimization."},
        {"doc_id": "doc_6", "title": "NoSQL Databases", "content": "Document stores and key-value databases for scalability."},
        {"doc_id": "doc_7", "title": "Financial Markets", "content": "Stock market analysis and trading strategies."},
        {"doc_id": "doc_8", "title": "Investment Banking", "content": "Corporate finance and investment portfolio management."},
    ]


@pytest.fixture
def sample_embeddings() -> np.ndarray:
    """Sample embeddings for 8 documents"""
    np.random.seed(42)
    # Create clustered embeddings: 3 clusters
    cluster_1 = np.random.normal([1, 0, 0], 0.2, (4, 3))  # ML docs
    cluster_2 = np.random.normal([0, 1, 0], 0.2, (2, 3))  # DB docs
    cluster_3 = np.random.normal([0, 0, 1], 0.2, (2, 3))  # Finance docs
    return np.vstack([cluster_1, cluster_2, cluster_3])


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service"""
    mock = MagicMock()
    mock.generate_embedding = AsyncMock()
    mock.generate_embeddings_batch = AsyncMock()
    return mock


# ============================================================================
# Test: BERTopic Integration
# ============================================================================


class TestBERTopicIntegration:
    """Tests for BERTopic-based topic modeling"""

    @pytest.mark.asyncio
    async def test_extract_topics_from_documents(
        self,
        sample_documents,
        mock_embedding_service,
    ):
        """Should extract topics using BERTopic-style approach"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        mock_embedding_service.generate_embeddings_batch.return_value = np.random.rand(8, 384)

        service = AdvancedClusteringService(
            embedding_service=mock_embedding_service
        )

        topics = await service.extract_topics(
            documents=sample_documents,
            n_topics=3,
        )

        assert len(topics) > 0
        assert all("topic_id" in t for t in topics)
        assert all("keywords" in t for t in topics)
        assert all("document_ids" in t for t in topics)

    @pytest.mark.asyncio
    async def test_topic_keywords_extraction(
        self,
        sample_documents,
        mock_embedding_service,
    ):
        """Should extract representative keywords for each topic"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        mock_embedding_service.generate_embeddings_batch.return_value = np.random.rand(8, 384)

        service = AdvancedClusteringService(
            embedding_service=mock_embedding_service
        )

        topics = await service.extract_topics(
            documents=sample_documents,
            n_topics=3,
            n_keywords=5,
        )

        # Each topic should have keywords
        for topic in topics:
            if topic["topic_id"] != -1:  # Ignore outlier topic
                assert len(topic["keywords"]) > 0
                assert len(topic["keywords"]) <= 5

    @pytest.mark.asyncio
    async def test_topic_coherence_score(
        self,
        sample_documents,
        mock_embedding_service,
    ):
        """Should calculate topic coherence score"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        mock_embedding_service.generate_embeddings_batch.return_value = np.random.rand(8, 384)

        service = AdvancedClusteringService(
            embedding_service=mock_embedding_service
        )

        topics = await service.extract_topics(
            documents=sample_documents,
            n_topics=3,
            calculate_coherence=True,
        )

        # Should have coherence score
        for topic in topics:
            if topic["topic_id"] != -1:
                assert "coherence_score" in topic
                assert 0 <= topic["coherence_score"] <= 1


# ============================================================================
# Test: Hierarchical Clustering
# ============================================================================


class TestHierarchicalClustering:
    """Tests for hierarchical/agglomerative clustering"""

    @pytest.mark.asyncio
    async def test_build_dendrogram(
        self,
        sample_embeddings,
    ):
        """Should build dendrogram from embeddings"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        service = AdvancedClusteringService()

        dendrogram = service.build_dendrogram(
            embeddings=sample_embeddings,
            linkage_method="ward",
        )

        assert dendrogram is not None
        assert "linkage_matrix" in dendrogram
        assert "n_samples" in dendrogram
        assert dendrogram["n_samples"] == len(sample_embeddings)

    @pytest.mark.asyncio
    async def test_extract_hierarchy_at_depth(
        self,
        sample_embeddings,
    ):
        """Should extract clusters at specified depth"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        service = AdvancedClusteringService()

        # Build dendrogram first
        dendrogram = service.build_dendrogram(sample_embeddings)

        # Extract at different depths
        clusters_depth_1 = service.extract_at_depth(dendrogram, depth=1)
        clusters_depth_2 = service.extract_at_depth(dendrogram, depth=2)

        # More depth = more clusters
        assert len(clusters_depth_1) <= len(clusters_depth_2)

    @pytest.mark.asyncio
    async def test_generate_taxonomy_tree(
        self,
        sample_documents,
        sample_embeddings,
        mock_embedding_service,
    ):
        """Should generate full taxonomy tree structure"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        mock_embedding_service.generate_embeddings_batch.return_value = sample_embeddings

        service = AdvancedClusteringService(
            embedding_service=mock_embedding_service
        )

        tree = await service.generate_taxonomy_tree(
            documents=sample_documents,
            max_depth=3,
        )

        assert tree is not None
        assert "root" in tree
        assert "children" in tree["root"]

    @pytest.mark.asyncio
    async def test_flatten_tree_to_categories(
        self,
        sample_documents,
        sample_embeddings,
        mock_embedding_service,
    ):
        """Should flatten tree to flat category list"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        mock_embedding_service.generate_embeddings_batch.return_value = sample_embeddings

        service = AdvancedClusteringService(
            embedding_service=mock_embedding_service
        )

        tree = await service.generate_taxonomy_tree(
            documents=sample_documents,
            max_depth=3,
        )

        categories = service.flatten_tree(tree, include_parents=True)

        assert len(categories) > 0
        assert all("id" in c for c in categories)
        assert all("name" in c for c in categories)


# ============================================================================
# Test: Streaming Clustering
# ============================================================================


class TestStreamingClustering:
    """Tests for incremental/streaming clustering"""

    @pytest.mark.asyncio
    async def test_initialize_streaming_model(self):
        """Should initialize streaming clustering model"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        service = AdvancedClusteringService()

        model = service.initialize_streaming_model(
            n_clusters=5,
            batch_size=100,
        )

        assert model is not None
        assert model.get("initialized") is True
        assert "model" in model

    @pytest.mark.asyncio
    async def test_incremental_update(
        self,
        sample_embeddings,
    ):
        """Should update clusters incrementally"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        # Create fresh service instance to avoid shared state
        service = AdvancedClusteringService()

        # Initialize fresh model
        model = service.initialize_streaming_model(n_clusters=3)

        # First batch
        result_1 = service.incremental_update(
            model=model,
            new_embeddings=sample_embeddings[:4],
        )
        first_count = result_1["n_samples_seen"]

        # Second batch
        result_2 = service.incremental_update(
            model=model,
            new_embeddings=sample_embeddings[4:],
        )

        # Check incremental increase
        assert result_2["n_samples_seen"] > first_count
        assert result_2["n_samples_seen"] == first_count + len(sample_embeddings[4:])

    @pytest.mark.asyncio
    async def test_get_cluster_assignments(
        self,
        sample_embeddings,
    ):
        """Should return current cluster assignments"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        service = AdvancedClusteringService()

        model = service.initialize_streaming_model(n_clusters=3)
        service.incremental_update(model, sample_embeddings)

        assignments = service.get_cluster_assignments(model)

        assert len(assignments) == len(sample_embeddings)
        assert all(0 <= a < 3 for a in assignments)


# ============================================================================
# Test: Confidence Calibration
# ============================================================================


class TestConfidenceCalibration:
    """Tests for prediction confidence calibration"""

    @pytest.mark.asyncio
    async def test_calibrate_probabilities(self):
        """Should calibrate raw probabilities"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        service = AdvancedClusteringService()

        # Raw uncalibrated probabilities (often overconfident)
        raw_probs = np.array([0.95, 0.88, 0.72, 0.65, 0.51])
        true_labels = np.array([1, 1, 0, 1, 0])

        calibrated = service.calibrate_probabilities(
            raw_probs=raw_probs,
            true_labels=true_labels,
            method="isotonic",
        )

        assert len(calibrated) == len(raw_probs)
        assert all(0 <= p <= 1 for p in calibrated)

    @pytest.mark.asyncio
    async def test_calculate_calibration_error(self):
        """Should calculate Expected Calibration Error"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        service = AdvancedClusteringService()

        predictions = np.array([0.9, 0.8, 0.7, 0.6, 0.5])
        true_labels = np.array([1, 1, 0, 1, 0])

        ece = service.calculate_calibration_error(
            predictions=predictions,
            true_labels=true_labels,
            n_bins=5,
        )

        assert 0 <= ece <= 1

    @pytest.mark.asyncio
    async def test_apply_temperature_scaling(self):
        """Should apply temperature scaling for calibration"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        service = AdvancedClusteringService()

        logits = np.array([2.5, 1.8, 0.5, -0.3])

        # High temperature = softer probabilities
        soft = service.apply_temperature_scaling(logits, temperature=2.0)
        # Low temperature = sharper probabilities
        sharp = service.apply_temperature_scaling(logits, temperature=0.5)

        # Soft should be more uniform
        assert np.std(soft) < np.std(sharp)

    @pytest.mark.asyncio
    async def test_confidence_threshold_recommendation(self):
        """Should recommend confidence threshold"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        service = AdvancedClusteringService()

        # Simulated validation results
        validation_data = {
            "predictions": np.random.rand(100),
            "true_labels": np.random.randint(0, 2, 100),
        }

        threshold = service.recommend_confidence_threshold(
            validation_data=validation_data,
            target_precision=0.9,
        )

        assert 0 <= threshold <= 1


# ============================================================================
# Test: Domain Ontology Support
# ============================================================================


class TestDomainOntology:
    """Tests for domain-specific ontology integration"""

    @pytest.mark.asyncio
    async def test_load_domain_ontology(self):
        """Should load domain ontology from config"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        service = AdvancedClusteringService()

        ontology = service.load_domain_ontology(
            domain="technology",
            config={
                "root_concepts": ["Software", "Hardware", "Data"],
                "relationships": [
                    {"parent": "Software", "child": "Machine Learning"},
                    {"parent": "Data", "child": "Database"},
                ],
            },
        )

        assert ontology is not None
        assert "concepts" in ontology
        assert len(ontology["concepts"]) > 0

    @pytest.mark.asyncio
    async def test_align_clusters_to_ontology(
        self,
        sample_documents,
        sample_embeddings,
        mock_embedding_service,
    ):
        """Should align discovered clusters to ontology concepts"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        mock_embedding_service.generate_embeddings_batch.return_value = sample_embeddings

        service = AdvancedClusteringService(
            embedding_service=mock_embedding_service
        )

        ontology = {
            "concepts": [
                {"id": "ml", "name": "Machine Learning", "keywords": ["learning", "neural", "model"]},
                {"id": "db", "name": "Database", "keywords": ["database", "sql", "query"]},
                {"id": "fin", "name": "Finance", "keywords": ["market", "trading", "investment"]},
            ]
        }

        clusters = await service.extract_topics(sample_documents, n_topics=3)

        aligned = service.align_to_ontology(
            clusters=clusters,
            ontology=ontology,
            similarity_threshold=0.5,
        )

        assert len(aligned) > 0
        for cluster in aligned:
            if "aligned_concept" in cluster:
                assert cluster["aligned_concept"] in ["ml", "db", "fin"]


# ============================================================================
# Test: Quality Metrics
# ============================================================================


class TestClusteringQuality:
    """Tests for clustering quality metrics"""

    @pytest.mark.asyncio
    async def test_calculate_silhouette_score(
        self,
        sample_embeddings,
    ):
        """Should calculate silhouette score"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        service = AdvancedClusteringService()

        labels = np.array([0, 0, 0, 0, 1, 1, 2, 2])

        score = service.calculate_silhouette(
            embeddings=sample_embeddings,
            labels=labels,
        )

        assert -1 <= score <= 1

    @pytest.mark.asyncio
    async def test_calculate_davies_bouldin_index(
        self,
        sample_embeddings,
    ):
        """Should calculate Davies-Bouldin index"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        service = AdvancedClusteringService()

        labels = np.array([0, 0, 0, 0, 1, 1, 2, 2])

        dbi = service.calculate_davies_bouldin(
            embeddings=sample_embeddings,
            labels=labels,
        )

        assert dbi >= 0  # Lower is better

    @pytest.mark.asyncio
    async def test_find_optimal_n_clusters(
        self,
        sample_embeddings,
    ):
        """Should find optimal number of clusters"""
        from apps.api.services.advanced_clustering import AdvancedClusteringService

        service = AdvancedClusteringService()

        optimal = service.find_optimal_clusters(
            embeddings=sample_embeddings,
            min_clusters=2,
            max_clusters=5,
            method="silhouette",
        )

        assert 2 <= optimal["n_clusters"] <= 5
        assert "score" in optimal
