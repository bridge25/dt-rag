"""
Unit Tests for Taxonomy Evolution Service

Tests for ML-powered taxonomy generation and evolution suggestions.
TDD RED phase - tests written before implementation.

@TEST:TAXONOMY-EVOLUTION-001
"""

import pytest
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from apps.api.models.evolution_models import (
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


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_documents() -> List[Dict[str, Any]]:
    """Sample documents for testing"""
    return [
        {"doc_id": "doc1", "content": "Machine learning algorithms for image classification", "title": "ML Image"},
        {"doc_id": "doc2", "content": "Deep neural networks in natural language processing", "title": "NLP Deep"},
        {"doc_id": "doc3", "content": "Convolutional neural networks for object detection", "title": "CNN Detection"},
        {"doc_id": "doc4", "content": "Transformer models for text generation", "title": "Transformers"},
        {"doc_id": "doc5", "content": "Financial analysis using machine learning techniques", "title": "Finance ML"},
        {"doc_id": "doc6", "content": "Stock market prediction with neural networks", "title": "Stock NN"},
        {"doc_id": "doc7", "content": "Healthcare diagnostics using deep learning", "title": "Health DL"},
        {"doc_id": "doc8", "content": "Medical image analysis with CNNs", "title": "Medical CNN"},
        {"doc_id": "doc9", "content": "Database optimization techniques", "title": "DB Optimize"},
        {"doc_id": "doc10", "content": "SQL query performance tuning", "title": "SQL Tuning"},
    ]


@pytest.fixture
def sample_embeddings() -> List[List[float]]:
    """Mock embeddings (1536-dim) for testing"""
    np.random.seed(42)
    # Create 10 embeddings with some clustering structure
    base_vectors = [
        np.random.normal(0, 1, 1536),  # Cluster 1: ML/AI
        np.random.normal(0, 1, 1536),  # Cluster 2: Finance
        np.random.normal(0, 1, 1536),  # Cluster 3: Healthcare
        np.random.normal(0, 1, 1536),  # Cluster 4: Database
    ]
    embeddings = []
    # Docs 1-4: ML/AI cluster
    for i in range(4):
        emb = base_vectors[0] + np.random.normal(0, 0.1, 1536)
        embeddings.append(emb.tolist())
    # Docs 5-6: Finance cluster
    for i in range(2):
        emb = base_vectors[1] + np.random.normal(0, 0.1, 1536)
        embeddings.append(emb.tolist())
    # Docs 7-8: Healthcare cluster
    for i in range(2):
        emb = base_vectors[2] + np.random.normal(0, 0.1, 1536)
        embeddings.append(emb.tolist())
    # Docs 9-10: Database cluster
    for i in range(2):
        emb = base_vectors[3] + np.random.normal(0, 0.1, 1536)
        embeddings.append(emb.tolist())
    return embeddings


@pytest.fixture
def generator_config() -> GeneratorConfig:
    """Default generator config for testing"""
    return GeneratorConfig(
        max_depth=3,
        min_documents_per_category=2,
        granularity=Granularity.MEDIUM,
        algorithm=GenerationAlgorithm.KMEANS,
        n_clusters=4,
    )


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service"""
    mock = AsyncMock()
    mock.batch_generate_embeddings = AsyncMock()
    mock.calculate_similarity = MagicMock(return_value=0.85)
    return mock


# ============================================================================
# Test: GeneratorConfig
# ============================================================================


class TestGeneratorConfig:
    """Tests for GeneratorConfig dataclass"""

    def test_default_config(self):
        """Should create config with default values"""
        config = GeneratorConfig()

        assert config.max_depth == 4
        assert config.min_documents_per_category == 5
        assert config.granularity == Granularity.MEDIUM
        assert config.algorithm == GenerationAlgorithm.KMEANS
        assert config.n_clusters is None
        assert config.similarity_threshold == 0.7

    def test_custom_config(self):
        """Should create config with custom values"""
        config = GeneratorConfig(
            max_depth=3,
            min_documents_per_category=10,
            granularity=Granularity.FINE,
            algorithm=GenerationAlgorithm.HDBSCAN,
            domain_hints=["technology", "finance"],
        )

        assert config.max_depth == 3
        assert config.min_documents_per_category == 10
        assert config.granularity == Granularity.FINE
        assert config.algorithm == GenerationAlgorithm.HDBSCAN
        assert config.domain_hints == ["technology", "finance"]


# ============================================================================
# Test: ProposedCategory
# ============================================================================


class TestProposedCategory:
    """Tests for ProposedCategory dataclass"""

    def test_create_category(self):
        """Should create proposed category with required fields"""
        category = ProposedCategory(
            id="cat_1",
            name="Machine Learning",
            description="Documents about ML",
            parent_id=None,
            confidence_score=0.85,
            document_count=10,
            sample_document_ids=["doc1", "doc2"],
            keywords=["ml", "neural", "deep learning"],
        )

        assert category.id == "cat_1"
        assert category.name == "Machine Learning"
        assert category.confidence_score == 0.85
        assert category.document_count == 10
        assert len(category.keywords) == 3

    def test_auto_generate_id(self):
        """Should auto-generate ID if not provided"""
        category = ProposedCategory(
            id="",
            name="Test",
            description="Test",
            parent_id=None,
            confidence_score=0.5,
            document_count=5,
            sample_document_ids=[],
            keywords=[],
        )

        assert category.id.startswith("cat_")
        assert len(category.id) > 4


# ============================================================================
# Test: TaxonomyEvolutionService
# ============================================================================


class TestTaxonomyEvolutionService:
    """Tests for TaxonomyEvolutionService"""

    @pytest.mark.asyncio
    async def test_generate_taxonomy_basic(
        self,
        sample_documents,
        sample_embeddings,
        generator_config,
        mock_embedding_service,
    ):
        """Should generate taxonomy from documents"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        mock_embedding_service.batch_generate_embeddings.return_value = sample_embeddings

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)
        proposal = await service.generate_taxonomy(
            documents=sample_documents,
            config=generator_config,
        )

        assert proposal is not None
        assert proposal.status == ProposalStatus.COMPLETED
        assert len(proposal.categories) > 0
        assert proposal.total_documents == len(sample_documents)
        assert proposal.processing_time_seconds > 0

    @pytest.mark.asyncio
    async def test_generate_taxonomy_respects_min_documents(
        self,
        sample_documents,
        sample_embeddings,
        mock_embedding_service,
    ):
        """Should not create categories with fewer documents than minimum"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        config = GeneratorConfig(
            min_documents_per_category=3,
            n_clusters=4,
        )

        mock_embedding_service.batch_generate_embeddings.return_value = sample_embeddings

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)
        proposal = await service.generate_taxonomy(
            documents=sample_documents,
            config=config,
        )

        for category in proposal.categories:
            assert category.document_count >= config.min_documents_per_category

    @pytest.mark.asyncio
    async def test_generate_taxonomy_with_kmeans(
        self,
        sample_documents,
        sample_embeddings,
        mock_embedding_service,
    ):
        """Should use KMeans algorithm when specified"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        config = GeneratorConfig(
            algorithm=GenerationAlgorithm.KMEANS,
            n_clusters=3,
        )

        mock_embedding_service.batch_generate_embeddings.return_value = sample_embeddings

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)
        proposal = await service.generate_taxonomy(
            documents=sample_documents,
            config=config,
        )

        assert proposal.status == ProposalStatus.COMPLETED
        # With n_clusters=3, should have approximately 3 categories
        assert len(proposal.categories) <= 4

    @pytest.mark.asyncio
    async def test_generate_taxonomy_extracts_keywords(
        self,
        sample_documents,
        sample_embeddings,
        mock_embedding_service,
    ):
        """Should extract meaningful keywords for each category"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        config = GeneratorConfig(n_clusters=3)
        mock_embedding_service.batch_generate_embeddings.return_value = sample_embeddings

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)
        proposal = await service.generate_taxonomy(
            documents=sample_documents,
            config=config,
        )

        for category in proposal.categories:
            assert len(category.keywords) > 0

    @pytest.mark.asyncio
    async def test_generate_taxonomy_includes_sample_docs(
        self,
        sample_documents,
        sample_embeddings,
        mock_embedding_service,
    ):
        """Should include sample document IDs in each category"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        config = GeneratorConfig(n_clusters=3)
        mock_embedding_service.batch_generate_embeddings.return_value = sample_embeddings

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)
        proposal = await service.generate_taxonomy(
            documents=sample_documents,
            config=config,
        )

        for category in proposal.categories:
            assert len(category.sample_document_ids) > 0
            assert len(category.sample_document_ids) <= 5  # Max 5 samples

    @pytest.mark.asyncio
    async def test_generate_taxonomy_handles_empty_documents(
        self,
        mock_embedding_service,
    ):
        """Should handle empty document list gracefully"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)
        proposal = await service.generate_taxonomy(
            documents=[],
            config=GeneratorConfig(),
        )

        assert proposal.status == ProposalStatus.FAILED
        assert proposal.error_message is not None
        assert "empty" in proposal.error_message.lower() or "no documents" in proposal.error_message.lower()

    @pytest.mark.asyncio
    async def test_generate_taxonomy_handles_few_documents(
        self,
        mock_embedding_service,
    ):
        """Should handle case with fewer documents than clusters"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        few_docs = [{"doc_id": "doc1", "content": "Test document", "title": "Test"}]
        mock_embedding_service.batch_generate_embeddings.return_value = [[0.1] * 1536]

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)
        proposal = await service.generate_taxonomy(
            documents=few_docs,
            config=GeneratorConfig(n_clusters=5),
        )

        # Should either reduce clusters or handle gracefully
        assert proposal.status in [ProposalStatus.COMPLETED, ProposalStatus.FAILED]


# ============================================================================
# Test: Clustering Operations
# ============================================================================


class TestClusteringOperations:
    """Tests for clustering operations"""

    @pytest.mark.asyncio
    async def test_kmeans_clustering(
        self,
        sample_embeddings,
        mock_embedding_service,
    ):
        """Should correctly cluster embeddings with KMeans"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)

        result = service._cluster_documents(
            embeddings=sample_embeddings,
            algorithm=GenerationAlgorithm.KMEANS,
            n_clusters=4,
        )

        assert len(result) == 4
        for cluster in result:
            assert isinstance(cluster, ClusteringResult)
            assert cluster.size > 0
            assert len(cluster.document_ids) == cluster.size

    @pytest.mark.asyncio
    async def test_clustering_assigns_all_documents(
        self,
        sample_embeddings,
        mock_embedding_service,
    ):
        """Should assign all documents to clusters"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)

        result = service._cluster_documents(
            embeddings=sample_embeddings,
            algorithm=GenerationAlgorithm.KMEANS,
            n_clusters=3,
        )

        total_docs = sum(cluster.size for cluster in result)
        assert total_docs == len(sample_embeddings)


# ============================================================================
# Test: Keyword Extraction
# ============================================================================


class TestKeywordExtraction:
    """Tests for keyword extraction"""

    @pytest.mark.asyncio
    async def test_extract_keywords_from_documents(
        self,
        sample_documents,
        mock_embedding_service,
    ):
        """Should extract relevant keywords from document content"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)

        # Get ML-related docs
        ml_docs = sample_documents[:4]
        keywords = service._extract_keywords(ml_docs, max_keywords=10)

        assert len(keywords) > 0
        assert len(keywords) <= 10
        # Should find common ML terms
        keywords_lower = [k.lower() for k in keywords]
        assert any(term in keywords_lower for term in ["machine", "learning", "neural", "deep"])

    @pytest.mark.asyncio
    async def test_extract_keywords_handles_empty(
        self,
        mock_embedding_service,
    ):
        """Should handle empty document list"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)
        keywords = service._extract_keywords([], max_keywords=10)

        assert keywords == []


# ============================================================================
# Test: Label Generation
# ============================================================================


class TestLabelGeneration:
    """Tests for automatic label generation"""

    @pytest.mark.asyncio
    async def test_generate_label_from_keywords(
        self,
        mock_embedding_service,
    ):
        """Should generate meaningful label from keywords"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)

        keywords = ["machine", "learning", "neural", "networks"]
        label = service._generate_label(keywords)

        assert label is not None
        assert len(label) > 0
        assert len(label) <= 50  # Reasonable label length

    @pytest.mark.asyncio
    async def test_generate_label_handles_empty_keywords(
        self,
        mock_embedding_service,
    ):
        """Should handle empty keywords list"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)

        label = service._generate_label([])

        assert label is not None
        assert "Unnamed" in label or "Unknown" in label or "Category" in label


# ============================================================================
# Test: Evolution Suggestions
# ============================================================================


class TestEvolutionSuggestions:
    """Tests for evolution suggestion generation"""

    @pytest.mark.asyncio
    async def test_detect_overlapping_categories(
        self,
        mock_embedding_service,
    ):
        """Should detect categories with high overlap"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)

        # Two categories with overlapping keywords
        categories = [
            {"id": "cat1", "keywords": ["ml", "machine", "learning", "ai"], "embedding": [0.1] * 1536},
            {"id": "cat2", "keywords": ["machine", "learning", "deep", "neural"], "embedding": [0.12] * 1536},
            {"id": "cat3", "keywords": ["database", "sql", "query"], "embedding": [0.9] * 1536},
        ]

        mock_embedding_service.calculate_similarity.side_effect = [
            0.95,  # cat1 vs cat2 - high overlap
            0.3,   # cat1 vs cat3 - low overlap
            0.25,  # cat2 vs cat3 - low overlap
        ]

        suggestions = await service.detect_merge_opportunities(categories)

        # Should suggest merging cat1 and cat2
        merge_suggestions = [s for s in suggestions if s.suggestion_type == SuggestionType.MERGE]
        assert len(merge_suggestions) > 0

    @pytest.mark.asyncio
    async def test_create_merge_suggestion(
        self,
        mock_embedding_service,
    ):
        """Should create valid merge suggestion"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)

        suggestion = service._create_merge_suggestion(
            category_ids=["cat1", "cat2"],
            overlap_score=0.9,
            shared_keywords=["machine", "learning"],
            affected_docs=50,
        )

        assert suggestion.suggestion_type == SuggestionType.MERGE
        assert suggestion.confidence >= 0.8
        assert suggestion.affected_documents == 50
        assert "cat1" in suggestion.details["source_categories"]
        assert "cat2" in suggestion.details["source_categories"]


# ============================================================================
# Test: Proposal Management
# ============================================================================


class TestProposalManagement:
    """Tests for proposal lifecycle management"""

    def test_create_proposal(self):
        """Should create proposal with pending status"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        proposal = TaxonomyProposal(
            proposal_id="",
            status=ProposalStatus.PENDING,
            categories=[],
            config=GeneratorConfig(),
            total_documents=100,
            processing_time_seconds=0.0,
            created_at=datetime.utcnow(),
        )

        assert proposal.proposal_id.startswith("prop_")
        assert proposal.status == ProposalStatus.PENDING
        assert proposal.completed_at is None

    def test_proposal_transition_to_completed(self):
        """Should transition proposal to completed status"""
        proposal = TaxonomyProposal(
            proposal_id="prop_test",
            status=ProposalStatus.PROCESSING,
            categories=[],
            config=GeneratorConfig(),
            total_documents=100,
            processing_time_seconds=0.0,
            created_at=datetime.utcnow(),
        )

        proposal.status = ProposalStatus.COMPLETED
        proposal.completed_at = datetime.utcnow()
        proposal.processing_time_seconds = 5.5

        assert proposal.status == ProposalStatus.COMPLETED
        assert proposal.completed_at is not None
        assert proposal.processing_time_seconds == 5.5


# ============================================================================
# Test: Error Handling
# ============================================================================


class TestErrorHandling:
    """Tests for error handling"""

    @pytest.mark.asyncio
    async def test_handles_embedding_failure(
        self,
        sample_documents,
        mock_embedding_service,
    ):
        """Should handle embedding service failure gracefully"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        mock_embedding_service.batch_generate_embeddings.side_effect = Exception("API Error")

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)
        proposal = await service.generate_taxonomy(
            documents=sample_documents,
            config=GeneratorConfig(),
        )

        assert proposal.status == ProposalStatus.FAILED
        assert "API Error" in proposal.error_message or "embedding" in proposal.error_message.lower()

    @pytest.mark.asyncio
    async def test_handles_clustering_failure(
        self,
        mock_embedding_service,
    ):
        """Should handle clustering algorithm failure"""
        from apps.api.services.taxonomy_evolution_service import TaxonomyEvolutionService

        service = TaxonomyEvolutionService(embedding_service=mock_embedding_service)

        # Pass invalid embeddings
        result = service._cluster_documents(
            embeddings=[],
            algorithm=GenerationAlgorithm.KMEANS,
            n_clusters=3,
        )

        # Should return empty list instead of crashing
        assert result == []
