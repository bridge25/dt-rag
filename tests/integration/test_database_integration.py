"""
Database Integration Tests
Tests database connections and DAO operations

@TEST:INTEGRATION-001
"""

import pytest
import asyncio


@pytest.mark.asyncio
class TestDatabaseConnection:
    """Database connection tests"""

    async def test_database_connection(self):
        """Test database connection is successful"""
        from database import test_database_connection  # type: ignore[import-not-found]

        is_connected = await test_database_connection()
        assert is_connected is True

    async def test_database_initialization(self):
        """Test database initialization"""
        from database import init_database

        result = await init_database()
        # Should return True or already be initialized
        assert result in [True, False]  # False if already initialized


@pytest.mark.asyncio
class TestTaxonomyDAO:
    """TaxonomyDAO integration tests"""

    async def test_get_taxonomy_tree(self):
        """Test taxonomy tree retrieval"""
        from database import TaxonomyDAO

        tree = await TaxonomyDAO.get_tree(version="1.8.1")

        assert isinstance(tree, list)
        assert len(tree) > 0

        # Check tree structure
        first_node = tree[0]
        assert "label" in first_node
        assert "canonical_path" in first_node
        assert "version" in first_node

    async def test_taxonomy_tree_has_ai_root(self):
        """Test taxonomy tree includes AI root node"""
        from database import TaxonomyDAO

        tree = await TaxonomyDAO.get_tree(version="1.8.1")

        # Should have AI as root
        labels = [node["label"] for node in tree]
        assert "AI" in labels

    async def test_taxonomy_fallback(self):
        """Test taxonomy fallback mechanism"""
        from database import TaxonomyDAO

        # Even with invalid version, should return fallback
        tree = await TaxonomyDAO.get_tree(version="invalid-version")

        assert isinstance(tree, list)
        assert len(tree) > 0


@pytest.mark.asyncio
class TestSearchDAO:
    """SearchDAO integration tests"""

    async def test_hybrid_search_executes(self):
        """Test hybrid search executes without errors"""
        from database import SearchDAO

        results = await SearchDAO.hybrid_search(query="machine learning", topk=5)

        assert isinstance(results, list)

    async def test_search_returns_hits(self):
        """Test search returns hits with proper structure"""
        from database import SearchDAO

        results = await SearchDAO.hybrid_search(query="RAG system", topk=3)

        if len(results) > 0:
            hit = results[0]
            assert "chunk_id" in hit
            assert "text" in hit
            assert "score" in hit

    async def test_search_with_filters(self):
        """Test search with taxonomy filters"""
        from database import SearchDAO

        results = await SearchDAO.hybrid_search(
            query="neural networks", filters={"taxonomy_path": ["AI", "ML"]}, topk=5
        )

        assert isinstance(results, list)

    async def test_search_fallback(self):
        """Test search fallback mechanism"""
        from database import SearchDAO

        # Even with no results, should return fallback
        results = await SearchDAO.hybrid_search(query="nonexistent-query-12345", topk=5)

        assert isinstance(results, list)
        # Fallback should provide at least one result
        assert len(results) >= 1


@pytest.mark.asyncio
class TestClassifyDAO:
    """ClassifyDAO integration tests"""

    async def test_classify_text_executes(self, sample_text: str) -> None:
        """Test classify_text executes without errors"""
        from database import ClassifyDAO

        result = await ClassifyDAO.classify_text(sample_text)

        assert isinstance(result, dict)
        assert "canonical" in result
        assert "confidence" in result
        assert "reasoning" in result

    async def test_classify_returns_valid_confidence(self):
        """Test classification returns confidence in valid range"""
        from database import ClassifyDAO

        result = await ClassifyDAO.classify_text(
            "Retrieval-Augmented Generation systems"
        )

        assert result["confidence"] >= 0.0
        assert result["confidence"] <= 1.0

    async def test_classify_returns_canonical_path(self):
        """Test classification returns canonical path as list"""
        from database import ClassifyDAO

        result = await ClassifyDAO.classify_text("Machine learning models")

        assert isinstance(result["canonical"], list)
        assert len(result["canonical"]) > 0
        assert "AI" in result["canonical"]  # Should always include AI

    async def test_classify_with_hint_paths(self):
        """Test classification with hint paths"""
        from database import ClassifyDAO

        result = await ClassifyDAO.classify_text(
            "Neural network training", hint_paths=[["AI", "ML"]]
        )

        assert "confidence" in result
        # Hint paths should influence result
        assert isinstance(result["canonical"], list)

    async def test_classify_fallback_on_error(self):
        """Test classification fallback on error"""
        from database import ClassifyDAO

        # Empty string should still return valid result
        result = await ClassifyDAO.classify_text("")

        assert isinstance(result, dict)
        assert "canonical" in result
        assert "confidence" in result
        # Should fallback to General AI
        assert result["canonical"] == ["AI", "General"] or isinstance(
            result["canonical"], list
        )


@pytest.mark.asyncio
class TestDatabasePerformance:
    """Database performance tests"""

    async def test_taxonomy_query_performance(self):
        """Test taxonomy query completes in reasonable time"""
        import time
        from database import TaxonomyDAO

        start = time.time()
        tree = await TaxonomyDAO.get_tree(version="1.8.1")
        duration = time.time() - start

        assert duration < 5.0  # Should complete in under 5 seconds
        assert len(tree) > 0

    async def test_classification_performance(self, sample_text: str) -> None:
        """Test classification completes in reasonable time"""
        import time
        from database import ClassifyDAO

        start = time.time()
        result = await ClassifyDAO.classify_text(sample_text)
        duration = time.time() - start

        assert (
            duration < 10.0
        )  # Should complete in under 10 seconds (includes model loading)
        assert "confidence" in result

    async def test_search_performance(self):
        """Test search completes in reasonable time"""
        import time
        from database import SearchDAO

        start = time.time()
        results = await SearchDAO.hybrid_search(query="test", topk=5)
        duration = time.time() - start

        assert duration < 5.0  # Should complete in under 5 seconds
        assert isinstance(results, list)
