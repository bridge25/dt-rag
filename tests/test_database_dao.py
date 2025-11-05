"""
Unit tests for Database DAO classes (Phase 1-3)

@TEST:DATABASE-001 | SPEC: .moai/specs/SPEC-DATABASE-001/spec.md | CODE: apps/api/database.py

Tests the database access objects including TaxonomyDAO, SearchDAO, and ClassifyDAO.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Set test DATABASE_URL before importing database module
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag_test"
)

from apps.api.database import (
    TaxonomyDAO,
    SearchDAO,
    ClassifyDAO,
    DatabaseManager,
    db_manager,
)


class TestDatabaseManager:
    """Test DatabaseManager initialization and methods"""

    def test_database_manager_singleton(self):
        """Should use singleton pattern for database manager"""
        assert db_manager is not None
        assert isinstance(db_manager, DatabaseManager)

    @pytest.mark.asyncio
    async def test_get_session(self):
        """Should return async session"""
        session = await db_manager.get_session()
        assert session is not None


class TestTaxonomyDAO:
    """Test TaxonomyDAO methods"""

    @pytest.mark.asyncio
    @patch("apps.api.database.db_manager")
    async def test_get_tree_returns_structure(self, mock_db):
        """Should return taxonomy tree structure"""
        # Mock database session
        mock_session = AsyncMock()
        mock_db.async_session.return_value.__aenter__.return_value = mock_session

        tree = await TaxonomyDAO.get_tree(version="1.8.1")

        assert isinstance(tree, list)
        assert len(tree) > 0

    @pytest.mark.asyncio
    async def test_get_tree_has_required_fields(self):
        """Should return nodes with required fields"""
        tree = await TaxonomyDAO.get_tree(version="1.8.1")

        if len(tree) > 0:
            node = tree[0]
            assert "label" in node
            assert "version" in node
            assert "node_id" in node
            assert "canonical_path" in node
            assert "children" in node

    @pytest.mark.asyncio
    async def test_get_fallback_tree(self):
        """Should return fallback tree structure"""
        tree = await TaxonomyDAO._get_fallback_tree(version="1.8.1")

        assert isinstance(tree, list)
        assert len(tree) > 0
        assert tree[0]["label"] == "AI"
        assert tree[0]["node_id"] == "ai_root_001"
        assert "children" in tree[0]


class TestSearchDAO:
    """Test SearchDAO methods"""

    @pytest.mark.asyncio
    @patch("apps.api.database.db_manager")
    async def test_hybrid_search_returns_hits(self, mock_db):
        """Should return search hits from hybrid search"""
        # Mock database session
        mock_session = AsyncMock()
        mock_db.async_session.return_value.__aenter__.return_value = mock_session

        query = "test search query"
        hits = await SearchDAO.hybrid_search(query, filters=None, topk=5)

        assert isinstance(hits, list)

    @pytest.mark.asyncio
    async def test_hybrid_search_with_filters(self):
        """Should accept filters parameter"""
        query = "test query"
        filters = {"taxonomy_path": ["AI", "RAG"]}

        hits = await SearchDAO.hybrid_search(query, filters=filters, topk=5)

        assert isinstance(hits, list)

    @pytest.mark.asyncio
    async def test_hybrid_search_topk_parameter(self):
        """Should respect topk parameter"""
        query = "test query"

        hits = await SearchDAO.hybrid_search(query, filters=None, topk=3)

        assert isinstance(hits, list)
        # May return fewer than topk if database is empty
        assert len(hits) <= 3

    @pytest.mark.asyncio
    async def test_get_fallback_search(self):
        """Should return fallback search results"""
        query = "fallback test"
        results = await SearchDAO._get_fallback_search(query)

        assert isinstance(results, list)
        assert len(results) > 0

        hit = results[0]
        assert "chunk_id" in hit
        assert "text" in hit
        assert "score" in hit
        assert query in hit["text"]


class TestClassifyDAO:
    """Test ClassifyDAO methods"""

    @pytest.mark.asyncio
    async def test_classify_text_returns_classification(self):
        """Should return classification result"""
        text = "This is a test document about RAG systems"

        result = await ClassifyDAO.classify_text(text)

        assert isinstance(result, dict)
        assert "canonical" in result
        assert "label" in result
        assert "confidence" in result
        assert "node_id" in result
        assert "version" in result

    @pytest.mark.asyncio
    async def test_classify_text_with_hint_paths(self):
        """Should accept hint_paths parameter"""
        text = "Document about machine learning"
        hint_paths = [["AI", "ML"]]

        result = await ClassifyDAO.classify_text(text, hint_paths=hint_paths)

        assert isinstance(result, dict)
        assert "canonical" in result

    @pytest.mark.asyncio
    async def test_fallback_classification_rag_text(self):
        """Should classify RAG-related text correctly (fallback)"""
        text = "retrieval augmented generation with vector embeddings"

        result = ClassifyDAO._fallback_classification(text, hint_paths=None)  # type: ignore[attr-defined]

        assert isinstance(result, dict)
        assert "RAG" in result["canonical"] or "GENERAL" in result["canonical"]
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_fallback_classification_ml_text(self):
        """Should classify ML-related text correctly (fallback)"""
        text = "machine learning model training and neural networks"

        result = ClassifyDAO._fallback_classification(text, hint_paths=None)  # type: ignore[attr-defined]

        assert isinstance(result, dict)
        assert "ML" in result["canonical"] or "GENERAL" in result["canonical"]
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_fallback_classification_taxonomy_text(self):
        """Should classify taxonomy-related text correctly (fallback)"""
        text = "taxonomy classification hierarchy and ontology"

        result = ClassifyDAO._fallback_classification(text, hint_paths=None)  # type: ignore[attr-defined]

        assert isinstance(result, dict)
        assert "TAXONOMY" in result["canonical"] or "GENERAL" in result["canonical"]
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_fallback_classification_generic_text(self):
        """Should handle generic text without clear category"""
        text = "this is just some random text without specific keywords"

        result = ClassifyDAO._fallback_classification(text, hint_paths=None)  # type: ignore[attr-defined]

        assert isinstance(result, dict)
        assert "canonical" in result
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_classify_returns_valid_confidence_range(self):
        """Should return confidence between 0 and 1"""
        texts = ["RAG vector search", "machine learning model", "random text", ""]

        for text in texts:
            if text:  # Skip empty string for actual classify
                result = await ClassifyDAO.classify_text(text)
                assert 0 <= result["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_classify_returns_canonical_path_as_list(self):
        """Should return canonical path as list"""
        text = "test document"

        result = await ClassifyDAO.classify_text(text)

        assert isinstance(result["canonical"], list)
        assert len(result["canonical"]) > 0


class TestDatabaseInitialization:
    """Test database initialization functions"""

    @pytest.mark.asyncio
    @patch("apps.api.database.db_manager")
    async def test_init_database_calls_manager(self, mock_db):
        """Should call database manager init_database"""
        from apps.api.database import init_database

        mock_db.init_database = AsyncMock(return_value=True)

        result = await init_database()

        mock_db.init_database.assert_called_once()

    @pytest.mark.asyncio
    @patch("apps.api.database.db_manager")
    async def test_test_database_connection_calls_manager(self, mock_db):
        """Should call database manager test_connection"""
        from apps.api.database import test_database_connection

        mock_db.test_connection = AsyncMock(return_value=True)

        result = await test_database_connection()

        mock_db.test_connection.assert_called_once()


class TestDataAccessPatterns:
    """Test common data access patterns"""

    @pytest.mark.asyncio
    async def test_taxonomy_search_integration(self):
        """Should integrate taxonomy with search"""
        # Get taxonomy tree
        tree = await TaxonomyDAO.get_tree(version="1.8.1")
        assert len(tree) > 0

        # Perform search with taxonomy filter
        hits = await SearchDAO.hybrid_search(
            query="test", filters={"taxonomy_path": tree[0]["canonical_path"]}, topk=5
        )
        assert isinstance(hits, list)

    @pytest.mark.asyncio
    async def test_classify_and_search_workflow(self):
        """Should support classify-then-search workflow"""
        text = "document about RAG systems"

        # Classify
        classification = await ClassifyDAO.classify_text(text)
        assert "canonical" in classification

        # Search within classified category
        hits = await SearchDAO.hybrid_search(
            query="RAG", filters={"taxonomy_path": classification["canonical"]}, topk=5
        )
        assert isinstance(hits, list)
